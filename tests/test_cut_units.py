"""
Tests for the cut-unit feature: TIME, PERCENT, and FRAMES input units.

These tests verify the pure conversion logic and AppState fields.
Integration tests on real videos live in tests/integration/test_cut_units.py.
"""

import pytest

from src.state import AppState, CutMode, CutUnit
from src.video_processor import convert_cut_value_to_seconds


class TestCutUnitEnum:
    """Test the CutUnit enum exists with the right values."""

    def test_enum_has_three_values(self):
        assert CutUnit.TIME == CutUnit("time")
        assert CutUnit.PERCENT == CutUnit("percent")
        assert CutUnit.FRAMES == CutUnit("frames")

    def test_enum_values(self):
        assert CutUnit.TIME.value == "time"
        assert CutUnit.PERCENT.value == "percent"
        assert CutUnit.FRAMES.value == "frames"


class TestAppStateDefaults:
    """Test AppState has the new fields with correct defaults."""

    def test_default_unit_is_time(self):
        """Default unit must be TIME for backward compatibility."""
        state = AppState()
        assert state.cut_unit == CutUnit.TIME

    def test_percent_fields_exist_with_defaults(self):
        state = AppState()
        assert state.cut_amount_percent == 5.0
        assert state.cut_start_percent == 0.0
        assert state.cut_end_percent is None

    def test_frame_fields_exist_with_defaults(self):
        state = AppState()
        assert state.cut_amount_frames == 0
        assert state.cut_start_frame == 0
        assert state.cut_end_frame is None


class TestConvertTimeUnit:
    """TIME unit is a pass-through (value is already seconds)."""

    def test_time_passes_through(self):
        assert convert_cut_value_to_seconds(90, CutUnit.TIME, 7200, 24) == 90

    def test_time_negative_clamps_to_zero(self):
        assert convert_cut_value_to_seconds(-5, CutUnit.TIME, 7200, 24) == 0

    def test_time_zero(self):
        assert convert_cut_value_to_seconds(0, CutUnit.TIME, 7200, 24) == 0


class TestConvertPercentUnit:
    """PERCENT unit converts a percentage of the total duration to seconds."""

    def test_five_percent_of_two_hours(self):
        # 5% of 7200s = 360s
        assert convert_cut_value_to_seconds(5, CutUnit.PERCENT, 7200, 24) == 360

    def test_ten_percent_of_one_minute(self):
        # 10% of 60s = 6s
        assert convert_cut_value_to_seconds(10, CutUnit.PERCENT, 60, 30) == 6

    def test_zero_percent(self):
        assert convert_cut_value_to_seconds(0, CutUnit.PERCENT, 7200, 24) == 0

    def test_one_hundred_percent(self):
        assert convert_cut_value_to_seconds(100, CutUnit.PERCENT, 7200, 24) == 7200

    def test_over_100_clamps_to_100(self):
        # 150% should clamp to 100%
        assert convert_cut_value_to_seconds(150, CutUnit.PERCENT, 7200, 24) == 7200

    def test_negative_clamps_to_zero(self):
        assert convert_cut_value_to_seconds(-5, CutUnit.PERCENT, 7200, 24) == 0


class TestConvertFramesUnit:
    """FRAMES unit converts a frame number to seconds using fps."""

    def test_frame_720_at_24fps(self):
        # 720 frames / 24 fps = 30 seconds
        assert convert_cut_value_to_seconds(720, CutUnit.FRAMES, 7200, 24) == 30

    def test_frame_60_at_30fps(self):
        # 60 frames / 30 fps = 2 seconds
        assert convert_cut_value_to_seconds(60, CutUnit.FRAMES, 10, 30) == 2

    def test_frame_zero(self):
        assert convert_cut_value_to_seconds(0, CutUnit.FRAMES, 7200, 24) == 0

    def test_zero_fps_raises_error(self):
        """Frame-based cut with unknown/zero FPS must raise ValueError."""
        with pytest.raises(ValueError, match="FPS"):
            convert_cut_value_to_seconds(100, CutUnit.FRAMES, 7200, 0)


class TestConvertUnknownUnit:
    """Unknown unit must raise ValueError."""

    def test_unknown_unit_raises(self):
        with pytest.raises(ValueError, match="Unknown unit"):
            convert_cut_value_to_seconds(100, "invalid_unit", 7200, 24)


class TestBackwardCompatibility:
    """Existing time-based AppState fields and CutMode must still work."""

    def test_existing_cut_mode_enum_unchanged(self):
        assert CutMode.NONE == CutMode("none")
        assert CutMode.CUT_LAST == CutMode("cut_last")
        assert CutMode.CUT_FIRST == CutMode("cut_first")
        assert CutMode.CUT_RANGE == CutMode("cut_range")

    def test_time_fields_preserved(self):
        state = AppState()
        state.cut_hours = 1.0
        state.cut_minutes = 5.0
        state.cut_seconds = 30.0
        assert state.cut_total_seconds == 3930.0

    def test_unit_default_does_not_break_existing_trim_tests(self):
        """The AppState used by test_trim_modes.py must still work identically."""
        state = AppState()
        assert state.cut_unit == CutUnit.TIME
        assert state.cut_mode == CutMode.CUT_LAST
