"""
Test UI validation logic for hours support
"""

import pytest
from src.state import AppState, CutMode


def test_validation_with_hours_in_range_mode():
    """Test that validation correctly compares hours in CUT_RANGE mode"""
    state = AppState()
    state.cut_mode = CutMode.CUT_RANGE

    # Test case: Start at 1h 30m, End at 2h 15m (should be valid)
    state.cut_start_hours = 1.0
    state.cut_start_minutes = 30.0
    state.cut_start_seconds = 0.0
    state.cut_end_hours = 2.0
    state.cut_end_minutes = 15.0
    state.cut_end_seconds = 0.0

    start_total = state.cut_start_total_seconds
    end_total = state.cut_end_total_seconds

    assert start_total == (1 * 3600) + (30 * 60)  # 5400 seconds
    assert end_total == (2 * 3600) + (15 * 60)     # 8100 seconds
    assert end_total > start_total, "End time should be after start time"


def test_validation_catches_reversed_hours():
    """Test that validation catches when end hour is before start hour"""
    state = AppState()
    state.cut_mode = CutMode.CUT_RANGE

    # Test case: Start at 2h 0m, End at 1h 30m (should be INVALID)
    state.cut_start_hours = 2.0
    state.cut_start_minutes = 0.0
    state.cut_start_seconds = 0.0
    state.cut_end_hours = 1.0
    state.cut_end_minutes = 30.0
    state.cut_end_seconds = 0.0

    start_total = state.cut_start_total_seconds
    end_total = state.cut_end_total_seconds

    assert start_total == (2 * 3600)               # 7200 seconds
    assert end_total == (1 * 3600) + (30 * 60)    # 5400 seconds
    assert end_total < start_total, "End time is before start time (invalid)"


def test_validation_edge_case_same_hour_different_minutes():
    """Test validation when hours are same but minutes differ"""
    state = AppState()
    state.cut_mode = CutMode.CUT_RANGE

    # Test case: Start at 1h 45m, End at 1h 50m (should be valid)
    state.cut_start_hours = 1.0
    state.cut_start_minutes = 45.0
    state.cut_start_seconds = 0.0
    state.cut_end_hours = 1.0
    state.cut_end_minutes = 50.0
    state.cut_end_seconds = 0.0

    start_total = state.cut_start_total_seconds
    end_total = state.cut_end_total_seconds

    assert start_total == (1 * 3600) + (45 * 60)  # 6300 seconds
    assert end_total == (1 * 3600) + (50 * 60)    # 6600 seconds
    assert end_total > start_total, "End time should be after start time"


def test_user_reported_scenario():
    """Test the exact scenario user reported: 2h movie, start=10s, end=4m10s"""
    state = AppState()
    state.cut_mode = CutMode.CUT_RANGE

    # User's test case
    state.cut_start_hours = 0.0
    state.cut_start_minutes = 0.0
    state.cut_start_seconds = 10.0
    state.cut_end_hours = 0.0
    state.cut_end_minutes = 4.0
    state.cut_end_seconds = 10.0

    start_total = state.cut_start_total_seconds  # 10 seconds
    end_total = state.cut_end_total_seconds      # 250 seconds (4m 10s)
    duration = end_total - start_total            # 240 seconds = 4 minutes

    assert start_total == 10
    assert end_total == 250
    assert duration == 240
    assert duration / 60 == 4.0, "Output should be exactly 4 minutes"


def test_hours_in_cut_last_mode():
    """Test hours calculation for CUT_LAST mode"""
    state = AppState()
    state.cut_mode = CutMode.CUT_LAST

    # Remove last 2 hours 15 minutes 30 seconds
    state.cut_hours = 2.0
    state.cut_minutes = 15.0
    state.cut_seconds = 30.0

    total = state.cut_total_seconds
    expected = (2 * 3600) + (15 * 60) + 30  # 8130 seconds

    assert total == expected


def test_hours_in_cut_first_mode():
    """Test hours calculation for CUT_FIRST mode"""
    state = AppState()
    state.cut_mode = CutMode.CUT_FIRST

    # Remove first 1 hour 5 minutes 0 seconds
    state.cut_hours = 1.0
    state.cut_minutes = 5.0
    state.cut_seconds = 0.0

    total = state.cut_total_seconds
    expected = (1 * 3600) + (5 * 60)  # 3900 seconds

    assert total == expected
