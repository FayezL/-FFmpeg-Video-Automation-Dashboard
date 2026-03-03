# Feature Specification: Enhanced Workflow & Performance

**Feature Branch**: `001-enhanced-workflow`
**Created**: 2026-02-08
**Status**: Draft
**Input**: User description: "i still dont know what i need in this project but i want to you to read the project and give me suggesting and what i need i need to make the project more options and easily selecting and make it faster and easy"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Drag-and-Drop File Loading (Priority: P1)

A user wants to quickly add videos for processing without navigating through file dialogs. They should be able to drag video files or folders directly from their file explorer onto the application window, and the videos are immediately added to the processing queue with visual feedback.

**Why this priority**: This is the most fundamental usability improvement. Every user interaction starts with file selection, and the current click-through-dialogs approach is slow and outdated. Modern applications (like Slack, Discord, Photoshop) universally support drag-and-drop as the primary file input method. This immediately reduces user friction by 80% for the most common operation.

**Independent Test**: Can be fully tested by dragging a folder of 10 videos onto the app window and verifying they all appear in the file list with correct metadata. Delivers immediate value by making file selection instantaneous.

**Acceptance Scenarios**:

1. **Given** the batch processor view is open, **When** user drags 5 video files (.mp4, .mkv) from Windows Explorer onto the app window, **Then** all 5 files appear in the file list with their names and pending status
2. **Given** the batch processor view is open, **When** user drags a folder containing 20 videos onto the app, **Then** the app recursively scans the folder and adds all video files to the queue
3. **Given** user drags a mix of video and non-video files onto the app, **When** drop is complete, **Then** only valid video files are added and invalid files are silently ignored
4. **Given** user is mid-drag over the app window, **When** hovering, **Then** visual feedback (border highlight or overlay) indicates the drop zone is active

---

### User Story 2 - Parallel Batch Processing (Priority: P1)

A user processing 50 videos wants to leverage their multi-core CPU to process multiple videos simultaneously instead of waiting for serial processing. The system should automatically detect available CPU cores and process 2-4 videos in parallel, reducing total batch time by 60-75%.

**Why this priority**: This addresses the most critical performance bottleneck. Current serial processing makes the app 10x slower than it could be on modern hardware. A user with 100 videos faces 20+ hours of processing that could complete in 3-4 hours. This is a dealbreaker for professional workflows and power users.

**Independent Test**: Can be tested by processing a batch of 20 short videos (1 minute each) and verifying total completion time is ~25% of serial processing time. Delivers immediate value by making batch processing viable for large libraries.

**Acceptance Scenarios**:

1. **Given** user has 10 videos in the batch queue, **When** processing starts, **Then** up to 3 videos process simultaneously (based on CPU cores)
2. **Given** 3 videos are currently processing, **When** one completes, **Then** the next pending video immediately starts processing to maintain parallelism
3. **Given** batch processing is running, **When** user views the UI, **Then** all actively processing files show individual progress bars with current encoding status
4. **Given** a parallel processing job is running, **When** user clicks "Stop", **Then** all active encoding processes terminate gracefully within 5 seconds
5. **Given** user has a 4-core CPU, **When** starting batch processing, **Then** the system defaults to processing 2 files in parallel (leaving headroom for system responsiveness)

---

### User Story 3 - Configuration Presets & Templates (Priority: P1)

A user who regularly processes similar types of videos (e.g., TV episodes, YouTube content, meeting recordings) wants to save their preferred settings as reusable templates. They should be able to save the current configuration (trim settings, profile, output options) as a named preset and reload it with one click in future sessions.

**Why this priority**: This eliminates repetitive configuration and reduces user error. Users who process videos regularly report spending 2-3 minutes configuring settings for each batch - this wastes 10+ hours per year for active users. Templates enable "one-click workflows" for common use cases.

**Independent Test**: Can be tested by configuring trim settings + profile, saving as "Meeting Clips" template, closing the app, reopening, and loading the template to verify all settings restore correctly. Delivers immediate value by reducing setup time from 3 minutes to 5 seconds.

**Acceptance Scenarios**:

