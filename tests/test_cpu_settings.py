"""
Tests for CPU usage control: FFmpeg thread limiting and process priority.
"""

from src.state import AppState


class TestCpuSettingsDefaults:
    """Test that CPU control fields exist with sensible defaults."""

    def test_ffmpeg_threads_default(self):
        state = AppState()
        assert state.ffmpeg_threads == 2

    def test_process_priority_default(self):
        state = AppState()
        assert state.process_priority == "low"

    def test_ffmpeg_threads_can_be_changed(self):
        state = AppState()
        state.ffmpeg_threads = 4
        assert state.ffmpeg_threads == 4

    def test_process_priority_can_be_changed(self):
        state = AppState()
        state.process_priority = "normal"
        assert state.process_priority == "normal"


class TestThreadsInCommand:
    """Test that -threads flag appears in the FFmpeg command."""

    def test_threads_flag_in_command(self):
        """The subprocess command should include -threads with the configured value."""
        import shutil
        import subprocess
        from pathlib import Path
        import pytest

        if not shutil.which("ffmpeg"):
            pytest.skip("ffmpeg not available")

        # Create a tiny test video
        import tempfile
        tmp = Path(tempfile.mkdtemp())
        inp = tmp / "in.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=160x120:rate=1",
             "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(inp)],
            check=True, capture_output=True,
        )

        from src.video_processor import VideoProcessor

        state = AppState()
        state.ffmpeg_threads = 3
        state.cut_start_enabled = False
        state.cut_end_enabled = False

        proc = VideoProcessor(state)
        out = tmp / "out.mp4"

        # Capture the command by intercepting on_log
        logged_cmd = []
        def capture_log(msg):
            if "Command:" in msg:
                logged_cmd.append(msg)

        success, err = proc.process_video(str(inp), str(out), on_log=capture_log)
        assert success, f"Processing failed: {err}"

        # The command should contain -threads 3
        cmd_text = " ".join(logged_cmd)
        assert "-threads 3" in cmd_text, f"Threads flag missing from command: {cmd_text}"
