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
        self.cut_start_minutes: float = 0.0     # Start time for range (minutes)
        self.cut_end_minutes: Optional[float] = None  # End time for range (None = to end)
        
        # Legacy compatibility
        self.cut_last_5_minutes: bool = True
        
        # Processing options
        self.apply_delogo: bool = False
        self.delogo_params: DelogoParams = DelogoParams()
        
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


