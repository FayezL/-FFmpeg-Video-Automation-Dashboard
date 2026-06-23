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

from typing import Callable, List, Optional, Tuple

import cv2
import numpy as np

from src.data_models import DetectionConfig, DetectionResult, DetectionSession
from src.exceptions import (
    DetectionCancelledError,
    DetectionFailedError,
    VideoReadError,
)
from src.logo_detection_utils import (
    Rect,
    passes_aspect_ratio_filter,
    passes_position_filter,
    passes_size_filter,
)


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

    @staticmethod
    def _score_candidate(
        rect: Rect,
        variance_map: np.ndarray,
        video_resolution,
        position_zones: List[str],
        min_w: int,
        min_h: int,
        max_w: int,
        max_h: int,
    ) -> float:
        """Score a candidate rectangle: blend of stability, corner fit, and size fit.

        Weights (per spec):
          - Stability 70% (primary): inverse of mean variance inside the box.
          - Corner fit 20%: how close the box center is to its nearest enabled zone corner.
          - Size fit   10%: how close the box dimensions are to the midpoint of the allowed range.

        Returns:
            Float score in [0.0, 1.0]. Higher is better.
        """
        # --- Stability (70%) ---
        roi = variance_map[rect.y:rect.y + rect.h, rect.x:rect.x + rect.w]
        mean_var = float(np.mean(roi)) if roi.size > 0 else 1.0
        # Map variance [0, 0.01] → stability [1.0, 0.0].
        # Variance of 0 = perfectly static = stability 1.0.
        # Variance >= 0.01 = very unstable = stability 0.0.
        stability = max(0.0, 1.0 - mean_var / 0.01)

        # --- Corner fit (20%) ---
        corner_fit = TemporalLogoDetector._corner_fit_score(
            rect, video_resolution, position_zones
        )

        # --- Size fit (10%) ---
        mid_w = (min_w + max_w) / 2.0
        mid_h = (min_h + max_h) / 2.0
        # 1.0 at midpoint, falls off toward the bounds.
        w_fit = 1.0 - abs(rect.w - mid_w) / max(1.0, (max_w - min_w) / 2.0)
        h_fit = 1.0 - abs(rect.h - mid_h) / max(1.0, (max_h - min_h) / 2.0)
        size_fit = max(0.0, (w_fit + h_fit) / 2.0)

        score = 0.70 * stability + 0.20 * corner_fit + 0.10 * size_fit
        return max(0.0, min(1.0, score))

    @staticmethod
    def _corner_fit_score(
        rect: Rect,
        video_resolution,
        position_zones: List[str],
    ) -> float:
        """Return 1.0 if the rect center is at a zone corner, falling to 0.0 at frame center."""
        if not position_zones:
            return 0.5  # neutral when position filtering disabled
        vw, vh = video_resolution
        cx = rect.x + rect.w / 2.0
        cy = rect.y + rect.h / 2.0

        best = 0.0
        for zone in position_zones:
            if zone == "top-left":
                corner_x, corner_y = 0.0, 0.0
            elif zone == "top-right":
                corner_x, corner_y = vw, 0.0
            elif zone == "bottom-left":
                corner_x, corner_y = 0.0, vh
            elif zone == "bottom-right":
                corner_x, corner_y = vw, vh
            else:
                continue
            # Normalized distance from corner (0 = at corner, 1 = opposite corner)
            dist = ((cx - corner_x) ** 2 + (cy - corner_y) ** 2) ** 0.5
            max_dist = (vw ** 2 + vh ** 2) ** 0.5
            score = max(0.0, 1.0 - dist / max_dist)
            best = max(best, score)
        return best

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

            if progress_callback:
                progress_callback(0.0, "Sampling frames...")

            indices = self._sample_frame_indices(
                total_frames=frame_count,
                num_frames=self.config.temporal_num_frames,
                skip_intro_frac=self.config.temporal_skip_intro_frac,
                skip_outro_frac=self.config.temporal_skip_outro_frac,
            )
            session.total_frames_to_analyze = len(indices)

            scale_max_h = getattr(self.config, "detection_scale_max_height", 720)
            full_w, full_h = session.video_resolution
            if scale_max_h > 0 and full_h > scale_max_h:
                scale = scale_max_h / full_h
                target_h = int(full_h * scale)
                target_w = int(full_w * scale)
            else:
                target_h, target_w = full_h, full_w
                scale = 1.0

            frames = []
            for i, frame_index in enumerate(indices):
                if cancel_check and cancel_check():
                    session.cancel()
                    raise DetectionCancelledError()
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                ret, frame = cap.read()
                if not ret:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if scale != 1.0:
                    gray = cv2.resize(gray, (target_w, target_h), interpolation=cv2.INTER_AREA)
                frames.append(gray)
                session.frames_analyzed += 1
                session.progress = (i + 1) / max(1, len(indices))
                if progress_callback:
                    progress_callback(session.progress, f"Sampled frame {i + 1}/{len(indices)}")

            if len(frames) < 3:
                session.complete()
                if progress_callback:
                    progress_callback(1.0, "Insufficient frames for detection")
                return session

            if progress_callback:
                progress_callback(0.85, "Analyzing temporal stability...")

            stack = np.stack(frames)
            results = self._detect_from_frame_stack(
                stack, video_resolution=(target_w, target_h),
            )

            if scale != 1.0:
                inv = 1.0 / scale
                for r in results:
                    r.x = int(r.x * inv)
                    r.y = int(r.y * inv)
                    r.width = int(r.width * inv)
                    r.height = int(r.height * inv)

            for r in results:
                session.add_result(r)

            session.complete()
            if progress_callback:
                progress_callback(1.0, f"Complete! Found {len(session.results)} logo region(s)")
            return session

        except DetectionCancelledError:
            raise
        except (VideoReadError, DetectionFailedError):
            raise
        except Exception as e:
            session.error(str(e))
            raise DetectionFailedError(str(e), video_path) from e
        finally:
            if cap is not None:
                cap.release()

    def _detect_from_frame_stack(
        self,
        stack: np.ndarray,
        video_resolution,
    ) -> List[DetectionResult]:
        """Run the full pipeline on a pre-built stack of grayscale frames.

        Package-private: used by `detect_in_video` and by unit tests that want
        to bypass video I/O.

        Args:
            stack: np.ndarray of shape (N, H, W), dtype uint8.
            video_resolution: (width, height) of the frames in the stack.

        Returns:
            List of DetectionResult, sorted by confidence descending. Each
            result's `detection_method` is set to "temporal".
        """
        cfg = self.config

        var_map = self._compute_variance_map(stack)
        mask = self._threshold_variance_map(
            var_map,
            sensitivity=cfg.sensitivity,
            base_threshold=cfg.temporal_variance_threshold,
        )
        mask = self._cleanup_mask(mask, min_region_pixels=cfg.temporal_min_region_pixels)
        raw_candidates = self._find_candidates(mask)

        scored: List[Tuple[float, Rect]] = []
        for rect in raw_candidates:
            if not passes_size_filter(
                rect.w, rect.h,
                min_w=cfg.min_logo_width, min_h=cfg.min_logo_height,
                max_w=cfg.max_logo_width, max_h=cfg.max_logo_height,
            ):
                continue
            if not passes_aspect_ratio_filter(
                rect.w, rect.h,
                ar_min=cfg.aspect_ratio_min, ar_max=cfg.aspect_ratio_max,
            ):
                continue
            if not passes_position_filter(
                rect, video_resolution=video_resolution,
                position_zones=cfg.position_zones,
            ):
                continue
            score = self._score_candidate(
                rect, var_map, video_resolution=video_resolution,
                position_zones=cfg.position_zones,
                min_w=cfg.min_logo_width, min_h=cfg.min_logo_height,
                max_w=cfg.max_logo_width, max_h=cfg.max_logo_height,
            )
            scored.append((score, rect))

        scored.sort(key=lambda s: s[0], reverse=True)

        min_conf = getattr(cfg, "min_confidence_to_report", 0.25)
        results: List[DetectionResult] = []
        for score, rect in scored:
            if score < min_conf:
                continue
            results.append(DetectionResult(
                x=rect.x, y=rect.y, width=rect.w, height=rect.h,
                confidence=float(score),
                frame_index=0,
                timestamp=0.0,
                detection_method="temporal",
                status="pending",
            ))
        return results
