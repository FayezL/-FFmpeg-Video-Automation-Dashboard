# New Cut Options: Split + Timestamp Markers

**Date:** 2026-07-23
**Status:** Approved
**Replaces:** Percent and Frames cut units

## Problem

The current cut-unit dropdown offers three options: **Time**, **Percent**, and **Frames**. Percent and Frames see little real-world use and add complexity. The user wants to replace them with two more practical options: **Split** (divide a video into N equal parts) and **Markers** (cut by typing start/end timestamps directly).

## Design

The unit dropdown changes from `Time / Percent / Frames` to **`Time / Split / Markers`**. Time mode is unchanged.

### Mode 1: TIME (unchanged)

Keep exactly as-is — checkbox "Remove from START" + h/m/s fields, checkbox "Remove from END" + h/m/s fields. One input → one output.

### Mode 2: MARKERS (replaces Percent)

User types two text timestamps directly:

- **Start:** `00:01:30` (HH:MM:SS format)
- **End:** `00:45:00` (leave blank for "to end")

The video is cut to that exact range. Parsing accepts:
- `HH:MM:SS` or `HH:MM:SS.cs`
- `MM:SS`
- Plain seconds (`90`)

One input → one output. Simpler and more direct than h/m/s spinboxes for users who already know the timestamps.

**State fields:**
- `cut_markers_start: str = "00:00:00"`
- `cut_markers_end: str = ""` (empty = to end)

### Mode 3: SPLIT (replaces Frames)

User enters **Number of parts: [N]**. The workflow is:

1. Start/end trim is applied first using the existing TIME h/m/s fields (skip intro / cut outro still available in the time rows above).
2. The remaining video is divided into N equal segments.
3. Each segment becomes a separate output file with a `_part{i}` suffix: `video_part1.mp4`, `video_part2.mp4`, etc.

This is the biggest change — **one input → N output files**. The video processor runs FFmpeg N times per file, each with the right `-ss`/`-t` flags for its segment.

**State fields:**
- `split_parts: int = 2`

**Output naming:** `{prefix}{base_name}_part{i}{suffix}.{ext}` where i is 1-indexed and zero-padded to match the number of digits in N (e.g., part01..part10 for 10 parts).

## Architecture Changes

### `src/state.py`

1. **CutUnit enum** — replace `PERCENT` and `FRAMES` with `SPLIT` and `MARKERS`:
   ```python
   class CutUnit(Enum):
       TIME = "time"
       SPLIT = "split"
       MARKERS = "markers"
   ```

2. **Remove** percent/frame fields:
   - `cut_amount_percent`, `cut_start_percent`, `cut_end_percent`
   - `cut_amount_frames`, `cut_start_frame`, `cut_end_frame`

3. **Add** new fields:
   - `cut_markers_start: str = "00:00:00"`
   - `cut_markers_end: str = ""`
   - `split_parts: int = 2`

### `src/video_processor.py`

1. **Remove** `convert_cut_value_to_seconds()` — no longer needed (was for percent/frame conversion).

2. **Add** `parse_timestamp(ts: str) -> float`:
   - Parses `HH:MM:SS`, `MM:SS`, or plain seconds strings to float seconds.
   - Raises `ValueError` on invalid format.

3. **Update** `process_video()`:
   - If `cut_unit == MARKERS`: parse `cut_markers_start` and `cut_markers_end` to get start_time/end_time.
   - If `cut_unit == SPLIT`: compute start_time/end_time from the existing TIME trim fields, then loop N times calling `_process_with_subprocess()` for each segment. Each call gets adjusted `-ss`/`-t` values and a `_part{i}` output path.
   - Remove the `_compute_cut_from_unit()` method (was for percent/frame).

4. **Update** `_get_output_path()` — add optional `part_index` and `part_total` parameters for split-mode suffixes.

### `src/ui/batch_processor.py`

1. **Unit dropdown** values: `["time", "split", "markers"]`.

2. **Replace** percent/frame input rows with:
   - **Markers rows** (`_markers_rows_frame`): two `CTkEntry` fields for start/end timestamps with `HH:MM:SS` placeholder labels.
   - **Split rows** (`_split_rows_frame`): a single `CTkEntry` for "Number of parts" + keep the time trim rows visible above (since trim-then-split applies).

3. **Update** `_sync_unit_visibility()` to show/hide the three frames.

4. **Remove** `_on_percent_trim_change()`, `_on_frame_trim_change()`, and related percent/frame widget references.

5. **Add** `_on_markers_change()` and `_on_split_change()` to sync UI → state.

### Tests

- **Remove** `tests/test_cut_units.py` content (tests percent/frame conversion).
- **Add** `tests/test_timestamp_parser.py` — tests for `parse_timestamp()`.
- **Add** `tests/test_split_mode.py` — unit tests for split logic (segment calculation, output naming).
- **Update** `tests/integration/test_cut_units_processing.py` — replace percent/frame integration tests with markers/split integration tests on real FFmpeg output.

## Data Flow

### MARKERS mode
```
User types "00:01:30" → "00:45:00"
  → parse_timestamp("00:01:30") = 90.0
  → parse_timestamp("00:45:00") = 2700.0
  → FFmpeg: ffmpeg -ss 90 -t 2610 -i input.mp4 ... output.mp4
```

### SPLIT mode
```
Video is 3600s. User set parts=4. Trim: skip first 60s.
  → effective_start = 60.0
  → effective_end = 3600.0
  → segment_duration = (3600 - 60) / 4 = 885.0s
  → Part 1: ffmpeg -ss 60    -t 885 -i input.mp4 ... output_part1.mp4
  → Part 2: ffmpeg -ss 945   -t 885 -i input.mp4 ... output_part2.mp4
  → Part 3: ffmpeg -ss 1830  -t 885 -i input.mp4 ... output_part3.mp4
  → Part 4: ffmpeg -ss 2715  -t 885 -i input.mp4 ... output_part4.mp4
```

## Migration / Backward Compatibility

- Existing saved templates referencing `percent` or `frames` units will fail to load (enum value not found). This is acceptable — templates are user-managed JSON and the old units are being removed intentionally.
- The `cut_unit` defaults to `TIME`, so no behavior changes unless the user explicitly selects the new modes.
