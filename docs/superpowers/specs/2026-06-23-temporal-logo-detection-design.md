# Design: Smart Logo Detection via Temporal Stability

**Feature Branch**: `003-temporal-logo-detection`
**Created**: 2026-06-23
**Status**: Approved (pending spec review)
**Supersedes**: Improves on detection in `002-executable-ai-delogo` (does not remove it)

## Context

The existing logo detector (`src/logo_detector.py`) uses Canny edge detection. The user reports that **detection is unreliable**, specifically producing **too many false positives** (junk boxes on text overlays, busy scenes, faces, etc.). Edge density is a poor confidence signal because high-contrast edges exist everywhere in video.

This design replaces the default detection algorithm with **temporal stability analysis** — a classical, proven technique for static-watermark detection that directly eliminates the root cause of false positives.

## Goals & Non-Goals

### Goals

- Detect **static corner logos** with high precision (target: ≤5% false-positive rate on typical TV episode content)
- **Zero operating cost** — no paid APIs, no account/setup required, no API keys
- **No new heavy dependencies** — uses existing OpenCV + NumPy
- **Batch workflow** — detect once on a representative file, apply coordinates to all files in the batch
- **Backward compatible** — existing edge-based detector preserved as a legacy option

### Non-Goals

- Detecting moving, animated, or intermittent logos
- Per-video detection inside a batch (we detect once on the representative file)
- Improving the removal step (FFmpeg `delogo` filter remains — detection is the pain)
- Cloud-based LLM semantic check (can be added later as an optional layer without redesign)
- Replacing the existing Google Cloud Vision backend (kept as-is for users who already use it)

## Algorithm (Core Insight)

**Logos don't move.** Across many frames of a video, logo pixels stay nearly identical while everything else (action, scene cuts, characters, subtitles that come and go) changes dramatically. By computing per-pixel variance over a sample of frames, we isolate the static overlay layer.

| Old (Canny edges) | New (Temporal stability) |
|---|---|
| Fires on text overlays | Text comes/goes → high variance → rejected |
| Fires on busy scene edges | Action changes → high variance → rejected |
| Fires on faces/hair | Faces move → high variance → rejected |
| Misses faint logos | Faint-but-static logos still have low variance → detected |
| Confidence = edge density (noisy) | Confidence = stability score (semantically meaningful) |

A region that is **static + corner-positioned + correctly-sized** is almost never not a watermark — so the false-positive rate collapses.

## Algorithm Pipeline

1. **Sample N frames** (default 15) evenly spaced across the video duration, skipping the first/last 2% (avoids intro/outro fades and black buffers)
2. **Convert to grayscale** + optional downscale (max height 720, for speed — matches existing `detection_scale_max_height`)
3. **Stack frames** into a 3D NumPy array of shape `(N, H, W)`
4. **Compute per-pixel variance** across the time axis: `np.var(frames, axis=0)`
5. **Threshold** the variance map → binary mask of low-variance (static) pixels. Threshold is derived from the **existing** `DetectionConfig.sensitivity` field (0.0–1.0) so users have one familiar control. Higher `sensitivity` → lower variance threshold → more candidates reported. Exact mapping is defined in the implementation plan.
6. **Morphological cleanup**: dilate to merge fragmented logo pixels, then close small holes
7. **Find contours** on the cleaned mask → bounding rectangles
8. **Filter** each candidate by the existing criteria (no changes needed):
   - Size (`min_logo_width/height` … `max_logo_width/height`)
   - Aspect ratio (`aspect_ratio_min` / `aspect_ratio_max`)
   - Corner position (`position_zones`)
9. **Score** each surviving candidate (concrete weights defined in the implementation plan):
   - **Stability** (primary, ~70% weight): inverse of mean variance inside the box — lower variance = higher score
   - **Corner bonus** (~20% weight): closer to the configured corner zone center = small boost
   - **Size fit** (~10% weight): closer to the midpoint of the allowed size range = small boost
10. **Cluster** candidates (reuse existing `_cluster_detections` / IoU logic) and return the top-N sorted by score

## Components

### New module: `src/logo_detector_temporal.py`

Public class implementing the same interface as the existing `LogoDetector`:

```python
class TemporalLogoDetector:
    def __init__(self, config: DetectionConfig): ...
    def detect_in_video(
        self,
        video_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> DetectionSession: ...
```

Internal methods (private):

- `_sample_frames(cap, total_frames) -> List[np.ndarray]` — evenly-spaced frame indices, skipping intro/outro, returns grayscale (optionally downscaled) frames
- `_compute_variance_map(frames) -> np.ndarray` — `np.var` over the time axis
- `_threshold_variance_map(variance_map) -> np.ndarray` — converts `sensitivity` (0–1) into a variance threshold; returns binary mask
- `_cleanup_mask(mask) -> np.ndarray` — morphological dilate + close
- `_find_candidates(mask, video_resolution) -> List[Rect]` — contours → bounding rectangles
- `_score_candidate(rect, variance_map, video_resolution) -> float` — stability + corner + size blend

