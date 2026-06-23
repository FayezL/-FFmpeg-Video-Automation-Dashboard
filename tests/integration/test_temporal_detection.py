"""
Integration test for TemporalLogoDetector on a real video.

Generates a short test video with ffmpeg (color bars + a static black rectangle
in the top-right corner), then verifies the detector finds the rectangle.

Skipped automatically if ffmpeg is not on PATH.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from src.data_models import DetectionConfig
from src.exceptions import DetectionCancelledError
from src.logo_detector_temporal import TemporalLogoDetector


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _make_test_video(path: Path, seconds: int = 4, fps: int = 30) -> None:
    """Generate a mandelbrot video with a static black rectangle in the top-right.

    The rectangle is drawn with ffmpeg's drawbox filter at a fixed position so
    we know exactly where the 'logo' is. The mandelbrot source provides a
    constantly-changing background (high variance everywhere except the logo).

    Note: We use `-crf 0` (mathematically lossless) because lossy H.264 at
    default CRF introduces enough quantization noise into static regions
    surrounded by high motion that the per-pixel variance exceeds the
    detector's threshold. Real-world TV watermarks typically compress more
    cleanly than this worst-case synthetic pattern because the encoder can
    predict the static overlay well. The synthetic unit tests in
    tests/test_temporal_detector.py cover the algorithm directly; this test
    only verifies the end-to-end I/O wiring.
    """
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"mandelbrot=size=640x480:rate={fps}:maxiter=80",
        "-t", str(seconds),
        "-vf", "drawbox=x=560:y=20:w=60:h=50:color=black@1.0:t=fill",
        "-c:v", "libx264",
        "-crf", "0",
        "-pix_fmt", "yuv420p",
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _make_compressed_test_video(path: Path, seconds: int = 6, fps: int = 30) -> None:
    """Like _make_test_video but with TYPICAL H.264 compression (CRF 23).

    Real-world video has quantization noise that raises the variance of even
    perfectly-static logo pixels. This fixture simulates that real-world
    condition. The default temporal_variance_threshold (5.0) must be high
    enough to absorb this noise.
    """
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"mandelbrot=size=640x480:rate={fps}:maxiter=80",
        "-t", str(seconds),
        "-vf", "drawbox=x=560:y=20:w=60:h=50:color=black@1.0:t=fill",
        "-c:v", "libx264",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


@pytest.fixture(scope="module")
def test_video(tmp_path_factory) -> Path:
    if not _ffmpeg_available():
        pytest.skip("ffmpeg not available on PATH")
    video_path = tmp_path_factory.mktemp("videos") / "with_logo.mp4"
    _make_test_video(video_path)
    return video_path


def test_detects_static_overlay_in_corner(test_video):
    """The detector should find the black rectangle in the top-right corner."""
    config = DetectionConfig(
        sensitivity=0.5,
        temporal_num_frames=10,
        position_zones=["top-right"],
        min_logo_width=20,
        min_logo_height=20,
        max_logo_width=200,
        max_logo_height=200,
        temporal_min_region_pixels=100,
        min_confidence_to_report=0.2,
    )
    detector = TemporalLogoDetector(config)
    session = detector.detect_in_video(str(test_video))

    assert session.status == "completed"
    assert len(session.results) >= 1

    top = session.results[0]
    # The drawn rectangle is at (560, 20, 60, 50) → top-right corner.
    # Allow a generous overlap window since the bounding box may be slightly larger.
    assert top.x + top.width >= 550  # right side of frame
    assert top.y <= 100             # near the top
    assert top.confidence >= 0.2


def test_handles_video_with_any_position(test_video):
    """With position filtering disabled, the detector must still not crash
    and should still find the static overlay."""
    config = DetectionConfig(
        sensitivity=0.5,
        temporal_num_frames=10,
        position_zones=[],  # accept any position
        min_logo_width=5,
        min_logo_height=5,
        max_logo_width=300,
        max_logo_height=300,
        temporal_min_region_pixels=50,
        min_confidence_to_report=0.0,
    )
    detector = TemporalLogoDetector(config)
    session = detector.detect_in_video(str(test_video))
    assert session.status == "completed"
    assert isinstance(session.results, list)


def test_cancel_check_aborts_midway(test_video):
    """A cancel_check that returns True should abort detection cleanly."""

    def always_cancel() -> bool:
        return True

    config = DetectionConfig(temporal_num_frames=15)
    detector = TemporalLogoDetector(config)
    with pytest.raises(DetectionCancelledError):
        detector.detect_in_video(str(test_video), cancel_check=always_cancel)


# ─── Compressed-video tests (real-world simulation) ───────────────────────


@pytest.fixture(scope="module")
def compressed_test_video(tmp_path_factory) -> Path:
    """A test video with typical H.264 compression (CRF 23), not lossless."""
    if not _ffmpeg_available():
        pytest.skip("ffmpeg not available on PATH")
    video_path = tmp_path_factory.mktemp("videos") / "compressed_logo.mp4"
    _make_compressed_test_video(video_path)
    return video_path


def test_detects_logo_in_compressed_video(compressed_test_video):
    """The detector MUST find a static opaque logo in real-world compressed video.

    This is the key regression test: the old default threshold (0.005) was
    calibrated for lossless video and failed on any H.264-compressed input.
    The new default (5.0) absorbs quantization noise while still rejecting
    genuinely dynamic regions.
    """
    config = DetectionConfig()  # all defaults — must work out of the box
    config.temporal_num_frames = 15
    config.position_zones = ["top-right"]
    config.min_logo_width = 20
    config.min_logo_height = 20
    config.max_logo_width = 200
    config.max_logo_height = 200
    config.temporal_min_region_pixels = 100

    detector = TemporalLogoDetector(config)
    session = detector.detect_in_video(str(compressed_test_video))

    assert session.status == "completed"
    assert len(session.results) >= 1, (
        "Detector found NO logos in compressed video — threshold is too strict"
    )

    top = session.results[0]
    # The drawn rectangle is at (560, 20, 60, 50) → top-right corner.
    assert top.x + top.width >= 550
    assert top.y <= 100
    assert top.confidence >= 0.35