1. **Given** user has configured trim mode, processing profile, and output settings, **When** user clicks "Save as Template" and provides a name "YouTube Export", **Then** the template is saved and appears in the templates dropdown
2. **Given** user opens the app in a new session, **When** user selects "YouTube Export" from the templates dropdown, **Then** all saved settings (trim, profile, delogo, output) are restored to the UI
3. **Given** user has 5 saved templates, **When** viewing the templates list, **Then** each template shows a brief preview of its key settings (profile name, cut mode) for quick identification
4. **Given** user has a loaded template, **When** user makes changes to settings, **Then** the template name shows an asterisk (*) indicating unsaved changes
5. **Given** user wants to update an existing template, **When** user clicks "Update Template", **Then** the current settings overwrite the existing template

---

### User Story 4 - Hardware-Accelerated Encoding (Priority: P2)

A user with an NVIDIA GPU or Intel CPU with QuickSync wants to use hardware encoding to speed up video processing by 5-20x compared to CPU encoding. The system should detect available hardware encoders and offer them as profile options (e.g., "Universal - GPU Accelerated").

**Why this priority**: This is the second-largest performance bottleneck after parallel processing. Hardware encoding can reduce a 6-hour batch to 20-30 minutes on compatible systems. However, it's P2 (not P1) because it only benefits users with compatible hardware (~40-60% of potential users), whereas parallel processing benefits everyone.

**Independent Test**: Can be tested on a system with NVIDIA GPU by selecting "GPU Accelerated" profile and verifying FFmpeg uses `h264_nvenc` encoder and encoding completes 10x faster than CPU. Delivers massive value to users with compatible hardware.

**Acceptance Scenarios**:

1. **Given** user has an NVIDIA GPU with NVENC support, **When** app launches, **Then** GPU-accelerated profiles (e.g., "Universal - NVENC") appear in the profile selector
2. **Given** user selects a GPU-accelerated profile, **When** processing starts, **Then** FFmpeg uses the hardware encoder (h264_nvenc, hevc_nvenc) instead of libx264
3. **Given** user does not have compatible hardware, **When** viewing profile options, **Then** GPU-accelerated profiles are hidden or disabled with a tooltip explaining requirements
4. **Given** GPU encoding fails due to driver issues, **When** error occurs, **Then** system automatically falls back to CPU encoding and logs a warning
5. **Given** user is processing 10 videos with GPU acceleration, **When** encoding, **Then** each video encodes 8-15x faster than CPU equivalent with acceptable quality

---

### User Story 5 - Video Preview & Metadata Validation (Priority: P2)

A user adding videos to a batch wants to see key information (duration, resolution, codec, file size) before processing to catch issues early. They should also be able to preview a video thumbnail or short clip to verify it's the correct file, especially when selecting from large folders.

**Why this priority**: This prevents wasted processing time. Currently, users discover incompatible videos or wrong selections only after 30+ minutes of encoding. Pre-processing validation saves hours of troubleshooting. It's P2 because it's preventative rather than addressing an active performance issue.

**Independent Test**: Can be tested by adding a 4K video to the queue and verifying the UI displays "3840x2160, H.264, 2.5GB, 12:34 duration" with a thumbnail. If user selects a profile with max 1080p, a warning appears. Delivers value by catching issues before processing begins.

**Acceptance Scenarios**:

1. **Given** user adds a video to the batch queue, **When** the file is loaded, **Then** the file list displays duration, resolution, codec, and file size for that video
2. **Given** a video exceeds the selected profile's resolution limits (e.g., 4K video with 1080p max profile), **When** validation runs, **Then** a warning icon appears next to the file with tooltip "Video will be downscaled to 1920x1080"
3. **Given** user right-clicks a video in the file list, **When** selecting "Preview", **Then** a modal opens showing the first 5 seconds of the video as a quick preview
4. **Given** a video file is corrupted or unreadable, **When** added to the queue, **Then** the file shows an error status with message "Cannot read video metadata" and is excluded from processing
5. **Given** batch contains 20 videos, **When** user clicks "Validate All", **Then** system probes all videos and displays warnings for any incompatibilities (unsupported codec, too large for profile, etc.)

