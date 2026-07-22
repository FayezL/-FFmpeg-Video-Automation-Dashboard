"""
Integration tests for the cut-unit feature (TIME / SPLIT / MARKERS).

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


# --- probe_video --------------------------------------------------------

def test_probe_video_returns_duration(test_video):
    """probe_video must return correct duration for a real video."""
    state = AppState()
    processor = VideoProcessor(state)
    meta = processor.probe_video(str(test_video))
    assert meta["duration"] == pytest.approx(10.0, abs=0.5)


# --- MARKERS unit --------------------------------------------------------

def test_markers_cut_range(tmp_path, test_video):
    """Cut from 2s to 8s of a 10s video → output ≈ 6s."""
    state = AppState()
    state.cut_unit = CutUnit.MARKERS
    state.cut_markers_start = "00:00:02"
    state.cut_markers_end = "00:00:08"

    out = tmp_path / "out_markers_range.mp4"
    _run_processor(state, test_video, out)
    duration = _probe_duration(out)
    assert duration == pytest.approx(6.0, abs=0.5)


def test_markers_cut_start_only(tmp_path, test_video):
    """Cut from 3s to end of a 10s video → output ≈ 7s."""
    state = AppState()
    state.cut_unit = CutUnit.MARKERS
    state.cut_markers_start = "00:00:03"
    state.cut_markers_end = ""  # blank = to end

    out = tmp_path / "out_markers_start.mp4"
    _run_processor(state, test_video, out)
    duration = _probe_duration(out)
    assert duration == pytest.approx(7.0, abs=0.5)


def test_markers_short_format(tmp_path, test_video):
    """Using MM:SS format for timestamps should work the same."""
    state = AppState()
    state.cut_unit = CutUnit.MARKERS
    state.cut_markers_start = "00:04"  # 4 seconds
    state.cut_markers_end = "00:08"   # 8 seconds

    out = tmp_path / "out_markers_short.mp4"
    _run_processor(state, test_video, out)
    duration = _probe_duration(out)
    assert duration == pytest.approx(4.0, abs=0.5)


def test_markers_plain_seconds(tmp_path, test_video):
    """Using plain seconds should also work."""
    state = AppState()
    state.cut_unit = CutUnit.MARKERS
    state.cut_markers_start = "5"
    state.cut_markers_end = "9"

    out = tmp_path / "out_markers_plain.mp4"
    _run_processor(state, test_video, out)
    duration = _probe_duration(out)
    assert duration == pytest.approx(4.0, abs=0.5)


# --- SPLIT unit ----------------------------------------------------------

def test_split_into_two(tmp_path, test_video):
    """Split a 10s video into 2 parts → each ≈ 5s."""
    state = AppState()
    state.cut_unit = CutUnit.SPLIT
    state.split_parts = 2
    state.cut_start_enabled = False
    state.cut_end_enabled = False

    out = tmp_path / "out_split.mp4"
    processor = VideoProcessor(state)
    success, error = processor.process_video(str(test_video), str(out))
    assert success, f"Split failed: {error}"

    part1 = tmp_path / "out_split_part1.mp4"
    part2 = tmp_path / "out_split_part2.mp4"
    assert part1.exists(), "Part 1 not created"
    assert part2.exists(), "Part 2 not created"

    d1 = _probe_duration(part1)
    d2 = _probe_duration(part2)
    assert d1 == pytest.approx(5.0, abs=0.7)
    assert d2 == pytest.approx(5.0, abs=0.7)


def test_split_into_four(tmp_path, test_video):
    """Split a 10s video into 4 parts → each ≈ 2.5s."""
    state = AppState()
    state.cut_unit = CutUnit.SPLIT
    state.split_parts = 4
    state.cut_start_enabled = False
    state.cut_end_enabled = False

    out = tmp_path / "out_split4.mp4"
    processor = VideoProcessor(state)
    success, error = processor.process_video(str(test_video), str(out))
    assert success, f"Split failed: {error}"

    for i in range(1, 5):
        part = tmp_path / f"out_split4_part{i}.mp4"
        assert part.exists(), f"Part {i} not created"
        d = _probe_duration(part)
        assert d == pytest.approx(2.5, abs=0.8), f"Part {i} duration {d}s not ~2.5s"


def test_split_with_trim(tmp_path, test_video):
    """Trim 2s from start, then split remaining 8s into 2 parts → each ≈ 4s."""
    state = AppState()
    state.cut_unit = CutUnit.SPLIT
    state.split_parts = 2
    state.cut_start_enabled = True
    state.cut_start_hours = 0
    state.cut_start_minutes = 0
    state.cut_start_seconds = 2.0
    state.cut_end_enabled = False

    out = tmp_path / "out_split_trim.mp4"
    processor = VideoProcessor(state)
    success, error = processor.process_video(str(test_video), str(out))
    assert success, f"Split with trim failed: {error}"

    part1 = tmp_path / "out_split_trim_part1.mp4"
    part2 = tmp_path / "out_split_trim_part2.mp4"
    assert part1.exists(), "Part 1 not created"
    assert part2.exists(), "Part 2 not created"

    d1 = _probe_duration(part1)
    d2 = _probe_duration(part2)
    assert d1 == pytest.approx(4.0, abs=0.7)
    assert d2 == pytest.approx(4.0, abs=0.7)


# --- Backward compatibility -----------------------------------------------

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
    state.cut_unit = CutUnit.MARKERS
    state.cut_markers_start = "00:00:00"
    state.cut_markers_end = ""

    out = tmp_path / "out_nocut.mp4"
    _run_processor(state, test_video, out)
    duration = _probe_duration(out)
    assert duration == pytest.approx(10.0, abs=0.5)
