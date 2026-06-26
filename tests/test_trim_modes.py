"""
Tests for video trim/cut modes with hours support.

Validates all trim mode calculations are correct.
"""

from src.state import AppState, CutMode


class TestTrimModes:
    """Test suite for video trim mode calculations"""

    def test_cut_total_seconds_with_hours(self):
        """Test cut_total_seconds property includes hours"""
        state = AppState()
        state.cut_hours = 1.0
        state.cut_minutes = 5.0
        state.cut_seconds = 30.0

        # 1 hour + 5 minutes + 30 seconds = 3600 + 300 + 30 = 3930 seconds
        assert state.cut_total_seconds == 3930.0

    def test_cut_total_seconds_no_hours(self):
        """Test cut_total_seconds without hours (backward compatibility)"""
        state = AppState()
        state.cut_hours = 0.0
        state.cut_minutes = 5.0
        state.cut_seconds = 0.0

        # 5 minutes = 300 seconds
        assert state.cut_total_seconds == 300.0

    def test_cut_start_total_seconds_with_hours(self):
        """Test cut_start_total_seconds includes hours"""
        state = AppState()
        state.cut_start_hours = 0.0
        state.cut_start_minutes = 2.0
        state.cut_start_seconds = 30.0

        # 2 minutes + 30 seconds = 120 + 30 = 150 seconds
        assert state.cut_start_total_seconds == 150.0

    def test_cut_start_total_seconds_with_full_time(self):
        """Test cut_start_total_seconds with hours, minutes, seconds"""
        state = AppState()
        state.cut_start_hours = 1.0
        state.cut_start_minutes = 30.0
        state.cut_start_seconds = 45.0

        # 1h 30m 45s = 3600 + 1800 + 45 = 5445 seconds
        assert state.cut_start_total_seconds == 5445.0

    def test_cut_end_total_seconds_none(self):
        """Test cut_end_total_seconds returns None when all fields are None"""
        state = AppState()
        state.cut_end_hours = None
        state.cut_end_minutes = None
        state.cut_end_seconds = None

        assert state.cut_end_total_seconds is None

    def test_cut_end_total_seconds_with_values(self):
        """Test cut_end_total_seconds with values"""
        state = AppState()
        state.cut_end_hours = 0.0
        state.cut_end_minutes = 4.0
        state.cut_end_seconds = 10.0

        # 4 minutes + 10 seconds = 240 + 10 = 250 seconds
        assert state.cut_end_total_seconds == 250.0

    def test_cut_end_total_seconds_with_hours(self):
        """Test cut_end_total_seconds with hours"""
        state = AppState()
        state.cut_end_hours = 1.0
        state.cut_end_minutes = 55.0
        state.cut_end_seconds = 50.0

        # 1h 55m 50s = 3600 + 3300 + 50 = 6950 seconds
        assert state.cut_end_total_seconds == 6950.0