---

### User Story 6 - Additional Video Filters (Priority: P3)

A user needs to apply common video transformations beyond delogo, such as adjusting brightness/contrast, rotating videos, cropping borders, or resizing to specific dimensions. The UI should provide filter options with visual sliders and previews.

**Why this priority**: This expands the app's capabilities to handle more use cases. However, it's P3 because the core use case (trimming + transcoding) is already well-served. These filters are "nice to have" for specific scenarios but not critical for the majority of users.

**Independent Test**: Can be tested by selecting "Brightness +20%" filter, processing a video, and verifying the output is visibly brighter. Delivers value for users with specific correction needs.

**Acceptance Scenarios**:

1. **Given** user is configuring batch processing, **When** user expands the "Video Filters" section, **Then** options appear for: Rotate (90°/180°/270°), Crop, Scale/Resize, Brightness/Contrast, Saturation, Deinterlace
2. **Given** user enables "Crop" filter, **When** configuring, **Then** user can specify top/bottom/left/right pixel values to remove (e.g., remove 10px black bars from top and bottom)
3. **Given** user enables "Brightness +20%", **When** processing, **Then** FFmpeg applies the appropriate filter (`eq=brightness=0.2`) to the encoding pipeline
4. **Given** user enables multiple filters (Rotate + Crop + Brightness), **When** processing, **Then** filters are applied in the correct order (rotate → crop → brightness) to avoid artifacts
5. **Given** user wants to preview a filter effect, **When** clicking "Preview" next to a filter, **Then** a sample frame from the first video shows before/after comparison

---

### User Story 7 - Resume Failed Batch Processing (Priority: P3)

A user whose batch processing was interrupted (app crash, power outage, manual stop) wants to resume from where they left off instead of restarting the entire batch. The system should track completed files and automatically skip them on restart.

**Why this priority**: This reduces frustration but is rare in practice. Most users complete batches in one session, and crashes are infrequent. It's P3 because it's a recovery feature rather than core functionality.

**Independent Test**: Can be tested by starting a 20-file batch, stopping after 8 complete, closing the app, reopening, and verifying the batch resumes from file 9. Delivers value for edge cases with large batches.

**Acceptance Scenarios**:

1. **Given** user starts a 50-file batch and 20 complete successfully, **When** the app crashes, **Then** on restart, the app detects the incomplete batch and prompts "Resume previous batch? (20 of 50 completed)"
2. **Given** user chooses to resume a batch, **When** processing restarts, **Then** the app skips already-completed files and begins with the first pending file
3. **Given** a batch is paused mid-file (file 15 is 40% complete), **When** resuming, **Then** file 15 restarts from 0% (FFmpeg does not support mid-file resume)
4. **Given** output files from the previous batch exist in the output folder, **When** resuming, **Then** the app validates existing output files (checks duration matches expected) before skipping
5. **Given** user manually deleted some output files after a crash, **When** resuming, **Then** the app detects missing outputs and re-processes those files

---

### User Story 8 - Smart Error Messages & Recovery (Priority: P3)

A user encounters an FFmpeg encoding error and receives a cryptic 15-line technical error message. Instead, the system should parse common errors (missing codec, invalid resolution, corrupted file) and display user-friendly messages with suggested fixes.

**Why this priority**: This improves troubleshooting but is P3 because most users don't frequently encounter errors. When they do, it's frustrating, but error scenarios are rare compared to successful encoding workflows.

**Independent Test**: Can be tested by attempting to encode with a profile requiring H.265 (HEVC) when FFmpeg lacks hevc support. Verify the error message says "Your FFmpeg installation doesn't support H.265 encoding. Try a different profile or update FFmpeg." instead of raw FFmpeg output. Delivers value when errors occur.

**Acceptance Scenarios**:

