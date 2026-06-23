"""
Data models for logo detection feature

This module contains detection-related dataclasses:
- DetectionResult: Single detected logo region
- DetectionSession: Complete detection run for a video
- DetectionConfig: Algorithm configuration
- DetectionProfile: Saved detection settings (Phase 5)
- LogoPattern: Template for matching (Phase 5)
- ProfileStatistics: Usage stats (Phase 5)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime
import uuid


@dataclass
class DetectionResult:
    """
    Represents a single detected logo region in a video frame.

    Attributes:
        id: Unique identifier for this detection
        x: Top-left X coordinate (pixels)
        y: Top-left Y coordinate (pixels)
        width: Region width (pixels)
        height: Region height (pixels)
        confidence: Detection confidence score (0.0-1.0)
        frame_index: Video frame where detected
        timestamp: Video timestamp (seconds)
        status: User review status (pending/accepted/rejected)
        detection_method: Algorithm that found this region
        preview_image: Optional base64-encoded preview image
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    confidence: float = 0.0
    frame_index: int = 0
    timestamp: float = 0.0
    status: str = "pending"  # pending, accepted, rejected
    detection_method: str = "edge"  # edge, corner, template
    preview_image: Optional[str] = None

    def validate(self) -> bool:
        """Validate all constraints"""
        assert self.x >= 0, "x must be >= 0"
        assert self.y >= 0, "y must be >= 0"
        assert self.width > 0, "width must be > 0"
        assert self.height > 0, "height must be > 0"
        assert 0.0 <= self.confidence <= 1.0, "confidence must be 0-1"
        assert self.status in ["pending", "accepted", "rejected"], "invalid status"
        assert self.detection_method in ["edge", "corner", "template", "vision", "temporal"], "invalid method"
        return True

    def to_delogo_params(self) -> Tuple[int, int, int, int]:
        """Convert to delogo parameters (x, y, w, h)"""
        return (self.x, self.y, self.width, self.height)


@dataclass
class DetectionConfig:
    """
    Configuration settings for logo detection algorithm.

    All parameters can be adjusted for different video types and logo patterns.
    """
    # Detection sensitivity
    sensitivity: float = 0.75  # 0.0-1.0, higher = more detections

    # Frame sampling (legacy; used only when not using keyframe mode)
    frame_sampling: int = 30  # Analyze every Nth frame
    # Fast mode: analyze only this many evenly spaced keyframes (e.g. 5 = much faster)
    max_frames_to_analyze: int = 5
    # Downscale frame to this max height for detection (0 = full size). 720 = faster, still accurate.
    detection_scale_max_height: int = 720

    # Logo size constraints (allow typical TV/broadcast logo sizes)
    min_logo_width: int = 20
    min_logo_height: int = 20
    max_logo_width: int = 450
    max_logo_height: int = 220

    # Aspect ratio constraints
    aspect_ratio_min: float = 0.5
    aspect_ratio_max: float = 5.0

    # Position zones (where logos typically appear)
    position_zones: List[str] = field(default_factory=lambda: [
        "top-left", "top-right", "bottom-left", "bottom-right"
    ])

    # Edge detection thresholds
    edge_threshold_low: int = 50
    edge_threshold_high: int = 150

    # Template matching (Phase 5)
    enable_template_matching: bool = False

    # Region merging
    merge_overlap_threshold: float = 0.5

    # Only report regions with at least this confidence (0.0-1.0). Higher = fewer but more accurate.
    min_confidence_to_report: float = 0.35

    # --- Temporal stability parameters (new default detector) ---
    # Number of evenly-spaced frames to sample across the video for variance analysis.
    temporal_num_frames: int = 15
    # Pixels with per-pixel variance below this value are considered "static" (part of a logo).
    # Grayscale intensity variance (0-255 scale). Lower threshold = stricter (fewer candidates).
    # Default 5.0 is calibrated for real-world H.264 compressed video where static regions
    # have variance ~0.1-1.0 due to quantization noise. (The old default of 0.005 only worked
    # for near-lossless video.)
    temporal_variance_threshold: float = 5.0
    # Skip the first/last X fraction of the video to avoid intro/outro fades and black buffers.
    temporal_skip_intro_frac: float = 0.02
    temporal_skip_outro_frac: float = 0.02
    # Discard candidate regions smaller than this many pixels (noise cleanup).
    temporal_min_region_pixels: int = 200

    def validate(self) -> bool:
        """Validate all configuration constraints"""
        assert 0.0 <= self.sensitivity <= 1.0, "sensitivity must be 0-1"
        assert self.frame_sampling >= 1, "frame_sampling must be >= 1"
        assert 1 <= self.max_frames_to_analyze <= 20, "max_frames_to_analyze must be 1-20"
        assert self.detection_scale_max_height >= 0, "detection_scale_max_height must be >= 0"
        assert self.min_logo_width > 0, "min_logo_width must be > 0"
        assert self.min_logo_height > 0, "min_logo_height must be > 0"
        assert self.max_logo_width > self.min_logo_width, "max > min width"
        assert self.max_logo_height > self.min_logo_height, "max > min height"
        assert self.aspect_ratio_min > 0, "aspect_ratio_min must be > 0"
        assert self.aspect_ratio_max > self.aspect_ratio_min, "max > min aspect ratio"
        assert 0 <= self.edge_threshold_low <= 255, "edge_threshold_low must be 0-255"
        assert self.edge_threshold_low < self.edge_threshold_high <= 255, "high > low"
        assert 0.0 <= self.merge_overlap_threshold <= 1.0, "merge threshold must be 0-1"
        assert 0.0 <= self.min_confidence_to_report <= 1.0, "min_confidence_to_report must be 0-1"
        assert 3 <= self.temporal_num_frames <= 60, "temporal_num_frames must be 3-60"
        assert 0.0 <= self.temporal_variance_threshold <= 10000.0, "temporal_variance_threshold must be 0-10000"
        assert 0.0 <= self.temporal_skip_intro_frac < 0.5, "temporal_skip_intro_frac must be 0 to <0.5"
        assert 0.0 <= self.temporal_skip_outro_frac < 0.5, "temporal_skip_outro_frac must be 0 to <0.5"
        assert self.temporal_min_region_pixels > 0, "temporal_min_region_pixels must be > 0"
        return True


