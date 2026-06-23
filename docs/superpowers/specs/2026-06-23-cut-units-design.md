# Design: Multiple Cut Units (Time / Percent / Frames)

**Feature Branch**: `004-cut-units`
**Created**: 2026-06-23
**Status**: Approved (pending spec review)

## Context

The app currently supports 4 trim modes (NONE, CUT_FIRST, CUT_LAST, CUT_RANGE) but only with **time-based** input (HH:MM:SS). The user wants to specify cuts using two additional units:

- **Percentage of total duration** — "remove last 5%" adapts to each file's length in a batch
- **Frame numbers** — frame-accurate cuts for precise editing

This is especially useful for batch processing where files have different durations but the same relative structure (e.g., all episodes have a 5% intro and a 3% outro).

## Goals & Non-Goals

### Goals

- Add **PERCENT** and **FRAMES** as alternative input units for the existing cut modes
- All three cut operations (CUT_FIRST, CUT_LAST, CUT_RANGE) work in all three units
- Percentage and frame values **convert at processing time** so one setting adapts to different-length files in a batch
- **Backward compatible** — existing time-based configs and profiles default to `TIME` unit unchanged

### Non-Goals

- Chapter-marker cuts (requires reading MKV/MP4 chapter metadata)
- Silence/ad-break detection (requires audio analysis)
- SPLIT mode (produces multiple output files — different feature)
- Mixing units within a single cut (e.g., start at frame 100, end at 90%)
- Multiple cuts per video (each video still gets one cut operation)
- Changing the underlying ffmpeg invocation (`-ss` / `-t` with seconds remains the universal internal format)

## Core Concept

Two orthogonal selectors in the UI:

- **Mode** (existing): what the cut does — NONE, CUT_FIRST, CUT_LAST, CUT_RANGE
- **Unit** (new): how values are expressed — TIME, PERCENT, FRAMES

The input fields adapt to both selections. The processor converts percent/frames to seconds **after probing each file**.

## Data Model (`src/state.py`)

### New enum

```python
class CutUnit(Enum):
    TIME = "time"
    PERCENT = "percent"
    FRAMES = "frames"
```

### New AppState fields

```python
# Unit selector (applies to all cut modes)
self.cut_unit: CutUnit = CutUnit.TIME

# Amount fields for CUT_FIRST / CUT_LAST (single value)
self.cut_amount_percent: float = 5.0       # e.g. 5 means "5%"
self.cut_amount_frames: int = 0

# Range fields for CUT_RANGE (start + end pair)
self.cut_start_percent: float = 0.0
self.cut_end_percent: Optional[float] = None   # None = to end
self.cut_start_frame: int = 0
self.cut_end_frame: Optional[int] = None       # None = to end
```

Existing time-based fields (`cut_hours`, `cut_minutes`, `cut_seconds`, `cut_start_hours_range`, `cut_end_hours`, etc.) are preserved unchanged.

## Conversion Logic (`src/video_processor.py`)