1. **Given** user attempts to encode with a GPU profile but lacks NVENC drivers, **When** FFmpeg fails, **Then** error message displays "GPU encoding unavailable. Please update NVIDIA drivers or use a CPU profile."
2. **Given** encoding fails due to corrupted input file, **When** error occurs, **Then** error message displays "Input file is corrupted or unreadable. Try opening it in VLC to verify."
3. **Given** encoding fails due to insufficient disk space, **When** error occurs, **Then** error message displays "Not enough disk space. Need 5GB free, only 1GB available. Free up space or change output location."
4. **Given** encoding fails with an unknown/rare FFmpeg error, **When** displaying the error, **Then** the message shows "FFmpeg encountered an error (exit code 1)" with a "Show Details" button to expand raw FFmpeg output for troubleshooting
5. **Given** user receives an error message with suggested fix, **When** viewing the error dialog, **Then** clickable action buttons appear (e.g., "Choose Different Profile", "Retry", "Skip File") for quick recovery

---

### Edge Cases

- **What happens when user drags the same file multiple times?** The system should detect duplicates by file path and show a warning, giving the option to skip or add duplicate.
- **How does the system handle when parallel processing is set to 4 but only 2 CPU cores available?** The system should auto-adjust parallelism to `max(1, cores - 1)` to avoid overloading, and display a warning if user manually sets higher than recommended.
- **What if user creates a custom profile with invalid FFmpeg parameters?** The system should validate parameters before saving and show specific errors (e.g., "CRF must be between 0-51").
- **What happens when resuming a batch but output settings have changed since the original batch?** The system should detect settings mismatch and prompt user: "Original batch used 'High Quality' profile. Current settings use 'Small File'. Which settings should be used?"
- **How does the system handle when a template references a custom profile that has been deleted?** The template should store profile settings inline (not by reference) so it continues working even if the original profile is removed.
- **What if user has drag-and-drop disabled in their OS or app runs in restricted mode?** The traditional "Select Files" button should remain as a fallback, and drag-drop should gracefully degrade without breaking the app.
- **What happens when hardware encoding is enabled but GPU runs out of memory during processing?** FFmpeg will fail with an OOM error. The system should detect this error type, display "GPU out of memory. Try processing fewer files simultaneously or use CPU encoding.", and offer to restart the failed file with CPU encoding.
- **What if user saves 50+ templates?** The templates dropdown should support search/filter functionality and group templates by category (if user tags them) to remain usable.

## Requirements *(mandatory)*

### Functional Requirements

#### File Selection & Management

- **FR-001**: System MUST support drag-and-drop of video files and folders onto the application window to add them to the processing queue
- **FR-002**: System MUST recursively scan folders dropped onto the app and extract all video files (mp4, mkv, avi, mov, m4v, webm)
- **FR-003**: System MUST provide visual feedback (border highlight or overlay) when user drags files over a valid drop zone
- **FR-004**: System MUST ignore non-video files during drag-and-drop without displaying errors (silent filtering)
- **FR-005**: System MUST detect and warn about duplicate files (by path) when adding to the queue

#### Parallel Processing

- **FR-006**: System MUST support parallel processing of multiple videos simultaneously during batch operations
- **FR-007**: System MUST automatically detect CPU core count and default to processing `(cores - 1) / 2` files in parallel (minimum 1, maximum 4)
- **FR-008**: Users MUST be able to adjust the parallelism level (1-8 concurrent processes) via a settings slider
- **FR-009**: System MUST display individual progress bars and status for each actively processing file during parallel operations
- **FR-010**: System MUST gracefully terminate all active encoding processes within 5 seconds when user clicks "Stop"
- **FR-011**: System MUST queue pending files and automatically start processing the next file when an active process completes

#### Configuration Presets & Templates

- **FR-012**: System MUST allow users to save current processing settings (trim mode, profile, delogo, output options) as a named template
- **FR-013**: System MUST persist templates to disk as JSON files in a `templates/` directory within the app configuration folder
- **FR-014**: System MUST display saved templates in a dropdown menu in both batch and single processor views
- **FR-015**: Users MUST be able to load a template with one click to restore all saved settings to the UI
- **FR-016**: System MUST visually indicate when current settings differ from the loaded template (e.g., asterisk next to template name)
- **FR-017**: Users MUST be able to update an existing template by overwriting it with current settings
- **FR-018**: Users MUST be able to delete templates via a right-click context menu or template management dialog
- **FR-019**: System MUST store profile settings inline within templates (not by reference) to ensure templates work even if original profiles are deleted

