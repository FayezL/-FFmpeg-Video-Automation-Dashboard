# Data Model: Enhanced Workflow & Performance

**Feature**: 001-enhanced-workflow
**Date**: 2026-02-08
**Status**: Draft

## Overview

This document defines the data structures and entities required for the Enhanced Workflow & Performance feature. All entities are defined as Python dataclasses for type safety and clarity.

---

## Core Entities

### 1. Template

Represents a saved configuration preset that users can load to quickly apply settings.

```python
@dataclass
class Template:
    """Saved configuration preset"""
    # Identification
    name: str                           # Template name (max 50 chars)
    description: str                    # User-provided description
    created_timestamp: float            # Unix timestamp

    # Trim/Cut Settings
    trim_mode: CutMode                  # CUT_NONE, CUT_LAST, CUT_FIRST, CUT_RANGE
    cut_minutes: float = 0.0            # Minutes to cut (for CUT_LAST/CUT_FIRST)
    cut_seconds: float = 0.0            # Additional seconds to cut
    cut_start_minutes: float = 0.0      # Start time for CUT_RANGE (minutes)
    cut_start_seconds: float = 0.0      # Additional seconds for range start
    cut_end_minutes: Optional[float] = None    # End time for CUT_RANGE (None = to end)
    cut_end_seconds: Optional[float] = None    # Additional seconds for range end

    # Processing Profile (stored as key to PROCESSING_PROFILES)
    processing_profile_key: str = "universal"

    # Delogo Settings
    apply_delogo: bool = False
    delogo_x: int = 0
    delogo_y: int = 0
    delogo_w: int = 0
    delogo_h: int = 0

    # Filter Settings
    apply_filters: bool = False
    filters: Dict[str, Any] = field(default_factory=dict)  # Filter name -> params

    # Output Settings
    output_format: str = "mp4"          # mp4, mkv
    output_suffix: str = ""             # e.g. "_processed"
    output_prefix: str = ""             # e.g. "converted_"
    create_output_subfolder: bool = False
    overwrite_existing: bool = True

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict"""
        return {
            "name": self.name,
            "description": self.description,
            "created_timestamp": self.created_timestamp,
            "trim_mode": self.trim_mode.value,
            "cut_minutes": self.cut_minutes,
            "cut_seconds": self.cut_seconds,
            "cut_start_minutes": self.cut_start_minutes,
            "cut_start_seconds": self.cut_start_seconds,
            "cut_end_minutes": self.cut_end_minutes,
            "cut_end_seconds": self.cut_end_seconds,
            "processing_profile_key": self.processing_profile_key,
            "apply_delogo": self.apply_delogo,
            "delogo_x": self.delogo_x,
            "delogo_y": self.delogo_y,
            "delogo_w": self.delogo_w,
            "delogo_h": self.delogo_h,
            "apply_filters": self.apply_filters,
            "filters": self.filters,
            "output_format": self.output_format,
            "output_suffix": self.output_suffix,
            "output_prefix": self.output_prefix,
            "create_output_subfolder": self.create_output_subfolder,
            "overwrite_existing": self.overwrite_existing
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Template':
        """Deserialize from JSON dict"""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            created_timestamp=data["created_timestamp"],
            trim_mode=CutMode(data["trim_mode"]),
            cut_minutes=data.get("cut_minutes", 0.0),
            cut_seconds=data.get("cut_seconds", 0.0),
            cut_start_minutes=data.get("cut_start_minutes", 0.0),
            cut_start_seconds=data.get("cut_start_seconds", 0.0),
            cut_end_minutes=data.get("cut_end_minutes"),
            cut_end_seconds=data.get("cut_end_seconds"),
            processing_profile_key=data.get("processing_profile_key", "universal"),
            apply_delogo=data.get("apply_delogo", False),
            delogo_x=data.get("delogo_x", 0),
            delogo_y=data.get("delogo_y", 0),
            delogo_w=data.get("delogo_w", 0),
            delogo_h=data.get("delogo_h", 0),
            apply_filters=data.get("apply_filters", False),
            filters=data.get("filters", {}),
            output_format=data.get("output_format", "mp4"),
            output_suffix=data.get("output_suffix", ""),
            output_prefix=data.get("output_prefix", ""),
            create_output_subfolder=data.get("create_output_subfolder", False),
            overwrite_existing=data.get("overwrite_existing", True)
        )
```

