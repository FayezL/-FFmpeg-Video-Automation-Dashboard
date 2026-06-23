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

from typing import Callable, List, Optional, Tuple  # noqa: F401

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