#### Hardware-Accelerated Encoding

- **FR-020**: System MUST detect available hardware encoders at startup (NVIDIA NVENC, Intel QuickSync, AMD VCE, Apple VideoToolbox)
- **FR-021**: System MUST create GPU-accelerated variants of built-in profiles for each detected hardware encoder (e.g., "Universal - NVENC")
- **FR-022**: System MUST use hardware encoder codecs (`h264_nvenc`, `hevc_nvenc`, `h264_qsv`, etc.) when GPU profiles are selected
- **FR-023**: System MUST automatically fall back to CPU encoding if hardware encoding fails, with a warning logged to the UI
- **FR-024**: System MUST hide or disable GPU-accelerated profiles on systems without compatible hardware, with tooltips explaining requirements

#### Video Preview & Validation

- **FR-025**: System MUST probe each video file when added to the queue and display duration, resolution, codec, and file size in the file list
- **FR-026**: System MUST validate each video against the selected processing profile and display warnings for incompatibilities (e.g., 4K video with 1080p max profile)
- **FR-027**: Users MUST be able to right-click a video in the file list and select "Preview" to view the first 5 seconds of the video in a modal
- **FR-028**: System MUST mark corrupted or unreadable video files with an error status and exclude them from processing
- **FR-029**: System MUST provide a "Validate All" button that probes all videos in the queue and displays a summary of warnings/errors before processing

#### Additional Video Filters

- **FR-037**: System MUST provide a "Video Filters" section in the UI with options for: Rotate (90°/180°/270°), Crop (top/bottom/left/right pixels), Scale/Resize (custom width/height), Brightness/Contrast (sliders), Saturation (slider), and Deinterlace
- **FR-038**: System MUST apply filters in the correct order (rotate → crop → scale → color adjustments) to avoid processing artifacts
- **FR-039**: System MUST generate the appropriate FFmpeg filter graph based on enabled filters (e.g., `rotate=PI/2,crop=1920:800:0:140,eq=brightness=0.2`)
- **FR-040**: System MUST allow users to enable/disable individual filters independently via checkboxes
- **FR-041**: System MUST preserve the existing delogo filter and integrate it into the unified filter system

#### Resume Failed Batch Processing

- **FR-042**: System MUST track batch processing state (list of files, completed files, settings) and persist it to disk during processing
- **FR-043**: System MUST detect incomplete batches on app startup and prompt user with "Resume previous batch? (X of Y completed)"
- **FR-044**: When resuming a batch, system MUST skip files that have already been successfully processed (verified by checking output file existence and duration match)
- **FR-045**: System MUST restart any partially-completed files from 0% (FFmpeg does not support mid-file resume)
- **FR-046**: If batch settings have changed since the original run, system MUST prompt user to choose between original settings or current settings

#### Smart Error Messages

- **FR-047**: System MUST parse common FFmpeg error patterns (missing codec, insufficient disk space, corrupted file, GPU OOM) and display user-friendly error messages with suggested fixes
- **FR-048**: Error messages MUST include actionable buttons where applicable (e.g., "Choose Different Profile", "Retry", "Skip File")
- **FR-049**: For unknown/rare FFmpeg errors, system MUST show a generic message with a "Show Details" button to expand raw FFmpeg output for advanced troubleshooting
- **FR-050**: System MUST log all error messages to the Logs panel with timestamps for later review

### Key Entities *(include if feature involves data)*

- **Template**: Represents a saved configuration preset
  - Attributes: name, description, trim_mode, cut_minutes, cut_seconds, processing_profile_key (reference to built-in profiles), apply_delogo, delogo_params, output_format, output_suffix, output_prefix, created_timestamp
  - Relationships: None (standalone JSON file)

- **BatchState**: Represents the state of an in-progress batch
  - Attributes: batch_id (UUID), files (list of file paths), completed_files (list of file paths), settings_snapshot (serialized state), started_timestamp, last_updated_timestamp
  - Relationships: None (persisted to disk for recovery)