Reuse from the existing detector (do not duplicate):

- `DetectionSession`, `DetectionResult`, `DetectionConfig` (extended — see below)
- `_cluster_detections`, `_calculate_overlap`, `_merge_cluster` (move to a shared helper or import from `logo_detector.py`)
- Exception classes from `src/exceptions.py` (`VideoReadError`, `DetectionFailedError`, `DetectionCancelledError`)

### Extend `DetectionConfig` (in `src/data_models.py`)

Add new fields with defaults so existing saved profiles continue to load:

```python
# Temporal stability parameters
temporal_num_frames: int = 15
temporal_variance_threshold: float = 0.005   # pixels with var < this are "static"
temporal_skip_intro_frac: float = 0.02       # skip first 2% of video
temporal_skip_outro_frac: float = 0.02       # skip last 2%
temporal_min_region_pixels: int = 200        # filter tiny stable blobs (noise)
```

Also extend `validate()` with appropriate bounds checks.

### Detection method dropdown (in `src/ui/batch_processor.py`)

The dropdown already exists. Add a new entry and re-order:

1. **"Temporal Stability (recommended)"** → new default
2. **"OpenCV Edges (legacy)"** → existing detector
3. **"Google Cloud Vision (AI)"** → existing, shown only when available

The detection method choice is persisted in the saved detection profile.

## Batch Workflow (matches user requirement: detect once, apply to all)

```
[Load batch of files]
        ↓
[Click "Detect Logo"]
        ↓
[Uses FIRST selected file as the representative sample]
        ↓
[TemporalLogoDetector.detect_in_video()]
        ├─ sample 15 frames (skip intro/outro)
        ├─ compute variance map
        ├─ threshold → binary mask
        ├─ morphological cleanup
        ├─ contours → candidate rectangles
        ├─ filter (size, aspect, corner position)
        └─ score by stability
        ↓
[Show candidates in UI with bounding-box overlays + "Stability: 94%" labels]
        ↓
[User accepts one (or none) ]
        ↓
[Coordinates populate delogo_params (X/Y/W/H)]
        ↓
[All files in batch use those coords — existing flow, no changes]
        ↓
[Process batch]
```

Rationale for "first selected file" as representative: in TV series batches, the logo position is consistent across episodes. Detecting on every file would waste time and produce inconsistent results. The user can always re-run detection on a different file if the first is atypical.

## UI Changes (`src/ui/batch_processor.py`)

- **Detection method dropdown** (3 options as above)
- **Variance-map preview**: alongside the existing frame preview, show the thresholded variance map so the user can visually confirm "yes, that region is stable = logo." This builds trust in the new algorithm.
- **Confidence relabel**: candidates show **"Stability: 94%"** instead of generic "Confidence: 94%"

No new UI infrastructure — both previews render into the existing detection-results panel.

## Data Flow

Same as today, with the temporal detector substituted in:

```
batch_processor.py (UI)
   → dispatches on detection_method
   → TemporalLogoDetector.detect_in_video() OR LogoDetector.detect_in_video() OR VisionLogoDetector
   → returns DetectionSession
   → UI shows results
   → on accept, sets state.delogo_params
   → video_processor.py reads state.delogo_params at processing time
```

## Error Handling

| Condition | Behavior |
|---|---|
| Video cannot be opened | Raise `VideoReadError` (existing) |
| Video has < 5 frames available | Use what's available, log a warning to UI |
| Variance map is uniformly zero (degenerate input) | Return empty result + UI message: "No stable regions found — lower sensitivity or check if a corner logo exists" |
| No candidates pass filters | UI message: "No logos detected. Try lower sensitivity or enter coords manually" |
| User cancels | Raise `DetectionCancelledError` (existing) |
| All candidates rejected by user | Fall back to manual coordinate entry (current behavior, unchanged) |
| Sampling fails partway (corrupt frame) | Skip the corrupt frame, continue with remaining samples as long as ≥5 valid frames remain |

## Testing Strategy

### Unit tests — `tests/unit/test_temporal_detector.py`

Test against **synthetic frame stacks** built with NumPy (no real video files needed):

- `_sample_frames` returns N evenly-spaced frame indices, skipping intro/outro window
- `_compute_variance_map` produces an array of shape `(H, W)` for an input stack of shape `(N, H, W)`
- `_threshold_variance_map` correctly binarizes at the threshold derived from `sensitivity`
- `_cleanup_mask` removes blobs smaller than `temporal_min_region_pixels`
- `_score_candidate` rewards low-variance regions and penalizes off-corner positions

