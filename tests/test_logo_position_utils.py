"""
Tests for logo position utilities: coordinate parsing, frame extraction,
and frame scaling.
"""

import numpy as np
import pytest

from src.logo_position_utils import (
    extract_preview_frame,
    parse_logo_coordinates,
    scale_frame_for_display,
)


# ─── parse_logo_coordinates ───────────────────────────────────────────────


class TestParseLogoCoordinates:
    """Test parsing of pasted coordinate text in various formats."""

    def test_plain_comma_separated(self):
        assert parse_logo_coordinates("100, 200, 50, 30") == (100, 200, 50, 30)

    def test_plain_space_separated(self):
        assert parse_logo_coordinates("100 200 50 30") == (100, 200, 50, 30)

    def test_with_labels_and_commas(self):
        assert parse_logo_coordinates("x=100, y=200, w=50, h=30") == (100, 200, 50, 30)

    def test_with_colon_labels(self):
        assert parse_logo_coordinates("x:100 y:200 w:50 h:30") == (100, 200, 50, 30)

    def test_uppercase_labels(self):
        assert parse_logo_coordinates("X: 100  Y: 200  W: 50  H: 30") == (100, 200, 50, 30)

    def test_mixed_separators(self):
        assert parse_logo_coordinates("x=100 y:200, w=50, h:30") == (100, 200, 50, 30)

    def test_gimp_format(self):
        """GIMP's 'Image > Properties' shows position and size."""
        assert parse_logo_coordinates("Position: 100, 200\nSize: 50 x 30") == (100, 200, 50, 30)

    def test_tab_separated(self):
        assert parse_logo_coordinates("100\t200\t50\t30") == (100, 200, 50, 30)

    def test_extra_text_around_numbers(self):
        assert parse_logo_coordinates("Logo at (100, 200) size 50x30") == (100, 200, 50, 30)

    def test_returns_none_for_too_few_numbers(self):
        assert parse_logo_coordinates("100, 200") is None

    def test_returns_none_for_too_many_numbers(self):
        assert parse_logo_coordinates("100, 200, 50, 30, 99") is None

    def test_returns_none_for_empty_string(self):
        assert parse_logo_coordinates("") is None

    def test_returns_none_for_no_numbers(self):
        assert parse_logo_coordinates("hello world") is None

    def test_returns_none_for_negative_values(self):
        assert parse_logo_coordinates("-100, 200, 50, 30") is None

    def test_handles_newlines(self):
        text = "x=100\ny=200\nw=50\nh=30"
        assert parse_logo_coordinates(text) == (100, 200, 50, 30)

    def test_zero_values_accepted(self):
        assert parse_logo_coordinates("0, 0, 0, 0") == (0, 0, 0, 0)


# ─── scale_frame_for_display ──────────────────────────────────────────────


class TestScaleFrameForDisplay:
    """Test frame scaling for preview display."""

    def test_no_scaling_when_small_enough(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        scaled, factor = scale_frame_for_display(frame, max_width=900, max_height=600)
        assert factor == 1.0
        assert scaled.shape == (480, 640, 3)

    def test_scales_down_large_frame(self):
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        scaled, factor = scale_frame_for_display(frame, max_width=900, max_height=600)
        assert factor < 1.0
        assert scaled.shape[1] <= 900
        assert scaled.shape[0] <= 600

    def test_preserves_aspect_ratio(self):
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        scaled, factor = scale_frame_for_display(frame, max_width=900, max_height=600)
        original_ratio = 1920 / 1080
        scaled_ratio = scaled.shape[1] / scaled.shape[0]
        assert abs(original_ratio - scaled_ratio) < 0.01

    def test_width_constrained(self):
        """Wide frame should be limited by max_width."""
        frame = np.zeros((100, 2000, 3), dtype=np.uint8)
        scaled, factor = scale_frame_for_display(frame, max_width=900, max_height=600)
        assert scaled.shape[1] <= 900

    def test_height_constrained(self):
        """Tall frame should be limited by max_height."""
        frame = np.zeros((2000, 100, 3), dtype=np.uint8)
        scaled, factor = scale_frame_for_display(frame, max_width=900, max_height=600)
        assert scaled.shape[0] <= 600

    def test_custom_max_dimensions(self):
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        scaled, factor = scale_frame_for_display(frame, max_width=400, max_height=300)
        assert scaled.shape[1] <= 400
        assert scaled.shape[0] <= 300


# ─── extract_preview_frame ────────────────────────────────────────────────


class TestExtractPreviewFrame:
    """Test frame extraction from video files."""

    def test_returns_none_for_nonexistent_file(self):
        result = extract_preview_frame("/nonexistent/video.mp4")
        assert result is None

    def test_extracts_frame_from_real_video(self, tmp_path):
        """Requires ffmpeg — creates a tiny test video."""
        import shutil
        import subprocess

        if not shutil.which("ffmpeg"):
            pytest.skip("ffmpeg not available")

        video = tmp_path / "test.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i",
             "testsrc=size=320x240:rate=30", "-t", "3",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)],
            check=True, capture_output=True,
        )

        frame = extract_preview_frame(str(video))
        assert frame is not None
        assert frame.shape == (240, 320, 3)

    def test_position_frac_seeks_into_video(self, tmp_path):
        """Different position_frac should give different frames."""
        import shutil
        import subprocess

        if not shutil.which("ffmpeg"):
            pytest.skip("ffmpeg not available")

        video = tmp_path / "test.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i",
             "mandelbrot=size=320x240:rate=30", "-t", "5",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)],
            check=True, capture_output=True,
        )

        frame_start = extract_preview_frame(str(video), position_frac=0.0)
        frame_mid = extract_preview_frame(str(video), position_frac=0.5)
        assert frame_start is not None
        assert frame_mid is not None
        # Mandelbrot changes over time, so frames should differ
        assert not np.array_equal(frame_start, frame_mid)
