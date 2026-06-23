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

import cv2
import numpy as np

from src.data_models import DetectionConfig, DetectionResult, DetectionSession  # noqa: F401
from src.exceptions import (  # noqa: F401
    DetectionCancelledError,
    DetectionFailedError,
    VideoReadError,
)
from src.logo_detection_utils import Rect


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

    @staticmethod
    def _compute_variance_map(frames_stack: np.ndarray) -> np.ndarray:
        """Compute per-pixel temporal variance across a stack of grayscale frames.

        Args:
            frames_stack: NumPy array of shape (N, H, W), dtype uint8 (grayscale).

        Returns:
            np.ndarray of shape (H, W), dtype float32 — per-pixel variance.
            For an empty stack (N=0), returns zeros of shape (H, W).
        """
        if frames_stack.shape[0] == 0:
            h, w = frames_stack.shape[1], frames_stack.shape[2]
            return np.zeros((h, w), dtype=np.float32)

        # Convert to float to avoid integer overflow in variance.
        frames_float = frames_stack.astype(np.float32)
        return np.var(frames_float, axis=0)

    @staticmethod
    def _threshold_variance_map(
        variance_map: np.ndarray,
        sensitivity: float,
        base_threshold: float,
    ) -> np.ndarray:
        """Convert variance map to a binary mask of "static" pixels.

        Pixels whose variance is below the effective threshold are marked 255
        (static), the rest are marked 0.

        The effective threshold scales with sensitivity:
            effective = base * (0.1 + 0.9 * sensitivity)
        Higher sensitivity → higher threshold → more pixels accepted.
        The 0.1 floor guarantees we still catch truly-static pixels at
        sensitivity=0.0 (otherwise the threshold would be 0 and nothing
        would qualify, since variance is never negative).

        Args:
            variance_map: Per-pixel variance, shape (H, W), float32.
            sensitivity: 0.0 (strict) to 1.0 (permissive).
            base_threshold: The configured `temporal_variance_threshold`.

        Returns:
            Binary mask (uint8), 255 where static, 0 elsewhere.
        """
        effective_threshold = base_threshold * (0.1 + 0.9 * float(sensitivity))
        mask = np.where(variance_map < effective_threshold, 255, 0).astype(np.uint8)
        return mask

    @staticmethod
    def _cleanup_mask(mask: np.ndarray, min_region_pixels: int) -> np.ndarray:
        """Clean a binary mask: dilate to merge nearby blobs, then drop tiny ones.

        Args:
            mask: Binary mask (uint8, 0 or 255).
            min_region_pixels: Connected components with fewer pixels than this
                are removed as noise.

        Returns:
            Cleaned binary mask (uint8, 0 or 255).
        """
        # Close small gaps so a fragmented logo merges into one blob.
        # Kernel size 5 gives a ~5px bridge between nearby regions.
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Remove tiny connected components (noise).
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
        cleaned = np.zeros_like(mask)
        for label_idx in range(1, num_labels):  # 0 = background
            area = int(stats[label_idx, cv2.CC_STAT_AREA])
            if area >= min_region_pixels:
                cleaned[labels == label_idx] = 255
        return cleaned

    @staticmethod
    def _find_candidates(mask: np.ndarray) -> List[Rect]:
        """Extract candidate rectangles from a cleaned binary mask.

        Uses OpenCV contour detection. Each external contour's bounding
        rectangle becomes one candidate.

        Args:
            mask: Cleaned binary mask (uint8, 0 or 255).

        Returns:
            List of `Rect` objects, one per detected external contour.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: List[Rect] = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            candidates.append(Rect(x=int(x), y=int(y), w=int(w), h=int(h)))
        return candidates

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