**Storage Location**: `~/.magictvbox/templates/{name}.json`

**Relationships**: None (standalone JSON file)

---

### 2. BatchState

Represents the state of an in-progress batch for recovery after interruption.

```python
@dataclass
class BatchState:
    """State of an in-progress batch for recovery"""
    # Identification
    batch_id: str                       # UUID for this batch
    started_timestamp: float            # Unix timestamp when batch started
    last_updated_timestamp: float       # Unix timestamp of last update

    # File List
    files: List[str]                    # List of all input file paths (absolute)
    completed_files: List[str]          # List of successfully completed file paths
    failed_files: List[str] = field(default_factory=list)  # List of failed file paths

    # Settings Snapshot (serialized AppState)
    settings_snapshot: dict = field(default_factory=dict)

    # Output Tracking
    output_folder: str = ""

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict"""
        return {
            "batch_id": self.batch_id,
            "started_timestamp": self.started_timestamp,
            "last_updated_timestamp": self.last_updated_timestamp,
            "files": self.files,
            "completed_files": self.completed_files,
            "failed_files": self.failed_files,
            "settings_snapshot": self.settings_snapshot,
            "output_folder": self.output_folder
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BatchState':
        """Deserialize from JSON dict"""
        return cls(
            batch_id=data["batch_id"],
            started_timestamp=data["started_timestamp"],
            last_updated_timestamp=data["last_updated_timestamp"],
            files=data["files"],
            completed_files=data["completed_files"],
            failed_files=data.get("failed_files", []),
            settings_snapshot=data.get("settings_snapshot", {}),
            output_folder=data.get("output_folder", "")
        )

    def is_complete(self) -> bool:
        """Check if batch is complete"""
        return len(self.completed_files) + len(self.failed_files) >= len(self.files)

    def get_pending_files(self) -> List[str]:
        """Get list of files not yet processed"""
        processed = set(self.completed_files) | set(self.failed_files)
        return [f for f in self.files if f not in processed]
```

**Storage Location**: `~/.magictvbox/batch_states/{batch_id}.json`

**Lifecycle**:
1. Created when batch processing starts
2. Updated after each file completes (checkpoint)
3. Detected on app startup if incomplete
4. Deleted when batch completes or user dismisses

---

### 3. VideoMetadata

Represents probed metadata from a video file, cached for performance.

```python
@dataclass
class VideoMetadata:
    """Cached metadata from video file probing"""
    # File Information
    file_path: str                      # Absolute path to video file
    file_size: int                      # File size in bytes

    # Video Properties
    duration: float                     # Duration in seconds
    width: int                          # Video width in pixels
    height: int                         # Video height in pixels
    codec: str                          # Video codec name (e.g., "h264")
    bitrate: Optional[int] = None       # Bitrate in bits/second
    fps: Optional[float] = None         # Frame rate
    pixel_format: Optional[str] = None  # Pixel format (e.g., "yuv420p")

    # Audio Properties
    audio_codec: Optional[str] = None   # Audio codec name (e.g., "aac")
    audio_bitrate: Optional[int] = None # Audio bitrate in bits/second

    # Validation
    is_valid: bool = True               # Whether file is readable
    validation_warnings: List[str] = field(default_factory=list)

    # Caching
    probed_timestamp: float = field(default_factory=lambda: time.time())

    def exceeds_resolution(self, max_width: Optional[int], max_height: Optional[int]) -> bool:
        """Check if video exceeds resolution limits"""
        if max_width and self.width > max_width:
            return True
        if max_height and self.height > max_height:
            return True
        return False

    def get_resolution_string(self) -> str:
        """Get resolution as string (e.g., '1920x1080')"""
        return f"{self.width}x{self.height}"

    def get_file_size_mb(self) -> float:
        """Get file size in MB"""
        return self.file_size / (1024 * 1024)

    def get_duration_string(self) -> str:
        """Get duration as formatted string (e.g., '12:34')"""
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return f"{minutes}:{seconds:02d}"
```

