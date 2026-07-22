"""Unit tests for SPLIT mode segment calculation and output naming.

These tests verify the split logic without needing real FFmpeg, by
mocking the actual encode calls and checking the parameters passed.
"""

import pytest
from unittest.mock import patch

from src.state import AppState, CutUnit
from src.video_processor import VideoProcessor


@pytest.fixture
def fake_video(tmp_path):
    """Create a real empty file so os.path.isfile() passes."""
    p = tmp_path / "input.mp4"
    p.write_bytes(b"\x00")
    return p


class TestSplitSegmentCalculation:
    """Test that split mode divides the video into correct segments."""

    def _setup_state(self, n_parts=2, trim_start=False, trim_end=False):
        state = AppState()
        state.cut_unit = CutUnit.SPLIT
        state.split_parts = n_parts
        state.cut_start_enabled = trim_start
        state.cut_end_enabled = trim_end
        return state

    @patch.object(VideoProcessor, "_process_with_subprocess")
    @patch.object(VideoProcessor, "probe_video")
    def test_two_parts_no_trim(self, mock_probe, mock_subprocess, fake_video):
        """10s video split into 2 → each segment 5s."""
        mock_probe.return_value = {"duration": 10.0, "fps": 30.0}
        mock_subprocess.return_value = (True, None)

        state = self._setup_state(n_parts=2)
        proc = VideoProcessor(state)
        out = str(fake_video.parent / "output.mp4")
        proc.process_video(str(fake_video), out)

        assert mock_subprocess.call_count == 2
        # First call: start=0, duration=5
        args1 = mock_subprocess.call_args_list[0][0]
        assert args1[3] == pytest.approx(0.0)   # start_time
        assert args1[2] == pytest.approx(5.0)   # duration

        # Second call: start=5, duration=5
        args2 = mock_subprocess.call_args_list[1][0]
        assert args2[3] == pytest.approx(5.0)
        assert args2[2] == pytest.approx(5.0)

    @patch.object(VideoProcessor, "_process_with_subprocess")
    @patch.object(VideoProcessor, "probe_video")
    def test_four_parts_no_trim(self, mock_probe, mock_subprocess, fake_video):
        """12s video split into 4 → each segment 3s."""
        mock_probe.return_value = {"duration": 12.0, "fps": 30.0}
        mock_subprocess.return_value = (True, None)

        state = self._setup_state(n_parts=4)
        proc = VideoProcessor(state)
        out = str(fake_video.parent / "output.mp4")
        proc.process_video(str(fake_video), out)

        assert mock_subprocess.call_count == 4
        for i in range(4):
            args = mock_subprocess.call_args_list[i][0]
            assert args[3] == pytest.approx(i * 3.0)  # start_time
            assert args[2] == pytest.approx(3.0)       # duration

    @patch.object(VideoProcessor, "_process_with_subprocess")
    @patch.object(VideoProcessor, "probe_video")
    def test_split_with_start_trim(self, mock_probe, mock_subprocess, fake_video):
        """10s video, trim 2s from start, split into 2 → segments at 2s and 7s."""
        mock_probe.return_value = {"duration": 10.0, "fps": 30.0}
        mock_subprocess.return_value = (True, None)

        state = self._setup_state(n_parts=2, trim_start=True)
        state.cut_start_hours = 0
        state.cut_start_minutes = 0
        state.cut_start_seconds = 2.0
        proc = VideoProcessor(state)
        out = str(fake_video.parent / "output.mp4")
        proc.process_video(str(fake_video), out)

        assert mock_subprocess.call_count == 2
        # First segment: start=2, duration=4
        args1 = mock_subprocess.call_args_list[0][0]
        assert args1[3] == pytest.approx(2.0)
        assert args1[2] == pytest.approx(4.0)
        # Second segment: start=6, duration=4
        args2 = mock_subprocess.call_args_list[1][0]
        assert args2[3] == pytest.approx(6.0)
        assert args2[2] == pytest.approx(4.0)

    @patch.object(VideoProcessor, "_process_with_subprocess")
    @patch.object(VideoProcessor, "probe_video")
    def test_split_output_filenames(self, mock_probe, mock_subprocess, fake_video):
        """Output files should have _part1, _part2 suffixes."""
        mock_probe.return_value = {"duration": 10.0, "fps": 30.0}
        mock_subprocess.return_value = (True, None)

        state = self._setup_state(n_parts=3)
        proc = VideoProcessor(state)
        out = str(fake_video.parent / "output.mp4")
        proc.process_video(str(fake_video), out)

        output_paths = [call.args[1] for call in mock_subprocess.call_args_list]
        assert f"{fake_video.parent}/output_part1.mp4" in output_paths
        assert f"{fake_video.parent}/output_part2.mp4" in output_paths
        assert f"{fake_video.parent}/output_part3.mp4" in output_paths

    @patch.object(VideoProcessor, "_process_with_subprocess")
    @patch.object(VideoProcessor, "probe_video")
    def test_split_zero_pad_for_large_parts(self, mock_probe, mock_subprocess, fake_video):
        """10+ parts should zero-pad: part01, part02, ..., part10."""
        mock_probe.return_value = {"duration": 100.0, "fps": 30.0}
        mock_subprocess.return_value = (True, None)

        state = self._setup_state(n_parts=10)
        proc = VideoProcessor(state)
        out = str(fake_video.parent / "output.mp4")
        proc.process_video(str(fake_video), out)

        output_paths = [call.args[1] for call in mock_subprocess.call_args_list]
        assert f"{fake_video.parent}/output_part01.mp4" in output_paths
        assert f"{fake_video.parent}/output_part10.mp4" in output_paths

    @patch.object(VideoProcessor, "_process_with_subprocess")
    @patch.object(VideoProcessor, "probe_video")
    def test_split_failure_aborts_remaining(self, mock_probe, mock_subprocess, fake_video):
        """If one segment fails, processing should stop and return failure."""
        mock_probe.return_value = {"duration": 10.0, "fps": 30.0}
        mock_subprocess.side_effect = [(False, "encode error"), (True, None)]

        state = self._setup_state(n_parts=2)
        proc = VideoProcessor(state)
        out = str(fake_video.parent / "output.mp4")
        success, err = proc.process_video(str(fake_video), out)

        assert not success
        assert "Part 1" in err or "encode error" in err
        assert mock_subprocess.call_count == 1  # second part should not run
