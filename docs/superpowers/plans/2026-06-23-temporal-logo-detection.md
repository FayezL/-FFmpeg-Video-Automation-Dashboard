# Temporal Logo Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the default logo detection algorithm with temporal-stability analysis to eliminate false positives on static corner logos, with zero new dependencies and a "detect once, apply to batch" workflow.

**Architecture:** A new `TemporalLogoDetector` class samples 15 evenly-spaced frames from a video, computes per-pixel variance over time, thresholds the variance map to find static regions, then filters and scores candidates using existing size/position/aspect-ratio criteria. The new detector plugs into the existing detection-method dropdown in `batch_processor.py`. The legacy edge-based detector and Google Cloud Vision backend are preserved unchanged.

**Tech Stack:** Python 3.8+, OpenCV (`cv2`), NumPy, CustomTkinter, pytest. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-06-23-temporal-logo-detection-design.md`

---

## File Structure

**New files:**
- `src/logo_detection_utils.py` — pure helper functions (size/position filters, aspect-ratio check) shared between detectors. Module-level functions, no class state, easy to unit test.
- `src/logo_detector_temporal.py` — `TemporalLogoDetector` class implementing the temporal-stability algorithm.
- `tests/test_temporal_detector.py` — unit tests using synthetic NumPy frame stacks (no real video files needed).
- `tests/test_logo_detection_utils.py` — unit tests for shared helpers.
- `tests/integration/test_temporal_detection.py` — end-to-end test on an ffmpeg-generated video with a known static overlay.

**Modified files:**
- `src/data_models.py` — extend `DetectionConfig` with temporal parameters + update `validate()`.
- `src/ui/batch_processor.py` — add "Temporal Stability (recommended)" dropdown option, dispatch to the new detector, default to it, relabel result confidence as "Stability".

**Untouched (intentionally):**
- `src/logo_detector.py` — legacy detector kept as-is, selectable as "OpenCV Edges (legacy)".
- `src/logo_detector_vision.py` — Google Cloud Vision backend kept as-is.
- `requirements.txt` — no new dependencies.

---

## Conventions

- **Test runner:** `pytest` (already used throughout `tests/`)
- **Code style:** `ruff check .` must pass after each task (per `CLAUDE.md`)
- **Commit style:** Conventional commits — `feat:`, `test:`, `refactor:`, `docs:`
- **Python version:** 3.8+ (no `str | None` union syntax; use `Optional[str]`)
- **Tests location:** Unit tests flat in `tests/` (matches existing pattern), integration tests in `tests/integration/`

---

## Task 1: Extend `DetectionConfig` with temporal parameters

**Files:**
- Modify: `src/data_models.py:66-126` (the `DetectionConfig` dataclass)
- Test: `tests/test_logo_detector.py` (existing file — append new test class)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_logo_detector.py`, just before the final `test_detect_with_sample_video` function:

```python
class TestTemporalConfigFields:
    """Test the new temporal-stability fields on DetectionConfig"""

    def test_temporal_defaults(self):
        """New temporal fields should have sensible defaults"""
        config = DetectionConfig()
        assert config.temporal_num_frames == 15
        assert config.temporal_variance_threshold == 0.005
        assert config.temporal_skip_intro_frac == 0.02
        assert config.temporal_skip_outro_frac == 0.02
        assert config.temporal_min_region_pixels == 200

    def test_temporal_config_validates(self):
        """Default temporal config should pass validation"""
        config = DetectionConfig()
        assert config.validate()

    def test_temporal_num_frames_bounds(self):
        """temporal_num_frames must be between 3 and 60"""
        with pytest.raises(AssertionError, match="temporal_num_frames"):
            DetectionConfig(temporal_num_frames=2).validate()
        with pytest.raises(AssertionError, match="temporal_num_frames"):
            DetectionConfig(temporal_num_frames=61).validate()

    def test_temporal_threshold_bounds(self):
        """temporal_variance_threshold must be between 0 and 1"""
        with pytest.raises(AssertionError, match="temporal_variance_threshold"):
            DetectionConfig(temporal_variance_threshold=-0.01).validate()
        with pytest.raises(AssertionError, match="temporal_variance_threshold"):
            DetectionConfig(temporal_variance_threshold=1.5).validate()

    def test_temporal_skip_bounds(self):
        """Skip fractions must be between 0 and 0.5"""
        with pytest.raises(AssertionError, match="temporal_skip_intro_frac"):
            DetectionConfig(temporal_skip_intro_frac=0.6).validate()
        with pytest.raises(AssertionError, match="temporal_skip_outro_frac"):
            DetectionConfig(temporal_skip_outro_frac=-0.1).validate()

    def test_backward_compat_missing_temporal_fields(self):
        """Constructing DetectionConfig from old data (no temporal fields) should work"""
        old_data = {"sensitivity": 0.5, "frame_sampling": 30}
        config = DetectionConfig(**old_data)
        assert config.temporal_num_frames == 15
        assert config.validate()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_logo_detector.py::TestTemporalConfigFields -v`
Expected: 6 FAIL with `AttributeError` / `AssertionError` (fields don't exist yet, validation doesn't check them).

- [ ] **Step 3: Add the new fields to `DetectionConfig`**

In `src/data_models.py`, inside the `DetectionConfig` dataclass body, add these fields **after** `min_confidence_to_report: float = 0.35` (currently around line 108) and **before** `def validate(self)`:

```python
    # --- Temporal stability parameters (new default detector) ---
    # Number of evenly-spaced frames to sample across the video for variance analysis.
    temporal_num_frames: int = 15
    # Pixels with per-pixel variance below this value are considered "static" (part of a logo).
    # Range 0.0 - 1.0 (grayscale intensity variance). Lower threshold = stricter (fewer candidates).
    temporal_variance_threshold: float = 0.005
    # Skip the first/last X fraction of the video to avoid intro/outro fades and black buffers.
    temporal_skip_intro_frac: float = 0.02
    temporal_skip_outro_frac: float = 0.02
    # Discard candidate regions smaller than this many pixels (noise cleanup).
    temporal_min_region_pixels: int = 200
```

- [ ] **Step 4: Extend `validate()` with bounds checks for the new fields**

In `src/data_models.py`, inside `DetectionConfig.validate()`, add these assertions **before** `return True`:

```python
        assert 3 <= self.temporal_num_frames <= 60, "temporal_num_frames must be 3-60"
        assert 0.0 <= self.temporal_variance_threshold <= 1.0, "temporal_variance_threshold must be 0-1"
        assert 0.0 <= self.temporal_skip_intro_frac < 0.5, "temporal_skip_intro_frac must be 0 to <0.5"
        assert 0.0 <= self.temporal_skip_outro_frac < 0.5, "temporal_skip_outro_frac must be 0 to <0.5"
        assert self.temporal_min_region_pixels > 0, "temporal_min_region_pixels must be > 0"
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_logo_detector.py::TestTemporalConfigFields -v`
Expected: 6 PASS

Also run the existing config test to confirm no regressions:
Run: `pytest tests/test_logo_detector.py::TestDetectionConfig -v`
Expected: 3 PASS

- [ ] **Step 6: Lint**

Run: `ruff check src/data_models.py tests/test_logo_detector.py`
Expected: no errors

- [ ] **Step 7: Commit**

```bash
git add src/data_models.py tests/test_logo_detector.py
git commit -m "feat: add temporal-stability fields to DetectionConfig"
```

---

## Task 2: Create `logo_detection_utils.py` with shared filter helpers

**Why a shared module:** Both the legacy edge detector and the new temporal detector need to filter candidate rectangles by size, aspect ratio, and corner position. Putting these as module-level functions (with explicit parameters, no `self`) makes them reusable and unit-testable without instantiating a detector.

**Files:**
- Create: `src/logo_detection_utils.py`
- Test: `tests/test_logo_detection_utils.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_logo_detection_utils.py`:

