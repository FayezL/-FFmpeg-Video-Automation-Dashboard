"""
Application state management
"""

from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import os
import multiprocessing
import time

# Pydantic imports for enhanced settings (003-cpu-limit-options)
try:
    from pydantic import BaseModel, Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # Fallback


class FileStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class CutMode(Enum):
    """Video trimming mode"""
    NONE = "none"
    CUT_LAST = "cut_last"      # Cut last X minutes
    CUT_FIRST = "cut_first"    # Cut first X minutes
    CUT_RANGE = "cut_range"    # Cut from start_time to end_time


@dataclass
class ProcessingFile:
    """Represents a file being processed"""
    id: str
    path: str
    name: str
    status: FileStatus = FileStatus.PENDING
    progress: float = 0.0
    error: Optional[str] = None
    # Per-file cut times (override global settings if set)
    use_custom_cut: bool = False
    custom_cut_start_seconds: Optional[float] = None  # Start time for this file
    custom_cut_end_seconds: Optional[float] = None    # End time (None = to end)


@dataclass
class DelogoParams:
    """Delogo filter parameters"""
    x: int = 1635
    y: int = 240
    w: int = 176
    h: int = 147


@dataclass
class ProcessingProfile:
    """Video encoding profile settings"""
    name: str
    description: str

    # Video settings
    video_codec: str = "libx264"
    video_preset: str = "fast"
    video_crf: Optional[int] = 23
    video_bitrate: Optional[str] = None  # Use CRF or bitrate, not both
    pixel_format: str = "yuv420p"

    # Audio settings
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"

    # Container settings
    use_faststart: bool = True

    # Compatibility flags
    x264_profile: Optional[str] = None  # baseline, main, high
    x264_level: Optional[str] = None    # 3.0, 3.1, 4.0, etc.
    max_width: Optional[int] = None
    max_height: Optional[int] = None


