"""
Integration tests for the cut-unit feature (TIME / PERCENT / FRAMES).

Generates a short test video with ffmpeg, then runs VideoProcessor.process_video
with different cut_unit settings and verifies the output video duration matches
expectations.

Skipped automatically if ffmpeg is not on PATH.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from src.state import AppState, CutUnit
from src.video_processor import VideoProcessor


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def _make_test_video(path: Path, seconds: int = 10, fps: int = 30) -> None:
    """Generate a test-pattern video at a known frame rate."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"testsrc=size=320x240:rate={fps}",
        "-t", str(seconds),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _probe_duration(path: Path) -> float:
    """Return the duration of a video file in seconds via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


@pytest.fixture(scope="module")
def test_video(tmp_path_factory) -> Path:
    if not _ffmpeg_available():
        pytest.skip("ffmpeg/ffprobe not available on PATH")
    video_path = tmp_path_factory.mktemp("videos") / "input.mp4"
    _make_test_video(video_path, seconds=10, fps=30)
    return video_path


def _run_processor(state: AppState, input_path: Path, output_path: Path):
    """Helper: run process_video and assert success."""
    processor = VideoProcessor(state)
    success, error = processor.process_video(str(input_path), str(output_path))
    assert success, f"process_video failed: {error}"
    assert output_path.exists(), "Output file was not created"


# ─── probe_video ──────────────────────────────────────────────────────────

def test_probe_video_returns_fps(test_video):
    """probe_video must return a non-zero fps for a real video."""
    state = AppState()
    processor = VideoProcessor(state)
    meta = processor.probe_video(str(test_video))
    assert meta["fps"] == pytest.approx(30.0, abs=0.5)
    assert meta["duration"] == pytest.approx(10.0, abs=0.5)


# ─── PERCENT unit ──────────────────────────────────────────────────────────

def test_percent_cut_last_half(tmp_path, test_video):
    """Remove last 50% of a 10s video → output ≈ 5s."""
    state = AppState()
    state.cut_unit = CutUnit.PERCENT
    state.cut_start_enabled = False
    state.cut_end_enabled = True
    state.cut_end_percent = 50.0  # remove last 50 %

    out = tmp_path / "out_pct_half.mp4"
    _run_processor(state, test_video, out)
    duration = _probe_duration(out)
    assert duration == pytest.approx(5.0, abs=0.5)


def test_percent_cut_first_30(tmp_path, test_video):
    """Remove first 30% of a 10s video → output ≈ 7s."""
    state = AppState()
    state.cut_unit = CutUnit.PERCENT
    state.cut_start_enabled = True
    state.cut_start_percent = 30.0
    state.cut_end_enabled = False

    out = tmp_path / "out_pct_first30.mp4"
    _run_processor(state, test_video, out)
    duration = _probe_duration(out)
    assert duration == pytest.approx(7.0, abs=0.5)


def test_percent_range_keep_middle(tmp_path, test_video):
    """Keep 20%-80% of a 10s video → output ≈ 6s (from 2s to 8s)."""
    state = AppState()
    state.cut_unit = CutUnit.PERCENT
    state.cut_start_enabled = True
    state.cut_start_percent = 20.0
    state.cut_end_enabled = True
    state.cut_end_percent = 20.0  # remove 20% from end

    out = tmp_path / "out_pct_range.mp4"
    _run_processor(state, test_video, out)
    duration = _probe_duration(out)
    assert duration == pytest.approx(6.0, abs=0.5)


# ─── FRAMES unit ───────────────────────────────────────────────────────────

def test_frames_cut_last_90(tmp_path, test_video):
    """Remove last 90 frames at 30fps (=3s) from 10s video → output ≈ 7s."""
    state = AppState()
    state.cut_unit = CutUnit.FRAMES
    state.cut_start_enabled = False
    state.cut_end_enabled = True
    state.cut_end_frame = 90  # 90 frames / 30 fps = 3 seconds

    out = tmp_path / "out_frames_last90.mp4"
    _run_processor(state, test_video, out)
    duration = _probe_duration(out)
    assert duration == pytest.approx(7.0, abs=0.5)


def test_frames_cut_first_60(tmp_path, test_video):
    """Remove first 60 frames at 30fps (=2s) from 10s video → output ≈ 8s."""
    state = AppState()
    state.cut_unit = CutUnit.FRAMES
    state.cut_start_enabled = True
    state.cut_start_frame = 60
    state.cut_end_enabled = False

    out = tmp_path / "out_frames_first60.mp4"
    _run_processor(state, test_video, out)
    duration = _probe_duration(out)
    assert duration == pytest.approx(8.0, abs=0.5)


def test_frames_range_keep_middle(tmp_path, test_video):
    """Keep frames 60-240 (2s-8s at 30fps) → output ≈ 6s."""
    state = AppState()
    state.cut_unit = CutUnit.FRAMES
    state.cut_start_enabled = True
    state.cut_start_frame = 60
    state.cut_end_enabled = True
    state.cut_end_frame = 60  # remove last 60 frames (2s)

    out = tmp_path / "out_frames_range.mp4"
    _run_processor(state, test_video, out)
    duration = _probe_duration(out)
    assert duration == pytest.approx(6.0, abs=0.5)


# ─── Backward compatibility ────────────────────────────────────────────────

def test_time_unit_still_works(tmp_path, test_video):
    """With cut_unit=TIME (default), the legacy time-based path must work."""
    state = AppState()
    state.cut_unit = CutUnit.TIME
    state.cut_start_enabled = True
    state.cut_start_hours = 0.0
    state.cut_start_minutes = 0.0
    state.cut_start_seconds = 4.0
    state.cut_end_enabled = False

    out = tmp_path / "out_time.mp4"
    _run_processor(state, test_video, out)
    duration = _probe_duration(out)
    assert duration == pytest.approx(6.0, abs=0.5)


def test_no_cut_passes_through(tmp_path, test_video):
    """With no trim enabled, output duration should match input."""
    state = AppState()
    state.cut_unit = CutUnit.PERCENT
    state.cut_start_enabled = False
    state.cut_end_enabled = False

    out = tmp_path / "out_nocut.mp4"
    _run_processor(state, test_video, out)
    duration = _probe_duration(out)
    assert duration == pytest.approx(10.0, abs=0.5)
