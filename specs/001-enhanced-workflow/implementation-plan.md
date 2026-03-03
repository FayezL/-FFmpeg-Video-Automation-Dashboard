# Implementation Plan: Enhanced Workflow & Performance Feature

**Feature Branch**: `001-enhanced-workflow`
**Specification**: `specs/001-enhanced-workflow/spec.md`
**Date**: 2026-02-08
**Status**: Draft

---

## 1. Technical Context

### Project Overview
**MagicTVBox** is a Python desktop application for FFmpeg-based video batch processing with GUI automation. Users can process multiple videos with trimming, format conversion, and filter application.

### Language & Framework
- **Language**: Python 3.8+
- **GUI Framework**: CustomTkinter 5.0+ (modern Tkinter wrapper with native theming)
- **Video Processing**: FFmpeg 4.0+ (subprocess-based, with optional ffmpeg-python wrapper)
- **Threading Model**: Python threading (not multiprocessing, to avoid IPC complexity)
- **Standard Library**: subprocess, threading, json, pathlib, os, re, uuid, dataclasses

### Project Architecture
```
MagicTVBox/
├── main.py                     # Application entry point
├── src/
│   ├── state.py               # Central state management (AppState)
│   ├── video_processor.py      # FFmpeg command building and execution
│   └── ui/
│       ├── main_window.py      # Window management and sidebar
│       ├── batch_processor.py  # Batch processing UI
│       ├── single_processor.py # Single file UI
│       ├── settings_panel.py   # Settings UI
│       └── logs_panel.py       # Logs display
└── specs/
    └── 001-enhanced-workflow/
        └── spec.md             # Feature specification
```

### Key Design Patterns
- **Singleton State**: `AppState` centralized state management with callback system
- **Subprocess-based Processing**: FFmpeg invoked via subprocess.Popen for streaming output
- **Callback-based Progress**: on_progress/on_log callbacks for event notification
- **Threading for UI Responsiveness**: Processing happens in background threads

### Current Capabilities
- Single-file and batch video processing
- Trimming modes: Cut Last/First, Range selection
- Delogo filter application with configurable parameters
- Output format/naming customization
- Real-time progress tracking via regex parsing of FFmpeg output
- Serial (sequential) file processing only

### Dependencies Summary
```
CustomTkinter==5.0+         # GUI
FFmpeg 4.0+                 # Video processing (external binary)
ffmpeg-python (optional)    # Python FFmpeg wrapper
Python 3.8+ std libs
```

---

## 2. Performance & System Constraints

### Target Platform
- **OS**: Windows, macOS desktop
- **Architecture**: x86-64
- **RAM**: 2GB minimum system, 2GB per active encode process
- **Storage**: Output location must have free space ≥ input size

### Performance Goals
- **UI Responsiveness**: All UI interactions <200ms (no freezing during encoding)
- **Parallel Processing**: 2-4 simultaneous encodes on typical 4-core system
- **Metadata Probing**: <1 second per video file (cached)
- **Hardware Encoding**: 8-15x faster than CPU encoding on compatible systems
- **Batch Handling**: Support 100+ videos without crashes/memory leaks

### System Constraints
- **Maximum Parallel Processes**: 8 (configurable, default 2-4)
- **RAM per Process**: 2GB per active encode
- **Filter Chain Complexity**: ~50 filters max (FFmpeg limitation)
- **Template/Profile Names**: 50 characters max
- **Error Message Length**: 300 characters max (expandable details)

### Scale Requirements
- Handle 100+ video batches without crashes
- Template library of 50+ saved configs
- Support file lists of 500+ videos (performance degrades)

---

## 3. Feature Implementation Breakdown

### P1 Features (Must Have - Core Workflow)

#### Feature 1: Drag-and-Drop File Loading (P1)
**User Story**: Quickly add videos from file explorer without dialogs.

**Acceptance Criteria**:
- Drag 5 video files → all appear in file list with names and "pending" status
- Drag folder with 20 videos → recursively scanned, all videos added to queue
- Drag mixed files → only valid video files added, invalid silently ignored
- Visual feedback on hover (border highlight or overlay)

**Technical Implementation**:
- Module: `src/ui/drag_drop.py` (new)
- Classes:
  - `DragDropManager`: Wraps Tkinter drag-drop binding (register_drop_zone, setup_drop_target)
  - Methods for validating video extensions (mp4, mkv, avi, mov, m4v, webm)
- Integration points:
  - Register drag-drop zone in `BatchProcessorFrame._create_file_section()`
  - Add `_on_files_dropped(files: List[str])` callback to update file list
  - Validate duplicates before adding (warn if duplicate file path detected)

**Key Decision**: Use Tkinter's native drag-drop support via `tkinterdnd` OR fallback to Tkinter's DND_FILES on Windows. **Decision**: Use subprocess-based drag-drop detection via file dialog + improve UX with drag-drop visual hints where native support exists.

---

#### Feature 2: Parallel Batch Processing (P1)
**User Story**: Process 2-4 videos simultaneously to reduce batch time by 60-75%.

**Acceptance Criteria**:
- Start processing 10 videos → up to 3 process simultaneously based on CPU cores
- When video completes → next pending video starts immediately
- UI shows individual progress bars for each active file
- "Stop" button terminates all active processes within 5 seconds
- 4-core system → defaults to 2 parallel processes

**Technical Implementation**:
- Module: `src/parallel_processor.py` (new)
- Classes:
  - `ParallelVideoProcessor(VideoProcessor)`: Subclass with parallel queue management
  - `ProcessQueue`: Manages queue of pending/active files
  - Methods:
    - `process_batch_parallel(files, max_workers, on_progress_callback)`
    - `_worker_thread(queue, worker_id)`: Worker thread that pulls from queue, processes, updates state
    - `stop_all_workers()`: Graceful shutdown with timeout
