"""
Tests for the cut-unit feature: TIME, SPLIT, and MARKERS input units.

These tests verify the enum values, AppState fields, and backward compatibility.
Integration tests on real videos live in tests/integration/test_cut_units_processing.py.
"""


from src.state import AppState, CutMode, CutUnit


class TestCutUnitEnum:
    """Test the CutUnit enum exists with the right values."""

    def test_enum_has_three_values(self):
        assert CutUnit.TIME == CutUnit("time")
        assert CutUnit.SPLIT == CutUnit("split")
        assert CutUnit.MARKERS == CutUnit("markers")

    def test_enum_values(self):
        assert CutUnit.TIME.value == "time"
        assert CutUnit.SPLIT.value == "split"
        assert CutUnit.MARKERS.value == "markers"


class TestAppStateDefaults:
    """Test AppState has the new fields with correct defaults."""

    def test_default_unit_is_time(self):
        """Default unit must be TIME for backward compatibility."""
        state = AppState()
        assert state.cut_unit == CutUnit.TIME

    def test_markers_fields_exist_with_defaults(self):
        state = AppState()
        assert state.cut_markers_start == "00:00:00"
        assert state.cut_markers_end == ""

    def test_split_parts_default(self):
        state = AppState()
        assert state.split_parts == 2

    def test_split_parts_can_be_changed(self):
        state = AppState()
        state.split_parts = 4
        assert state.split_parts == 4


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
