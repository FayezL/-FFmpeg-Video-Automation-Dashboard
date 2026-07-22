"""Tests for the parse_timestamp function used by MARKERS cut mode."""

import pytest

from src.video_processor import parse_timestamp


class TestParseTimestampValid:
    """Test valid timestamp formats."""

    def test_hh_mm_ss(self):
        assert parse_timestamp("01:30:45") == pytest.approx(5445.0)

    def test_hh_mm_ss_with_centiseconds(self):
        assert parse_timestamp("00:01:30.50") == pytest.approx(90.5)

    def test_mm_ss(self):
        assert parse_timestamp("05:30") == pytest.approx(330.0)

    def test_mm_ss_with_centiseconds(self):
        assert parse_timestamp("02:30.25") == pytest.approx(150.25)

    def test_plain_seconds(self):
        assert parse_timestamp("90") == pytest.approx(90.0)

    def test_plain_seconds_float(self):
        assert parse_timestamp("90.5") == pytest.approx(90.5)

    def test_zero(self):
        assert parse_timestamp("0") == pytest.approx(0.0)

    def test_zero_time(self):
        assert parse_timestamp("00:00:00") == pytest.approx(0.0)

    def test_large_hours(self):
        assert parse_timestamp("10:00:00") == pytest.approx(36000.0)

    def test_single_digit_parts(self):
        assert parse_timestamp("1:2:3") == pytest.approx(3723.0)

    def test_whitespace_trimmed(self):
        assert parse_timestamp("  01:30:00  ") == pytest.approx(5400.0)


class TestParseTimestampEmpty:
    """Test empty / None values."""

    def test_empty_string_returns_zero(self):
        assert parse_timestamp("") == 0.0

    def test_whitespace_only_returns_zero(self):
        assert parse_timestamp("   ") == 0.0


class TestParseTimestampInvalid:
    """Test invalid inputs raise ValueError."""

    def test_negative_seconds(self):
        with pytest.raises(ValueError):
            parse_timestamp("-5")

    def test_non_numeric(self):
        with pytest.raises(ValueError):
            parse_timestamp("abc")

    def test_too_many_colons(self):
        with pytest.raises(ValueError):
            parse_timestamp("1:2:3:4")

    def test_empty_parts(self):
        with pytest.raises(ValueError):
            parse_timestamp("1::30")

    def test_non_numeric_in_time(self):
        with pytest.raises(ValueError):
            parse_timestamp("ab:30:00")

    def test_minutes_over_59(self):
        with pytest.raises(ValueError):
            parse_timestamp("01:75:00")

    def test_seconds_over_59(self):
        with pytest.raises(ValueError):
            parse_timestamp("01:00:75")