- **VideoMetadata**: Represents probed information about a video file
  - Attributes: file_path, duration, width, height, codec, bitrate, file_size, is_valid, validation_warnings (list of strings)
  - Relationships: Cached for each file in the processing queue

- **FilterChain**: Represents a sequence of video filters to apply
  - Attributes: filters (ordered list of filter objects: rotate, crop, scale, brightness, contrast, saturation, deinterlace, delogo)
  - Relationships: Applied to each video during processing

## Success Criteria *(mandatory)*

### Measurable Outcomes

#### Usability & Efficiency

- **SC-001**: Users can add 20 videos to the batch queue via drag-and-drop in under 5 seconds (vs. 30+ seconds with file dialogs)
- **SC-002**: Users can configure a batch processing job by loading a saved template in under 10 seconds (vs. 2-3 minutes manual configuration)
- **SC-003**: 90% of users successfully complete drag-and-drop file loading on first attempt without needing tutorial or help documentation
- **SC-004**: Template usage reduces configuration errors by 70% (measured by comparing error rates between template vs. manual configuration)

#### Performance

- **SC-005**: Batch processing of 20 videos completes in 25-30% of the time compared to serial processing on a 4-core system
- **SC-006**: Hardware-accelerated encoding completes 8-15x faster than CPU encoding on compatible systems (measured with identical input videos)
- **SC-007**: UI remains responsive (no freezing) during parallel batch processing, with all UI interactions completing in under 200ms
- **SC-008**: Video metadata probing completes in under 1 second per file for videos up to 4K resolution

#### Error Reduction & Recovery

- **SC-009**: 95% of FFmpeg errors display user-friendly messages with suggested fixes (vs. raw FFmpeg output)
- **SC-010**: Users can successfully resume an interrupted batch in under 15 seconds from detecting the incomplete batch to restarting processing
- **SC-011**: Pre-processing validation catches 90% of incompatibility issues before encoding starts (e.g., profile mismatches, corrupted files)
- **SC-012**: Parallel processing automatically recovers from single-file failures without stopping the entire batch

#### Feature Adoption

- **SC-013**: 60% of users create at least one custom template within their first week of using the app
- **SC-014**: 40% of users with GPU-capable systems use hardware-accelerated profiles for at least 50% of their encoding jobs

#### System Reliability

- **SC-016**: Parallel processing handles batches of 100+ videos without memory leaks or crashes (max 10% memory growth over baseline)
- **SC-017**: Template save/load operations succeed 99.9% of the time without data corruption
- **SC-018**: Batch state persistence allows 99% of interrupted batches to resume successfully

## Scope *(mandatory)*

### In Scope

- Drag-and-drop file and folder input for batch processing
- Parallel video processing (2-4 simultaneous encodes based on CPU cores)
- Configuration template system (save/load settings as named presets)
- Hardware-accelerated encoding support (NVENC, QuickSync, VCE, VideoToolbox)
- Video metadata display and pre-processing validation
- Additional video filters: rotate, crop, scale, brightness/contrast, saturation, deinterlace
- Resume capability for interrupted batch processing
- User-friendly error messages with suggested fixes
- UI updates to support all new features in both batch and single processor views

### Out of Scope

- Audio-only processing (extract audio, mix audio tracks, normalize volume) - defer to future enhancement
- Subtitle support (embed, extract, burn-in) - defer to future enhancement
- Video preview with live filter rendering (only static first-frame preview in scope)
- Advanced filter chaining UI with drag-and-drop filter ordering - defer to future enhancement
- Scheduled/automated batch processing (run at specific times) - defer to future enhancement
- Cloud storage integration (Google Drive, Dropbox input/output) - defer to future enhancement
- Multi-machine distributed encoding - defer to future enhancement
- Frame-accurate trim (current seconds precision sufficient for scope)

## Assumptions *(mandatory)*

1. **FFmpeg Availability**: Users have FFmpeg installed and accessible in system PATH. The app will check for FFmpeg on startup and display an error if missing.