- Integration:
  - In `BatchProcessorFrame.process_batch()`, detect batch operation and use `ParallelVideoProcessor` instead of `VideoProcessor.process_queue()`
  - Add parallelism slider to settings (1-8 workers, default (cores-1)/2 capped at 4)
  - Update file state objects with `worker_id` for tracking which file is processed by which worker
  - Add "active" status to FileStatus enum (separate from PROCESSING to track active workers)

**Architecture**:
```python
# Pseudo-code
class ParallelVideoProcessor:
    def __init__(self, state, max_workers=3):
        self.workers = []
        self.work_queue = queue.Queue()

    def process_batch_parallel(self, files):
        # Spawn worker threads
        for i in range(self.max_workers):
            w = threading.Thread(target=self._worker_thread)
            w.start()

        # Populate queue with files
        for f in files:
            self.work_queue.put(f)

        # Wait for completion or user stop
        while not self.work_queue.empty():
            # Update UI from file state objects
            time.sleep(0.1)
```

**Key Decision**: Threading vs Multiprocessing → **Threading** chosen to avoid:
- Pickling overhead (videos are large, state complex)
- IPC complexity with queue synchronization
- GIL is acceptable because FFmpeg runs as subprocess (releases GIL)
- Simpler state sharing via shared AppState object

---

#### Feature 3: Configuration Templates (P1)
**User Story**: Save settings as reusable presets (trim, profile, delogo, output) and load with one click.

**Acceptance Criteria**:
- Save current config as "YouTube Export" template
- Load template in new session → all settings restored
- Template list shows brief preview of key settings
- Loaded template name shows asterisk (*) if settings changed
- Update button overwrites existing template
- Right-click to delete templates

**Technical Implementation**:
- Module: `src/templates.py` (new)
- Classes:
  - `Template`: Dataclass with serialization
    - Fields: name, description, cut_mode, cut_minutes, cut_seconds, cut_start_min/sec, cut_end_min/sec,
              processing_profile_key, apply_delogo, delogo_params, output_format, output_suffix, output_prefix,
              created_timestamp, last_modified_timestamp
  - `TemplateManager`: Disk persistence
    - `save_template(template: Template) → bool`
    - `load_template(name: str) → Template`
    - `delete_template(name: str) → bool`
    - `list_templates() → List[Template]`
- Storage: `~/.magictvbox/templates/` directory (JSON files per template)
- Integration:
  - Add `TemplateManager` instance to `AppState`
  - In `BatchProcessorFrame._create_ui()`, add template dropdown + "Save as Template" button
  - Add callback to track template changes (compare current state to loaded template, set asterisk)
  - Load templates on app startup, cache in AppState

**Template Schema** (JSON):
```json
{
  "name": "YouTube Export",
  "description": "High quality for YouTube uploads",
  "cut_mode": "cut_last",
  "cut_minutes": 5.0,
  "cut_seconds": 0.0,
  "cut_start_minutes": 0.0,
  "cut_start_seconds": 0.0,
  "cut_end_minutes": null,
  "cut_end_seconds": null,
  "processing_profile_key": "universal",
  "apply_delogo": false,
  "delogo_params": {"x": 1635, "y": 240, "w": 176, "h": 147},
  "output_format": "mp4",
  "output_suffix": "_yt",
  "output_prefix": "",
  "created_timestamp": "2026-02-08T10:30:00Z",
  "last_modified_timestamp": "2026-02-08T10:30:00Z"
}
```

---

### P2 Features (High Priority - Performance)

#### Feature 4: Hardware-Accelerated Encoding (P2)
**User Story**: Use GPU encoders (NVENC, QuickSync, VideoToolbox, VCE) for 8-15x speedup on compatible systems.

**Acceptance Criteria**:
- NVIDIA GPU → "Universal - NVENC" profile appears in selector
- GPU profile selected → FFmpeg uses h264_nvenc/hevc_nvenc
- No compatible hardware → GPU profiles hidden/disabled with tooltip
- GPU encoding fails → fallback to CPU with warning logged
- 10 videos with GPU → encode 8-15x faster than CPU

**Technical Implementation**:
- Module: `src/hardware_encoders.py` (new)
- Classes:
  - `HardwareEncoderDetector`: Detects available encoders
    - `detect_encoders() → Dict[str, bool]`: {"nvidia": true, "intel": false, "amd": false, "apple": false}
    - Runs `ffmpeg -encoders` and parses output for nvenc, qsv, hevc_nvenc, h264_videotoolbox, etc.
  - Methods to create GPU profile variants from CPU profiles
- Integration:
  - At AppState initialization, call `HardwareEncoderDetector.detect_encoders()`
  - Store detection results in AppState
  - In profile selector UI, conditionally show GPU profiles based on detection
  - Add fallback logic in `VideoProcessor._process_with_subprocess()`:
    - If GPU encoding fails, catch error, detect "GPU OOM" or "encoder not found", retry with CPU profile
- New Profiles (added to PROCESSING_PROFILES if hardware detected):
  - "universal_nvenc": Same as universal but uses h264_nvenc
  - "high_quality_nvenc": High quality with h264_nvenc
  - "universal_qsv": Intel QuickSync variant
  - etc.

**Key Decision**: Profile creation strategy → **Template inline approach** (store full profile settings in template, not references) ensures templates work even if profiles change/deleted.

---

#### Feature 5: Video Metadata & Validation (P2)
**User Story**: Display video info (duration, resolution, codec) and catch incompatibilities before processing.

**Acceptance Criteria**:
- Add video → display "duration: 12:34, resolution: 1920x1080, codec: H.264, size: 2.5GB"
- 4K video + 1080p max profile → warning icon with tooltip
- Right-click video → "Preview" modal shows first 5 seconds
- Corrupted file → error status "Cannot read video metadata", excluded from processing
- "Validate All" button → probes all files, shows summary of warnings/errors