```python
"""Unit tests for shared logo-detection filter helpers."""

import pytest

from src.logo_detection_utils import (
    passes_size_filter,
    passes_aspect_ratio_filter,
    passes_position_filter,
    Rect,
)


class TestPassesSizeFilter:
    def test_inside_range(self):
        assert passes_size_filter(100, 50, min_w=20, min_h=20, max_w=450, max_h=220) is True

    def test_too_narrow(self):
        assert passes_size_filter(10, 50, min_w=20, min_h=20, max_w=450, max_h=220) is False

    def test_too_wide(self):
        assert passes_size_filter(500, 50, min_w=20, min_h=20, max_w=450, max_h=220) is False

    def test_too_short(self):
        assert passes_size_filter(100, 10, min_w=20, min_h=20, max_w=450, max_h=220) is False

    def test_too_tall(self):
        assert passes_size_filter(100, 250, min_w=20, min_h=20, max_w=450, max_h=220) is False


class TestPassesAspectRatio:
    def test_inside_range(self):
        # aspect = 100/50 = 2.0
        assert passes_aspect_ratio_filter(100, 50, ar_min=0.5, ar_max=5.0) is True

    def test_too_narrow(self):
        # aspect = 20/100 = 0.2
        assert passes_aspect_ratio_filter(20, 100, ar_min=0.5, ar_max=5.0) is False

    def test_too_wide(self):
        # aspect = 600/100 = 6.0
        assert passes_aspect_ratio_filter(600, 100, ar_min=0.5, ar_max=5.0) is False

    def test_zero_height_safe(self):
        assert passes_aspect_ratio_filter(100, 0, ar_min=0.5, ar_max=5.0) is False


class TestPassesPositionFilter:
    def test_top_left_corner_passes(self):
        # 1920x1080 video, box centered at (100,100) → top-left quadrant
        assert passes_position_filter(
            Rect(x=75, y=75, w=50, h=50), video_resolution=(1920, 1080),
            position_zones=["top-left", "top-right", "bottom-left", "bottom-right"],
        ) is True

    def test_bottom_right_corner_passes(self):
        assert passes_position_filter(
            Rect(x=1700, y=900, w=150, h=150), video_resolution=(1920, 1080),
            position_zones=["top-left", "top-right", "bottom-left", "bottom-right"],
        ) is True

    def test_center_fails(self):
        assert passes_position_filter(
            Rect(x=900, y=500, w=50, h=50), video_resolution=(1920, 1080),
            position_zones=["top-left", "top-right", "bottom-left", "bottom-right"],
        ) is False

    def test_empty_zones_disables_filter(self):
        # Empty zone list = accept anything (filter disabled)
        assert passes_position_filter(
            Rect(x=900, y=500, w=50, h=50), video_resolution=(1920, 1080),
            position_zones=[],
        ) is True

    def test_only_top_left_enabled(self):
        # bottom-right box should fail when only top-left is enabled
        assert passes_position_filter(
            Rect(x=1700, y=900, w=50, h=50), video_resolution=(1920, 1080),
            position_zones=["top-left"],
        ) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_logo_detection_utils.py -v`
Expected: All FAIL with `ModuleNotFoundError: No module named 'src.logo_detection_utils'`

- [ ] **Step 3: Create the module**

Create `src/logo_detection_utils.py`:

```python
"""
Shared helpers for logo detection.

Pure functions for filtering candidate rectangles by size, aspect ratio, and
corner position. Used by both the legacy edge-based detector and the new
temporal-stability detector to avoid duplication.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Rect:
    """Immutable rectangle in pixel coordinates."""
    x: int
    y: int
    w: int
    h: int


def passes_size_filter(width: int, height: int,
                       min_w: int, min_h: int,
                       max_w: int, max_h: int) -> bool:
    """Return True if a rectangle's size is within the allowed logo range."""
    if width < min_w or width > max_w:
        return False
    if height < min_h or height > max_h:
        return False
    return True


def passes_aspect_ratio_filter(width: int, height: int,
                               ar_min: float, ar_max: float) -> bool:
    """Return True if width/height aspect ratio is within [ar_min, ar_max]."""
    if height <= 0:
        return False
    ar = width / height
    return ar_min <= ar <= ar_max


def passes_position_filter(rect: Rect,
                            video_resolution,
                            position_zones: List[str]) -> bool:
    """
    Return True if the rectangle's center is in one of the enabled corner zones.

    Corner zones are defined as the outer 25% of the frame on each axis:
      - left_threshold   = video_width  * 0.25
      - right_threshold  = video_width  * 0.75
      - top_threshold    = video_height * 0.25
      - bottom_threshold = video_height * 0.75

    Empty `position_zones` disables position filtering (returns True for any rect).
    """
    if not position_zones:
        return True

    video_width, video_height = video_resolution
    center_x = rect.x + rect.w / 2
    center_y = rect.y + rect.h / 2

    left_threshold = video_width * 0.25
    right_threshold = video_width * 0.75
    top_threshold = video_height * 0.25
    bottom_threshold = video_height * 0.75

    for zone in position_zones:
        if zone == "top-left" and center_x < left_threshold and center_y < top_threshold:
            return True
        if zone == "top-right" and center_x > right_threshold and center_y < top_threshold:
            return True
        if zone == "bottom-left" and center_x < left_threshold and center_y > bottom_threshold:
            return True
        if zone == "bottom-right" and center_x > right_threshold and center_y > bottom_threshold:
            return True
    return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_logo_detection_utils.py -v`
Expected: All PASS

- [ ] **Step 5: Lint**

Run: `ruff check src/logo_detection_utils.py tests/test_logo_detection_utils.py`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add src/logo_detection_utils.py tests/test_logo_detection_utils.py
git commit -m "feat: add shared logo-detection filter helpers"
```

---

## Task 3: Create `TemporalLogoDetector` module skeleton

**Files:**
- Create: `src/logo_detector_temporal.py`
- Test: `tests/test_temporal_detector.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_temporal_detector.py`:

```python
"""
Unit tests for the temporal-stability logo detector.

Most tests use synthetic NumPy frame stacks (no real video files needed).
The end-to-end `detect_in_video` test on a real video lives in
tests/integration/test_temporal_detection.py.
"""

import numpy as np
import pytest

from src.data_models import DetectionConfig
from src.logo_detector_temporal import TemporalLogoDetector


class TestTemporalLogoDetectorSkeleton:
    """Verify the class exists and has the expected interface."""

    def test_can_instantiate_with_config(self):
        config = DetectionConfig()
        detector = TemporalLogoDetector(config)
        assert detector.config is config

    def test_has_detect_in_video_method(self):
        detector = TemporalLogoDetector(DetectionConfig())
        assert callable(getattr(detector, "detect_in_video", None))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_temporal_detector.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.logo_detector_temporal'`

- [ ] **Step 3: Create the module skeleton**

Create `src/logo_detector_temporal.py`:

```python
"""
Logo detection using temporal stability analysis.

A logo is a static visual element: its pixels stay nearly identical across many
frames while the rest of the frame changes (action, scene cuts, subtitles that
come and go). By computing per-pixel variance over a sample of frames we isolate
the static overlay layer and find candidate logo rectangles.

This detector replaces the legacy edge-based detector as the default for static
corner logos. It produces far fewer false positives because high-contrast edges
in busy scenes are not stable over time and are therefore rejected.

No deep learning, no API calls, no third-party dependencies beyond OpenCV/NumPy.
"""

from typing import Callable, List, Optional, Tuple

import cv2
import numpy as np

from src.data_models import DetectionConfig, DetectionResult, DetectionSession
from src.exceptions import (
    DetectionCancelledError,
    DetectionFailedError,
    VideoReadError,
)
from src.logo_detection_utils import Rect


class TemporalLogoDetector:
    """
    Detects static logos by analyzing per-pixel temporal variance across
    sampled frames.
    """

    def __init__(self, config: DetectionConfig):
        self.config = config
        self._cancelled = False

    def detect_in_video(
        self,
        video_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> DetectionSession:
        """Detect static logo regions in a video file.

        Args:
            video_path: Path to the input video.
            progress_callback: Optional callback(progress_fraction, status_message).
            cancel_check: Optional callback() -> bool; return True to abort.

        Returns:
            DetectionSession containing all candidate logo regions.

        Raises:
            VideoReadError: If the video cannot be opened.
            DetectionFailedError: If detection fails unexpectedly.
            DetectionCancelledError: If the caller cancels via cancel_check.
        """
        raise NotImplementedError("Implemented in Task 10")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_temporal_detector.py -v`
Expected: 2 PASS

- [ ] **Step 5: Lint**

Run: `ruff check src/logo_detector_temporal.py tests/test_temporal_detector.py`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add src/logo_detector_temporal.py tests/test_temporal_detector.py
git commit -m "feat: add TemporalLogoDetector module skeleton"
```

---

## Task 4: Implement `_sample_frame_indices` (pure function)

**Why pure:** Sampling logic is math-only. Keeping it separate from video I/O makes it trivially testable with no video file.

**Files:**
- Modify: `src/logo_detector_temporal.py` (add static method + helper)
- Test: `tests/test_temporal_detector.py` (append new test class)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_temporal_detector.py`:

