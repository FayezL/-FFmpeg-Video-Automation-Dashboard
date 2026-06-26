"""
Logo detection using classical computer vision algorithms

This module implements automatic logo detection using:
- Edge detection (Canny)
- Corner detection (Harris/Shi-Tomasi)
- Region clustering and filtering
- Position-based filtering

No deep learning required - fast and lightweight.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Callable

from src.data_models import DetectionResult, DetectionConfig, DetectionSession
from src.exceptions import VideoReadError, DetectionFailedError, DetectionCancelledError


class LogoDetector:
    """
    Main logo detection engine using classical CV algorithms.

    This detector analyzes video frames to find logo-like regions using:
    1. Frame sampling (every Nth frame)
    2. Edge detection (high-contrast regions)
    3. Corner detection (rectangular patterns)
    4. Region clustering (merge similar detections)
    5. Position filtering (corners of frame)
    """

    def __init__(self, config: DetectionConfig):
        """
        Initialize detector with configuration.

        Args:
            config: Detection algorithm parameters
        """
        self.config = config
        self._cancelled = False

    def detect_in_video(
        self,
        video_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> DetectionSession:
        """
        Detect logos in a video file.

        Args:
            video_path: Path to video file
            progress_callback: Optional callback(progress_fraction, status_message)
            cancel_check: Optional callback() -> bool that returns True to cancel

        Returns:
            DetectionSession with all detected regions

        Raises:
            VideoReadError: If video cannot be opened
            DetectionFailedError: If detection fails
            DetectionCancelledError: If user cancels
        """
        # Create session
        session = DetectionSession(video_path=video_path, config=self.config)

        # Open video
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                raise VideoReadError(video_path, "Failed to open video file")

            # Get video properties
            session.video_fps = cap.get(cv2.CAP_PROP_FPS) or 1.0  # Avoid division by zero
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            session.video_duration = frame_count / session.video_fps if session.video_fps > 0 else 0.0
            session.video_resolution = (
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )

            total_frames = max(1, frame_count)
            max_frames = getattr(self.config, "max_frames_to_analyze", 5)
            max_frames = max(1, min(20, max_frames))
            keyframe_indices = self._keyframe_indices(total_frames, max_frames)
            session.total_frames_to_analyze = len(keyframe_indices)

            scale_max_h = getattr(self.config, "detection_scale_max_height", 720)
            full_w, full_h = session.video_resolution

            if progress_callback:
                progress_callback(0.0, "Starting detection (fast mode)...")

            all_detections = []
            for i, frame_index in enumerate(keyframe_indices):
                if cancel_check and cancel_check():
                    session.cancel()
                    raise DetectionCancelledError()

                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                ret, frame = cap.read()
                if not ret:
                    continue

                timestamp = frame_index / session.video_fps if session.video_fps > 0 else 0.0

                # Optionally downscale for speed (then scale boxes back)
                if scale_max_h > 0 and full_h > scale_max_h:
                    scale = scale_max_h / full_h
                    small_h = int(full_h * scale)
                    small_w = int(full_w * scale)
                    frame = cv2.resize(frame, (small_w, small_h), interpolation=cv2.INTER_AREA)
                    detect_resolution = (small_w, small_h)
                else:
                    scale = 1.0
                    detect_resolution = session.video_resolution

                frame_detections = self._detect_in_frame(
                    frame, frame_index, timestamp, detect_resolution
                )

                # Scale detections back to full resolution if we downscaled
                if scale > 0 and scale != 1.0:
                    inv = 1.0 / scale
                    for d in frame_detections:
                        d.x = int(d.x * inv)
                        d.y = int(d.y * inv)
                        d.width = int(d.width * inv)
                        d.height = int(d.height * inv)

                all_detections.extend(frame_detections)
                session.frames_analyzed += 1
                session.progress = (i + 1) / len(keyframe_indices)
                if progress_callback:
                    progress_callback(
                        session.progress,
                        f"Frame {i + 1}/{len(keyframe_indices)}..."
                    )

            # Cluster and merge similar detections across frames
            if progress_callback:
                progress_callback(0.95, "Merging similar detections...")

            merged_detections = self._cluster_detections(all_detections)

            # Only keep regions above minimum confidence (more reliable results)
            min_conf = getattr(
                self.config, "min_confidence_to_report", 0.25
            )
            for detection in merged_detections:
                if detection.confidence >= min_conf:
                    session.add_result(detection)

            # Mark complete
            session.complete()

            if progress_callback:
                progress_callback(1.0, f"Complete! Found {len(session.results)} logo regions")

            return session

        except DetectionCancelledError:
            raise
        except Exception as e:
            session.error(str(e))
            raise DetectionFailedError(str(e), video_path) from e
        finally:
            if cap is not None:
                cap.release()

    def _detect_in_frame(
        self,
        frame: np.ndarray,
        frame_index: int,
        timestamp: float,
        video_resolution: Tuple[int, int]
    ) -> List[DetectionResult]:
        """
        Detect logo-like regions in a single frame.

        Args:
            frame: BGR video frame
            frame_index: Frame number in video
            timestamp: Time in seconds
            video_resolution: (width, height) of video

        Returns:
            List of DetectionResult objects for this frame
        """
        results = []

        # Convert to grayscale and light blur to reduce noise
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        # Edge detection
        edges = cv2.Canny(
            gray,
            self.config.edge_threshold_low,
            self.config.edge_threshold_high
        )
        # Dilate to merge broken logo edges into one region (better bounding box)
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel)

        # Find contours (potential logo boundaries)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Merge nearby contours in same frame so one logo = one box (correct x,y,w,h)
        rects = [cv2.boundingRect(c) for c in contours]
        rects = self._merge_nearby_rects(rects, video_resolution)

        # Analyze each merged rect
        for (x, y, w, h) in rects:

            # Filter by size constraints
            if not self._passes_size_filter(w, h):
                continue

            # Filter by aspect ratio
            aspect_ratio = w / h if h > 0 else 0
            if not (self.config.aspect_ratio_min <= aspect_ratio <= self.config.aspect_ratio_max):
                continue

            # Filter by position (logos typically in corners)
            if not self._passes_position_filter(x, y, w, h, video_resolution):
                continue

            # Confidence: edge density in this region (use original edges before dilate for density)
            roi_edges = edges[max(0, y):min(edges.shape[0], y + h), max(0, x):min(edges.shape[1], x + w)]
            edge_density = np.sum(roi_edges > 0) / (w * h) if (w * h) > 0 else 0
            confidence = min(edge_density * 2.0, 1.0)  # Normalize to 0-1

            # Apply sensitivity threshold
            if confidence < (1.0 - self.config.sensitivity):
                continue

            # Create detection result
            result = DetectionResult(
                x=int(x),
                y=int(y),
                width=int(w),
                height=int(h),
                confidence=float(confidence),
                frame_index=frame_index,
                timestamp=timestamp,
                detection_method="edge"
            )

            results.append(result)

        return results

    def _keyframe_indices(self, total_frames: int, num_wanted: int) -> List[int]:
        """Return evenly spaced frame indices for fast analysis."""
        if total_frames <= num_wanted:
            return list(range(total_frames))
        step = (total_frames - 1) / max(1, num_wanted - 1)
        return [int(i * step) for i in range(num_wanted)]

    def _merge_nearby_rects(
        self,
        rects: List[Tuple[int, int, int, int]],
        video_resolution: Tuple[int, int]
    ) -> List[Tuple[int, int, int, int]]:
        """
        Merge rectangles that overlap or are very close (same logo fragment).
        Returns list of (x, y, w, h) that pass size/position and are merged.
        """
        if not rects:
            return []
        # Merge by overlap or proximity (gap <= 15px)
        gap = 15
        out = []
        for (x, y, w, h) in rects:
            if w < self.config.min_logo_width or h < self.config.min_logo_height:
                continue
            if w > self.config.max_logo_width or h > self.config.max_logo_height:
                continue
            merged = False
            for i, (ox, oy, ow, oh) in enumerate(out):
                # Expand both rects by gap and check overlap
                if (x + w + gap >= ox and ox + ow + gap >= x and
                        y + h + gap >= oy and oy + oh + gap >= y):
                    # Union box
                    nx = min(x, ox)
                    ny = min(y, oy)
                    nx2 = max(x + w, ox + ow)
                    ny2 = max(y + h, oy + oh)
                    out[i] = (nx, ny, nx2 - nx, ny2 - ny)
                    merged = True
                    break
            if not merged:
                out.append((x, y, w, h))
        # Second pass: merge any that still overlap after first merge
        again = True
        while again and len(out) > 1:
            again = False
            new_out = []
            for (x, y, w, h) in out:
                merged = False
                for i, (ox, oy, ow, oh) in enumerate(new_out):
                    if (x + w >= ox and ox + ow >= x and y + h >= oy and oy + oh >= y):
                        nx = min(x, ox)
                        ny = min(y, oy)
                        nx2 = max(x + w, ox + ow)
                        ny2 = max(y + h, oy + oh)
                        new_out[i] = (nx, ny, nx2 - nx, ny2 - ny)
                        merged = True
                        again = True
                        break
                if not merged:
                    new_out.append((x, y, w, h))
            out = new_out
        return out

    def _passes_size_filter(self, width: int, height: int) -> bool:
        """Check if region size is within acceptable range"""
        if width < self.config.min_logo_width or width > self.config.max_logo_width:
            return False
        if height < self.config.min_logo_height or height > self.config.max_logo_height:
            return False
        return True

    def _passes_position_filter(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        video_resolution: Tuple[int, int]
    ) -> bool:
        """
        Check if region is in a typical logo position (corners).

        Returns True if region is in any of the configured position zones.
        """
        if not self.config.position_zones:
            return True  # No position filtering

        video_width, video_height = video_resolution

        # Calculate region center
        center_x = x + width / 2
        center_y = y + height / 2

        # Define corner thresholds (logos typically in outer 25% of frame)
        left_threshold = video_width * 0.25
        right_threshold = video_width * 0.75
        top_threshold = video_height * 0.25
        bottom_threshold = video_height * 0.75

        # Check each enabled zone
        for zone in self.config.position_zones:
            if zone == "top-left" and center_x < left_threshold and center_y < top_threshold:
                return True
            elif zone == "top-right" and center_x > right_threshold and center_y < top_threshold:
                return True
            elif zone == "bottom-left" and center_x < left_threshold and center_y > bottom_threshold:
                return True
            elif zone == "bottom-right" and center_x > right_threshold and center_y > bottom_threshold:
                return True

        return False

    def _cluster_detections(self, detections: List[DetectionResult]) -> List[DetectionResult]:
        """
        Cluster similar detections across frames and merge them.

        Strategy:
        1. Group detections by spatial similarity (overlapping regions)
        2. For each cluster, keep the detection with highest confidence
        3. Average the coordinates for stability

        Args:
            detections: All detections from all frames

        Returns:
            Merged list of unique logo regions
        """
        if not detections:
            return []

        # Sort by confidence (highest first)
        sorted_detections = sorted(detections, key=lambda d: d.confidence, reverse=True)

        clusters = []
        used = set()

        for i, detection in enumerate(sorted_detections):
            if i in used:
                continue

            # Start new cluster with this detection
            cluster = [detection]
            used.add(i)

            # Find all detections that overlap with this one
            for j, other in enumerate(sorted_detections):
                if j in used or j == i:
                    continue

                # Check overlap
                overlap = self._calculate_overlap(detection, other)
                if overlap > self.config.merge_overlap_threshold:
                    cluster.append(other)
                    used.add(j)

            # Merge cluster into single detection
            merged = self._merge_cluster(cluster)
            clusters.append(merged)

        return clusters

    def _calculate_overlap(self, det1: DetectionResult, det2: DetectionResult) -> float:
        """
        Calculate IoU (Intersection over Union) between two detections.

        Returns:
            Overlap ratio (0.0 = no overlap, 1.0 = perfect overlap)
        """
        # Calculate intersection
        x1 = max(det1.x, det2.x)
        y1 = max(det1.y, det2.y)
        x2 = min(det1.x + det1.width, det2.x + det2.width)
        y2 = min(det1.y + det1.height, det2.y + det2.height)

        if x2 < x1 or y2 < y1:
            return 0.0  # No intersection

        intersection = (x2 - x1) * (y2 - y1)

        # Calculate union
        area1 = det1.width * det1.height
        area2 = det2.width * det2.height
        union = area1 + area2 - intersection

        if union == 0:
            return 0.0

        return intersection / union

    def _merge_cluster(self, cluster: List[DetectionResult]) -> DetectionResult:
        """
        Merge a cluster into one detection using the enclosing box (full logo coverage).
        Uses min/max coordinates so the final x,y,w,h fully contain every detection.
        """
        if len(cluster) == 1:
            return cluster[0]

        # Enclosing box: union of all boxes so we get correct full logo area
        x_min = min(d.x for d in cluster)
        y_min = min(d.y for d in cluster)
        x_max = max(d.x + d.width for d in cluster)
        y_max = max(d.y + d.height for d in cluster)
        w = max(1, x_max - x_min)
        h = max(1, y_max - y_min)

        max_confidence = max(d.confidence for d in cluster)
        if len(cluster) >= 2:
            boost = min(1.0, 0.25 + 0.12 * len(cluster))
            max_confidence = max(max_confidence, boost)

        first = min(cluster, key=lambda d: d.frame_index)

        return DetectionResult(
            x=int(x_min),
            y=int(y_min),
            width=int(w),
            height=int(h),
            confidence=max_confidence,
            frame_index=first.frame_index,
            timestamp=first.timestamp,
            detection_method="edge",
            status="pending"
        )


def quick_detect(video_path: str, sensitivity: float = 0.75) -> List[DetectionResult]:
    """
    Convenience function for quick logo detection with default settings.

    Args:
        video_path: Path to video file
        sensitivity: Detection sensitivity (0.0-1.0, default 0.75)

    Returns:
        List of detected logo regions

    Example:
        >>> results = quick_detect("video.mp4", sensitivity=0.8)
        >>> print(f"Found {len(results)} logos")
    """
    config = DetectionConfig(sensitivity=sensitivity)
    detector = LogoDetector(config)
    session = detector.detect_in_video(video_path)
    return session.results