**Technical Implementation**:
- Module: `src/video_metadata.py` (new)
- Classes:
  - `VideoMetadata`: Dataclass
    - Fields: file_path, duration, width, height, codec, bitrate, file_size, is_valid, validation_warnings
  - `MetadataProber`: Caches and validates
    - `probe_file(path) → VideoMetadata`: Calls `VideoProcessor.probe_video()`, caches result
    - `validate_against_profile(metadata, profile) → List[str]`: Returns list of warning strings
- Integration:
  - In `BatchProcessorFrame._on_files_added()`, spawn thread to probe each file
  - Display metadata in file list columns (add columns: Duration, Resolution, Codec, Size)
  - Add validation warnings as icons/tooltips next to files
  - Add "Validate All" button in file section
  - Add preview modal with `cv2` or `PIL` to extract first frame, or ffmpeg thumbnail generation

**Key Decision**: Preview implementation → Use ffmpeg to generate single thumbnail (fast) rather than video playback (complex). **Decision**: Generate thumbnail using `ffmpeg -ss 00:00:01 -vframes 1 -f image2 pipe:1` output as PIL Image, display in modal.

---

### P3 Features (Nice to Have)

#### Feature 6: Additional Video Filters (P3)
**User Story**: Apply rotate, crop, scale, brightness/contrast, saturation, deinterlace beyond delogo.

**Technical Implementation**:
- Module: `src/video_filters.py` (new)
- Class: `FilterChain`
  - Attributes: rotate (90/180/270), crop (top/bottom/left/right), scale (width/height),
                brightness, contrast, saturation, deinterlace (bool), delogo (existing)
  - Methods: `build_ffmpeg_filter_graph() → str`: Generates FFmpeg -vf parameter
  - Filter order: rotate → crop → scale → color adjustments → delogo
- Integration:
  - Add "Video Filters" section to UI with checkboxes + sliders for adjustable params
  - Store FilterChain in AppState
  - Modify `VideoProcessor._process_with_subprocess()` to include filter graph in FFmpeg command

**Filter Graph Example**:
```bash
-vf "rotate=PI/2,crop=1920:800:0:140,scale=1280:720,eq=brightness=0.2:contrast=1.1,delogo=..."
```

---

#### Feature 7: Resume Failed Batch Processing (P3)
**User Story**: Recover from app crashes/interruptions by resuming from last successful file.

**Acceptance Criteria**:
- Start 50-file batch, 20 complete, app crashes → restart prompts "Resume? (20 of 50 completed)"
- Resume selected → skips completed files, starts with file 21
- Partially completed file (40% done) → restarts from 0% on resume
- Output files exist → validates by checking duration matches expected, skips if valid
- Manual resume → if user deleted output files, re-processes

**Technical Implementation**:
- Module: `src/batch_state.py` (new)
- Classes:
  - `BatchState`: Checkpoint of batch progress
    - Fields: batch_id (UUID), files (list of file paths), completed_files, settings_snapshot (JSON),
              started_timestamp, last_updated_timestamp
  - `BatchStateManager`: Persistence
    - `save_checkpoint(batch_state)`
    - `load_last_checkpoint() → Optional[BatchState]`
    - `clear_checkpoint(batch_id)`
- Integration:
  - Before batch processing, create BatchState checkpoint
  - After each file completes successfully, update checkpoint
  - On app startup, check for incomplete batches, prompt user
  - When resuming, verify output files (check duration via ffprobe matches expected), skip valid ones

---

#### Feature 8: Smart Error Messages (P3)
**User Story**: Parse FFmpeg errors and display user-friendly messages with suggested fixes.

**Acceptance Criteria**:
- GPU encoder missing → "GPU encoding unavailable. Update NVIDIA drivers or use CPU profile."
- Corrupted input → "Input file is corrupted. Try opening in VLC."
- No disk space → "Need 5GB free, only 1GB available. Free up space or change output location."
- Unknown error → Shows generic message + "Show Details" button for raw output
- Error dialog includes action buttons: "Choose Different Profile", "Retry", "Skip File"

**Technical Implementation**:
- Module: `src/error_handler.py` (new)
- Class: `ErrorMessageParser`
  - Methods: `parse_ffmpeg_error(exit_code, stderr_output) → (user_message, action_buttons)`
  - Regex patterns for common errors:
    - "Unknown encoder" → GPU unavailable error
    - "No space left on device" → disk full
    - "Invalid data found when processing input" → corrupted file
    - GPU OOM patterns
- Integration:
  - In `VideoProcessor._process_with_subprocess()`, when process fails, pass stderr to parser
  - In UI error dialog, display parsed message + action buttons
  - "Retry" button restarts current file
  - "Skip File" button marks completed with warning, moves to next

---

## 4. Research Topics & Key Questions

### Research Module 1: Drag-and-Drop Implementation
**File**: `RESEARCH.md` → Section "Drag-and-Drop"

**Questions to Answer**:
1. What's the best way to implement drag-and-drop in Tkinter/CustomTkinter?
   - Option A: Use tkinterdnd library (cross-platform, pip installable)
   - Option B: Native OS integration (Windows DragAcceptFiles API)
   - Option C: Hybrid (try tkinterdnd, fallback to file dialog)
   - **Decision**: Research which CustomTkinter supports best, implement Option C for robustness

2. How to detect when drag-over occurs and change visual feedback?
   - Tkinter drag-drop events: DragEnter, DragOver, DragLeave, Drop
   - CustomTkinter integration: Check if custom widgets support these events
   - **Deliverable**: Code example of bind('<<Drop>>', callback)

