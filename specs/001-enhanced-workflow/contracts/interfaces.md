# Service Interfaces & Contracts

**Feature**: 001-enhanced-workflow
**Date**: 2026-02-08
**Type**: Python Interface Contracts

## Overview

This document defines the public interfaces for all new service classes in the Enhanced Workflow feature. These contracts serve as the API boundary between components and must remain stable.

---

## 1. TemplateManager

Manages saving, loading, and listing of configuration templates.

```python
class TemplateManager:
    """Template persistence and retrieval service"""

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize template manager.

        Args:
            templates_dir: Directory for template storage. Defaults to ~/.magictvbox/templates/
        """
        ...

    def save_template(self, template: Template) -> None:
        """
        Save a template to disk.

        Args:
            template: Template object to save

        Raises:
            ValueError: If template name invalid
            IOError: If unable to write file
        """
        ...

    def load_template(self, name: str) -> Template:
        """
        Load a template by name.

        Args:
            name: Template name (without .json extension)

        Returns:
            Template object

        Raises:
            FileNotFoundError: If template doesn't exist
            ValueError: If template JSON is invalid
        """
        ...

    def list_templates(self) -> List[Tuple[str, str]]:
        """
        List all available templates.

        Returns:
            List of (name, description) tuples sorted by name
        """
        ...

    def delete_template(self, name: str) -> None:
        """
        Delete a template.

        Args:
            name: Template name to delete

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        ...

    def template_exists(self, name: str) -> bool:
        """
        Check if a template exists.

        Args:
            name: Template name to check

        Returns:
            True if template exists, False otherwise
        """
        ...

    def export_template(self, name: str, export_path: str) -> None:
        """
        Export a template to a specific file path.

        Args:
            name: Template name to export
            export_path: Absolute path for exported JSON file

        Raises:
            FileNotFoundError: If template doesn't exist
            IOError: If unable to write export file
        """
        ...

    def import_template(self, import_path: str, new_name: Optional[str] = None) -> Template:
        """
        Import a template from a file.

        Args:
            import_path: Path to template JSON file
            new_name: Optional new name for imported template

        Returns:
            Imported Template object

        Raises:
            FileNotFoundError: If import file doesn't exist
            ValueError: If template JSON is invalid
        """
        ...
```

---

## 2. ParallelProcessor

Manages parallel batch video processing with thread pooling.

```python
class ParallelProcessor:
    """Parallel video processing with worker pool"""

    def __init__(
        self,
        state: AppState,
        video_processor: VideoProcessor,
        max_workers: int = 2
    ):
        """
        Initialize parallel processor.

        Args:
            state: Application state
            video_processor: Video processor instance
            max_workers: Maximum concurrent workers
        """
        ...

    def process_batch(
        self,
        files: List[ProcessingFile],
        on_file_start: Optional[Callable[[ProcessingFile], None]] = None,
        on_file_complete: Optional[Callable[[ProcessingFile, bool, Optional[str]], None]] = None,
        on_progress: Optional[Callable[[str, float], None]] = None
    ) -> None:
        """
        Process a batch of files in parallel.

        Args:
            files: List of files to process
            on_file_start: Callback when file processing starts (file)
            on_file_complete: Callback when file completes (file, success, error_msg)
            on_progress: Callback for progress updates (file_id, percent)

        Note:
            Processing runs in background thread. Call stop() to terminate.
        """
        ...

    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop all active processing gracefully.

        Args:
            timeout: Maximum seconds to wait for workers to stop

        Note:
            Terminates all FFmpeg subprocesses and waits for threads to exit.
        """
        ...

    def is_processing(self) -> bool:
        """
        Check if batch processing is active.

        Returns:
            True if workers are processing, False otherwise
        """
        ...

    def get_active_count(self) -> int:
        """
        Get number of currently active workers.

        Returns:
            Count of workers currently processing files
        """
        ...

    def get_queue_size(self) -> int:
        """
        Get number of files waiting in queue.

        Returns:
            Count of pending files not yet started
        """
        ...
```

---

## 3. HardwareEncoderDetector

Detects and manages hardware video encoders.

