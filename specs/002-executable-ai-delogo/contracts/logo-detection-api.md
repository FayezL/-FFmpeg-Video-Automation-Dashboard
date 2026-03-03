# Logo Detection API Contract

**Feature**: Standalone Executable & AI Logo Detection
**Date**: 2026-02-08
**Status**: Complete
**Version**: 1.0

## Overview

This document defines the programmatic interface for logo detection functionality. All functions are designed to be called from the UI layer and execute detection in background threads to avoid blocking the interface.

---

## Core Detection API

### `detect_logos()`

Analyze a video file and detect logo regions.

**Function Signature**:
```python
def detect_logos(
    video_path: str,
    config: DetectionConfig,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    cancel_flag: Optional[threading.Event] = None
) -> DetectionSession
```

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `video_path` | `str` | Yes | Absolute path to video file |
| `config` | `DetectionConfig` | Yes | Detection configuration |
| `progress_callback` | `Callable` | No | Called with (progress: float, message: str) |
| `cancel_flag` | `threading.Event` | No | Set to cancel detection |

**Returns**:
- `DetectionSession` - Complete session with all results

**Raises**:
- `FileNotFoundError` - Video file doesn't exist
- `VideoReadError` - Cannot open or read video
- `DetectionCancelledError` - User cancelled via cancel_flag
- `DetectionTimeoutError` - Processing took longer than 5 minutes

**Progress Callback Invocations**:
1. `(0.0, "Analyzing video...")` - Starting
2. `(0.1, "Video opened: 1920x1080, 30fps")` - Video info extracted
3. `(0.15, "Sampling frames...")` - Frame extraction started
4. `(0.2 - 0.9, "Processing frame 500/4000...")` - Progress updates every 10%
5. `(0.95, "Clustering results...")` - Post-processing
6. `(1.0, "Detection complete: 3 regions found")` - Done

**Example Usage**:
```python
import threading
from src.logo_detector import detect_logos
from src.data_model import DetectionConfig

# Setup
config = DetectionConfig(
    sensitivity=0.75,
    frame_sampling=30,
    position_zones=["top-right", "bottom-right"]
)
cancel_event = threading.Event()

# Progress callback
def on_progress(progress: float, message: str):
    print(f"{progress:.0%}: {message}")
    progress_bar.set(progress)

# Run detection
try:
    session = detect_logos(
        video_path="C:/Videos/movie.mp4",
        config=config,
        progress_callback=on_progress,
        cancel_flag=cancel_event
    )

    print(f"Found {len(session.results)} logo regions")
    for result in session.results:
        print(f"  - Region at ({result.x}, {result.y}) with {result.confidence:.0%} confidence")

except DetectionCancelledError:
    print("User cancelled detection")
except VideoReadError as e:
    print(f"Error reading video: {e}")
```

**Performance Contract**:
- Must complete within 5 minutes or raise `DetectionTimeoutError`
- Progress updates at least every 10%
- Memory usage must not exceed 2GB
- Must release video file handle on completion or error

**Threading Contract**:
- Safe to call from background thread
- Does NOT block UI thread
- Checks `cancel_flag` every frame
- Progress callback invoked from worker thread (UI must use thread-safe updates)

---

### `preview_detection()`

Generate a preview image showing detected region on a video frame.

**Function Signature**:
```python
def preview_detection(
    result: DetectionResult,
    video_path: str,
    draw_confidence: bool = True
) -> PIL.Image.Image
```

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `result` | `DetectionResult` | Yes | Detection result to preview |
| `video_path` | `str` | Yes | Path to source video |
| `draw_confidence` | `bool` | No | Show confidence label (default: True) |

**Returns**:
- `PIL.Image.Image` - Preview image with bounding box overlay

**Raises**:
- `FileNotFoundError` - Video file doesn't exist
- `FrameNotFoundError` - Frame index invalid for video

**Preview Specifications**:
- Bounding box color: Green (0, 255, 0) for accepted, Red (255, 0, 0) for rejected, Yellow (255, 255, 0) for pending
- Box line thickness: 2 pixels
- Confidence label position: Top-left of box, 5px offset
- Confidence label format: "87%" (percentage with no decimal)
- Image size: Original frame dimensions (no scaling)

