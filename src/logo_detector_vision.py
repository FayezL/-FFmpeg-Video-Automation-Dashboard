"""
Optional logo detection using Google Cloud Vision API.

Uses fewer frames (e.g. 5 keyframes) and Google's logo detection model
for higher accuracy. Requires:
  - pip install google-cloud-vision
  - GOOGLE_APPLICATION_CREDENTIALS set to a service account JSON path,
    or other Application Default Credentials.

If the library or credentials are missing, is_available() returns False.
"""

from typing import List, Optional, Callable
import cv2

from src.data_models import DetectionResult, DetectionConfig, DetectionSession
from src.exceptions import VideoReadError, DetectionFailedError, DetectionCancelledError

try:
    from google.cloud import vision
    _VISION_AVAILABLE = True
except ImportError:
    _VISION_AVAILABLE = False
    vision = None


# Number of keyframes to send to the API (few frames, more powerful AI)
DEFAULT_FRAMES_TO_ANALYZE = 5


def is_available() -> bool:
    """Return True if Google Cloud Vision can be used (library + credentials)."""
    if not _VISION_AVAILABLE:
        return False
    try:
        client = vision.ImageAnnotatorClient()
        return client is not None
    except Exception:
        return False


class VisionLogoDetector:
    """
    Logo detection using Google Cloud Vision API.
    Analyzes only a few keyframes for speed and uses Google's logo model for accuracy.
    """

    def __init__(self, config: DetectionConfig):
        self.config = config
        self._num_frames = getattr(
            config, "vision_max_frames", DEFAULT_FRAMES_TO_ANALYZE
        )

    def detect_in_video(
        self,
        video_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> DetectionSession:
        """
        Detect logos by sending a few keyframes to Google Cloud Vision API.
        """
        if not _VISION_AVAILABLE:
            raise DetectionFailedError(
                "Google Cloud Vision is not available. Install: pip install google-cloud-vision "
                "and set GOOGLE_APPLICATION_CREDENTIALS.",
                video_path,
            )

        session = DetectionSession(video_path=video_path, config=self.config)
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise VideoReadError(video_path, "Failed to open video file")

            session.video_fps = cap.get(cv2.CAP_PROP_FPS) or 1.0
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            session.video_duration = (
                frame_count / session.video_fps if session.video_fps > 0 else 0.0
            )
            session.video_resolution = (
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            )
            total_frames = max(1, frame_count)
            session.total_frames_to_analyze = min(self._num_frames, total_frames)

            if progress_callback:
                progress_callback(0.0, "Connecting to Google Cloud Vision...")

            client = vision.ImageAnnotatorClient()
            all_detections: List[DetectionResult] = []
            frames_to_read = self._keyframe_indices(total_frames, session.total_frames_to_analyze)

            for i, frame_index in enumerate(frames_to_read):
                if cancel_check and cancel_check():
                    session.cancel()
                    raise DetectionCancelledError()

                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                ret, frame = cap.read()
                if not ret:
                    continue

                timestamp = frame_index / session.video_fps if session.video_fps > 0 else 0.0
                if progress_callback:
                    progress_callback(
                        (i + 1) / len(frames_to_read),
                        f"Analyzing frame {i + 1}/{len(frames_to_read)} (AI)...",
                    )

                detections = self._detect_logos_in_image(
                    client, frame, frame_index, timestamp, session.video_resolution
                )
                all_detections.extend(detections)

            # Dedupe by merging overlapping boxes (keep highest confidence per area)
            merged = self._merge_overlapping(all_detections)
            for det in merged:
                session.add_result(det)

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

    def _keyframe_indices(self, total_frames: int, num_wanted: int) -> List[int]:
        """Return evenly spaced frame indices."""
        if total_frames <= num_wanted:
            return list(range(total_frames))
        step = (total_frames - 1) / max(1, num_wanted - 1)
        return [int(i * step) for i in range(num_wanted)]

    def _detect_logos_in_image(
        self,
        client,
        frame,
        frame_index: int,
        timestamp: float,
        video_resolution: tuple,
    ) -> List[DetectionResult]:
        """Send one frame to Vision API logo detection and return DetectionResults."""
        _, jpeg = cv2.imencode(".jpg", frame)
        image = vision.Image(content=jpeg.tobytes())
        response = client.logo_detection(image=image)
        if response.error.message:
            return []

        results = []
        for annotation in response.logo_annotations:
            x, y, w, h = self._bounding_poly_to_rect(annotation.bounding_poly, video_resolution)
            if w <= 0 or h <= 0:
                continue
            confidence = getattr(annotation, "score", 0.9) or 0.9
            results.append(
                DetectionResult(
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    confidence=float(confidence),
                    frame_index=frame_index,
                    timestamp=timestamp,
                    detection_method="vision",
                )
            )
        return results

    def _bounding_poly_to_rect(self, bounding_poly, video_resolution: tuple) -> tuple:
        """Convert Vision API bounding_poly.vertices to (x, y, w, h) pixels."""
        vertices = list(bounding_poly.vertices) if bounding_poly.vertices else []
        if len(vertices) < 2:
            return (0, 0, 0, 0)
        xs = [getattr(v, "x", 0) for v in vertices]
        ys = [getattr(v, "y", 0) for v in vertices]
        x_min = max(0, int(min(xs)))
        y_min = max(0, int(min(ys)))
        x_max = int(max(xs))
        y_max = int(max(ys))
        w = max(1, x_max - x_min)
        h = max(1, y_max - y_min)
        return (x_min, y_min, w, h)

    def _merge_overlapping(
        self, detections: List[DetectionResult], iou_threshold: float = 0.3
    ) -> List[DetectionResult]:
        """Keep one detection per overlapping group (highest confidence)."""
        if not detections:
            return []
        sorted_det = sorted(detections, key=lambda d: d.confidence, reverse=True)
        kept: List[DetectionResult] = []
        for det in sorted_det:
            if any(self._iou(det, k) > iou_threshold for k in kept):
                continue
            kept.append(det)
        return kept

    def _iou(self, a: DetectionResult, b: DetectionResult) -> float:
        """Intersection over union of two boxes."""
        x1 = max(a.x, b.x)
        y1 = max(a.y, b.y)
        x2 = min(a.x + a.width, b.x + b.width)
        y2 = min(a.y + a.height, b.y + b.height)
        if x2 <= x1 or y2 <= y1:
            return 0.0
        inter = (x2 - x1) * (y2 - y1)
        area_a = a.width * a.height
        area_b = b.width * b.height
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0