@dataclass
class ParallelProcessingConfig:
    """Configuration for parallel batch processing"""
    max_workers: int = 2
    auto_adjust: bool = True
    memory_limit_per_worker_mb: int = 2048

    @staticmethod
    def calculate_optimal_workers() -> int:
        """
        Calculate optimal number of workers based on CPU cores.

        Formula: max(1, min(4, (cores-1)//2))
        Ensures system remains responsive while maximizing throughput.

        Returns:
            Recommended worker count (1-4)
        """
        try:
            cores = multiprocessing.cpu_count()
            optimal = max(1, min(4, (cores - 1) // 2))
            return optimal
        except:
            return 2  # Safe default

    def estimate_memory_usage(self) -> int:
        """
        Estimate total memory usage in MB.

        Returns:
            Estimated memory usage in megabytes
        """
        return self.max_workers * self.memory_limit_per_worker_mb


@dataclass
class HardwareEncoder:
    """Detected hardware video encoder"""
    name: str  # e.g., "NVENC", "QuickSync", "VideoToolbox"
    codec: str  # e.g., "h264_nvenc", "h264_qsv"
    description: str
    is_available: bool = False
    is_tested: bool = False


@dataclass
class VideoFilter:
    """Single video filter with parameters"""
    filter_type: str  # rotate, crop, scale, brightness, etc.
    enabled: bool = False
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FilterChain:
    """Ordered chain of video filters"""
    filters: List[VideoFilter] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Check if filter chain has any enabled filters"""
        return not any(f.enabled for f in self.filters)


# ============================================================================
# CPU Limiting Data Structures (003-cpu-limit-options Phase 2: T005-T006)
# ============================================================================

@dataclass
class CPULimitConfig:
    """Configuration for CPU limiting during video processing"""
    enabled: bool = False
    limit_percent: int = 75  # Range: 20-95
    monitor_interval: float = 1.0  # Seconds between CPU checks
    priority_level: str = "normal"  # Options: low, normal, high

    def validate(self) -> tuple[bool, str]:
        """Validate configuration values"""
        if self.limit_percent < 20 or self.limit_percent > 95:
            return False, "CPU limit must be between 20% and 95%"
        if self.priority_level not in ["low", "normal", "high"]:
            return False, "Priority must be low, normal, or high"
        if self.monitor_interval < 0.5 or self.monitor_interval > 5.0:
            return False, "Monitor interval must be between 0.5 and 5.0 seconds"
        return True, ""


@dataclass
class CPUMetrics:
    """Current CPU usage metrics"""
    process_cpu_percent: float = 0.0  # This process only
    system_cpu_percent: float = 0.0   # Entire system
    thread_count: int = 0              # FFmpeg threads in use
    target_limit: int = 75             # User-configured limit
    timestamp: float = 0.0             # time.time() of last update

    @property
    def is_within_limit(self) -> bool:
        """Check if current usage is within 5% of target"""
        return abs(self.process_cpu_percent - self.target_limit) <= 5.0

    @property
    def variance_percent(self) -> float:
        """Calculate variance from target limit"""
        return self.process_cpu_percent - self.target_limit


# ============================================================================
# Enhanced Settings Data Structures (003-cpu-limit-options Phase 2: T007)
# ============================================================================

if PYDANTIC_AVAILABLE:
    class PerformanceSettings(BaseModel):
        """Performance and resource control settings"""
        cpu_limiting_enabled: bool = False
        cpu_limit_percent: int = Field(75, ge=20, le=95)
        max_parallel_jobs: int = Field(2, ge=1, le=4)
        ffmpeg_priority: str = Field("normal", pattern="^(low|normal|high)$")

        @field_validator('cpu_limit_percent')
        @classmethod
        def validate_cpu_limit(cls, v):
            if v % 5 != 0:  # Enforce 5% increments
                raise ValueError("CPU limit must be in 5% increments")
            return v

    class OutputSettings(BaseModel):
        """Output file naming and organization settings"""
        naming_pattern: str = "{prefix}{filename}{suffix}"
        prefix: str = ""
        suffix: str = ""
        output_format: str = "mp4"
        create_subfolder: bool = True
        overwrite_policy: str = Field("ask", pattern="^(ask|skip|overwrite)$")

    class QualitySettings(BaseModel):
        """Video and audio quality settings"""
        default_profile: str = "universal"
        video_bitrate_override: Optional[int] = Field(None, ge=500, le=50000)  # kbps
        audio_quality: str = Field("medium", pattern="^(low|medium|high|lossless)$")
        maintain_aspect_ratio: bool = True

    class AdvancedSettings(BaseModel):
        """Advanced and experimental settings"""
        custom_ffmpeg_params: str = ""
        logging_level: str = Field("info", pattern="^(error|warning|info|debug)$")
        enable_intro_detection: bool = False
        detection_confidence_threshold: float = Field(0.75, ge=0.5, le=0.95)
        keep_temp_files: bool = False

    class ApplicationSettings(BaseModel):
        """Complete application settings"""
        version: str = "1.0.0"
        performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
        output: OutputSettings = Field(default_factory=OutputSettings)
        quality: QualitySettings = Field(default_factory=QualitySettings)
        advanced: AdvancedSettings = Field(default_factory=AdvancedSettings)
else:
    # Fallback if pydantic not installed
    class ApplicationSettings:
        def __init__(self):
            self.version = "1.0.0"

        def model_dump_json(self, indent: int = 2) -> str:
            import json
            return json.dumps({"version": self.version}, indent=indent)


# ============================================================================
# Intro/Outro Detection Data Structures (003-cpu-limit-options Phase 2: T008)
# ============================================================================

@dataclass
class SegmentPattern:
    """Pattern data for intro or outro segment"""
    perceptual_hashes: List[str]  # 64-bit pHash as hex strings
    duration_seconds: float
    start_offset: float = 0.0  # Typical start time in video
    audio_fingerprint: Optional[str] = None  # Optional audio pattern
    sample_count: int = 1  # Number of episodes used to create pattern

    def similarity_score(self, other_hashes: List[str]) -> float:
        """Calculate similarity between this pattern and candidate hashes"""
        if len(other_hashes) != len(self.perceptual_hashes):
            return 0.0

        total_distance = 0
        for p1, p2 in zip(self.perceptual_hashes, other_hashes):
            # Hamming distance between hashes
            h1 = int(p1, 16)
            h2 = int(p2, 16)
            distance = bin(h1 ^ h2).count('1')
            total_distance += distance

        max_distance = len(self.perceptual_hashes) * 64  # 64 bits per hash
        similarity = 1.0 - (total_distance / max_distance)
        return similarity


@dataclass
class DetectionProfile:
    """Complete detection profile for a series"""
    series_id: str  # Unique identifier (hash of series name)
    series_name: str  # Human-readable name
    intro_pattern: Optional[SegmentPattern] = None
    outro_pattern: Optional[SegmentPattern] = None
    confidence_threshold: float = 0.75
    user_corrections: int = 0  # Count of manual corrections
    episodes_analyzed: int = 0
    last_updated: float = 0.0  # timestamp


@dataclass
class DetectedSegment:
    """A single detected intro or outro segment"""
    segment_type: str  # "intro" or "outro"
    start_time: float  # seconds
    end_time: float    # seconds
    confidence: float  # 0.0 to 1.0
    method: str        # "hash_match", "audio_match", "user_confirmed"

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def needs_review(self) -> bool:
        """True if confidence below threshold"""
        return self.confidence < 0.75


@dataclass
class DetectionResult:
    """Complete detection result for a video file"""
    file_path: str
    series_id: Optional[str] = None  # None if no matching profile
    intro: Optional[DetectedSegment] = None
    outro: Optional[DetectedSegment] = None
    analysis_duration: float = 0.0  # seconds to analyze
    error: Optional[str] = None  # Error message if detection failed

    @property
    def has_detections(self) -> bool:
        return self.intro is not None or self.outro is not None

    @property
    def all_high_confidence(self) -> bool:
        """True if all detected segments have high confidence"""
        if not self.has_detections:
            return False
        segments = [s for s in [self.intro, self.outro] if s is not None]
        return all(not s.needs_review for s in segments)


# Predefined processing profiles
PROCESSING_PROFILES = {
    "universal": ProcessingProfile(
        name="Universal Compatibility",
        description="Maximum compatibility - works on all devices (iPhone, Android, Smart TVs, web browsers)",
        video_codec="libx264",
        video_preset="slow",
        video_crf=23,
        pixel_format="yuv420p",
        audio_codec="aac",
        audio_bitrate="192k",
        use_faststart=True,
        x264_profile="baseline",
        x264_level="3.1",
        max_width=1920,
        max_height=1080
    ),
    "high_quality": ProcessingProfile(
        name="High Quality",
        description="Larger file size, better visual quality - ideal for archiving or high-quality streaming",
        video_preset="slow",
        video_crf=18,
        x264_profile="high",
        audio_bitrate="256k"
    ),
    "small_file": ProcessingProfile(
        name="Smaller File Size",
        description="Faster streaming, lower quality - good for quick uploads or bandwidth-constrained scenarios",
        video_preset="fast",
        video_crf=28,
        audio_bitrate="128k"
    ),
    "ios_optimized": ProcessingProfile(
        name="iOS Optimized",
        description="Optimized for iPhone, iPad, and Apple TV with best compatibility and quality balance",
        video_preset="slow",
        video_crf=22,
        x264_profile="main",
        x264_level="4.0",
        audio_codec="aac",
        audio_bitrate="192k",
        use_faststart=True
    )
}


class AppState:
    """Application state singleton"""

    def __init__(self):
        # Files
        self.selected_files: List[ProcessingFile] = []
        self.input_folder: Optional[str] = None  # For folder-based input
        self.output_folder: Optional[str] = None

        # Cut/Trim options
        self.cut_mode: CutMode = CutMode.CUT_LAST

        # For CUT_LAST and CUT_FIRST modes: Amount of time to remove
        self.cut_hours: float = 0.0            # Hours to cut (last or first)
        self.cut_minutes: float = 5.0          # Minutes to cut (last or first)
        self.cut_seconds: float = 0.0          # Seconds to cut (last or first)

        # For CUT_RANGE mode: Absolute timestamps
        self.cut_start_hours: float = 0.0      # Start time hours (absolute position)
        self.cut_start_minutes: float = 0.0    # Start time minutes (absolute position)
        self.cut_start_seconds: float = 0.0    # Start time seconds (absolute position)
        self.cut_end_hours: Optional[float] = None    # End time hours (None = to end of video)
        self.cut_end_minutes: Optional[float] = None  # End time minutes (None = to end of video)
        self.cut_end_seconds: Optional[float] = None  # End time seconds (None = to end of video)

        # Legacy compatibility
        self.cut_last_5_minutes: bool = True

        # Processing options
        self.apply_delogo: bool = False
        self.delogo_params: DelogoParams = DelogoParams()
        self.processing_profile: str = "universal"  # Key into PROCESSING_PROFILES

        # Output options
        self.output_format: str = "mp4"         # mp4, mkv
        self.output_suffix: str = ""             # e.g. "_processed"
        self.output_prefix: str = ""             # e.g. "converted_"
        self.create_output_subfolder: bool = False  # Create "output" subfolder
        self.overwrite_existing: bool = True

        # Rename Plan — sequential episode numbering for any batch size (1 to 50+)
        # When enabled, output files are named: {rename_base}{N:0rename_pad}{ext}
        # e.g. rename_base="hamo", rename_start=1, rename_pad=2 → hamo01, hamo02 …
        self.rename_enabled: bool = False   # Toggle rename plan on/off
        self.rename_base: str = ""          # Base name  (e.g. "hamo")
        self.rename_start: int = 1          # First episode number (default 1)
        self.rename_pad: int = 2            # Zero-pad width: 2→"01", 3→"001"

        # Processing state
        self.is_processing: bool = False
        self.current_file_index: int = 0

        # Second task slot (Task 2) - separate file list and output so you can run two batches and know what is where
        self.task2_files: List[ProcessingFile] = []
        self.task2_output_folder: Optional[str] = None
        self.task2_processing: bool = False

        # Additional task slots (Task 3, 4, ...) - each dict: files, output_folder, processing
        self.extra_task_slots: List[Dict[str, Any]] = []

        # Logs
        self.logs: List[str] = []
        self.log_callbacks: List[Callable[[str], None]] = []

        # Template management (T011-T012)
        self.current_template: Optional[str] = None  # Name of loaded template
        self.template_modified: bool = False  # True if settings differ from loaded template

        # Parallel processing (T013-T014)
        self.parallel_config: ParallelProcessingConfig = ParallelProcessingConfig()
        self.active_processes: List[str] = []  # IDs of currently processing files

        # Hardware encoding (T015-T017)
        self.detected_encoders: List[HardwareEncoder] = []
        self.use_hardware_encoding: bool = False
        self.selected_encoder: Optional[HardwareEncoder] = None

        # Video filters (T018)
        self.filter_chain: FilterChain = FilterChain()

        # Metadata caching (T019)
        self._metadata_cache: Dict[str, Any] = {}

        # Batch state management (T020)
        self.current_batch_state: Optional[Any] = None  # Will be BatchState once defined

        # Logo detection (Phase 4 - User Story 2) - Placeholders for MVP
        self.detection_enabled: bool = False  # Enable logo detection feature
        self.detection_results: List[Any] = []  # Will store DetectionResult objects
        self.active_profile: Optional[str] = None  # Name of active detection profile
        self.detection_progress: float = 0.0  # Detection progress (0.0-1.0)
        self.detection_status: str = "idle"  # idle, running, completed, cancelled, error

        # ============================================================================
        # CPU Limiting (003-cpu-limit-options Phase 2: T009)
        # ============================================================================
        self.cpu_limit_config: CPULimitConfig = CPULimitConfig()
        self.current_cpu_metrics: Optional[CPUMetrics] = None

        # ============================================================================
        # Enhanced Settings (003-cpu-limit-options Phase 2: T009)
        # ============================================================================
        self.settings_manager: Optional[Any] = None  # SettingsManager instance (created in main.py)

        # ============================================================================
        # Intro/Outro Detection (003-cpu-limit-options Phase 2: T009)
        # ============================================================================
        self.detection_profiles: Dict[str, DetectionProfile] = {}  # series_id -> profile
        self.intro_outro_enabled: bool = False  # Enable intro/outro detection feature

    def add_log(self, message: str):
        """Add a log message and notify callbacks"""
        self.logs.append(message)
        for callback in self.log_callbacks:
            callback(message)
    
    def clear_logs(self):
        """Clear all logs"""
        self.logs.clear()
    
    def register_log_callback(self, callback: Callable[[str], None]):
        """Register a callback for log updates"""
        self.log_callbacks.append(callback)
    
    def unregister_log_callback(self, callback: Callable[[str], None]):
        """Unregister a log callback"""
        if callback in self.log_callbacks:
            self.log_callbacks.remove(callback)

    # Time helper properties
    @property
    def cut_total_seconds(self) -> float:
        """
        Total cut time in seconds (hours + minutes + seconds combined).

        Used for CUT_LAST and CUT_FIRST modes to specify how much to remove.
        Example: cut_hours=0, cut_minutes=5, cut_seconds=30 = 330 seconds to remove
        """
        return (self.cut_hours * 3600) + (self.cut_minutes * 60) + self.cut_seconds

    @property
    def cut_start_total_seconds(self) -> float:
        """
        Total start time in seconds for CUT_RANGE mode (hours + minutes + seconds).

        This is the ABSOLUTE timestamp where the output video should START.
        Example: cut_start_hours=0, cut_start_minutes=2, cut_start_seconds=30
        means start the output video at the 2:30 mark of the input video.
        """
        return (self.cut_start_hours * 3600) + (self.cut_start_minutes * 60) + self.cut_start_seconds

    @property
    def cut_end_total_seconds(self) -> Optional[float]:
        """
        Total end time in seconds for CUT_RANGE mode (hours + minutes + seconds).

        This is the ABSOLUTE timestamp where the output video should END.
        If all end fields are None, the video continues to the end of the input.
        Example: cut_end_hours=0, cut_end_minutes=5, cut_end_seconds=0
        means end the output video at the 5:00 mark of the input video.

        Returns None if no end time is specified (meaning "to end of video").
        """
        if self.cut_end_hours is None and self.cut_end_minutes is None and self.cut_end_seconds is None:
            return None
        hours = self.cut_end_hours or 0.0
        mins = self.cut_end_minutes or 0.0
        secs = self.cut_end_seconds or 0.0
        return (hours * 3600) + (mins * 60) + secs