**Example Usage**:
```python
from PIL import ImageTk

# Generate preview
preview_img = preview_detection(
    result=detection_results[0],
    video_path="C:/Videos/movie.mp4",
    draw_confidence=True
)

# Display in CustomTkinter
photo = ImageTk.PhotoImage(preview_img)
preview_label.configure(image=photo)
preview_label.image = photo  # Keep reference
```

**Performance Contract**:
- Must complete within 500ms
- Memory usage for preview: max 50MB
- Must close video file after frame extraction

---

## Profile Management API

### `save_profile()`

Save a detection profile to disk.

**Function Signature**:
```python
def save_profile(
    profile: DetectionProfile,
    path: Optional[str] = None
) -> str
```

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `profile` | `DetectionProfile` | Yes | Profile to save |
| `path` | `str` | No | Custom save path (default: profiles dir) |

**Returns**:
- `str` - Absolute path where profile was saved

**Raises**:
- `ValueError` - Profile validation failed
- `IOError` - Cannot write to file system
- `DuplicateProfileError` - Profile name already exists

**File Naming**:
- Default: `{sanitized_name}.json` in `%APPDATA%/MagicTVBox/profiles/`
- Sanitized: Lowercase, spaces → underscores, special chars removed
- Example: "CNN News Watermark" → "cnn_news_watermark.json"

**Example Usage**:
```python
from src.detection_profiles import save_profile
from src.data_model import DetectionProfile, DetectionConfig

# Create profile
profile = DetectionProfile(
    version="1.0",
    profile_id="prof_xyz789",
    name="CNN News Watermark",
    description="For CNN broadcasts",
    created_at="2026-02-08T10:00:00Z",
    modified_at="2026-02-08T10:00:00Z",
    config=DetectionConfig(sensitivity=0.8, frame_sampling=30, ...),
    known_patterns=[],
    statistics=ProfileStatistics(...),
    tags=["cnn", "news"]
)

# Save
try:
    path = save_profile(profile)
    print(f"Profile saved to: {path}")
except DuplicateProfileError:
    print("Profile name already exists. Choose different name.")
```

**Storage Contract**:
- JSON format with 2-space indentation
- UTF-8 encoding
- Atomic write (temp file → rename to avoid corruption)
- File permissions: User read/write only (Windows ACLs)

---

### `load_profile()`

Load a detection profile from disk.

**Function Signature**:
```python
def load_profile(
    path: str
) -> DetectionProfile
```

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `str` | Yes | Path to profile JSON file |

**Returns**:
- `DetectionProfile` - Loaded and validated profile

**Raises**:
- `FileNotFoundError` - Profile file doesn't exist
- `JSONDecodeError` - Invalid JSON format
- `ProfileValidationError` - Profile data invalid
- `ProfileVersionError` - Unsupported profile version

**Example Usage**:
```python
from src.detection_profiles import load_profile

try:
    profile = load_profile("C:/Users/User/AppData/Roaming/MagicTVBox/profiles/cnn_news_watermark.json")
    print(f"Loaded profile: {profile.name}")
    print(f"Sensitivity: {profile.config.sensitivity}")
except ProfileVersionError as e:
    print(f"Profile version not supported: {e.version}")
```

**Migration Contract**:
- If profile version < current, attempt migration
- If migration fails, raise `ProfileVersionError`
- Preserve original file, save migrated version with `.v2` suffix

---

### `list_profiles()`

List all available detection profiles.

**Function Signature**:
```python
def list_profiles(
    profiles_dir: Optional[str] = None
) -> List[ProfileMetadata]
```

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `profiles_dir` | `str` | No | Custom profiles directory (default: standard location) |

**Returns**:
- `List[ProfileMetadata]` - List of profile metadata (name, description, tags, stats)

**ProfileMetadata Structure**:
```python
@dataclass
class ProfileMetadata:
    filename: str
    name: str
    description: Optional[str]
    tags: List[str]
    last_used: Optional[str]
    videos_processed: int
    average_accuracy: float
```

**Example Usage**:
```python
from src.detection_profiles import list_profiles

profiles = list_profiles()
for p in profiles:
    print(f"{p.name}: {p.average_accuracy:.0%} accuracy across {p.videos_processed} videos")
    print(f"  Tags: {', '.join(p.tags)}")
```

