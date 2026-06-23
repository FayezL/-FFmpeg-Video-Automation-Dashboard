"""
Shared helpers for logo detection.

Pure functions for filtering candidate rectangles by size, aspect ratio, and
corner position. Used by both the legacy edge-based detector and the new
temporal-stability detector to avoid duplication.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Rect:
    """Immutable rectangle in pixel coordinates."""
    x: int
    y: int
    w: int
    h: int


def passes_size_filter(width: int, height: int,
                       min_w: int, min_h: int,
                       max_w: int, max_h: int) -> bool:
    """Return True if a rectangle's size is within the allowed logo range."""
    if width < min_w or width > max_w:
        return False
    if height < min_h or height > max_h:
        return False
    return True


def passes_aspect_ratio_filter(width: int, height: int,
                               ar_min: float, ar_max: float) -> bool:
    """Return True if width/height aspect ratio is within [ar_min, ar_max]."""
    if height <= 0:
        return False
    ar = width / height
    return ar_min <= ar <= ar_max


def passes_position_filter(rect: Rect,
                            video_resolution,
                            position_zones: List[str]) -> bool:
    """
    Return True if the rectangle's center is in one of the enabled corner zones.

    Corner zones are defined as the outer 25% of the frame on each axis:
      - left_threshold   = video_width  * 0.25
      - right_threshold  = video_width  * 0.75
      - top_threshold    = video_height * 0.25
      - bottom_threshold = video_height * 0.75

    Empty `position_zones` disables position filtering (returns True for any rect).
    """
    if not position_zones:
        return True

    video_width, video_height = video_resolution
    center_x = rect.x + rect.w / 2
    center_y = rect.y + rect.h / 2

    left_threshold = video_width * 0.25
    right_threshold = video_width * 0.75
    top_threshold = video_height * 0.25
    bottom_threshold = video_height * 0.75

    for zone in position_zones:
        if zone == "top-left" and center_x < left_threshold and center_y < top_threshold:
            return True
        if zone == "top-right" and center_x > right_threshold and center_y < top_threshold:
            return True
        if zone == "bottom-left" and center_x < left_threshold and center_y > bottom_threshold:
            return True
        if zone == "bottom-right" and center_x > right_threshold and center_y > bottom_threshold:
            return True
    return False