```python
class HardwareEncoderDetector:
    """Hardware encoder detection and management"""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Initialize encoder detector.

        Args:
            ffmpeg_path: Path to FFmpeg binary
        """
        ...

    def detect_encoders(self) -> List[HardwareEncoder]:
        """
        Detect all available hardware encoders.

        Returns:
            List of detected HardwareEncoder objects

        Note:
            Runs 'ffmpeg -encoders' and parses output.
            Returns empty list if no hardware encoders found.
        """
        ...

    def test_encoder(self, encoder: HardwareEncoder) -> bool:
        """
        Test if an encoder is actually functional.

        Args:
            encoder: Encoder to test

        Returns:
            True if encoder works, False if fails

        Note:
            Attempts a quick 1-second test encode to verify functionality.
        """
        ...

    def create_gpu_profiles(
        self,
        encoders: List[HardwareEncoder],
        base_profiles: Dict[str, ProcessingProfile]
    ) -> Dict[str, ProcessingProfile]:
        """
        Create GPU-accelerated variants of base profiles.

        Args:
            encoders: List of available encoders
            base_profiles: Dictionary of base processing profiles

        Returns:
            Dictionary of new GPU profiles with keys like "universal_nvenc"

        Note:
            Only creates profiles for encoders that pass test_encoder().
        """
        ...

    def get_recommended_encoder(self, encoders: List[HardwareEncoder]) -> Optional[HardwareEncoder]:
        """
        Get the recommended encoder for this system.

        Args:
            encoders: List of available encoders

        Returns:
            Recommended encoder or None if no good option

        Note:
            Prefers NVENC > QuickSync > VideoToolbox > AMF based on performance.
        """
        ...
```

---

## 4. VideoMetadataExtractor

Extracts and caches video metadata.

```python
class VideoMetadataExtractor:
    """Video metadata extraction and caching"""

    def __init__(self, ffprobe_path: str = "ffprobe", cache_size: int = 1000):
        """
        Initialize metadata extractor.

        Args:
            ffprobe_path: Path to ffprobe binary
            cache_size: Maximum cache entries (LRU eviction)
        """
        ...

    def extract_metadata(self, file_path: str) -> VideoMetadata:
        """
        Extract metadata from a video file.

        Args:
            file_path: Absolute path to video file

        Returns:
            VideoMetadata object with extracted information

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a valid video

        Note:
            Result is cached by file path. Cache expires after 5 minutes.
        """
        ...

    def validate_against_profile(
        self,
        metadata: VideoMetadata,
        profile: ProcessingProfile
    ) -> List[str]:
        """
        Validate video metadata against a processing profile.

        Args:
            metadata: Video metadata
            profile: Processing profile

        Returns:
            List of warning messages (empty if no issues)

        Example warnings:
            - "Video will be downscaled from 4K to 1080p"
            - "Video codec may be incompatible with profile"
        """
        ...

    def clear_cache(self) -> None:
        """Clear all cached metadata."""
        ...

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with keys: 'size', 'hits', 'misses', 'hit_rate'
        """
        ...
```

---

## 5. FilterChainBuilder

Builds FFmpeg filter chains from user configuration.

```python
class FilterChainBuilder:
    """FFmpeg filter chain construction"""

    @staticmethod
    def build_filter_string(filter_chain: FilterChain) -> str:
        """
        Build FFmpeg -vf filter string from FilterChain.

        Args:
            filter_chain: FilterChain object with ordered filters

        Returns:
            FFmpeg filter string (e.g., "rotate=PI/2,crop=1920:800:0:140")

        Note:
            Returns empty string if no enabled filters.
            Filters are always applied in fixed order to prevent artifacts.
        """
        ...

    @staticmethod
    def validate_filter_params(filter_name: str, params: Dict[str, Any]) -> List[str]:
        """
        Validate filter parameters.

        Args:
            filter_name: Name of filter (e.g., "crop", "rotate")
            params: Dictionary of filter parameters

        Returns:
            List of validation error messages (empty if valid)

        Example errors:
            - "Crop width must be positive"
            - "Rotate angle must be 90, 180, or 270"
        """
        ...

    @staticmethod
    def get_filter_defaults(filter_name: str) -> Dict[str, Any]:
        """
        Get default parameters for a filter.

        Args:
            filter_name: Name of filter

        Returns:
            Dictionary of default parameter values
        """
        ...
```