**Performance Contract**:
- Must complete within 1 second for up to 100 profiles
- Does NOT load full profile content (only metadata)
- Caches results for 10 seconds

---

### `delete_profile()`

Delete a detection profile.

**Function Signature**:
```python
def delete_profile(
    path: str,
    confirm: bool = False
) -> bool
```

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `str` | Yes | Path to profile file |
| `confirm` | `bool` | Yes | Must be True to actually delete |

**Returns**:
- `bool` - True if deleted, False if `confirm=False`

**Raises**:
- `FileNotFoundError` - Profile doesn't exist
- `IOError` - Cannot delete file

**Safety Contract**:
- Requires explicit `confirm=True` parameter
- No undo mechanism (permanent deletion)
- UI should show confirmation dialog before calling

**Example Usage**:
```python
from src.detection_profiles import delete_profile

# UI shows: "Are you sure you want to delete 'CNN News Watermark'?"
if user_confirmed:
    delete_profile(profile_path, confirm=True)
    print("Profile deleted")
```

---

## Utility Functions

### `estimate_detection_time()`

Estimate how long detection will take for a video.

**Function Signature**:
```python
def estimate_detection_time(
    video_path: str,
    config: DetectionConfig
) -> float
```

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `video_path` | `str` | Yes | Path to video file |
| `config` | `DetectionConfig` | Yes | Detection configuration |

**Returns**:
- `float` - Estimated time in seconds

**Estimation Formula**:
```python
video_info = get_video_info(video_path)
total_frames = video_info.frame_count
sampled_frames = total_frames // config.frame_sampling
processing_time_per_frame = 0.05  # 50ms average
estimated_time = sampled_frames * processing_time_per_frame
return estimated_time
```

**Example Usage**:
```python
estimated_seconds = estimate_detection_time("movie.mp4", config)
estimated_minutes = estimated_seconds / 60
print(f"Estimated detection time: {estimated_minutes:.1f} minutes")
```

---

### `validate_video()`

Check if a video file is valid and supported.

**Function Signature**:
```python
def validate_video(
    video_path: str
) -> Tuple[bool, Optional[str]]
```

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `video_path` | `str` | Yes | Path to video file |

**Returns**:
- `Tuple[bool, Optional[str]]` - (is_valid, error_message)

**Validation Checks**:
1. File exists
2. File is readable
3. OpenCV can open file
4. Video has at least 1 frame
5. Video codec is supported
6. Resolution is reasonable (16x16 to 7680x4320)

**Example Usage**:
```python
is_valid, error = validate_video("movie.mp4")
if not is_valid:
    print(f"Invalid video: {error}")
else:
    print("Video is valid for detection")
```

---

## Error Hierarchy

```
DetectionError (base exception)
├── VideoReadError
│   ├── FileNotFoundError (built-in)
│   └── InvalidVideoFormatError
├── DetectionFailedError
│   ├── DetectionTimeoutError
│   └── DetectionCancelledError
└── ProfileError
    ├── ProfileValidationError
    ├── ProfileVersionError
    └── DuplicateProfileError
```

**Exception Definitions**:

```python
class DetectionError(Exception):
    """Base exception for all detection errors"""
    pass

class VideoReadError(DetectionError):
    """Cannot read or parse video file"""
    def __init__(self, video_path: str, reason: str):
        self.video_path = video_path
        self.reason = reason
        super().__init__(f"Cannot read {video_path}: {reason}")

class DetectionCancelledError(DetectionError):
    """User cancelled detection"""
    def __init__(self, frames_processed: int, total_frames: int):
        self.frames_processed = frames_processed
        self.total_frames = total_frames
        super().__init__(f"Detection cancelled ({frames_processed}/{total_frames} frames processed)")

class DetectionTimeoutError(DetectionError):
    """Detection took too long"""
    def __init__(self, elapsed_time: float):
        self.elapsed_time = elapsed_time
        super().__init__(f"Detection timeout after {elapsed_time:.1f} seconds")

class ProfileValidationError(DetectionError):
    """Profile data is invalid"""
    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"Invalid profile field '{field}': {reason}")
```

---

## Threading & Concurrency

### Thread Safety Guarantees

**Thread-Safe Functions** (can be called from any thread):
- `detect_logos()` - Designed for background thread execution
- `preview_detection()` - Read-only operation
- `save_profile()` - File I/O with locks
- `load_profile()` - Read-only operation
- `list_profiles()` - Read-only with caching