Synthetic end-to-end cases (no video file):

- **Positive**: build a stack of 15 frames where a fixed rectangle in the top-right corner has identical pixels across all frames, and the rest of each frame is random noise → detector returns exactly one candidate inside that rectangle
- **Negative**: build a stack of 15 frames that are entirely random noise (no static regions) → detector returns no candidates
- **Distractor**: build a stack with a static rectangle (the "logo") **and** a flickering text-overlay region (visible in ~30% of frames) → detector returns only the static rectangle, not the flickering text
- **Sensitivity sweep**: as `sensitivity` decreases, more candidates are reported (sanity check on threshold derivation)

### Integration tests — `tests/integration/test_temporal_detection.py`

Generate a real test video with FFmpeg: take a base video (or a generated color-bar/noise video) and overlay a static rectangle via `drawbox` or `drawtext`. Run `TemporalLogoDetector.detect_in_video()` on it and assert:

- At least one candidate is returned
- The top candidate's bounding box overlaps the known overlay rectangle (IoU ≥ 0.5)
- The top candidate's confidence (`stability` score) is ≥ 0.7

Integration tests are skipped automatically if FFmpeg is not on PATH.

### Backward compatibility tests

- Existing `tests/test_logo_detector.py` (for the legacy detector) must still pass unchanged
- An existing saved detection profile (JSON without the new temporal fields) must load successfully and use default values for the new fields

## Backward Compatibility

- **Old `LogoDetector`** (`src/logo_detector.py`) is **kept** and selectable as "OpenCV Edges (legacy)" — not deleted
- **`DetectionConfig`** gains new fields with defaults → existing serialized profiles still load (new fields auto-populated on read)
- **Detection method dropdown** defaults to **Temporal Stability** for fresh installs, but users with a saved profile retain whatever method was saved
- **`DetectionProfile`** JSON format unchanged in shape — just gains optional keys (forward-compatible)

## Dependencies

- **No new third-party dependencies.** NumPy and OpenCV (`cv2`) are already in `requirements.txt`
- No changes to PyInstaller spec file needed
- No changes to the executable build process

## Files Touched

| File | Change |
|---|---|
| `src/logo_detector_temporal.py` | **NEW** — `TemporalLogoDetector` class and helpers |
| `src/data_models.py` | Extend `DetectionConfig` with temporal fields + update `validate()` |
| `src/ui/batch_processor.py` | Add detection-method dropdown entry; dispatch to new detector; add variance-map preview; relabel confidence |
| `tests/unit/test_temporal_detector.py` | **NEW** — unit tests with synthetic frame stacks |
| `tests/integration/test_temporal_detection.py` | **NEW** — end-to-end test on an ffmpeg-generated video |
| `requirements.txt` | No change |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Temporal variance needs enough frames to be statistically meaningful; using too few causes noisy mask | High | Default to 15 frames (validated empirically via synthetic tests); minimum 5 enforced with warning |
| Letterbox bars (top/bottom black bars) are also static and could be detected as "logos" | Medium | Existing size + aspect-ratio + corner-position filters reject bars (bars span the full width, far outside `max_logo_width`) |
| Videos with very few scene changes (e.g., static interviews) may have many "stable" regions | Medium | Corner-position filter narrows the search; stability score ranks candidates so the best one floats to the top |
| Memory: holding 15 grayscale 720p frames is ~15 × 720 × 1280 ≈ 14 MB — trivial | Low | No mitigation needed |
| User has existing saved profiles pointing to "OpenCV Edges" | Low | Backward-compat path — dropdown preserves their choice |
| Hard-failed detection on unusual content | Low | Three fallback layers: (1) lower sensitivity, (2) switch method to legacy, (3) manual coordinate entry |

## Success Criteria

- **SC-001**: On a test batch of TV episodes with known corner watermarks, temporal-stability detection reports ≤1 false-positive box per video on average (compared to current 3–5+)
- **SC-002**: The top-ranked candidate overlaps the true logo rectangle with IoU ≥ 0.5 in ≥90% of test cases
- **SC-003**: Detection completes in ≤10 seconds for a typical 1-hour episode (15 sampled frames, downscaled)
- **SC-004**: Zero new third-party dependencies added to `requirements.txt`
- **SC-005**: Existing saved detection profiles continue to load without error
- **SC-006**: Existing unit tests for the legacy detector continue to pass unchanged

## Out of Scope (Deferred)

- LLM / Gemini-free-tier semantic check — can be added later as an optional layer
- Moving, animated, or intermittent logo tracking
- Better removal than FFmpeg `delogo` (inpainting, content-aware fill)
- Per-video detection inside a single batch
- Auto-retraining / learning from user accept/reject decisions