3. How to recursively scan dropped folders for all video files?
   - pathlib.glob('**/*.{mp4,mkv,avi,mov,m4v,webm}') with recursive=True
   - Filter by file extension, skip symlinks, handle permissions errors
   - **Deliverable**: Recursive folder scanner function

4. How to deduplicate dropped files (same file dropped twice)?
   - Convert to absolute path, store set of paths, check membership
   - Warn user with dialog: "File already in queue, add duplicate?"
   - **Deliverable**: Duplicate detection logic

---

### Research Module 2: Parallel Processing Architecture
**File**: `RESEARCH.md` → Section "Parallel Processing"

**Questions to Answer**:
1. Threading vs Multiprocessing trade-offs for FFmpeg?
   - **Threading Pros**: Shared state easy (AppState), no pickling, GIL not issue (subprocess releases it)
   - **Threading Cons**: Python GIL for parallel compute (not issue here, FFmpeg is external process)
   - **Multiprocessing Pros**: True parallelism for compute
   - **Multiprocessing Cons**: State synchronization complex, pickle overhead for large video metadata
   - **Decision**: Threading is correct choice for FFmpeg subprocess model
   - **Reference**: https://docs.python.org/3/library/threading.html

2. How to implement a work queue for processing files?
   - Use `queue.Queue()` for thread-safe work distribution
   - Worker threads pull from queue, process, update shared state
   - Main thread monitors queue status, updates UI
   - **Deliverable**: ParallelVideoProcessor class with worker pool pattern

3. How to track progress of multiple parallel processes?
   - Each file state object has progress field (0-100)
   - Worker thread updates file.progress in callback
   - Main thread polls file states, updates UI progress bars
   - **Problem**: Tkinter UI thread updates must be thread-safe
   - **Solution**: Use thread-safe callback system or after() method for UI updates
   - **Deliverable**: Thread-safe progress tracking example

4. How to gracefully stop all workers on user click?
   - Set shared flag `self.stop_requested = True`
   - Workers check flag between file processing
   - Terminate any active FFmpeg subprocess with process.terminate()
   - Join all threads with timeout, kill if necessary
   - **Deliverable**: Graceful shutdown with timeout logic

5. CPU core detection and optimal worker count calculation?
   - `os.cpu_count()` returns number of cores
   - Formula: `max(1, (cores - 1) // 2)` capped at 4
   - Example: 4-core → 1 worker, 8-core → 3 workers
   - **Deliverable**: get_recommended_worker_count() function

---

### Research Module 3: Hardware Encoder Detection
**File**: `RESEARCH.md` → Section "Hardware Encoders"

**Questions to Answer**:
1. How to detect NVIDIA NVENC, Intel QuickSync, AMD VCE, Apple VideoToolbox availability?
   - Run `ffmpeg -encoders` and parse output for encoder names
   - NVIDIA: h264_nvenc, hevc_nvenc
   - Intel: h264_qsv, hevc_qsv
   - AMD: h264_amf, hevc_amf (may be named differently)
   - Apple: h264_videotoolbox, hevc_videotoolbox
   - **Deliverable**: Encoder detection script that runs ffmpeg -encoders, returns dict of available encoders

2. How to verify encoder is usable (driver installed, not just FFmpeg support)?
   - Try encoding a short test video, catch errors
   - Parse FFmpeg error for driver issues: "NVENC device not found", "QuickSync not available"
   - **Deliverable**: Encoder capability test that attempts encode and catches known errors

3. What are the FFmpeg command-line differences for hardware encoders?
   - CPU: `-c:v libx264 -preset fast -crf 23`
   - NVIDIA: `-c:v h264_nvenc -preset fast -crf 23` (or -rc vbr for NVIDIA syntax differences)
   - Intel: `-c:v h264_qsv -preset fast -crf 23`
   - **Note**: Some encoders use different param syntax (rc=vbr vs crf)
   - **Deliverable**: Encoder-specific command builder that handles syntax differences

4. How to handle encoder fallback if GPU encoding fails mid-batch?
   - Catch specific FFmpeg error patterns: "NVENC device memory", "QSV initialization error"
   - Log warning, switch to CPU profile, retry current file
   - **Deliverable**: Error detection and fallback logic

5. What's the quality/speed tradeoff for hardware encoders vs CPU?
   - Hardware: 8-15x faster, slightly lower visual quality (acceptable for most use cases)
   - CPU: Slower but highest quality
   - User should be warned about quality differences in tooltip
   - **Deliverable**: Profile descriptions noting quality/speed differences

---

### Research Module 4: Template/Config Persistence
**File**: `RESEARCH.md` → Section "Template Persistence"