---

## 6. BatchStateManager

Manages batch processing state persistence and recovery.

```python
class BatchStateManager:
    """Batch state checkpoint and recovery management"""

    def __init__(self, state_dir: Optional[str] = None):
        """
        Initialize batch state manager.

        Args:
            state_dir: Directory for state files. Defaults to ~/.magictvbox/batch_states/
        """
        ...

    def create_batch(
        self,
        files: List[str],
        settings_snapshot: dict,
        output_folder: str
    ) -> BatchState:
        """
        Create a new batch state.

        Args:
            files: List of input file paths
            settings_snapshot: Serialized AppState settings
            output_folder: Output directory path

        Returns:
            New BatchState object with generated UUID
        """
        ...

    def save_checkpoint(self, batch_state: BatchState) -> None:
        """
        Save batch state checkpoint to disk.

        Args:
            batch_state: Current batch state

        Note:
            Updates last_updated_timestamp automatically.
            Checkpoint write is synchronous.
        """
        ...

    def load_batch(self, batch_id: str) -> BatchState:
        """
        Load a batch state from disk.

        Args:
            batch_id: UUID of batch to load

        Returns:
            BatchState object

        Raises:
            FileNotFoundError: If batch state file doesn't exist
            ValueError: If batch state JSON is invalid
        """
        ...

    def find_incomplete_batches(self) -> List[BatchState]:
        """
        Find all incomplete batch states.

        Returns:
            List of BatchState objects for incomplete batches sorted by most recent

        Note:
            Scans batch_states/ directory for any non-complete batches.
        """
        ...

    def delete_batch(self, batch_id: str) -> None:
        """
        Delete a batch state file.

        Args:
            batch_id: UUID of batch to delete
        """
        ...

    def verify_output_files(
        self,
        batch_state: BatchState,
        completed_files: List[str]
    ) -> List[str]:
        """
        Verify that output files exist and match expected duration.

        Args:
            batch_state: Batch state to verify
            completed_files: List of completed input file paths

        Returns:
            List of file paths that need reprocessing (missing or invalid output)
        """
        ...
```

---

## 7. ErrorMessageParser

Parses FFmpeg error output into user-friendly messages.

```python
class ErrorMessageParser:
    """FFmpeg error message parsing and user-friendly translation"""

    @staticmethod
    def parse_ffmpeg_error(
        error_output: str,
        exit_code: int
    ) -> Tuple[str, Optional[str], List[str]]:
        """
        Parse FFmpeg error output into user-friendly message.

        Args:
            error_output: Raw FFmpeg stderr output
            exit_code: FFmpeg process exit code

        Returns:
            Tuple of (user_message, suggested_action, recovery_options)

        Example:
            ("GPU encoding unavailable",
             "Please update NVIDIA drivers or use a CPU profile",
             ["Use CPU Profile", "Update Drivers", "Skip File"])

        Note:
            Falls back to generic message if error pattern not recognized.
        """
        ...

    @staticmethod
    def get_known_error_patterns() -> Dict[str, Dict[str, Any]]:
        """
        Get dictionary of known error patterns.

        Returns:
            Dict mapping regex patterns to error info with keys:
            - 'user_message': User-friendly error description
            - 'suggested_action': What user should do
            - 'recovery_options': List of action button labels
        """
        ...

    @staticmethod
    def extract_relevant_output(full_output: str, max_lines: int = 15) -> str:
        """
        Extract most relevant lines from FFmpeg output.

        Args:
            full_output: Full FFmpeg stderr output
            max_lines: Maximum lines to include

        Returns:
            Filtered error output (last N lines)
        """
        ...
```

---

## 8. DragDropHandler

Handles drag-and-drop events in the UI.