**Not Thread-Safe** (must be called from main thread):
- None (all functions are thread-safe)

### UI Integration Pattern

```python
import threading
from queue import Queue

class DetectionController:
    def __init__(self, ui_widget):
        self.ui_widget = ui_widget
        self.progress_queue = Queue()
        self.cancel_event = threading.Event()
        self.worker_thread = None

    def start_detection(self, video_path: str, config: DetectionConfig):
        """Start detection in background thread"""
        self.cancel_event.clear()
        self.worker_thread = threading.Thread(
            target=self._detection_worker,
            args=(video_path, config)
        )
        self.worker_thread.daemon = True
        self.worker_thread.start()

        # Start UI update loop
        self.ui_widget.after(100, self._check_progress)

    def _detection_worker(self, video_path: str, config: DetectionConfig):
        """Background worker thread"""
        try:
            session = detect_logos(
                video_path=video_path,
                config=config,
                progress_callback=lambda p, m: self.progress_queue.put(('progress', p, m)),
                cancel_flag=self.cancel_event
            )
            self.progress_queue.put(('done', session))
        except Exception as e:
            self.progress_queue.put(('error', e))

    def _check_progress(self):
        """Check for updates from worker thread (runs on main thread)"""
        try:
            while True:
                msg = self.progress_queue.get_nowait()

                if msg[0] == 'progress':
                    _, progress, message = msg
                    self.ui_widget.update_progress(progress, message)

                elif msg[0] == 'done':
                    _, session = msg
                    self.ui_widget.show_results(session.results)
                    return  # Done

                elif msg[0] == 'error':
                    _, error = msg
                    self.ui_widget.show_error(str(error))
                    return  # Done

        except queue.Empty:
            pass

        # Schedule next check if still running
        if self.worker_thread and self.worker_thread.is_alive():
            self.ui_widget.after(100, self._check_progress)

    def cancel_detection(self):
        """Request cancellation"""
        self.cancel_event.set()
```

---

## Performance Requirements

| Operation | Target | Maximum | Measurement |
|-----------|--------|---------|-------------|
| `detect_logos()` | <120s | 300s (5min) | 1-hour video, 30-frame sampling |
| `preview_detection()` | <200ms | 500ms | 1920x1080 frame with overlay |
| `save_profile()` | <50ms | 200ms | Standard profile size |
| `load_profile()` | <100ms | 500ms | Standard profile size |
| `list_profiles()` | <500ms | 1000ms | Up to 100 profiles |
| Frame processing | <50ms | 100ms | Per frame in `detect_logos()` |

**Memory Requirements**:
- `detect_logos()`: Max 2GB during processing
- `preview_detection()`: Max 50MB for frame + overlay
- Profile operations: Max 10MB per profile

---

## Backward Compatibility

### Profile Format Versioning

Profiles include a `version` field for forward compatibility:

```python
def load_profile(path: str) -> DetectionProfile:
    with open(path) as f:
        data = json.load(f)

    version = data.get("version", "1.0")

    if version == "1.0":
        return DetectionProfile(**data)

    elif version == "1.1":
        # Future version migration
        migrated_data = migrate_1_1_to_1_0(data)
        return DetectionProfile(**migrated_data)

    else:
        raise ProfileVersionError(f"Unsupported profile version: {version}")
```

---

## Testing Contract

All API functions must have:

1. **Unit Tests** covering:
   - Happy path with valid inputs
   - Error cases with invalid inputs
   - Edge cases (empty videos, corrupted profiles, etc.)

2. **Contract Tests** verifying:
   - Input validation
   - Output format
   - Exception types
   - Performance requirements

3. **Integration Tests** covering:
   - Full detection workflow
   - Profile save/load/delete cycle
   - Cancellation behavior
   - Thread safety

**Test Fixtures Location**: `tests/fixtures/`
- `sample_with_logo.mp4` - 10-second video with visible logo
- `sample_no_logo.mp4` - 10-second video without logos
- `sample_profile.json` - Valid profile for testing
- `corrupted_profile.json` - Invalid profile for error testing

---

**API contract complete. All functions defined with inputs, outputs, errors, and performance requirements.**