**Questions to Answer**:
1. What's the best directory structure for storing templates?
   - Windows: `C:\Users\<username>\AppData\Local\MagicTVBox\templates\`
   - macOS: `~/.magictvbox/templates/` or `~/Library/Application Support/MagicTVBox/templates/`
   - One JSON file per template: `templates/youtube_export.json`
   - **Deliverable**: Cross-platform config directory function

2. How to serialize AppState to JSON and deserialize back?
   - Custom JSON encoder/decoder for dataclasses (DelogoParams, etc.)
   - Handle Optional fields correctly
   - Version the schema for future compatibility
   - **Deliverable**: JSON serialization/deserialization code

3. How to detect unsaved changes to a loaded template?
   - Compare current AppState to loaded template state (deep equality check)
   - Set asterisk indicator in UI if different
   - **Deliverable**: State comparison function

4. How to handle deleted profiles referenced in templates?
   - Store full profile settings inline in template (not just profile_key reference)
   - This ensures template works even if original profile deleted
   - **Deliverable**: Template schema that includes full profile data

5. How to organize templates if user has 50+?
   - Add search/filter box to template selector
   - Support template categories/tags (future enhancement)
   - Sort by creation date, allow rename
   - **Deliverable**: Template management UI with search/sort

---

### Research Module 5: Video Metadata Extraction & Validation
**File**: `RESEARCH.md` → Section "Video Metadata"

**Questions to Answer**:
1. What metadata should be extracted and displayed?
   - Duration (formatted as HH:MM:SS)
   - Resolution (WIDTHxHEIGHT)
   - Codec name (H.264, H.265, VP9, etc.)
   - File size (in MB/GB)
   - Bitrate (kbps, optional)
   - Frame rate (fps, optional)
   - **Deliverable**: VideoMetadata dataclass with these fields

2. How to use ffprobe to extract metadata efficiently?
   - `ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,codec_name -of json video.mp4`
   - Parse JSON output
   - Cache results to avoid re-probing
   - **Deliverable**: Efficient ffprobe wrapper

3. How to validate video against processing profile?
   - Profile has max_width, max_height limits
   - Check video resolution ≤ profile limits
   - Check codec is supported (don't process if unsupported)
   - Check file not corrupted (ffprobe succeeds)
   - **Deliverable**: Validation function that returns list of warning strings

4. How to generate thumbnail for preview modal?
   - `ffmpeg -ss 00:00:01 -vframes 1 -f image2 pipe:1 input.mp4` → output binary to stdout
   - Convert binary to PIL Image, display in Tkinter Label
   - Cache thumbnail to avoid regeneration
   - **Deliverable**: Thumbnail generation and display code

5. How to display metadata in file list without cluttering UI?
   - Add columns to file list: Name, Duration, Resolution, Codec, Size, Status
   - Use compact format: "12:34 | 1920x1080 | H.264 | 256MB"
   - Hover tooltip shows full details
   - **Deliverable**: File list UI with metadata columns

---

### Research Module 6: FFmpeg Filter Chains & Ordering
**File**: `RESEARCH.md` → Section "FFmpeg Filters"

**Questions to Answer**:
1. What's the correct order for applying multiple filters?
   - Rotate → Crop → Scale → Color adjustments (brightness/contrast/saturation) → Delogo
   - Rotation changes dimensions, crop removes areas, scale resizes, color adjusts visuals, delogo last
   - **Deliverable**: Filter ordering logic documented

2. How to build FFmpeg filter graph string with variable filters?
   - Example: `rotate=PI/2,crop=1920:800:0:140,scale=1280:720,eq=brightness=0.2:contrast=1.1,delogo=...`
   - Build list of filters, join with commas
   - Handle optional/disabled filters by skipping them
   - **Deliverable**: FilterChain.build_ffmpeg_filter_graph() method

3. How to specify each filter's parameters in FFmpeg?
   - Rotate: `rotate=angle_in_radians` or `transpose=direction`
   - Crop: `crop=width:height:x:y`
   - Scale: `scale=width:height`
   - Brightness/Contrast: `eq=brightness=value:contrast=value`
   - Saturation: `hue=s=saturation_value`
   - Deinterlace: `yadif` or `bwdif`
   - **Deliverable**: Filter parameter documentation with examples

4. How to validate filter parameters before building command?
   - Brightness/Contrast: -1.0 to 1.0
   - Saturation: 0.0 to 2.0
   - Crop values: must be positive integers, within video dimensions
   - Scale: width/height positive, or -1 for preserve aspect
   - **Deliverable**: Validation function for each filter type

5. How to provide visual feedback when previewing filter effects?
   - Extract first frame (ffmpeg -vframes 1)
   - Apply filter to single frame (optional for performance)
   - Show before/after side-by-side in modal
   - **Deliverable**: Filter preview function

---

### Research Module 7: Batch State Persistence & Recovery
**File**: `RESEARCH.md` → Section "Batch State"

**Questions to Answer**:
1. What should batch state checkpoint include?
   - batch_id (UUID)
   - List of input files (file paths)
   - List of completed files (file paths)
   - Current processing state (settings, profiles used)
   - Timestamps (started, last updated)
   - **Deliverable**: BatchState dataclass

2. How often should checkpoint be saved?
   - After each successful file completion (safe recovery)
   - After every N files (balance safety vs I/O)
   - **Recommendation**: After each file (trivial JSON write)
   - **Deliverable**: Checkpoint saving strategy

3. Where to store batch state files?
   - `.magictvbox/batch_states/` directory with batch_id as filename
   - One JSON per batch: `batch_states/abc123def456.json`
   - Clean up old batches after completion (auto-delete after 7 days)
   - **Deliverable**: Batch state directory structure

4. How to verify output files exist and are valid before skipping?
   - Check file exists
   - ffprobe to get duration, compare to expected (from original video probe)
   - If duration matches ±5%, consider completed
   - If mismatch, re-encode to ensure quality
   - **Deliverable**: Output file validation function

5. How to handle batch settings changed between runs?
   - Store settings snapshot in checkpoint
   - Compare current settings to snapshot on resume
   - If different, prompt user: "Original batch used [old settings]. Current settings are [new]. Use which?"
   - **Deliverable**: Settings change detection and user prompt

---

### Research Module 8: FFmpeg Error Message Parsing
**File**: `RESEARCH.md` → Section "Error Parsing"

**Questions to Answer**:
1. What are common FFmpeg error patterns and how to parse them?
   - "Unknown encoder" → GPU not available
   - "No space left on device" → Disk full
   - "Invalid data found" → Corrupted input
   - "NVENC device not found" → GPU driver issue
   - "CRF must be between 0-51" → Invalid profile params
   - **Deliverable**: Error pattern regex library

2. How to extract error messages from FFmpeg stderr?
   - FFmpeg outputs errors to stderr (even though we redirect to stdout in Popen)
   - Parse last N lines of stderr for error messages
   - Filter out warnings and info lines
   - **Deliverable**: Error extraction function

3. How to map error patterns to user-friendly messages?
   - Dictionary: {error_pattern: user_message}
   - Use regex to match patterns
   - Provide suggested actions in user message
   - **Deliverable**: Error message mapping dictionary

4. How to include action buttons in error dialogs?
   - Dialog shows message + buttons: "Retry", "Skip", "Choose Profile", "Show Details"
   - Button callback performs action (retry processing, skip file, open profile selector, expand details)
   - **Deliverable**: Error dialog UI with action buttons

5. How to log detailed error info for debugging?
   - Store raw FFmpeg output in log
   - Store parsed user message in separate log field
   - Allow user to export logs for support
   - **Deliverable**: Structured error logging

---

## 5. Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
**Deliverable**: Foundation for all P1 features

1. Create `ParallelVideoProcessor` class with thread-based worker pool
   - File: `src/parallel_processor.py`
   - Tests: Verify 3 files process in parallel with correct state updates

2. Create `TemplateManager` and `Template` classes
   - File: `src/templates.py`
   - Tests: Save/load/delete templates, JSON schema validation

3. Create `HardwareEncoderDetector` to detect available encoders
   - File: `src/hardware_encoders.py`
   - Tests: Verify detection of NVIDIA/Intel/AMD encoders on various systems

4. Extend `AppState` with template and parallelism configuration
   - File: `src/state.py` (modify)
   - Add fields: templates_dir, template_manager, max_workers, current_template, hardware_encoders

5. Research & document findings in `RESEARCH.md`
   - Complete all 8 research topic sections
   - Document architectural decisions

### Phase 2: Drag-and-Drop & UI Improvements (Week 2-3)
**Deliverable**: Drag-drop file loading, template selector UI, parallelism settings

1. Implement drag-and-drop file input
   - File: `src/ui/drag_drop.py` (new)
   - Integration: Modify `BatchProcessorFrame` to register drop zone
   - Tests: Drag 5 files, 1 folder, mixed files - verify correct files added

2. Add template selector dropdown to UI
   - File: `src/ui/batch_processor.py` (modify)
   - Add dropdown with template list
   - Add "Save as Template" button
   - Add asterisk indicator for unsaved changes
   - Tests: Save template, load it, verify settings restored

3. Add parallelism slider to settings
   - File: `src/ui/settings_panel.py` (modify)
   - Slider: 1-8 workers, default recommended value
   - Label shows: "X workers (recommended: Y)"
   - Tests: Change slider, verify setting persists

4. Update main processor to use `ParallelVideoProcessor` for batches
   - File: `src/ui/batch_processor.py` (modify)
   - When batch processing starts, use parallel processor instead of serial
   - Tests: Process 8 files, verify 2-3 process simultaneously

### Phase 3: Metadata & Validation (Week 3-4)
**Deliverable**: Video metadata display, pre-processing validation, preview modal

1. Create `VideoMetadata` and `MetadataProber` classes
   - File: `src/video_metadata.py` (new)
   - Tests: Probe 10 files, verify metadata correct, caching works

2. Add metadata columns to file list UI
   - File: `src/ui/batch_processor.py` (modify)
   - Display: Duration, Resolution, Codec, Size
   - Tests: Add 5 files, verify all metadata displayed correctly

3. Add validation against profile and display warnings
   - File: `src/video_metadata.py` (modify)
   - Tests: Add 4K video to 1080p max profile, verify warning displayed

4. Create preview modal
   - File: `src/ui/preview_modal.py` (new)
   - Right-click file → "Preview" → shows thumbnail + metadata
   - Tests: Preview 5 files, verify thumbnail generates and displays

5. Add "Validate All" button
   - File: `src/ui/batch_processor.py` (modify)
   - Tests: Validate 20 files, displays summary of issues

### Phase 4: Hardware Encoders & Profiles (Week 4)
**Deliverable**: Hardware encoder detection, GPU profile variants, fallback logic

1. Implement encoder detection at startup
   - File: `src/hardware_encoders.py` (complete)
   - Run on app startup, store in AppState
   - Tests: Verify detection results on various systems

2. Create GPU profile variants in PROCESSING_PROFILES
   - File: `src/state.py` (modify)
   - Add profiles: universal_nvenc, high_quality_nvenc, etc. (only if detected)
   - Tests: Verify GPU profiles only shown if encoder detected

3. Add GPU profile visibility logic to UI
   - File: `src/ui/settings_panel.py` (modify)
   - Show only available profiles
   - Tests: System with GPU shows GPU profiles, system without hides them

4. Implement fallback logic in VideoProcessor
   - File: `src/video_processor.py` (modify)
   - If GPU encoding fails, catch error, retry with CPU profile
   - Tests: Simulate GPU failure, verify fallback to CPU works

### Phase 5: Advanced Filters (Week 5)
**Deliverable**: Additional video filters, filter chain building, filter preview

1. Create `FilterChain` class
   - File: `src/video_filters.py` (new)
   - Methods: enable_filter, disable_filter, build_ffmpeg_filter_graph()
   - Tests: Build filter graphs with various filter combinations

2. Add "Video Filters" section to UI
   - File: `src/ui/batch_processor.py` (modify)
   - Checkboxes for each filter type
   - Sliders for brightness/contrast/saturation
   - Text inputs for crop/scale values
   - Tests: Enable various filters, process video, verify output correct

3. Integrate filter chain into VideoProcessor
   - File: `src/video_processor.py` (modify)
   - Pass FilterChain to _process_with_subprocess, include in -vf parameter
   - Tests: Process with filters, verify FFmpeg output shows filter graph

4. Add filter preview UI
   - File: `src/ui/preview_modal.py` (modify)
   - Show before/after frames for enabled filters
   - Tests: Enable brightness filter, preview shows difference

### Phase 6: Error Handling & Recovery (Week 5-6)
**Deliverable**: Smart error messages, batch state recovery, graceful error handling

1. Create `ErrorMessageParser` class
   - File: `src/error_handler.py` (new)
   - Regex patterns for common FFmpeg errors
   - Mapping to user-friendly messages + suggested actions
   - Tests: Parse 10 different FFmpeg error patterns, verify correct messages

2. Create `BatchStateManager` for checkpoint persistence
   - File: `src/batch_state.py` (new)
   - Save checkpoint after each file, detect incomplete batches on startup
   - Tests: Interrupt batch, restart app, verify resume prompt appears

3. Integrate error handler into VideoProcessor
   - File: `src/video_processor.py` (modify)
   - When process fails, parse error and display friendly message
   - Tests: Trigger various errors, verify user-friendly messages shown

4. Add resume batch logic to UI
   - File: `src/ui/batch_processor.py` (modify)
   - On app startup, check for incomplete batches
   - If found, show resume prompt
   - Tests: Interrupt batch, restart, verify resume works correctly

5. Add error dialog with action buttons
   - File: `src/ui/error_dialog.py` (new)
   - Buttons: "Retry", "Skip", "Choose Profile", "Show Details"
   - Tests: Trigger error, verify buttons work

### Phase 7: Testing & Polish (Week 6-7)
**Deliverable**: Comprehensive testing, performance optimization, documentation

1. Create pytest test suite
   - File: `tests/` directory
   - Unit tests: Parallel processor, templates, metadata, filters, error parsing
   - Integration tests: Full batch processing workflows
   - Edge case tests: Duplicate files, corrupted files, invalid settings
   - Target: 80%+ code coverage

2. Performance testing
   - Benchmark parallel processing (compare to serial)
   - Benchmark GPU encoding (compare to CPU)
   - Benchmark metadata probing (single vs batch)
   - Verify UI responsiveness during processing

3. Documentation
   - User guide for new features
   - Developer guide for extending filters/profiles
   - Template schema documentation
   - Error message guide

4. Bug fixes and UX polish
   - Handle edge cases from spec
   - Improve error messages based on feedback
   - Optimize UI performance if needed
   - Clean up logging

---

## 6. Risk Analysis & Mitigation

### Risk 1: Thread Safety Issues in Parallel Processing
**Severity**: High
**Impact**: Race conditions, corrupted state, crashes

**Mitigation**:
- Use thread-safe queue.Queue() for work distribution
- Avoid shared mutable state (use copy-on-write patterns)
- Test with thread sanitizer (Python threading module + unittest)
- Lock access to AppState if modifying from multiple threads

### Risk 2: FFmpeg Command Complexity
**Severity**: Medium
**Impact**: Filter graphs fail, incorrect output

**Mitigation**:
- Test all filter combinations independently
- Document filter ordering and parameters
- Validate filter parameters before building command
- Provide clear error messages when filter chain invalid

### Risk 3: GPU Driver Incompatibility
**Severity**: Medium
**Impact**: GPU encoding unavailable, user frustration

**Mitigation**:
- Graceful fallback to CPU encoding
- Clear messaging about GPU requirements
- Test on multiple systems with different GPU/drivers
- Provide driver installation links in error messages

### Risk 4: Performance Regression with Parallel Processing
**Severity**: Low
**Impact**: Batch processing slower with parallelism enabled

**Mitigation**:
- Benchmark on various hardware configurations
- Allow user to disable parallelism if not beneficial
- Monitor resource usage (CPU, RAM)
- Cap maximum workers at 4 to prevent overload

### Risk 5: Template/Batch State Corruption
**Severity**: Medium
**Impact**: Lost user settings, incomplete recovery

**Mitigation**:
- Version template schema for compatibility
- Validate JSON on load, handle parse errors
- Atomic file writes (write to temp, then rename)
- Backup old templates/batch states

### Risk 6: Metadata Extraction Slow with Large Batch
**Severity**: Low
**Impact**: UI freeze when adding 100+ files

**Mitigation**:
- Spawn metadata probing in background thread
- Cache results aggressively
- Show progress indicator while probing
- Allow user to cancel probing

---

## 7. Definition of Done

For each feature to be considered complete:

1. **Code**:
   - Implemented per specification requirements
   - Code reviewed and linted
   - No type errors (use type hints throughout)
   - No unused imports or variables

2. **Testing**:
   - Unit tests written for all classes/functions (target 80%+ coverage)
   - Integration tests for feature workflows
   - Manual testing on Windows and macOS (or virtual machines)
   - Edge cases tested (duplicates, corrupted files, etc.)

3. **Documentation**:
   - Docstrings on all public methods
   - Inline comments for complex logic
   - Feature documented in user guide
   - Architectural decisions documented in RESEARCH.md

4. **Performance**:
   - No performance regressions from baseline
   - Meets performance goals (UI <200ms, metadata <1s/file, parallel 8-15x faster)
   - Memory usage stable over long runs

5. **UI/UX**:
   - UI changes reviewed and approved
   - Consistent with existing design
   - Accessibility: keyboard navigation works
   - Error messages clear and actionable

---

## 8. Success Metrics

After implementation, measure:

- **SC-001**: Users add 20 videos via drag-drop in <5 seconds (vs 30+ seconds with dialogs)
- **SC-002**: Load template in <10 seconds (vs 2-3 minutes manual config)
- **SC-005**: 20-video batch completes in 25-30% of serial time (with 2-4 workers on 4-core system)
- **SC-006**: Hardware-accelerated encoding 8-15x faster than CPU
- **SC-007**: UI responsive during processing (<200ms interaction latency)
- **SC-008**: Metadata probing <1 second per file
- **SC-009**: 95% of FFmpeg errors show user-friendly messages
- **SC-010**: Resume interrupted batch in <15 seconds
- **SC-013**: 60% of users create at least one template in first week
- **SC-014**: 40% of GPU users use hardware acceleration for 50%+ of jobs

---

## 9. Files to Create/Modify

### New Files
```
src/parallel_processor.py          # Parallel processing with thread pool
src/templates.py                   # Template save/load management
src/hardware_encoders.py           # GPU encoder detection
src/video_metadata.py              # Video metadata extraction & validation
src/video_filters.py               # Filter chain building
src/batch_state.py                 # Batch state checkpoint persistence
src/error_handler.py               # FFmpeg error parsing & user messages
src/ui/drag_drop.py                # Drag-and-drop handler
src/ui/preview_modal.py            # Video preview and thumbnail display
src/ui/error_dialog.py             # Error dialog with action buttons
RESEARCH.md                        # Research findings and technical decisions
tests/test_parallel_processor.py   # Parallel processing tests
tests/test_templates.py            # Template management tests
tests/test_hardware_encoders.py    # Encoder detection tests
tests/test_video_metadata.py       # Metadata extraction tests
tests/test_video_filters.py        # Filter chain tests
tests/test_batch_state.py          # Batch state recovery tests
tests/test_error_handler.py        # Error parsing tests
```

### Modified Files
```
src/state.py                       # Add template, parallelism, hardware config
src/video_processor.py             # Add filter chain, error handling, hardware fallback
src/ui/batch_processor.py          # Add drag-drop, templates, metadata UI, filters
src/ui/settings_panel.py           # Add parallelism slider
src/ui/single_processor.py         # Add template selector
main.py                            # Initialize TemplateManager, HardwareEncoderDetector
```

---

## Appendix A: Technology Decision Rationale

### Threading vs Multiprocessing
**Decision**: Threading

**Rationale**:
- FFmpeg runs as external subprocess (releases GIL)
- Shared AppState object easier with threading
- Avoid pickling overhead (large video metadata objects)
- Simpler synchronization with queue.Queue()
- Suitable for I/O-bound workload (waiting on subprocess)

### JSON for Template Storage
**Decision**: JSON files in `~/.magictvbox/templates/`

**Rationale**:
- Human-readable format for editing
- No database dependency
- Easy to backup/restore
- Cross-platform compatible paths
- Simple serialization with built-in json module

### FFmpeg Subprocess vs ffmpeg-python
**Decision**: Subprocess primary, ffmpeg-python fallback

**Rationale**:
- Subprocess gives direct control over command line
- Better error handling and output parsing
- ffmpeg-python wrapper adds abstraction without benefit
- Keep dependencies minimal
- Fallback to ffmpeg-python if available for better API

### Template Settings Inline vs Profiles by Reference
**Decision**: Inline (store full settings in template)

**Rationale**:
- Templates don't break if original profile deleted
- Users can modify template independently from profiles
- Simpler template format without external dependencies
- Ensures backwards compatibility

### Drag-Drop Library Choice
**Decision**: Research both tkinterdnd and native OS APIs, pick best for CustomTkinter

**Rationale**:
- tkinterdnd is mature and cross-platform
- Native OS APIs are complex but more reliable
- Fallback to file dialog ensures feature always works
- Test on both Windows and macOS to validate choice

---

## Appendix B: Acceptance Test Scenarios

### Scenario: Complete Drag-Drop Workflow
1. Open app, go to Batch Processor
2. Drag folder with 20 MP4 files from Windows Explorer
3. Verify all 20 files appear in file list within 2 seconds
4. Verify metadata (duration, resolution) displayed for all files
5. Verify "pending" status for all files
6. Select profile, click "Start Processing"
7. Verify 3 files start encoding simultaneously
8. Verify each has individual progress bar
9. Verify UI remains responsive (no freezing)
10. After first file completes, verify next pending file starts automatically
11. Total time ~25% of serial processing time
12. All files complete successfully

### Scenario: Template Save & Load
1. Open app, go to Batch Processor
2. Configure: Cut Last 5 min, Profile "High Quality", Delogo enabled, Output ".mp4"
3. Click "Save as Template", name it "YouTube"
4. Close app and reopen
5. Click template dropdown, select "YouTube"
6. Verify all settings restored to original values
7. Modify one setting (change profile to "Small File")
8. Verify asterisk (*) appears next to template name
9. Click "Update Template" to save changes
10. Close and reopen app
11. Load "YouTube" template again
12. Verify new settings (Small File) are loaded

### Scenario: Resume Interrupted Batch
1. Open app, add 20 files to batch
2. Start processing, let it run until 8 files complete
3. Force close app (simulate crash)
4. Reopen app, go to Batch Processor
5. Verify dialog appears: "Resume previous batch? (8 of 20 completed)"
6. Click "Resume"
7. Verify processing starts from file 9
8. Verify files 1-8 skipped (not re-encoded)
9. Verify all remaining files process successfully
10. Total processing time = time to encode 12 files (not 20)

---

## Appendix C: Glossary

- **Parallel Processing**: Multiple video encodes running simultaneously on separate worker threads
- **Hardware Encoder**: GPU-based video encoder (NVENC, QuickSync, VCE, VideoToolbox)
- **Filter Chain**: Sequence of video filters applied in order (rotate, crop, scale, color, delogo)
- **Template**: Saved configuration preset (trim settings, profile, output options)
- **Metadata**: Video file information (duration, resolution, codec, file size)
- **Checkpoint**: Snapshot of batch processing progress saved to disk for recovery
- **Worker Thread**: Background thread that processes files from work queue
- **Drag-and-Drop**: User interface feature allowing files/folders to be added by dragging from file explorer

---

**Document Version**: 1.0
**Last Updated**: 2026-02-08
**Status**: Ready for Implementation