```python
class DragDropHandler:
    """Drag-and-drop file handling for CustomTkinter"""

    def __init__(self, widget: ctk.CTkFrame, on_drop: Callable[[List[str]], None]):
        """
        Initialize drag-drop handler.

        Args:
            widget: CustomTkinter widget to enable drag-drop on
            on_drop: Callback when files are dropped (receives list of file paths)
        """
        ...

    def enable(self) -> None:
        """Enable drag-drop on the widget."""
        ...

    def disable(self) -> None:
        """Disable drag-drop on the widget."""
        ...

    def set_drop_callback(self, callback: Callable[[List[str]], None]) -> None:
        """
        Update the drop callback function.

        Args:
            callback: New callback function
        """
        ...

    def filter_video_files(self, file_paths: List[str]) -> List[str]:
        """
        Filter list to only valid video files.

        Args:
            file_paths: List of file or folder paths

        Returns:
            List of video file paths (recursively scans folders)

        Note:
            Supports: .mp4, .mkv, .avi, .mov, .m4v, .webm
        """
        ...
```

---

## Interface Contracts Summary

| Service | Primary Responsibility | Key Methods |
|---------|------------------------|-------------|
| TemplateManager | Template CRUD operations | save_template, load_template, list_templates |
| ParallelProcessor | Parallel batch processing | process_batch, stop, get_active_count |
| HardwareEncoderDetector | GPU encoder detection | detect_encoders, test_encoder, create_gpu_profiles |
| VideoMetadataExtractor | Video metadata extraction | extract_metadata, validate_against_profile |
| FilterChainBuilder | FFmpeg filter string building | build_filter_string, validate_filter_params |
| BatchStateManager | Batch state persistence | create_batch, save_checkpoint, find_incomplete_batches |
| ErrorMessageParser | Error message translation | parse_ffmpeg_error, get_known_error_patterns |
| DragDropHandler | Drag-drop event handling | enable, filter_video_files |

---

## Usage Example

```python
from src.templates import TemplateManager
from src.parallel_processor import ParallelProcessor
from src.hardware_encoders import HardwareEncoderDetector
from src.state import AppState

# Initialize services
template_manager = TemplateManager()
encoder_detector = HardwareEncoderDetector()
state = AppState()

# Detect hardware encoders
encoders = encoder_detector.detect_encoders()
if encoders:
    state.detected_encoders = encoders
    state.selected_encoder = encoder_detector.get_recommended_encoder(encoders)

# Load a template
try:
    template = template_manager.load_template("youtube-export")
    # Apply template settings to state
    state.cut_mode = template.trim_mode
    state.cut_minutes = template.cut_minutes
    # ... etc
except FileNotFoundError:
    print("Template not found")

# Start parallel processing
parallel_processor = ParallelProcessor(state, video_processor, max_workers=3)
parallel_processor.process_batch(
    state.selected_files,
    on_file_complete=lambda file, success, error: print(f"{file.name}: {success}")
)
```

---

## Testing Contracts

Each service interface must have:
1. **Unit tests**: Test each method in isolation with mocked dependencies
2. **Integration tests**: Test service interactions (e.g., TemplateManager + BatchStateManager)
3. **Contract tests**: Verify method signatures and return types match specification

Example test structure:
```python
# tests/test_template_manager.py
def test_save_template():
    """Test template saving with valid template"""
    manager = TemplateManager(temp_dir)
    template = Template(name="test", description="Test template", ...)
    manager.save_template(template)  # Should not raise
    assert manager.template_exists("test")

def test_load_nonexistent_template():
    """Test loading non-existent template raises FileNotFoundError"""
    manager = TemplateManager(temp_dir)
    with pytest.raises(FileNotFoundError):
        manager.load_template("nonexistent")
```

---

## Error Handling Contracts

All service methods must:
1. **Raise specific exceptions**: Use built-in exceptions (ValueError, FileNotFoundError, IOError)
2. **Document exceptions**: List all possible exceptions in docstring
3. **Validate inputs**: Check preconditions and raise ValueError if invalid
4. **Clean up resources**: Use try/finally or context managers

Example:
```python
def save_template(self, template: Template) -> None:
    """
    Save a template to disk.

    Raises:
        ValueError: If template.name contains invalid characters
        IOError: If unable to write file (permission denied, disk full)
    """
    if not self._is_valid_name(template.name):
        raise ValueError(f"Invalid template name: {template.name}")

    try:
        with open(self._get_path(template.name), 'w') as f:
            json.dump(template.to_dict(), f, indent=2)
    except OSError as e:
        raise IOError(f"Failed to save template: {e}")
```

---

**End of Interface Contracts**
