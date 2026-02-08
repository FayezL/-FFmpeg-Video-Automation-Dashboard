"""
Application state management
"""

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


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
        self.cut_minutes: float = 5.0           # Minutes to cut (last or first)
        self.cut_seconds: float = 0.0           # Additional seconds for cut
        self.cut_start_minutes: float = 0.0     # Start time for range (minutes)
        self.cut_start_seconds: float = 0.0     # Additional seconds for range start
        self.cut_end_minutes: Optional[float] = None  # End time for range (None = to end)
        self.cut_end_seconds: Optional[float] = None  # Additional seconds for range end

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
        
        # Processing state
        self.is_processing: bool = False
        self.current_file_index: int = 0
        
        # Logs
        self.logs: List[str] = []
        self.log_callbacks: List[Callable[[str], None]] = []
        
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
        """Total cut time in seconds (minutes + seconds combined)"""
        return (self.cut_minutes * 60) + self.cut_seconds

    @property
    def cut_start_total_seconds(self) -> float:
        """Total start time in seconds for range mode"""
        return (self.cut_start_minutes * 60) + self.cut_start_seconds

    @property
    def cut_end_total_seconds(self) -> Optional[float]:
        """Total end time in seconds for range mode"""
        if self.cut_end_minutes is None and self.cut_end_seconds is None:
            return None
        mins = self.cut_end_minutes or 0.0
        secs = self.cut_end_seconds or 0.0
        return (mins * 60) + secs