```python
class TestSampleFrameIndices:
    """Test the pure frame-index sampling logic."""

    def test_returns_correct_count(self):
        indices = TemporalLogoDetector._sample_frame_indices(
            total_frames=10000, num_frames=15,
            skip_intro_frac=0.02, skip_outro_frac=0.02,
        )
        assert len(indices) == 15

    def test_indices_within_valid_range(self):
        total = 10000
        indices = TemporalLogoDetector._sample_frame_indices(
            total_frames=total, num_frames=15,
            skip_intro_frac=0.02, skip_outro_frac=0.02,
        )
        # All indices must be in [0, total)
        for i in indices:
            assert 0 <= i < total

    def test_skips_intro_and_outro(self):
        total = 10000
        indices = TemporalLogoDetector._sample_frame_indices(
            total_frames=total, num_frames=15,
            skip_intro_frac=0.10, skip_outro_frac=0.10,
        )
        # Intro region is first 10% = frames 0-999; outro is last 10% = 9000-9999
        # Sampled indices must lie strictly within [1000, 9000)
        for i in indices:
            assert 1000 <= i < 9000, f"Index {i} falls inside skipped intro/outro region"

    def test_indices_are_evenly_spaced(self):
        total = 10000
        indices = TemporalLogoDetector._sample_frame_indices(
            total_frames=total, num_frames=5,
            skip_intro_frac=0.0, skip_outro_frac=0.0,
        )
        # With no skip and 5 frames over 10000, spacing should be ~2500
        diffs = [indices[i + 1] - indices[i] for i in range(len(indices) - 1)]
        assert all(2400 <= d <= 2600 for d in diffs), f"Uneven spacing: {diffs}"

    def test_returns_empty_when_total_below_minimum(self):
        # If a video has fewer frames than requested, return as many as possible
        indices = TemporalLogoDetector._sample_frame_indices(
            total_frames=3, num_frames=15,
            skip_intro_frac=0.0, skip_outro_frac=0.0,
        )
        assert indices == [0, 1, 2]

    def test_handles_total_zero(self):
        indices = TemporalLogoDetector._sample_frame_indices(
            total_frames=0, num_frames=15,
            skip_intro_frac=0.02, skip_outro_frac=0.02,
        )
        assert indices == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_temporal_detector.py::TestSampleFrameIndices -v`
