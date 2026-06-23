"""
Unit tests for the temporal-stability logo detector.

Most tests use synthetic NumPy frame stacks (no real video files needed).
The end-to-end `detect_in_video` test on a real video lives in
tests/integration/test_temporal_detection.py.
"""

import numpy as np

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