class TestTrimScenarios:
    """Test real-world trim scenarios"""

    def test_scenario_user_test_case(self):
        """Test user's actual scenario: 2h movie, start=10s, end=4m10s"""
        state = AppState()
        state.cut_mode = CutMode.CUT_RANGE

        # Start at 10 seconds
        state.cut_start_hours = 0.0
        state.cut_start_minutes = 0.0
        state.cut_start_seconds = 10.0

        # End at 4 minutes 10 seconds
        state.cut_end_hours = 0.0
        state.cut_end_minutes = 4.0
        state.cut_end_seconds = 10.0

        start_time = state.cut_start_total_seconds  # 10 seconds
        end_time = state.cut_end_total_seconds      # 250 seconds
        duration = end_time - start_time             # 240 seconds = 4 minutes

        assert start_time == 10.0
        assert end_time == 250.0
        assert duration == 240.0  # 4 minutes output

    def test_scenario_remove_first_10_seconds(self):
        """Test CUT_FIRST: Remove first 10 seconds"""
        state = AppState()
        state.cut_mode = CutMode.CUT_FIRST
        state.cut_hours = 0.0
        state.cut_minutes = 0.0
        state.cut_seconds = 10.0

        # For a 2-hour (7200s) movie
        total_duration = 7200.0
        start_time = state.cut_total_seconds  # 10 seconds
        duration = total_duration - start_time  # 7190 seconds

        assert start_time == 10.0
        assert duration == 7190.0

    def test_scenario_remove_last_5_minutes(self):
        """Test CUT_LAST: Remove last 5 minutes"""
        state = AppState()
        state.cut_mode = CutMode.CUT_LAST
        state.cut_hours = 0.0
        state.cut_minutes = 5.0
        state.cut_seconds = 0.0

        # For a 2-hour (7200s) movie
        total_duration = 7200.0
        cut_seconds = state.cut_total_seconds  # 300 seconds
        duration = total_duration - cut_seconds  # 6900 seconds
        start_time = 0.0

        assert cut_seconds == 300.0
        assert duration == 6900.0
        assert start_time == 0.0

    def test_scenario_extract_middle_hour(self):
        """Test CUT_RANGE: Extract from 0:30:00 to 1:30:00"""
        state = AppState()
        state.cut_mode = CutMode.CUT_RANGE

        # Start at 30 minutes
        state.cut_start_hours = 0.0
        state.cut_start_minutes = 30.0
        state.cut_start_seconds = 0.0

        # End at 1 hour 30 minutes
        state.cut_end_hours = 1.0
        state.cut_end_minutes = 30.0
        state.cut_end_seconds = 0.0

        start_time = state.cut_start_total_seconds  # 1800 seconds
        end_time = state.cut_end_total_seconds      # 5400 seconds
        duration = end_time - start_time             # 3600 seconds = 1 hour

        assert start_time == 1800.0
        assert end_time == 5400.0
        assert duration == 3600.0  # Exactly 1 hour

    def test_scenario_keep_from_10s_to_end(self):
        """Test CUT_RANGE: Start at 10s, end at video end"""
        state = AppState()
        state.cut_mode = CutMode.CUT_RANGE

        # Start at 10 seconds
        state.cut_start_hours = 0.0
        state.cut_start_minutes = 0.0
        state.cut_start_seconds = 10.0

        # End at None (to end of video)
        state.cut_end_hours = None
        state.cut_end_minutes = None
        state.cut_end_seconds = None

        start_time = state.cut_start_total_seconds
        end_time = state.cut_end_total_seconds

        assert start_time == 10.0
        assert end_time is None  # Means "to end of video"

    def test_scenario_remove_credits_both_ends(self):
        """Test complex scenario: Remove 1m30s opening and 2m closing credits"""
        state = AppState()
        state.cut_mode = CutMode.CUT_RANGE

        # For a 2-hour (7200s) movie

        # Start at 1 minute 30 seconds (skip opening)
        state.cut_start_hours = 0.0
        state.cut_start_minutes = 1.0
        state.cut_start_seconds = 30.0

        # End at total - 2 minutes (skip closing)
        # 7200 - 120 = 7080 seconds = 1:58:00
        state.cut_end_hours = 1.0
        state.cut_end_minutes = 58.0
        state.cut_end_seconds = 0.0

        start_time = state.cut_start_total_seconds  # 90 seconds
        end_time = state.cut_end_total_seconds      # 7080 seconds
        duration = end_time - start_time             # 6990 seconds

        assert start_time == 90.0
        assert end_time == 7080.0
        assert duration == 6990.0

    def test_scenario_extract_last_hour(self):
        """Test CUT_RANGE: Extract last hour of 2-hour movie"""
        state = AppState()
        state.cut_mode = CutMode.CUT_RANGE

        # Start at 1 hour
        state.cut_start_hours = 1.0
        state.cut_start_minutes = 0.0
        state.cut_start_seconds = 0.0

        # End at None (to end of video)
        state.cut_end_hours = None
        state.cut_end_minutes = None
        state.cut_end_seconds = None

        start_time = state.cut_start_total_seconds
        end_time = state.cut_end_total_seconds

        assert start_time == 3600.0  # 1 hour
        assert end_time is None  # To end of video


class TestBackwardCompatibility:
    """Ensure hour fields default to 0 and don't break existing functionality"""

    def test_default_hours_are_zero(self):
        """Test that hour fields default to 0"""
        state = AppState()

        assert state.cut_hours == 0.0
        assert state.cut_start_hours == 0.0
        assert state.cut_end_hours is None  # End defaults to None

    def test_existing_minutes_seconds_still_work(self):
        """Test that existing code using only minutes/seconds still works"""
        state = AppState()
        state.cut_minutes = 5.0
        state.cut_seconds = 30.0

        # Should calculate correctly without hours
        assert state.cut_total_seconds == 330.0  # 5m30s = 330 seconds