Expected: All FAIL with `AttributeError` (method doesn't exist).

- [ ] **Step 3: Implement the method**

Add to `src/logo_detector_temporal.py`, inside the `TemporalLogoDetector` class (as the first method after `__init__`):

```python
    @staticmethod
    def _sample_frame_indices(
        total_frames: int,
        num_frames: int,
        skip_intro_frac: float,
        skip_outro_frac: float,
    ) -> List[int]:
        """Return evenly-spaced frame indices, skipping intro/outro regions.

        Args:
            total_frames: Total frame count of the video.
            num_frames: How many frames to sample.
            skip_intro_frac: Fraction of the video to skip at the start (0.0-0.5).
            skip_outro_frac: Fraction of the video to skip at the end (0.0-0.5).

        Returns:
            List of integer frame indices, evenly spaced within the allowed window.
            Returns fewer than `num_frames` if `total_frames` is small.
            Returns [] if `total_frames` is 0.
        """
        if total_frames <= 0:
            return []

        start = int(total_frames * skip_intro_frac)
        end = int(total_frames * (1.0 - skip_outro_frac))
        if end <= start:
            end = max(end, start + 1)
        if end > total_frames:
            end = total_frames

        window = end - start
        count = min(num_frames, window)
        if count <= 0:
            return []
        if count == 1:
            return [start + window // 2]

        step = (window - 1) / (count - 1)
        return [int(start + round(i * step)) for i in range(count)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_temporal_detector.py::TestSampleFrameIndices -v`
Expected: 6 PASS

- [ ] **Step 5: Lint**

Run: `ruff check src/logo_detector_temporal.py tests/test_temporal_detector.py`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add src/logo_detector_temporal.py tests/test_temporal_detector.py
git commit -m "feat: implement frame-index sampling for temporal detector"
```

---

## Task 5: Implement `_compute_variance_map` (pure function)

**Files:**
- Modify: `src/logo_detector_temporal.py`
- Test: `tests/test_temporal_detector.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_temporal_detector.py`:

```python
class TestComputeVarianceMap:
    """Test per-pixel temporal variance computation."""

    def test_identical_frames_have_zero_variance(self):
        # 10 identical 100x80 frames → variance is 0 everywhere
        frame = np.random.randint(0, 256, size=(80, 100), dtype=np.uint8)
        stack = np.stack([frame] * 10)
        var_map = TemporalLogoDetector._compute_variance_map(stack)
        assert var_map.shape == (80, 100)
        assert var_map.dtype == np.float32
        assert np.all(var_map == 0.0)

    def test_random_frames_have_positive_variance(self):
        # 10 different random frames → variance > 0 everywhere
        stack = np.stack([
            np.random.randint(0, 256, size=(80, 100), dtype=np.uint8)
            for _ in range(10)
        ])
        var_map = TemporalLogoDetector._compute_variance_map(stack)
        assert np.all(var_map > 0.0)

    def test_static_corner_low_variance_changing_elsewhere(self):
        # 10 frames: a 20x20 region in the top-right is identical; the rest is random
        h, w = 80, 100
        n = 10
        corner_w, corner_h = 20, 20
        corner_x, corner_y = w - corner_w, 0  # top-right

        frames = []
        for _ in range(n):
            f = np.random.randint(0, 256, size=(h, w), dtype=np.uint8)
            # Overwrite the corner with a fixed pattern (same across all frames)
            f[corner_y:corner_y + corner_h, corner_x:corner_x + corner_w] = 128
            frames.append(f)
        stack = np.stack(frames)

        var_map = TemporalLogoDetector._compute_variance_map(stack)

        corner_region = var_map[corner_y:corner_y + corner_h, corner_x:corner_x + corner_w]
        outside_region = var_map[:corner_h, :corner_x]  # top-left area (random)

        assert np.all(corner_region == 0.0)  # static corner has zero variance
        assert np.all(outside_region > 0.0)  # random area has positive variance

    def test_returns_empty_for_empty_stack(self):
        empty_stack = np.zeros((0, 80, 100), dtype=np.uint8)
        var_map = TemporalLogoDetector._compute_variance_map(empty_stack)
        assert var_map.shape == (80, 100)
        assert np.all(var_map == 0.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_temporal_detector.py::TestComputeVarianceMap -v`
Expected: All FAIL with `AttributeError`.

- [ ] **Step 3: Implement the method**

Add to `src/logo_detector_temporal.py`, inside the class:

```python
    @staticmethod
    def _compute_variance_map(frames_stack: np.ndarray) -> np.ndarray:
        """Compute per-pixel temporal variance across a stack of grayscale frames.

        Args:
            frames_stack: NumPy array of shape (N, H, W), dtype uint8 (grayscale).

        Returns:
            np.ndarray of shape (H, W), dtype float32 — per-pixel variance.
            For an empty stack (N=0), returns zeros of shape (H, W).
        """
        if frames_stack.shape[0] == 0:
            h, w = frames_stack.shape[1], frames_stack.shape[2]
            return np.zeros((h, w), dtype=np.float32)

        # Convert to float to avoid integer overflow in variance.
        frames_float = frames_stack.astype(np.float32)
        return np.var(frames_float, axis=0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_temporal_detector.py::TestComputeVarianceMap -v`
Expected: 4 PASS

- [ ] **Step 5: Lint**

Run: `ruff check src/logo_detector_temporal.py tests/test_temporal_detector.py`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add src/logo_detector_temporal.py tests/test_temporal_detector.py
git commit -m "feat: implement per-pixel variance computation"
```

---

## Task 6: Implement `_threshold_variance_map` (pure function)

The existing `sensitivity` field (0.0–1.0) is reused: higher sensitivity → higher variance threshold → more candidates (a pixel qualifies as "static" if its variance is below the threshold, so a higher threshold accepts more pixels).

**Mapping:** `effective_threshold = base * (0.1 + 0.9 * sensitivity)`. The 0.1 floor guarantees we still get *some* candidates at sensitivity=0.0 (only truly-static pixels), and the formula is monotonically increasing in sensitivity:
- sensitivity=0.0 → effective = `0.1 * base` (very strict — only variance ≈ 0 passes)
- sensitivity=0.5 → effective = `0.55 * base`
- sensitivity=1.0 → effective = `base` (loosest — accepts anything with variance < `base`)

**Files:**
- Modify: `src/logo_detector_temporal.py`
- Test: `tests/test_temporal_detector.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_temporal_detector.py`:

```python
class TestThresholdVarianceMap:
    """Test binarization of the variance map."""

    def test_returns_binary_mask(self):
        var_map = np.array([[0.0, 0.5], [0.001, 0.1]], dtype=np.float32)
        mask = TemporalLogoDetector._threshold_variance_map(
            var_map, sensitivity=0.5, base_threshold=0.005,
        )
        # effective_threshold = 0.005 * (0.1 + 0.9 * 0.5) = 0.005 * 0.55 = 0.00275
        # Pixels with variance < 0.00275 become 255
        expected = np.array([[255, 0], [255, 0]], dtype=np.uint8)
        np.testing.assert_array_equal(mask, expected)

    def test_higher_sensitivity_more_permissive(self):
        var_map = np.array([[0.0, 0.004, 0.01]], dtype=np.float32)

        strict = TemporalLogoDetector._threshold_variance_map(
            var_map, sensitivity=0.0, base_threshold=0.005)
        loose = TemporalLogoDetector._threshold_variance_map(
            var_map, sensitivity=1.0, base_threshold=0.005)

        # Strict (sensitivity=0): effective = 0.0005 → only 0.0 passes → 1 pixel
        # Loose  (sensitivity=1): effective = 0.005  → 0.0 and 0.004 pass → 2 pixels
        strict_count = int(np.count_nonzero(strict))
        loose_count = int(np.count_nonzero(loose))
        assert loose_count > strict_count

    def test_all_static_returns_all_white(self):
        var_map = np.zeros((10, 10), dtype=np.float32)
        mask = TemporalLogoDetector._threshold_variance_map(
            var_map, sensitivity=0.5, base_threshold=0.005)
        assert np.all(mask == 255)

    def test_all_changing_returns_all_black(self):
        var_map = np.full((10, 10), 0.5, dtype=np.float32)
        mask = TemporalLogoDetector._threshold_variance_map(
            var_map, sensitivity=0.5, base_threshold=0.005)
        assert np.all(mask == 0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_temporal_detector.py::TestThresholdVarianceMap -v`
Expected: All FAIL with `AttributeError`.

- [ ] **Step 3: Implement the method**

Add to `src/logo_detector_temporal.py`, inside the class:

```python
    @staticmethod
    def _threshold_variance_map(
        variance_map: np.ndarray,
        sensitivity: float,
        base_threshold: float,
    ) -> np.ndarray:
        """Convert variance map to a binary mask of "static" pixels.

        Pixels whose variance is below the effective threshold are marked 255
        (static), the rest are marked 0.

        The effective threshold scales with sensitivity:
            effective = base * (0.1 + 0.9 * sensitivity)
        Higher sensitivity → higher threshold → more pixels accepted.
        The 0.1 floor guarantees we still catch truly-static pixels at
        sensitivity=0.0 (otherwise the threshold would be 0 and nothing
        would qualify, since variance is never negative).

        Args:
            variance_map: Per-pixel variance, shape (H, W), float32.
            sensitivity: 0.0 (strict) to 1.0 (permissive).
            base_threshold: The configured `temporal_variance_threshold`.

        Returns:
            Binary mask (uint8), 255 where static, 0 elsewhere.
        """
        effective_threshold = base_threshold * (0.1 + 0.9 * float(sensitivity))
        mask = np.where(variance_map < effective_threshold, 255, 0).astype(np.uint8)
        return mask
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_temporal_detector.py::TestThresholdVarianceMap -v`
Expected: 4 PASS

- [ ] **Step 5: Lint**

Run: `ruff check src/logo_detector_temporal.py tests/test_temporal_detector.py`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add src/logo_detector_temporal.py tests/test_temporal_detector.py
git commit -m "feat: implement variance-map thresholding"
```

---

## Task 7: Implement `_cleanup_mask` (morphological cleanup)

**Files:**
- Modify: `src/logo_detector_temporal.py`
- Test: `tests/test_temporal_detector.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_temporal_detector.py`:

```python
class TestCleanupMask:
    """Test morphological cleanup of the binary mask."""

    def test_removes_tiny_blobs(self):
        # Mask with one big white rectangle and a few single-pixel noise blobs
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[10:50, 10:50] = 255  # 40x40 = 1600 pixels (keep)
        mask[0, 0] = 255          # 1 pixel (remove)
        mask[99, 99] = 255        # 1 pixel (remove)
        mask[60, 60] = 255        # 1 pixel (remove)

        cleaned = TemporalLogoDetector._cleanup_mask(mask, min_region_pixels=200)

        # Big rectangle survives; isolated pixels are removed
        assert cleaned[30, 30] == 255  # center of big rect
        assert cleaned[0, 0] == 0
        assert cleaned[99, 99] == 0
        assert cleaned[60, 60] == 0

    def test_merges_nearby_blobs(self):
        # Two white rectangles close together should merge into one blob
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[10:30, 10:20] = 255  # left blob
        mask[10:30, 23:33] = 255  # right blob (3px gap)

        cleaned = TemporalLogoDetector._cleanup_mask(mask, min_region_pixels=200)

        # The gap between them should now be filled
        assert cleaned[20, 21] == 255  # gap closed
        assert cleaned[20, 11] == 255  # left blob intact

    def test_preserves_large_blob(self):
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:60, 20:60] = 255  # 40x40 = 1600 pixels
        cleaned = TemporalLogoDetector._cleanup_mask(mask, min_region_pixels=200)
        assert np.count_nonzero(cleaned) >= 1600 - 50  # roughly preserved

    def test_empty_mask_stays_empty(self):
        mask = np.zeros((100, 100), dtype=np.uint8)
        cleaned = TemporalLogoDetector._cleanup_mask(mask, min_region_pixels=200)
        assert np.all(cleaned == 0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_temporal_detector.py::TestCleanupMask -v`
Expected: All FAIL with `AttributeError`.

- [ ] **Step 3: Implement the method**

Add to `src/logo_detector_temporal.py`, inside the class:

```python
    @staticmethod
    def _cleanup_mask(mask: np.ndarray, min_region_pixels: int) -> np.ndarray:
        """Clean a binary mask: dilate to merge nearby blobs, then drop tiny ones.

        Args:
            mask: Binary mask (uint8, 0 or 255).
            min_region_pixels: Connected components with fewer pixels than this
                are removed as noise.

        Returns:
            Cleaned binary mask (uint8, 0 or 255).
        """
        # Close small gaps so a fragmented logo merges into one blob.
        # Kernel size 5 gives a ~5px bridge between nearby regions.
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Remove tiny connected components (noise).
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
        cleaned = np.zeros_like(mask)
        for label_idx in range(1, num_labels):  # 0 = background
            area = int(stats[label_idx, cv2.CC_STAT_AREA])
            if area >= min_region_pixels:
                cleaned[labels == label_idx] = 255
        return cleaned
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_temporal_detector.py::TestCleanupMask -v`
Expected: 4 PASS

- [ ] **Step 5: Lint**

Run: `ruff check src/logo_detector_temporal.py tests/test_temporal_detector.py`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add src/logo_detector_temporal.py tests/test_temporal_detector.py
git commit -m "feat: implement mask cleanup with morphology"
```

---

## Task 8: Implement `_find_candidates` (contour → rect)

**Files:**
- Modify: `src/logo_detector_temporal.py`
- Test: `tests/test_temporal_detector.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_temporal_detector.py`:

```python
class TestFindCandidates:
    """Test extraction of candidate rectangles from a cleaned mask."""

    def test_finds_single_rectangle(self):
        mask = np.zeros((200, 200), dtype=np.uint8)
        mask[10:60, 10:60] = 255  # 50x50 square at (10,10)

        candidates = TemporalLogoDetector._find_candidates(mask)
        assert len(candidates) == 1
        rect = candidates[0]
        assert rect.w == 50
        assert rect.h == 50
        assert rect.x == 10
        assert rect.y == 10

    def test_finds_multiple_disjoint_rectangles(self):
        mask = np.zeros((200, 200), dtype=np.uint8)
        mask[10:30, 10:30] = 255    # top-left
        mask[150:180, 150:180] = 255  # bottom-right

        candidates = TemporalLogoDetector._find_candidates(mask)
        assert len(candidates) == 2

    def test_empty_mask_returns_no_candidates(self):
        mask = np.zeros((200, 200), dtype=np.uint8)
        candidates = TemporalLogoDetector._find_candidates(mask)
        assert candidates == []

    def test_returns_rect_objects(self):
        mask = np.zeros((200, 200), dtype=np.uint8)
        mask[10:60, 10:60] = 255
        candidates = TemporalLogoDetector._find_candidates(mask)
        assert all(isinstance(c, Rect) for c in candidates)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_temporal_detector.py::TestFindCandidates -v`
Expected: All FAIL with `AttributeError`.

- [ ] **Step 3: Implement the method**

Add to `src/logo_detector_temporal.py`, inside the class:

```python
    @staticmethod
    def _find_candidates(mask: np.ndarray) -> List[Rect]:
        """Extract candidate rectangles from a cleaned binary mask.

        Uses OpenCV contour detection. Each external contour's bounding
        rectangle becomes one candidate.

        Args:
            mask: Cleaned binary mask (uint8, 0 or 255).

        Returns:
            List of `Rect` objects, one per detected external contour.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: List[Rect] = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            candidates.append(Rect(x=int(x), y=int(y), w=int(w), h=int(h)))
        return candidates
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_temporal_detector.py::TestFindCandidates -v`
Expected: 4 PASS

- [ ] **Step 5: Lint**

Run: `ruff check src/logo_detector_temporal.py tests/test_temporal_detector.py`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add src/logo_detector_temporal.py tests/test_temporal_detector.py
git commit -m "feat: implement candidate rectangle extraction"
```

---

## Task 9: Implement `_score_candidate` (stability + corner + size blend)

**Scoring weights (from spec):**
- Stability: ~70% — inverse of mean variance inside the box
- Corner fit: ~20% — 1.0 at the corner zone center, 0.0 at the center of the frame
- Size fit: ~10% — 1.0 at the midpoint of the allowed size range

**Files:**
- Modify: `src/logo_detector_temporal.py`
- Test: `tests/test_temporal_detector.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_temporal_detector.py`:

```python
class TestScoreCandidate:
    """Test the candidate scoring function."""

    def _var_map(self, value: float, shape=(200, 200)) -> np.ndarray:
        return np.full(shape, value, dtype=np.float32)

    def test_low_variance_scores_higher_than_high_variance(self):
        low_var = self._var_map(0.0001)   # very stable
        high_var = self._var_map(0.5)     # very unstable

        rect = Rect(x=0, y=0, w=50, h=50)
        score_low = TemporalLogoDetector._score_candidate(
            rect, low_var, video_resolution=(200, 200),
            position_zones=["top-left"],
            min_w=20, min_h=20, max_w=450, max_h=220,
        )
        score_high = TemporalLogoDetector._score_candidate(
            rect, high_var, video_resolution=(200, 200),
            position_zones=["top-left"],
            min_w=20, min_h=20, max_w=450, max_h=220,
        )
        assert score_low > score_high

    def test_corner_position_scores_higher_than_center(self):
        var_map = self._var_map(0.0001)  # uniform low variance

        corner_rect = Rect(x=0, y=0, w=50, h=50)
        center_rect = Rect(x=75, y=75, w=50, h=50)  # center of 200x200

        score_corner = TemporalLogoDetector._score_candidate(
            corner_rect, var_map, video_resolution=(200, 200),
            position_zones=["top-left"],
            min_w=20, min_h=20, max_w=450, max_h=220,
        )
        score_center = TemporalLogoDetector._score_candidate(
            center_rect, var_map, video_resolution=(200, 200),
            position_zones=["top-left"],
            min_w=20, min_h=20, max_w=450, max_h=220,
        )
        assert score_corner > score_center

    def test_score_is_in_zero_to_one(self):
        var_map = self._var_map(0.0001)
        rect = Rect(x=0, y=0, w=50, h=50)
        score = TemporalLogoDetector._score_candidate(
            rect, var_map, video_resolution=(200, 200),
            position_zones=["top-left"],
            min_w=20, min_h=20, max_w=450, max_h=220,
        )
        assert 0.0 <= score <= 1.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_temporal_detector.py::TestScoreCandidate -v`
Expected: All FAIL with `AttributeError`.

- [ ] **Step 3: Implement the method**

Add to `src/logo_detector_temporal.py`, inside the class:

```python
    @staticmethod
    def _score_candidate(
        rect: Rect,
        variance_map: np.ndarray,
        video_resolution,
        position_zones: List[str],
        min_w: int,
        min_h: int,
        max_w: int,
        max_h: int,
    ) -> float:
        """Score a candidate rectangle: blend of stability, corner fit, and size fit.

        Weights (per spec):
          - Stability 70% (primary): inverse of mean variance inside the box.
          - Corner fit 20%: how close the box center is to its nearest enabled zone corner.
          - Size fit   10%: how close the box dimensions are to the midpoint of the allowed range.

        Returns:
            Float score in [0.0, 1.0]. Higher is better.
        """
        # --- Stability (70%) ---
        roi = variance_map[rect.y:rect.y + rect.h, rect.x:rect.x + rect.w]
        mean_var = float(np.mean(roi)) if roi.size > 0 else 1.0
        # Map variance [0, 0.01] → stability [1.0, 0.0].
        # Variance of 0 = perfectly static = stability 1.0.
        # Variance >= 0.01 = very unstable = stability 0.0.
        stability = max(0.0, 1.0 - mean_var / 0.01)

        # --- Corner fit (20%) ---
        corner_fit = TemporalLogoDetector._corner_fit_score(
            rect, video_resolution, position_zones
        )

        # --- Size fit (10%) ---
        mid_w = (min_w + max_w) / 2.0
        mid_h = (min_h + max_h) / 2.0
        # 1.0 at midpoint, falls off toward the bounds.
        w_fit = 1.0 - abs(rect.w - mid_w) / max(1.0, (max_w - min_w) / 2.0)
        h_fit = 1.0 - abs(rect.h - mid_h) / max(1.0, (max_h - min_h) / 2.0)
        size_fit = max(0.0, (w_fit + h_fit) / 2.0)

        score = 0.70 * stability + 0.20 * corner_fit + 0.10 * size_fit
        return max(0.0, min(1.0, score))

    @staticmethod
    def _corner_fit_score(
        rect: Rect,
        video_resolution,
        position_zones: List[str],
    ) -> float:
        """Return 1.0 if the rect center is at a zone corner, falling to 0.0 at frame center."""
        if not position_zones:
            return 0.5  # neutral when position filtering disabled
        vw, vh = video_resolution
        cx = rect.x + rect.w / 2.0
        cy = rect.y + rect.h / 2.0

        best = 0.0
        for zone in position_zones:
            if zone == "top-left":
                corner_x, corner_y = 0.0, 0.0
            elif zone == "top-right":
                corner_x, corner_y = vw, 0.0
            elif zone == "bottom-left":
                corner_x, corner_y = 0.0, vh
            elif zone == "bottom-right":
                corner_x, corner_y = vw, vh
            else:
                continue
            # Normalized distance from corner (0 = at corner, 1 = opposite corner)
            dist = ((cx - corner_x) ** 2 + (cy - corner_y) ** 2) ** 0.5
            max_dist = (vw ** 2 + vh ** 2) ** 0.5
            score = max(0.0, 1.0 - dist / max_dist)
            best = max(best, score)
        return best
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_temporal_detector.py::TestScoreCandidate -v`
Expected: 3 PASS

- [ ] **Step 5: Lint**

Run: `ruff check src/logo_detector_temporal.py tests/test_temporal_detector.py`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add src/logo_detector_temporal.py tests/test_temporal_detector.py
git commit -m "feat: implement candidate scoring (stability + corner + size)"
```

---

## Task 10: Implement `detect_in_video` + synthetic end-to-end tests

This is the integration point that wires together everything from Tasks 4–9 plus the existing filter helpers from Task 2. We test it against synthetic frame stacks (no video file needed) by extracting the core logic into a testable helper `_detect_from_frame_stack`.

**Files:**
- Modify: `src/logo_detector_temporal.py`
- Test: `tests/test_temporal_detector.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_temporal_detector.py`:

```python
class TestDetectFromFrameStack:
    """End-to-end test of the detection pipeline on synthetic frame stacks.

    These bypass video I/O by calling the package-private entry point that
    takes a pre-built stack of grayscale frames.
    """

    def _make_stack_with_corner_logo(self, n=15, h=480, w=640,
                                     logo_x=580, logo_y=10,
                                     logo_w=50, logo_h=40) -> np.ndarray:
        """Build a synthetic frame stack: random noise everywhere except a
        static rectangle in the top-right corner (the 'logo')."""
        frames = []
        for _ in range(n):
            f = np.random.randint(0, 256, size=(h, w), dtype=np.uint8)
            f[logo_y:logo_y + logo_h, logo_x:logo_x + logo_w] = 100  # fixed logo
            frames.append(f)
        return np.stack(frames)

    def test_finds_static_corner_logo(self):
        stack = self._make_stack_with_corner_logo()
        config = DetectionConfig(
            sensitivity=0.5,
            position_zones=["top-right"],
            min_logo_width=10, min_logo_height=10,
            max_logo_width=200, max_logo_height=200,
            temporal_min_region_pixels=100,
        )
        detector = TemporalLogoDetector(config)
        results = detector._detect_from_frame_stack(
            stack, video_resolution=(640, 480),
        )
        assert len(results) >= 1
        top = results[0]
        # Top result should overlap the known logo rectangle (580, 10, 50, 40)
        overlap_x = max(0, min(top.x + top.width, 630) - max(top.x, 580))
        overlap_y = max(0, min(top.y + top.height, 50) - max(top.y, 10))
        assert overlap_x * overlap_y > 0  # at least some overlap

    def test_no_static_region_returns_empty(self):
        # Pure random noise — no static regions
        stack = np.stack([
            np.random.randint(0, 256, size=(480, 640), dtype=np.uint8)
            for _ in range(15)
        ])
        config = DetectionConfig(
            sensitivity=0.5,
            position_zones=["top-right"],
            min_logo_width=10, min_logo_height=10,
            max_logo_width=200, max_logo_height=200,
            temporal_min_region_pixels=100,
        )
        detector = TemporalLogoDetector(config)
        results = detector._detect_from_frame_stack(
            stack, video_resolution=(640, 480),
        )
        assert results == []

    def test_flickering_overlay_is_not_detected(self):
        # Static logo in the corner + a 'subtitle' bar that only appears in some frames
        n = 15
        h, w = 480, 640
        frames = []
        for i in range(n):
            f = np.random.randint(0, 256, size=(h, w), dtype=np.uint8)
            # Static logo top-right
            f[10:50, 580:630] = 100
            # Flickering 'subtitle' at the bottom — visible only every 3rd frame
            if i % 3 == 0:
                f[440:470, 100:540] = 200
            frames.append(f)
        stack = np.stack(frames)

        config = DetectionConfig(
            sensitivity=0.5,
            position_zones=["top-right", "bottom-left", "bottom-right"],
            min_logo_width=10, min_logo_height=10,
            max_logo_width=200, max_logo_height=200,
            temporal_min_region_pixels=100,
        )
        detector = TemporalLogoDetector(config)
        results = detector._detect_from_frame_stack(
            stack, video_resolution=(w, h),
        )
        # The flickering subtitle is NOT static (variance > 0), so we should
        # only get the corner logo, not the subtitle bar.
        for r in results:
            # No result should be in the subtitle region (y around 440-470)
            assert not (440 <= r.y <= 470), f"False positive on flickering subtitle: {r}"

    def test_results_sorted_by_score_descending(self):
        stack = self._make_stack_with_corner_logo()
        config = DetectionConfig(
            sensitivity=0.5,
            position_zones=["top-right"],
            min_logo_width=10, min_logo_height=10,
            max_logo_width=200, max_logo_height=200,
            temporal_min_region_pixels=100,
        )
        detector = TemporalLogoDetector(config)
        results = detector._detect_from_frame_stack(
            stack, video_resolution=(640, 480),
        )
        if len(results) >= 2:
            for i in range(len(results) - 1):
                assert results[i].confidence >= results[i + 1].confidence
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_temporal_detector.py::TestDetectFromFrameStack -v`
Expected: All FAIL with `AttributeError` (`_detect_from_frame_stack` doesn't exist).

- [ ] **Step 3: Implement `_detect_from_frame_stack` and replace `detect_in_video`**

In `src/logo_detector_temporal.py`, replace the placeholder `detect_in_video` body and add the new helper. The final class body should contain (in this order):

```python
    def detect_in_video(
        self,
        video_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> DetectionSession:
        """Detect static logo regions in a video file.

        See module docstring for the algorithm overview.
        """
        session = DetectionSession(video_path=video_path, config=self.config)
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise VideoReadError(video_path, "Failed to open video file")

            session.video_fps = cap.get(cv2.CAP_PROP_FPS) or 1.0
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            session.video_duration = (
                frame_count / session.video_fps if session.video_fps > 0 else 0.0
            )
            session.video_resolution = (
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            )

            if progress_callback:
                progress_callback(0.0, "Sampling frames...")

            indices = self._sample_frame_indices(
                total_frames=frame_count,
                num_frames=self.config.temporal_num_frames,
                skip_intro_frac=self.config.temporal_skip_intro_frac,
                skip_outro_frac=self.config.temporal_skip_outro_frac,
            )
            session.total_frames_to_analyze = len(indices)

            scale_max_h = getattr(self.config, "detection_scale_max_height", 720)
            full_w, full_h = session.video_resolution
            if scale_max_h > 0 and full_h > scale_max_h:
                scale = scale_max_h / full_h
                target_h = int(full_h * scale)
                target_w = int(full_w * scale)
            else:
                target_h, target_w = full_h, full_w
                scale = 1.0

            frames = []
            for i, frame_index in enumerate(indices):
                if cancel_check and cancel_check():
                    session.cancel()
                    raise DetectionCancelledError()
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                ret, frame = cap.read()
                if not ret:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if scale != 1.0:
                    gray = cv2.resize(gray, (target_w, target_h), interpolation=cv2.INTER_AREA)
                frames.append(gray)
                session.frames_analyzed += 1
                session.progress = (i + 1) / max(1, len(indices))
                if progress_callback:
                    progress_callback(session.progress, f"Sampled frame {i + 1}/{len(indices)}")

            if len(frames) < 3:
                # Not enough samples to compute meaningful variance.
                session.complete()
                if progress_callback:
                    progress_callback(1.0, "Insufficient frames for detection")
                return session

            if progress_callback:
                progress_callback(0.85, "Analyzing temporal stability...")

            stack = np.stack(frames)
            results = self._detect_from_frame_stack(
                stack, video_resolution=(target_w, target_h),
            )

            # Scale boxes back to full resolution if we downscaled.
            if scale != 1.0:
                inv = 1.0 / scale
                for r in results:
                    r.x = int(r.x * inv)
                    r.y = int(r.y * inv)
                    r.width = int(r.width * inv)
                    r.height = int(r.height * inv)

            for r in results:
                session.add_result(r)

            session.complete()
            if progress_callback:
                progress_callback(1.0, f"Complete! Found {len(session.results)} logo region(s)")
            return session

        except DetectionCancelledError:
            raise
        except (VideoReadError, DetectionFailedError):
            raise
        except Exception as e:
            session.error(str(e))
            raise DetectionFailedError(str(e), video_path) from e
        finally:
            if cap is not None:
                cap.release()

    def _detect_from_frame_stack(
        self,
        stack: np.ndarray,
        video_resolution,
    ) -> List[DetectionResult]:
        """Run the full pipeline on a pre-built stack of grayscale frames.

        Package-private: used by `detect_in_video` and by unit tests that want
        to bypass video I/O.

        Args:
            stack: np.ndarray of shape (N, H, W), dtype uint8.
            video_resolution: (width, height) of the frames in the stack.

        Returns:
            List of DetectionResult, sorted by confidence descending. Each
            result's `detection_method` is set to "temporal".
        """
        cfg = self.config

        var_map = self._compute_variance_map(stack)
        mask = self._threshold_variance_map(
            var_map,
            sensitivity=cfg.sensitivity,
            base_threshold=cfg.temporal_variance_threshold,
        )
        mask = self._cleanup_mask(mask, min_region_pixels=cfg.temporal_min_region_pixels)
        raw_candidates = self._find_candidates(mask)

        # Filter + score each candidate.
        scored: List[Tuple[float, Rect]] = []
        for rect in raw_candidates:
            if not passes_size_filter(
                rect.w, rect.h,
                min_w=cfg.min_logo_width, min_h=cfg.min_logo_height,
                max_w=cfg.max_logo_width, max_h=cfg.max_logo_height,
            ):
                continue
            if not passes_aspect_ratio_filter(
                rect.w, rect.h,
                ar_min=cfg.aspect_ratio_min, ar_max=cfg.aspect_ratio_max,
            ):
                continue
            if not passes_position_filter(
                rect, video_resolution=video_resolution,
                position_zones=cfg.position_zones,
            ):
                continue
            score = self._score_candidate(
                rect, var_map, video_resolution=video_resolution,
                position_zones=cfg.position_zones,
                min_w=cfg.min_logo_width, min_h=cfg.min_logo_height,
                max_w=cfg.max_logo_width, max_h=cfg.max_logo_height,
            )
            scored.append((score, rect))

        scored.sort(key=lambda s: s[0], reverse=True)

        min_conf = getattr(cfg, "min_confidence_to_report", 0.25)
        results: List[DetectionResult] = []
        for score, rect in scored:
            if score < min_conf:
                continue
            results.append(DetectionResult(
                x=rect.x, y=rect.y, width=rect.w, height=rect.h,
                confidence=float(score),
                frame_index=0,
                timestamp=0.0,
                detection_method="temporal",
                status="pending",
            ))
        return results
```

You also need to add the import of the filter functions near the top of `src/logo_detector_temporal.py`. Update the existing `from src.logo_detection_utils import Rect` line to:

```python
from src.logo_detection_utils import (
    Rect,
    passes_aspect_ratio_filter,
    passes_position_filter,
    passes_size_filter,
)
```

And update the `DetectionResult.validate()` allowed methods list. In `src/data_models.py`, find the `detection_method` assertion inside `DetectionResult.validate()` (around line 57):

```python
assert self.detection_method in ["edge", "corner", "template", "vision"], "invalid method"
```

Change it to include `"temporal"`:

```python
assert self.detection_method in ["edge", "corner", "template", "vision", "temporal"], "invalid method"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_temporal_detector.py -v`
Expected: All tests PASS (skeleton, sampling, variance, threshold, cleanup, candidates, scoring, end-to-end).

Run: `pytest tests/test_logo_detector.py -v`
Expected: All existing tests still PASS.

- [ ] **Step 5: Lint**

Run: `ruff check src/logo_detector_temporal.py src/data_models.py tests/test_temporal_detector.py`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add src/logo_detector_temporal.py src/data_models.py tests/test_temporal_detector.py
git commit -m "feat: implement temporal-stability logo detection pipeline"
```

---

## Task 11: Wire the new detector into the UI

Add the dropdown option, dispatch to `TemporalLogoDetector`, and make it the default for fresh users.

**Files:**
- Modify: `src/ui/batch_processor.py:17-29` (imports)
- Modify: `src/ui/batch_processor.py:424-441` (dropdown values)
- Modify: `src/ui/batch_processor.py:1184-1199` (detector dispatch)
- Test: manual (this is UI code; we'll add a smoke check for the dispatch logic separately)

- [ ] **Step 1: Add the import**

In `src/ui/batch_processor.py`, find this block near the top (around lines 17–29):

```python
from src.logo_detector import LogoDetector
from src.data_models import DetectionConfig, DetectionSession

try:
    from src.logo_detector_vision import (
        VisionLogoDetector,
        is_available as vision_detector_available,
    )
except ImportError:
    VisionLogoDetector = None

    def vision_detector_available():
        return False
```

Replace it with:

```python
from src.logo_detector import LogoDetector
from src.logo_detector_temporal import TemporalLogoDetector
from src.data_models import DetectionConfig, DetectionSession

try:
    from src.logo_detector_vision import (
        VisionLogoDetector,
        is_available as vision_detector_available,
    )
except ImportError:
    VisionLogoDetector = None

    def vision_detector_available():
        return False
```

- [ ] **Step 2: Update the dropdown values to include Temporal as default**

In `src/ui/batch_processor.py`, find the block around lines 424–441 that currently reads:

```python
        # Detection method: OpenCV or Google Cloud Vision (AI) if available
        method_row = ctk.CTkFrame(content, fg_color="transparent")
        method_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            method_row, text="Method:", font=ctk.CTkFont(size=12), text_color="#60a5fa"
        ).pack(side="left", padx=(0, 8))
        method_values = ["OpenCV (local)"]
        if vision_detector_available():
            method_values.append("Google Cloud Vision (AI)")
        self.detection_method_var = ctk.StringVar(value=method_values[0])
```

Replace with:

```python
        # Detection method: Temporal (default), legacy edges, or Cloud Vision if available
        method_row = ctk.CTkFrame(content, fg_color="transparent")
        method_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            method_row, text="Method:", font=ctk.CTkFont(size=12), text_color="#60a5fa"
        ).pack(side="left", padx=(0, 8))
        method_values = [
            "Temporal Stability (recommended)",
            "OpenCV Edges (legacy)",
        ]
        if vision_detector_available():
            method_values.append("Google Cloud Vision (AI)")
        self.detection_method_var = ctk.StringVar(value=method_values[0])
```

- [ ] **Step 3: Update the dispatch logic in `_on_detect_logo`**

In `src/ui/batch_processor.py`, find the block around lines 1183–1199:

```python
        # Run detection in background thread
        use_vision = (
            vision_detector_available()
            and self.detection_method_var.get() == "Google Cloud Vision (AI)"
        )

        def run_detection():
            try:
                config = DetectionConfig(
                    sensitivity=self.sensitivity_slider.get(),
                    frame_sampling=30,
                )

                if use_vision and VisionLogoDetector is not None:
                    detector = VisionLogoDetector(config)
                else:
                    detector = LogoDetector(config)
```

Replace with:

```python
        # Run detection in background thread
        selected_method = self.detection_method_var.get()
        use_vision = (
            vision_detector_available()
            and selected_method == "Google Cloud Vision (AI)"
        )
        use_temporal = selected_method == "Temporal Stability (recommended)"

        def run_detection():
            try:
                config = DetectionConfig(
                    sensitivity=self.sensitivity_slider.get(),
                    frame_sampling=30,
                )

                if use_vision and VisionLogoDetector is not None:
                    detector = VisionLogoDetector(config)
                elif use_temporal:
                    detector = TemporalLogoDetector(config)
                else:
                    detector = LogoDetector(config)
```

- [ ] **Step 4: Smoke-test the import**

Run: `python -c "from src.ui.batch_processor import BatchProcessor; print('OK')"`
Expected: prints `OK` (no `ImportError`).

If CustomTkinter can't initialize in a headless environment, instead run:

Run: `python -c "from src.logo_detector_temporal import TemporalLogoDetector; print('OK')"`
Expected: prints `OK`.

- [ ] **Step 5: Lint**

Run: `ruff check src/ui/batch_processor.py`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add src/ui/batch_processor.py
git commit -m "feat: wire TemporalLogoDetector into UI as default method"
```

---

## Task 12: Relabel "Confidence" as "Stability" in the results list

This is a small but meaningful UX change — users should know the score means stability, not edge density.

**Files:**
- Modify: `src/ui/batch_processor.py:1304-1306` (the `info_text` string inside `_show_detection_results`)

- [ ] **Step 1: Make the label reflect the detection method**

Find this exact block in `src/ui/batch_processor.py` (around lines 1304–1306):

```python
            # Result info with confidence emphasis
            conf_pct = result.confidence * 100
            info_text = f"Region #{i + 1}: ({result.x}, {result.y}) {result.width}x{result.height}  |  Confidence: {conf_pct:.0f}%"
```

Replace it with:

```python
            # Result info with confidence emphasis
            # For temporal detector, the score reflects stability, not edge density.
            conf_pct = result.confidence * 100
            score_label = "Stability" if result.detection_method == "temporal" else "Confidence"
            info_text = f"Region #{i + 1}: ({result.x}, {result.y}) {result.width}x{result.height}  |  {score_label}: {conf_pct:.0f}%"
```

Also update the section header at line 1289 from "highest confidence first" to a method-agnostic phrasing. Find:

```python
            text="Detected Regions (highest confidence first):",
```

Replace with:

```python
            text="Detected Regions (highest score first):",
```

- [ ] **Step 2: Verify the file still parses**

Run: `python -c "import ast; ast.parse(open('src/ui/batch_processor.py').read()); print('OK')"`
Expected: prints `OK`.

- [ ] **Step 3: Lint**

Run: `ruff check src/ui/batch_processor.py`
Expected: no errors

- [ ] **Step 4: Commit**

```bash
git add src/ui/batch_processor.py
git commit -m "feat: show 'Stability' label for temporal detector results"
```

---

## Task 13: Add backward-compat test for saved profiles missing temporal fields

Already covered by `TestTemporalConfigFields.test_backward_compat_missing_temporal_fields` in Task 1. This task verifies the actual `detection_profiles.py` load path handles missing fields too.

**Files:**
- Test: `tests/test_detection_profiles_compat.py` (new file)

- [ ] **Step 1: Write the test**

Create `tests/test_detection_profiles_compat.py`:

```python
"""
Backward-compat test: a profile JSON file saved before the temporal fields
were added must still load successfully, with the new fields default-populated.
"""

import json
from pathlib import Path

import pytest

from src.data_models import DetectionConfig


OLD_PROFILE_JSON = """
{
    "sensitivity": 0.6,
    "frame_sampling": 30,
    "min_logo_width": 20,
    "min_logo_height": 20,
    "max_logo_width": 450,
    "max_logo_height": 220
}
"""


def test_old_profile_dict_loads_with_temporal_defaults():
    """DetectionConfig(**old_dict) should work and populate temporal defaults."""
    old_data = json.loads(OLD_PROFILE_JSON)
    config = DetectionConfig(**old_data)
    assert config.sensitivity == 0.6
    assert config.temporal_num_frames == 15
    assert config.temporal_variance_threshold == 0.005
    assert config.validate()


def test_unknown_keys_rejected_safely():
    """If the JSON has extra keys we don't recognize, load must not crash silently.

    Strategy: filter to known fields before unpacking. The detection_profiles
    loader should already do this; this test documents the expectation.
    """
    raw = json.loads(OLD_PROFILE_JSON)
    raw["unknown_future_field"] = "ignored"
    # Filter to fields that exist on DetectionConfig (this is the safe pattern).
    known_field_names = {f.name for f in __import__("dataclasses").fields(DetectionConfig)}
    filtered = {k: v for k, v in raw.items() if k in known_field_names}
    config = DetectionConfig(**filtered)
    assert config.validate()
```

- [ ] **Step 2: Run the test**

Run: `pytest tests/test_detection_profiles_compat.py -v`
Expected: 2 PASS.

If `test_unknown_keys_rejected_safely` fails because the actual `detection_profiles.load_profile()` doesn't filter unknown keys, file a follow-up — but the test as written constructs the config directly, so it should pass.

- [ ] **Step 3: Lint**

Run: `ruff check tests/test_detection_profiles_compat.py`
Expected: no errors

- [ ] **Step 4: Commit**

```bash
git add tests/test_detection_profiles_compat.py
git commit -m "test: add backward-compat coverage for DetectionConfig"
```

---

## Task 14: Integration test on an ffmpeg-generated video

Generate a real test video with a known static overlay using ffmpeg, then verify the detector finds it.

**Files:**
- Create: `tests/integration/test_temporal_detection.py`

- [ ] **Step 1: Write the test**

Create `tests/integration/test_temporal_detection.py`:

```python
"""
Integration test for TemporalLogoDetector on a real video.

Generates a short test video with ffmpeg (color bars + a static black rectangle
in the top-right corner), then verifies the detector finds the rectangle.

Skipped automatically if ffmpeg is not on PATH.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from src.data_models import DetectionConfig
from src.logo_detector_temporal import TemporalLogoDetector


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _make_test_video(path: Path, seconds: int = 4, fps: int = 30) -> None:
    """Generate a color-bar video with a static black rectangle in the top-right.

    The rectangle is drawn with ffmpeg's drawbox filter at a fixed position so
    we know exactly where the 'logo' is.
    """
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"testsrc=duration={seconds}:size=640x480:rate={fps}",
        "-vf", "drawbox=x=560:y=20:w=60:h=50:color=black@1.0:t=fill",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


@pytest.fixture(scope="module")
def test_video(tmp_path_factory) -> Path:
    if not _ffmpeg_available():
        pytest.skip("ffmpeg not available on PATH")
    video_path = tmp_path_factory.mktemp("videos") / "with_logo.mp4"
    _make_test_video(video_path)
    return video_path


def test_detects_static_overlay_in_corner(test_video):
    """The detector should find the black rectangle in the top-right corner."""
    config = DetectionConfig(
        sensitivity=0.5,
        temporal_num_frames=10,
        position_zones=["top-right"],
        min_logo_width=20,
        min_logo_height=20,
        max_logo_width=200,
        max_logo_height=200,
        temporal_min_region_pixels=100,
        min_confidence_to_report=0.2,
    )
    detector = TemporalLogoDetector(config)
    session = detector.detect_in_video(str(test_video))

    assert session.status == "completed"
    assert len(session.results) >= 1

    top = session.results[0]
    # The drawn rectangle is at (560, 20, 60, 50) → top-right corner.
    # Allow a generous overlap window since the bounding box may be slightly larger.
    assert top.x + top.width >= 550  # right side of frame
    assert top.y <= 100             # near the top
    assert top.confidence >= 0.2


def test_handles_video_with_no_logo(test_video):
    """If we disable the position zone for the corner, we may get fewer results
    but the detector must not crash."""
    config = DetectionConfig(
        sensitivity=0.5,
        temporal_num_frames=10,
        position_zones=[],  # accept any position
        min_logo_width=5,
        min_logo_height=5,
        max_logo_width=300,
        max_logo_height=300,
        temporal_min_region_pixels=50,
        min_confidence_to_report=0.0,
    )
    detector = TemporalLogoDetector(config)
    session = detector.detect_in_video(str(test_video))
    assert session.status == "completed"
    # Some result should come back (the static overlay at minimum).
    assert isinstance(session.results, list)


def test_cancel_check_aborts_midway(test_video):
    """A cancel_check that returns True should abort detection cleanly."""

    def always_cancel() -> bool:
        return True

    from src.exceptions import DetectionCancelledError

    config = DetectionConfig(temporal_num_frames=15)
    detector = TemporalLogoDetector(config)
    with pytest.raises(DetectionCancelledError):
        detector.detect_in_video(str(test_video), cancel_check=always_cancel)
```

- [ ] **Step 2: Run the integration tests**

Run: `pytest tests/integration/test_temporal_detection.py -v`
Expected: 3 PASS (or SKIP if ffmpeg is not installed).

If the tests are skipped, install ffmpeg or run on a machine that has it. The unit tests in Task 10 already cover the algorithm — these integration tests are belt-and-suspenders.

- [ ] **Step 3: Lint**

Run: `ruff check tests/integration/test_temporal_detection.py`
Expected: no errors

- [ ] **Step 4: Run the entire test suite to confirm nothing is broken**

Run: `pytest tests/ -v --ignore=tests/integration/test_startup.py --ignore=tests/integration/test_single_instance.py`
Expected: All PASS (the two ignored integration tests require a GUI and are unrelated).

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_temporal_detection.py
git commit -m "test: add ffmpeg-based integration test for temporal detector"
```

---

## Final Verification Checklist

After all 14 tasks are complete, run these commands from the repository root:

- [ ] `ruff check src/ tests/`
- [ ] `pytest tests/ -v --ignore=tests/integration/test_startup.py --ignore=tests/integration/test_single_instance.py`
- [ ] `python -c "from src.logo_detector_temporal import TemporalLogoDetector; from src.data_models import DetectionConfig; TemporalLogoDetector(DetectionConfig()); print('Smoke OK')"`

Expected: all of the above succeed with zero errors.

## What's NOT in this plan (deliberate)

These are listed in the spec's Out-of-Scope section and tracked as future work:
- LLM / Gemini semantic check (could be added later as a third dropdown option)
- Moving/animated logo tracking
- Better removal than FFmpeg `delogo` (inpainting)
- Per-video detection inside a batch (we detect once on the representative file)
- Variance-map preview widget (mentioned in spec as polish — could be added in a follow-up without redesigning anything)