@dataclass
class DetectionSession:
    """
    Represents a complete logo detection run for a single video.

    Contains all detection results and metadata for one video analysis.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    video_path: str = ""
    video_duration: float = 0.0  # seconds
    video_fps: float = 0.0
    video_resolution: Tuple[int, int] = (0, 0)  # (width, height)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    status: str = "running"  # running, completed, cancelled, error
    progress: float = 0.0  # 0.0-1.0
    frames_analyzed: int = 0
    total_frames_to_analyze: int = 0
    results: List[DetectionResult] = field(default_factory=list)
    config: DetectionConfig = field(default_factory=DetectionConfig)
    error_message: Optional[str] = None

    def add_result(self, result: DetectionResult):
        """Add a detection result to this session"""
        self.results.append(result)

    def get_accepted_results(self) -> List[DetectionResult]:
        """Get only accepted detection results"""
        return [r for r in self.results if r.status == "accepted"]

    def get_pending_results(self) -> List[DetectionResult]:
        """Get only pending detection results"""
        return [r for r in self.results if r.status == "pending"]

    def complete(self):
        """Mark session as completed"""
        self.status = "completed"
        self.completed_at = datetime.now().isoformat()
        self.progress = 1.0

    def cancel(self):
        """Mark session as cancelled"""
        self.status = "cancelled"
        self.completed_at = datetime.now().isoformat()

    def error(self, message: str):
        """Mark session as errored"""
        self.status = "error"
        self.error_message = message
        self.completed_at = datetime.now().isoformat()


# Phase 5 models (placeholders for now)

@dataclass
class DetectionProfile:
    """
    Saved configuration and learned patterns for recurring logo detection.

    Will be fully implemented in Phase 5 (User Story 3).
    """
    profile_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Default Profile"
    description: Optional[str] = None
    config: DetectionConfig = field(default_factory=DetectionConfig)
    # Future: known_patterns, statistics


@dataclass
class LogoPattern:
    """
    Template for matching a specific logo using template matching.

    Will be fully implemented in Phase 5 (User Story 3).
    """
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Logo Pattern"
    # Future: reference_frame, coordinates, confidence_threshold


@dataclass
class ProfileStatistics:
    """
    Usage statistics for a detection profile.

    Will be fully implemented in Phase 5 (User Story 3).
    """
    videos_processed: int = 0
    total_detections: int = 0
    accepted_detections: int = 0
    rejected_detections: int = 0
    average_confidence: float = 0.0
    average_processing_time: float = 0.0  # seconds
