"""
Utilities for logo position input: coordinate parsing and frame extraction.
"""

import re
from typing import Optional, Tuple

import cv2
import numpy as np


def parse_logo_coordinates(text: str) -> Optional[Tuple[int, int, int, int]]:
    """Parse a pasted text string into (x, y, w, h) coordinates.

    Accepts many common formats:
        "100, 200, 50, 30"
        "x=100, y=200, w=50, h=30"
        "x:100 y:200 w:50 h:30"
        "100 200 50 30"
        "X: 100  Y: 200  W: 50  H: 30"

    Args:
        text: Raw pasted text.

    Returns:
        Tuple of (x, y, w, h) as ints, or None if the text doesn't contain
        exactly 4 non-negative integers.
    """
    numbers = re.findall(r"-?\d+", text)
    if len(numbers) != 4:
        return None
    try:
        vals = tuple(int(n) for n in numbers)
    except ValueError:
        return None
    if any(v < 0 for v in vals):
        return None
    return vals  # type: ignore[return-value]


def extract_preview_frame(
    video_path: str, position_frac: float = 0.1
) -> Optional[np.ndarray]:
    """Extract a single BGR frame from a video for preview display.

    Args:
        video_path: Path to the video file.
        position_frac: Fraction into the video to seek (0.0 = first frame,
            0.5 = middle). Defaults to 0.1 (past intro).

    Returns:
        BGR frame as np.ndarray (H, W, 3), or None if the video can't be
        opened or the frame can't be read.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    try:
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total > 0:
            target = int(total * max(0.0, min(1.0, position_frac)))
            cap.set(cv2.CAP_PROP_POS_FRAMES, target)
        ret, frame = cap.read()
        return frame if ret else None
    finally:
        cap.release()


def scale_frame_for_display(
    frame: np.ndarray, max_width: int = 900, max_height: int = 600
) -> Tuple[np.ndarray, float]:
    """Scale a frame to fit within max dimensions while keeping aspect ratio.

    Args:
        frame: BGR or RGB frame as np.ndarray (H, W, C).
        max_width: Maximum display width in pixels.
        max_height: Maximum display height in pixels.

    Returns:
        Tuple of (scaled_frame, scale_factor). scale_factor is the ratio
        display/original (e.g. 0.5 means displayed at half size).
        If no scaling needed, returns (frame, 1.0).
    """
    h, w = frame.shape[:2]
    scale = min(max_width / w, max_height / h, 1.0)
    if scale >= 1.0:
        return frame, 1.0
    new_w = int(w * scale)
    new_h = int(h * scale)
    scaled = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return scaled, scale