**Storage**: In-memory cache only (not persisted)

**Relationships**: Cached per file in processing queue

---

### 4. FilterChain

Represents a sequence of video filters to apply during encoding.

```python
@dataclass
class VideoFilter:
    """Single video filter with parameters"""
    name: str                           # Filter name (e.g., "rotate", "crop")
    params: Dict[str, Any]              # Filter-specific parameters
    enabled: bool = True                # Whether filter is active

    def to_ffmpeg_string(self) -> str:
        """Convert to FFmpeg filter string"""
        if self.name == "rotate":
            angle = self.params.get("angle", 90)
            angle_map = {90: "PI/2", 180: "PI", 270: "3*PI/2"}
            return f"rotate={angle_map.get(angle, '0')}"

        elif self.name == "crop":
            w = self.params.get("width", 0)
            h = self.params.get("height", 0)
            x = self.params.get("x", 0)
            y = self.params.get("y", 0)
            return f"crop={w}:{h}:{x}:{y}"

        elif self.name == "scale":
            w = self.params.get("width", -1)
            h = self.params.get("height", -1)
            return f"scale={w}:{h}"

        elif self.name == "brightness":
            value = self.params.get("value", 0.0)
            return f"eq=brightness={value}"

        elif self.name == "contrast":
            value = self.params.get("value", 1.0)
            return f"eq=contrast={value}"

        elif self.name == "saturation":
            value = self.params.get("value", 1.0)
            return f"eq=saturation={value}"

        elif self.name == "deinterlace":
            return "yadif"

        elif self.name == "delogo":
            x = self.params.get("x", 0)
            y = self.params.get("y", 0)
            w = self.params.get("w", 0)
            h = self.params.get("h", 0)
            return f"delogo=x={x}:y={y}:w={w}:h={h}"

        return ""


@dataclass
class FilterChain:
    """Ordered sequence of video filters"""
    filters: List[VideoFilter] = field(default_factory=list)

    def add_filter(self, name: str, params: Dict[str, Any]) -> None:
        """Add a filter to the chain"""
        self.filters.append(VideoFilter(name=name, params=params))

    def to_ffmpeg_string(self) -> str:
        """Build FFmpeg filter graph string"""
        # Fixed filter order to prevent artifacts
        filter_order = ["rotate", "crop", "scale", "brightness", "contrast",
                       "saturation", "deinterlace", "delogo"]

        # Sort filters by defined order
        sorted_filters = []
        for filter_name in filter_order:
            for f in self.filters:
                if f.enabled and f.name == filter_name:
                    sorted_filters.append(f)

        # Build comma-separated filter string
        filter_strings = [f.to_ffmpeg_string() for f in sorted_filters]
        return ",".join(filter_strings) if filter_strings else ""

    def is_empty(self) -> bool:
        """Check if chain has any enabled filters"""
        return not any(f.enabled for f in self.filters)
```

**Storage**: Part of AppState (not persisted separately)

**Relationships**: Applied to each video during processing

---

### 5. HardwareEncoder

Represents a detected hardware encoder with capability information.

