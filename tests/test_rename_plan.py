"""
Tests for the Rename Plan feature — sequential episode naming.

All tests are pure unit tests: no FFmpeg, no UI, no filesystem writes.
Works for any batch size: 1 file, 30 episodes, 50+.
"""

from src.state import AppState
from src.video_processor import VideoProcessor


def make_processor(state: AppState) -> VideoProcessor:
    """Create a VideoProcessor with a minimal AppState."""
    return VideoProcessor(state)


def get_output_name(processor: VideoProcessor, input_path: str, file_index: int = 0) -> str:
    """Helper: extract just the filename from _get_output_path."""
    import os
    full = processor._get_output_path(input_path, file_index=file_index)
    return os.path.basename(full)


# ---------------------------------------------------------------------------
# Rename DISABLED — must keep original filename behaviour
# ---------------------------------------------------------------------------

class TestRenameDisabled:
    def test_rename_off_keeps_original_name(self):
        """When rename_enabled=False, output keeps the original file stem."""
        state = AppState()
        state.rename_enabled = False
        state.output_format = "mp4"
        state.output_folder = "/output"
        proc = make_processor(state)

        assert get_output_name(proc, "/input/episode_01.mkv", file_index=0) == "episode_01.mp4"

    def test_rename_off_applies_prefix_suffix(self):
        """Prefix/suffix still apply when rename is off."""
        state = AppState()
        state.rename_enabled = False
        state.output_prefix = "OUT_"
        state.output_suffix = "_done"
        state.output_format = "mp4"
        state.output_folder = "/output"
        proc = make_processor(state)

        assert get_output_name(proc, "/input/hamo1.mkv", file_index=0) == "OUT_hamo1_done.mp4"

    def test_rename_off_empty_base_falls_back(self):
        """Enabling rename with an empty base falls back to original filename."""
        state = AppState()
        state.rename_enabled = True
        state.rename_base = ""          # Empty — should fall back
        state.output_format = "mp4"
        state.output_folder = "/output"
        proc = make_processor(state)

        assert get_output_name(proc, "/input/hamo5.mkv", file_index=4) == "hamo5.mp4"


# ---------------------------------------------------------------------------
# Rename ENABLED — sequential numbering
# ---------------------------------------------------------------------------

class TestRenameEnabled:
    def _make_state(self, base="hamo", start=1, pad=2, fmt="mp4") -> AppState:
        state = AppState()
        state.rename_enabled = True
        state.rename_base = base
        state.rename_start = start
        state.rename_pad = pad
        state.output_format = fmt
        state.output_folder = "/output"
        return state

    def test_single_file(self):
        """1 file → hamo01.mp4"""
        proc = make_processor(self._make_state())
        assert get_output_name(proc, "/input/anything.mkv", file_index=0) == "hamo01.mp4"

    def test_three_files(self):
        """3 files → hamo01, hamo02, hamo03"""
        proc = make_processor(self._make_state())
        results = [get_output_name(proc, f"/in/ep{i}.mkv", file_index=i) for i in range(3)]
        assert results == ["hamo01.mp4", "hamo02.mp4", "hamo03.mp4"]

    def test_thirty_files(self):
        """30 files → hamo01 … hamo30"""
        proc = make_processor(self._make_state())
        results = [get_output_name(proc, f"/in/ep{i}.mkv", file_index=i) for i in range(30)]
        assert results[0]  == "hamo01.mp4"
        assert results[29] == "hamo30.mp4"
        assert len(results) == 30

    def test_fifty_files(self):
        """50 files → hamo01 … hamo50"""
        proc = make_processor(self._make_state())
        results = [get_output_name(proc, f"/in/ep{i}.mkv", file_index=i) for i in range(50)]
        assert results[0]  == "hamo01.mp4"
        assert results[49] == "hamo50.mp4"

    def test_three_digit_padding(self):
        """pad=3 → hamo001, ..., hamo030 for 30 files"""
        proc = make_processor(self._make_state(pad=3))
        results = [get_output_name(proc, f"/in/ep{i}.mkv", file_index=i) for i in range(30)]
        assert results[0]  == "hamo001.mp4"
        assert results[29] == "hamo030.mp4"

    def test_custom_start_number(self):
        """start=10 → hamo10, hamo11, … for 3 files"""
        proc = make_processor(self._make_state(start=10))
        results = [get_output_name(proc, f"/in/ep{i}.mkv", file_index=i) for i in range(3)]
        assert results == ["hamo10.mp4", "hamo11.mp4", "hamo12.mp4"]

    def test_mkv_output_format(self):
        """Rename plan respects the chosen container format."""
        proc = make_processor(self._make_state(fmt="mkv"))
        assert get_output_name(proc, "/in/ep0.mkv", file_index=0) == "hamo01.mkv"

    def test_custom_base_name(self):
        """Any base name works → anime_S01E01.mp4 style."""
        proc = make_processor(self._make_state(base="anime_S01E", start=1, pad=2))
        results = [get_output_name(proc, f"/in/ep{i}.mkv", file_index=i) for i in range(3)]
        assert results == ["anime_S01E01.mp4", "anime_S01E02.mp4", "anime_S01E03.mp4"]

    def test_base_name_strips_whitespace(self):
        """Leading/trailing whitespace in base name is stripped."""
        state = self._make_state(base="  hamo  ")
        proc = make_processor(state)
        assert get_output_name(proc, "/in/ep.mkv", file_index=0) == "hamo01.mp4"