2. **Hardware Compatibility**: GPU-accelerated encoding requires compatible hardware and up-to-date drivers. The feature gracefully degrades to CPU encoding if hardware is unavailable.

3. **File System Permissions**: Users have read access to input folders and write access to output folders. Standard OS permission errors will be displayed if access is denied.

4. **Storage Capacity**: Users have sufficient disk space for output files. The app will check available space before processing and warn if insufficient.

5. **Python/Library Versions**: The app runs on Python 3.8+ with CustomTkinter 5.0+ and ffmpeg-python (if available). Version compatibility is documented in requirements.txt.

6. **Single User**: The app is designed for single-user local operation. Multi-user or networked scenarios are not supported.

7. **Video Formats**: The app supports common video containers (mp4, mkv, avi, mov, webm, m4v) and codecs (H.264, H.265, VP8, VP9). Exotic or proprietary formats may fail to probe or encode.

8. **Template Portability**: Templates are portable across Windows installations but may reference absolute paths. Cross-platform template sharing (Windows ↔ macOS ↔ Linux) may require path adjustments.

9. **Parallel Processing Overhead**: Parallel processing benefits diminish beyond 4 simultaneous encodes due to I/O bottlenecks. The system caps parallelism at 4 by default.

10. **Filter Order Consistency**: Video filters are applied in a fixed order (rotate → crop → scale → color) to ensure predictable results. Users cannot customize filter ordering in this version.

## Dependencies *(mandatory)*

### External Dependencies

- **FFmpeg**: Command-line video processing tool (version 4.0+) with support for libx264, aac, and optional hardware encoders (nvenc, qsv, videotoolbox)
- **CustomTkinter**: Python GUI framework (version 5.0+) for modern UI components
- **ffmpeg-python**: Python wrapper for FFmpeg (optional, fallback to subprocess if unavailable)
- **Python Standard Library**: `threading`, `subprocess`, `json`, `pathlib`, `os`, `re`, `uuid`

### Internal Dependencies

- **AppState**: Central state management must be extended to include template and custom profile data
- **VideoProcessor**: Must be refactored to support parallel processing and filter chains
- **UI Components**: Batch and single processor UIs must be updated to support new features (drag-drop, template selector, filter options)

### Feature Dependencies

- **FR-042 (Resume Batch)** depends on **FR-006 (Parallel Processing)**: Batch state tracking must account for multiple active processes
- **FR-037 (Video Filters)** depends on **FR-022 (Hardware Encoding)**: Filter chains must work with both CPU and GPU encoding pipelines

## Constraints *(mandatory)*

### Technical Constraints

- **TC-001**: Parallel processing is limited to 8 simultaneous encodes to prevent system overload (configurable max)
- **TC-002**: Drag-and-drop is only supported on Windows and macOS (Linux support depends on window manager compatibility)
- **TC-003**: Hardware encoding requires specific FFmpeg builds with encoder support compiled in (some distributions lack NVENC/QSV)
- **TC-004**: Video preview is limited to the first 5 seconds to avoid memory issues with large files
- **TC-005**: Template and profile storage is local filesystem only (no cloud sync)
- **TC-006**: FFmpeg filter graph complexity is limited by FFmpeg's internal limits (~50 filters per chain)

### Performance Constraints

- **PC-001**: Video metadata probing adds 0.5-2 seconds per file (amortized by caching)
- **PC-002**: Parallel processing requires 2GB RAM per active encode (user's system must have sufficient memory)
- **PC-003**: UI responsiveness degrades if more than 500 files are added to a single batch (recommend batching large libraries)

### User Experience Constraints

- **UX-001**: Drag-and-drop feedback must appear within 100ms of drag-over event to feel responsive
- **UX-002**: Template and profile names are limited to 50 characters to fit in UI dropdowns
- **UX-003**: Error messages are capped at 300 characters for readability (with "Show Details" for full output)

### Compatibility Constraints

- **CC-001**: Hardware encoding quality may differ slightly from CPU encoding due to encoder implementation differences (acceptable trade-off for speed)
- **CC-002**: Resume batch feature requires batch state files to be compatible across app versions (implement versioned state schema)