```python
@dataclass
class HardwareEncoder:
    """Detected hardware video encoder"""
    # Identification
    name: str                           # Display name (e.g., "NVIDIA NVENC")
    encoder_type: str                   # "nvenc", "qsv", "videotoolbox", "amf"

    # Codecs Supported
    h264_codec: Optional[str] = None    # FFmpeg codec name for H.264 (e.g., "h264_nvenc")
    hevc_codec: Optional[str] = None    # FFmpeg codec name for H.265 (e.g., "hevc_nvenc")

    # Availability
    available: bool = True              # Whether encoder is currently available

    # Performance
    estimated_speedup: float = 10.0     # Estimated speedup vs CPU (e.g., 10.0 = 10x faster)

    def get_codec_for_profile(self, profile_key: str) -> Optional[str]:
        """Get appropriate codec for a profile"""
        # For now, always return H.264 codec (H.265 support is future enhancement)
        return self.h264_codec

    def create_gpu_profile_variant(self, base_profile: ProcessingProfile) -> ProcessingProfile:
        """Create GPU-accelerated variant of a profile"""
        gpu_profile = ProcessingProfile(
            name=f"{base_profile.name} - GPU",
            description=f"{base_profile.description} (Hardware-accelerated)",
            video_codec=self.h264_codec or base_profile.video_codec,
            video_preset=base_profile.video_preset,
            video_crf=base_profile.video_crf,
            video_bitrate=base_profile.video_bitrate,
            pixel_format=base_profile.pixel_format,
            audio_codec=base_profile.audio_codec,
            audio_bitrate=base_profile.audio_bitrate,
            use_faststart=base_profile.use_faststart,
            x264_profile=base_profile.x264_profile,
            x264_level=base_profile.x264_level,
            max_width=base_profile.max_width,
            max_height=base_profile.max_height
        )
        return gpu_profile
```

**Storage**: Detected at app startup, stored in memory

**Relationships**: Used to create GPU-accelerated profile variants

---

### 6. ParallelProcessingConfig

Configuration for parallel batch processing.

```python
@dataclass
class ParallelProcessingConfig:
    """Configuration for parallel processing"""
    # Worker Configuration
    max_workers: int = 2                # Maximum concurrent processes
    auto_adjust: bool = True            # Auto-adjust based on CPU cores

    # Performance Tuning
    cpu_cores: int = field(default_factory=lambda: os.cpu_count() or 4)
    ram_per_process_gb: float = 2.0     # Estimated RAM per encode process

    def calculate_optimal_workers(self) -> int:
        """Calculate optimal worker count based on system"""
        if self.auto_adjust:
            # Formula: max(1, min(4, (cores-1)//2))
            # Examples: 2 cores -> 1, 4 cores -> 1, 8 cores -> 3
            optimal = max(1, min(4, (self.cpu_cores - 1) // 2))
            return min(optimal, self.max_workers)
        return self.max_workers

    def estimate_memory_usage(self) -> float:
        """Estimate total memory usage in GB"""
        workers = self.calculate_optimal_workers()
        return workers * self.ram_per_process_gb
```

**Storage**: Part of AppState

**Relationships**: Used by ParallelProcessor

---

## AppState Extensions

The following fields must be added to the existing `AppState` class:

```python
# In src/state.py, add to AppState.__init__():

# Template System
self.current_template: Optional[str] = None  # Currently loaded template name
self.template_modified: bool = False         # Whether settings differ from template

# Parallel Processing
self.parallel_config: ParallelProcessingConfig = ParallelProcessingConfig()
self.active_processes: List[str] = []        # List of currently processing file IDs

# Hardware Encoders
self.detected_encoders: List[HardwareEncoder] = []
self.use_hardware_encoding: bool = False
self.selected_encoder: Optional[HardwareEncoder] = None

# Video Filters
self.filter_chain: FilterChain = FilterChain()

# Metadata Cache
self._metadata_cache: Dict[str, VideoMetadata] = {}

# Batch Recovery
self.current_batch_state: Optional[BatchState] = None
```

---

## Directory Structure

### Configuration Directory