After probing the video (existing `probe_video()` already returns `duration`, `width`, `height`; we'll add `fps` to the return value), convert the unit-specific input to seconds:

| Unit | Formula | Example |
|---|---|---|
| TIME | value is already seconds | 90s → 90s |
| PERCENT | `duration * (value / 100)` | 5% of 7200s → 360s |
| FRAMES | `value / fps` | frame 720 at 24fps → 30s |

### Clamping & validation

- Percentage values are clamped to `[0, 100]` before conversion
- Frame values are clamped to `[0, total_frames]` when total frames can be derived (`duration * fps`)
- `None` end values (percent or frames) translate to "full duration"

### Conversion function (pure, unit-testable)

```python
def convert_cut_value_to_seconds(
    value: float,
    unit: CutUnit,
    video_duration: float,
    video_fps: float,
) -> float:
    if unit == CutUnit.TIME:
        return max(0.0, value)
    if unit == CutUnit.PERCENT:
        clamped = max(0.0, min(100.0, value))
        return video_duration * (clamped / 100.0)
    if unit == CutUnit.FRAMES:
        if video_fps <= 0:
            raise ValueError("Cannot use frame-based cut: video FPS is unknown or zero")
        return value / video_fps
    raise ValueError(f"Unknown unit: {unit}")
```

### Integration into `process_video`

The existing `process_video` method already computes `start_time` and `end_time` from AppState fields. We add a unit-aware conversion step **after** probing and **before** computing start/end:

1. Probe video → get `duration` and `fps`
2. Read the active unit from `state.cut_unit`
3. Branch on mode + unit to compute `start_time` and `end_time`:
   - **CUT_FIRST**: `start_time = convert(cut_amount, unit, duration, fps)`; `end_time = duration`
   - **CUT_LAST**: `start_time = 0`; `end_time = duration - convert(cut_amount, unit, duration, fps)`
   - **CUT_RANGE**: `start_time = convert(cut_start, unit, duration, fps)`; `end_time = convert(cut_end_or_None, unit, duration, fps) or duration`
4. Existing ffmpeg call (`-ss start -t duration`) runs unchanged

Time-unit behavior is identical to today (conversion is a no-op).

### Per-file overrides

`ProcessingFile.use_custom_cut`, `custom_cut_start_seconds`, `custom_cut_end_seconds` remain in **seconds**. Percent/frame conversion happens at the global AppState level only. Per-file overrides bypass the unit entirely (they're already in seconds).

## UI Changes (`src/ui/batch_processor.py`)

Add a **Unit dropdown** next to the existing Mode dropdown. The two are independent selectors.

### Field visibility matrix

| Mode \ Unit | TIME | PERCENT | FRAMES |
|---|---|---|---|
| NONE | (no fields) | (no fields) | (no fields) |
| CUT_FIRST | HH:MM:SS | one 0–100 number | one int field |
| CUT_LAST | HH:MM:SS | one 0–100 number | one int field |
| CUT_RANGE | start HH:MM:SS + end HH:MM:SS | start% + end% | start-frame + end-frame |

Only one set of fields is visible at a time. Switching unit or mode swaps the visible fields.

### Layout

The existing cut section in `batch_processor.py` has a mode dropdown followed by conditional input rows. We add the unit dropdown on the same row as (or immediately below) the mode dropdown, then the input fields adapt based on the selected combination.

## Processing Flow (batch-friendly)

```
User sets: Mode=CUT_LAST, Unit=PERCENT, Value=5.0
    ↓
Adds 30 files, clicks Process
    ↓
For EACH file:
    1. Probe → get duration + fps
    2. Convert: 5% of THIS file's duration → seconds (e.g. 5% of 7200s = 360s)
    3. Apply: start=0, end=7200 - 360 = 6840
    4. ffmpeg -ss 0 -t 6840 ...
```

A 30-minute episode loses 1.5 minutes; a 60-minute episode loses 3 minutes — same 5% setting, correct per-file behavior.

## Error Handling

| Condition | Behavior |
|---|---|
| FPS is 0 / unknown + FRAMES unit | Raise `ValueError("Cannot use frame-based cut: video FPS is unknown or zero")` — surfaced as file-level error in the batch |
| Duration is 0 / unknown + PERCENT unit | Treat as 0-second output (same as today's behavior for unknown duration) |
| Percentage > 100 | Clamp to 100 |
| Percentage < 0 | Clamp to 0 |
| Frame number exceeds total frames | Clamp to total frames (`duration * fps`) when derivable; otherwise apply as-is and let ffmpeg clamp |
| `cut_end_percent = None` / `cut_end_frame = None` | End = full duration |

## Testing Strategy

### Unit tests — `tests/test_cut_units.py`

Pure conversion tests (no video files needed):

- `convert_cut_value_to_seconds(90, TIME, ...)` → 90
- `convert_cut_value_to_seconds(5, PERCENT, duration=7200, fps=24)` → 360
- `convert_cut_value_to_seconds(10, PERCENT, duration=60, fps=30)` → 6
- `convert_cut_value_to_seconds(720, FRAMES, duration=..., fps=24)` → 30
- `convert_cut_value_to_seconds(0, FRAMES, ...)` → 0
- Frame at 0 fps raises `ValueError`
- Percentage > 100 clamps to 100 → `duration * 1.0`
- Percentage < 0 clamps to 0 → 0
- Negative time clamps to 0
- Unknown unit raises `ValueError`
- `CutUnit` enum exists with TIME/PERCENT/FRAMES values
- Default `cut_unit` on AppState is `CutUnit.TIME` (backward compat)

### Integration tests — `tests/integration/test_cut_units.py`

Generated test videos via ffmpeg (skipped if ffmpeg not on PATH):

- 10-second test video, `CUT_LAST` + `PERCENT(50)` → output ~5 seconds
- 10-second test video @ 30 fps, `CUT_FIRST` + `FRAMES(60)` → output starts at ~2 seconds (output ~8 seconds)
- `CUT_RANGE` + `PERCENT(20, 80)` on 10s video → output is the middle 6 seconds (2s to 8s)

### Regression coverage

Existing `tests/test_trim_modes.py` must continue to pass unchanged (the default `TIME` unit preserves current behavior).

## Backward Compatibility

- `cut_unit` defaults to `CutUnit.TIME` → existing configs, profiles, and UI behavior unchanged
- All existing time-based AppState fields preserved
- Per-file overrides remain in seconds (unit-agnostic)
- No saved-config migration needed — old configs without `cut_unit` load with the TIME default
- The mode dropdown still shows the same 4 modes first

## Dependencies

- **No new third-party dependencies.** Reuses existing ffprobe/ffmpeg calls.
- No changes to PyInstaller spec or executable build process.

## Files Touched

| File | Change |
|---|---|
| `src/state.py` | `CutUnit` enum + new AppState fields for percent/frame inputs |
| `src/video_processor.py` | Add `fps` to `probe_video` output; add `convert_cut_value_to_seconds` function; integrate conversion into `process_video` |
| `src/ui/batch_processor.py` | Unit dropdown + adaptive input fields (show/hide based on mode × unit) |
| `tests/test_cut_units.py` | NEW — conversion, clamping, and enum tests |
| `tests/integration/test_cut_units.py` | NEW — end-to-end tests on generated videos |
| `tests/test_trim_modes.py` | Verify existing time-based modes still pass with new `cut_unit` field present |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| FPS detection returns 0 for some codecs + user picks FRAMES | High | Explicit error message; UI could disable FRAMES unit when fps is unknown, but simpler to surface as file-level error |
| UI gets cluttered with 3 units × 4 modes | Medium | Only one input set visible at a time; unit dropdown is a single line addition |
| Percent values behave unexpectedly across very short clips (e.g., 5% of 3s = 0.15s) | Low | Expected behavior; user can switch to TIME or FRAMES for short clips |
| Existing trim tests break if AppState init changes | Low | Default `cut_unit=TIME` + existing fields preserved → no behavioral change |

## Success Criteria

- **SC-001**: User can select PERCENT or FRAMES from a Unit dropdown and enter cut values in that unit
- **SC-002**: A 5% CUT_LAST on a 7200s video produces a 6840s output (loses 360s)
- **SC-003**: A 60-frame CUT_FIRST at 30fps produces an output starting at exactly 2.0s
- **SC-004**: The same PERCENT setting produces different second-cuts on different-length files in one batch
- **SC-005**: All existing trim-mode tests pass unchanged
- **SC-006**: Default unit is TIME; existing configs load without modification

## Out of Scope (deferred)

- Chapter-marker cuts
- Silence / ad-break detection
- SPLIT mode (multiple output files from one input)
- Mixed-unit cuts (start in frames, end in percent)
- Multiple cuts per video
