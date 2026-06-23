"""
Logo detection using temporal stability analysis.

A logo is a static visual element: its pixels stay nearly identical across many
frames while the rest of the frame changes (action, scene cuts, subtitles that
come and go). By computing per-pixel variance over a sample of frames we isolate
the static overlay layer and find candidate logo rectangles.

This detector replaces the legacy edge-based detector as the default for static
corner logos. It produces far fewer false positives because high-contrast edges
in busy scenes are not stable over time and are therefore rejected.

No deep learning, no API calls, no third-party dependencies beyond OpenCV/NumPy.
"""

from typing import Callable, List, Optional
from typing import Tuple  # noqa: F401

import cv2  # noqa: F401
import numpy as np  # noqa: F401

from src.data_models import DetectionConfig, DetectionResult, DetectionSession  # noqa: F401
from src.exceptions import (  # noqa: F401
    DetectionCancelledError,
    DetectionFailedError,
    VideoReadError,
)
from src.logo_detection_utils import Rect  # noqa: F401


class TemporalLogoDetector:
    """
    Detects static logos by analyzing per-pixel temporal variance across
    sampled frames.
    """

    def __init__(self, config: DetectionConfig):
        self.config = config
        self._cancelled = False

    @staticmethod
    def _sample_frame_indices(
        total_frames: int,
        num_frames: int,
        skip_intro_frac: float,
        skip_outro_frac: float,
    ) -> List[int]:
        """Return evenly-spaced frame indices, skipping intro/outro regions.

        Args:
            total_frames: Total frame count of the video.
            num_frames: How many frames to sample.
            skip_intro_frac: Fraction of the video to skip at the start (0.0-0.5).
            skip_outro_frac: Fraction of the video to skip at the end (0.0-0.5).

        Returns:
            List of integer frame indices, evenly spaced within the allowed window.
            Returns fewer than `num_frames` if `total_frames` is small.
            Returns [] if `total_frames` is 0.
        """
        if total_frames <= 0:
            return []

        start = int(total_frames * skip_intro_frac)
        end = int(total_frames * (1.0 - skip_outro_frac))
        if end <= start:
            end = max(end, start + 1)
        if end > total_frames:
            end = total_frames

        window = end - start
        count = min(num_frames, window)
        if count <= 0:
            return []
        if count == 1:
            return [start + window // 2]

        step = (window - 1) / (count - 1)
        return [int(start + round(i * step)) for i in range(count)]

    def detect_in_video(
        self,
        video_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> DetectionSession:
        """Detect static logo regions in a video file.

        Args:
            video_path: Path to the input video.
            progress_callback: Optional callback(progress_fraction, status_message).
            cancel_check: Optional callback() -> bool; return True to abort.

        Returns:
            DetectionSession containing all candidate logo regions.

        Raises:
            VideoReadError: If the video cannot be opened.
            DetectionFailedError: If detection fails unexpectedly.
            DetectionCancelledError: If the caller cancels via cancel_check.
        """
        raise NotImplementedError("Implemented in Task 10")