**Windows**: `C:\Users\{username}\.magictvbox\`
**macOS**: `~/Library/Application Support/MagicTVBox/` or `~/.magictvbox/`

```
.magictvbox/
├── templates/
│   ├── youtube-export.json
│   ├── meeting-clips.json
│   └── ...
├── batch_states/
│   ├── {batch-uuid-1}.json
│   ├── {batch-uuid-2}.json
│   └── ...
└── config.json                  # App-wide settings
```

---

## JSON Schema Examples

### Template JSON

```json
{
  "name": "YouTube Export",
  "description": "Optimized for YouTube uploads - 1080p, high quality",
  "created_timestamp": 1707379200.0,
  "trim_mode": "cut_last",
  "cut_minutes": 5.0,
  "cut_seconds": 0.0,
  "cut_start_minutes": 0.0,
  "cut_start_seconds": 0.0,
  "cut_end_minutes": null,
  "cut_end_seconds": null,
  "processing_profile_key": "high_quality",
  "apply_delogo": false,
  "delogo_x": 0,
  "delogo_y": 0,
  "delogo_w": 0,
  "delogo_h": 0,
  "apply_filters": false,
  "filters": {},
  "output_format": "mp4",
  "output_suffix": "_yt",
  "output_prefix": "",
  "create_output_subfolder": false,
  "overwrite_existing": true
}
```

### BatchState JSON

```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "started_timestamp": 1707379200.0,
  "last_updated_timestamp": 1707380100.0,
  "files": [
    "C:/Videos/video1.mp4",
    "C:/Videos/video2.mp4",
    "C:/Videos/video3.mp4"
  ],
  "completed_files": [
    "C:/Videos/video1.mp4"
  ],
  "failed_files": [],
  "settings_snapshot": {
    "processing_profile": "universal",
    "cut_mode": "cut_last",
    "cut_minutes": 5.0
  },
  "output_folder": "C:/Videos/output/"
}
```

---

## Validation Rules

### Template Validation

- `name`: 1-50 characters, no special characters `/\:*?"<>|`
- `processing_profile_key`: Must exist in PROCESSING_PROFILES
- `output_format`: Must be "mp4" or "mkv"
- Time values: Non-negative floats
- Delogo coordinates: Non-negative integers

### BatchState Validation

- `batch_id`: Valid UUID format
- `files`: All paths must be absolute
- `completed_files` + `failed_files`: Subset of `files`
- Timestamps: Positive floats, `last_updated >= started`

### VideoMetadata Validation

- `duration`: Positive float (seconds)
- `width`, `height`: Positive integers (pixels)
- `codec`: Non-empty string
- `file_size`: Non-negative integer (bytes)

---

## Migration Notes

### From Previous Version

If upgrading from a version without templates:
- Create `~/.magictvbox/templates/` directory
- No existing templates to migrate

If batch processing interrupted in previous version:
- No recovery mechanism exists currently
- Users must restart from beginning
- New batch_states/ directory will enable recovery

---

## Performance Considerations

### Metadata Caching

- Cache VideoMetadata by absolute file path
- Evict cache entries after 5 minutes
- Max cache size: 1000 entries (LRU eviction)

### Template Loading

- Templates loaded on-demand (not all at startup)
- Template list cached (refresh on directory change)

### Batch State Checkpoints

- Write checkpoint after each file completes
- Checkpoint writes are async (don't block processing)
- Checkpoint failures logged but don't stop batch

---

## Error Handling

### Template Errors

- **Template Not Found**: Show error dialog, don't load
- **Invalid JSON**: Show parse error, allow manual fix
- **Missing Profile**: Fall back to "universal" profile
- **Validation Failure**: Show specific validation errors

### Batch State Errors

- **Corrupted State File**: Prompt user to start new batch
- **Missing Output Files**: Re-process missing files
- **Settings Mismatch**: Prompt user to choose settings

### Metadata Errors

- **Probe Failure**: Mark file invalid, exclude from batch
- **Missing Duration**: Estimate from file size
- **Unknown Codec**: Warn user, attempt processing anyway

---

## Future Enhancements

### Template System

- Template categories/tagging
- Template export/import (share with others)
- Template search/filter
- Default template selection

### Batch State

- Multi-batch history (last 10 batches)
- Batch analytics (total time, success rate)
- Batch scheduling (run at specific time)

### Metadata

- Thumbnail generation
- Detailed codec analysis
- Bitrate graphs
- Audio track detection

---

**End of Data Model Document**
