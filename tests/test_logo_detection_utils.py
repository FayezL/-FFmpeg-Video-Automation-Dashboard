"""Unit tests for shared logo-detection filter helpers."""

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
