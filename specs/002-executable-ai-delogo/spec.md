# Feature Specification: Standalone Executable & AI Logo Detection

**Feature Branch**: `002-executable-ai-delogo`
**Created**: 2026-02-08
**Status**: Draft
**Input**: User description: "i want to make the project clickable and can click and run it like a real program can we make this and i was thinking about ai helping me automatic spot the logos and remove them is this can be dont in good way"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Standalone Application Launch (Priority: P1)

Users can launch the video processing application by double-clicking an icon on their desktop or in a folder, without needing to open a command prompt or have Python installed. The application starts with a graphical interface and is immediately ready to process videos.

**Why this priority**: This is the foundation for accessibility. Without a standalone executable, the application is only accessible to technical users who can run Python scripts. This blocks all other features from reaching non-technical users.

**Independent Test**: Can be fully tested by double-clicking the application icon and verifying the main window appears with all UI elements functional. Delivers immediate value by making the existing application accessible to all users.

**Acceptance Scenarios**:

1. **Given** user has received the application file, **When** they double-click the application icon, **Then** the main window launches within 5 seconds showing the batch processor interface
2. **Given** user does not have Python installed, **When** they double-click the application, **Then** the application launches successfully without error
3. **Given** the application is running, **When** user closes the window, **Then** the application terminates cleanly and releases all resources
4. **Given** application is already running, **When** user double-clicks the icon again, **Then** the existing window is brought to focus (single instance) or a new window opens based on configuration

---

### User Story 2 - Automatic Logo Detection (Priority: P2)

Users can enable automatic logo detection which uses AI to scan videos and identify potential logo locations (watermarks, station IDs, channel logos). The system presents detected logo regions with confidence scores, allowing users to review and confirm before processing.

**Why this priority**: Reduces the tedious manual work of finding logo coordinates for each video. Current workflow requires users to manually specify X, Y, W, H coordinates. This feature provides a significant quality-of-life improvement but depends on having a working application first.

**Independent Test**: Can be tested by uploading a video with visible logos, enabling auto-detection, and verifying the system presents detected regions with preview boxes overlaid on the video. Delivers value by eliminating manual coordinate entry.

**Acceptance Scenarios**:

1. **Given** user has loaded a video file, **When** they click "Detect Logos", **Then** the system analyzes the video and displays detected logo regions with bounding boxes and confidence percentages
2. **Given** logos have been detected, **When** user reviews the detected regions, **Then** they can see a preview of each detected area overlaid on a video frame
3. **Given** multiple logos are detected, **When** user selects specific regions to remove, **Then** the selected coordinates are automatically populated into the delogo parameters
4. **Given** detection is running, **When** user cancels the operation, **Then** the detection stops and any partial results are discarded

---

### User Story 3 - Logo Detection Refinement (Priority: P3)

Users can adjust detection sensitivity, train the system on custom logos, and save detection profiles for recurring logo patterns. The system learns from user corrections to improve accuracy over time for their specific use cases.

**Why this priority**: Enhances the logo detection feature with advanced capabilities. While valuable, it's lower priority than basic detection. Can be implemented as an enhancement after basic detection is working.

**Independent Test**: Can be tested by adjusting sensitivity slider, saving a detection profile, and verifying it can be loaded and applied to new videos. Delivers value by personalizing detection to user's specific video sources.

**Acceptance Scenarios**:

1. **Given** user has detected logos, **When** they adjust the sensitivity slider, **Then** the detection re-runs with updated confidence thresholds showing more or fewer results
2. **Given** user frequently processes videos from the same source, **When** they save a detection profile, **Then** the profile stores logo patterns and can be applied to future videos from that source
3. **Given** the system incorrectly identified a region, **When** user marks it as "not a logo", **Then** the system adjusts its model to reduce similar false positives in future detections

---

### Edge Cases

- What happens when the video has no visible logos (system should report "No logos detected" without error)?
- What happens when a logo moves position (animated logos, corner bugs that appear/disappear)?
- How does the system handle low-resolution or heavily compressed videos where logos are difficult to identify?
- What happens if logo detection takes longer than 5 minutes (should timeout with partial results)?
- How does the system distinguish between actual logos and similar-looking graphical elements (e.g., text overlays, subtitles)?
- What happens when the user's computer doesn't meet minimum requirements for AI model inference?
- How does the system handle videos with multiple logos in different positions throughout the video?

## Requirements *(mandatory)*

### Functional Requirements

#### Standalone Executable

- **FR-001**: System MUST package the application as a standalone executable for Windows that includes all dependencies
- **FR-002**: System MUST launch the graphical interface within 5 seconds of user double-clicking the executable
- **FR-003**: System MUST function without requiring Python installation on the user's computer
- **FR-004**: System MUST include FFmpeg binaries within the package or provide clear instructions for one-time FFmpeg installation
- **FR-005**: System MUST create a single-instance application by default (prevent multiple windows) or clearly indicate multi-instance support
- **FR-006**: System MUST handle missing dependencies gracefully with user-friendly error messages
- **FR-007**: System MUST include an application icon visible in file explorer and taskbar

#### AI Logo Detection

- **FR-008**: System MUST analyze video frames to detect rectangular logo regions with confidence scores
- **FR-009**: System MUST display detected logo regions as bounding boxes overlaid on video preview
- **FR-010**: System MUST show confidence percentage for each detected region
- **FR-011**: System MUST allow users to accept, reject, or manually adjust detected regions
- **FR-012**: System MUST auto-populate delogo X, Y, W, H parameters when user accepts a detected region
- **FR-013**: System MUST provide a "Detect Logos" button in the delogo section of the UI
- **FR-014**: System MUST show progress indication during logo detection (progress bar or spinner)
- **FR-015**: System MUST allow users to cancel logo detection in progress
- **FR-016**: System MUST sample every 30th frame for logo detection to balance accuracy with performance
- **FR-017**: System MUST handle videos without logos by displaying "No logos detected" message
- **FR-018**: System MUST provide adjustable sensitivity/confidence threshold for logo detection

#### Detection Refinement

- **FR-019**: System MUST allow users to save detection profiles with a user-defined name
- **FR-020**: System MUST allow users to load saved detection profiles
- **FR-021**: System MUST store detection profiles in a human-readable format
- **FR-022**: System MUST allow users to adjust detection sensitivity via slider or numeric input

### Key Entities

- **Detection Result**: Represents a single detected logo region with coordinates (x, y, width, height), confidence score (0-100%), frame number where detected, and preview image
- **Detection Profile**: Named collection of detection settings including sensitivity threshold, frame sampling rate, minimum/maximum logo size constraints, and optionally learned patterns from user corrections
- **Application Package**: Bundled executable containing Python runtime, application code, UI assets, FFmpeg binaries (or installer), and AI detection model files

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Non-technical users can launch and use the application without installing Python or other dependencies (measured by zero support requests about Python installation)
- **SC-002**: Application launches within 5 seconds on systems meeting minimum requirements (Windows 10+, 4GB RAM)
- **SC-003**: Logo detection identifies logo regions with at least 80% accuracy on test videos containing common watermarks and station logos
- **SC-004**: Users can complete logo detection and selection in under 2 minutes per video (compared to 5+ minutes for manual coordinate entry)
- **SC-005**: Logo detection reduces manual parameter entry by 70% for users processing videos with logos
- **SC-006**: Application executable size is under 500MB for reasonable download and distribution
- **SC-007**: 90% of detected logo regions are accepted by users without manual adjustment
- **SC-008**: Application can be distributed as a single file or simple installer without requiring technical documentation

## Scope *(mandatory)*

### In Scope

- Windows executable generation with all dependencies bundled
- Application icon and branding for the executable
- AI-powered detection of static logo regions (watermarks, corner bugs, station IDs)
- Visual preview of detected logo regions
- User review and approval workflow for detected logos
- Adjustable detection sensitivity
- Save/load detection profiles
- Integration with existing delogo functionality (auto-populate X, Y, W, H parameters)
- Progress indication for detection operations
- Basic detection accuracy improvements from user feedback

### Out of Scope

- macOS or Linux executable generation (Windows only for this feature)
- Detection of moving/animated logos that change position during the video
- Automatic processing without user review (detection always requires user confirmation)
- Real-time logo detection during video playback
- Cloud-based logo detection or online model updates
- Logo removal without delogo parameters (detection only suggests regions, FFmpeg delogo still performs removal)
- Training custom AI models from scratch (will use existing pre-trained models adapted for logo detection)
- Batch detection across multiple videos simultaneously
- Advanced machine learning features like transfer learning or neural architecture search

## Assumptions *(mandatory)*

- Users are running Windows 10 or later (64-bit)
- Users have systems with at least 4GB RAM and basic GPU capability
- FFmpeg is available either bundled or through system PATH
- Logo detection will use existing computer vision models (OpenCV template matching, edge detection, or lightweight CNN models like MobileNet)
- Most logos are static and appear in consistent positions throughout the video
- Users want to review detected logos before applying removal (not fully automatic)
- Application will be distributed via direct download (not through app stores)
- Detection accuracy of 80% is acceptable for initial release (can improve over time)
- Sampling every 30th frame provides sufficient accuracy while maintaining performance
- Users primarily process videos with watermarks/logos in corners or consistent positions

## Dependencies *(if applicable)*

### External Dependencies

- **PyInstaller or similar tool** for creating Windows executable with Python bundled
- **FFmpeg binaries** (4.0+) either bundled or installed separately
- **Computer vision library** for logo detection (OpenCV or similar)
- **Pre-trained model or detection algorithm** for identifying logo-like regions (template matching, edge detection, or lightweight CNN)
- **CustomTkinter 5.0+** UI framework (already a dependency)
- **System requirements**: Windows 10+, 4GB RAM minimum, 8GB recommended

### Internal Dependencies

- Existing delogo functionality must remain functional
- Existing UI (batch_processor.py) needs extension for detection controls
- Existing state management (AppState) needs extension for detection results
- Application must maintain compatibility with current video processing pipeline

## Open Questions *(if applicable)*

1. **Detection Algorithm**: Should we use traditional computer vision (OpenCV template matching, edge detection) or a lightweight neural network approach? Traditional CV is faster but less accurate; neural networks are more accurate but require more processing power.

2. **Frame Sampling Strategy**: How many frames should be analyzed? Options:
   - Analyze all frames (most accurate, very slow)
   - Sample every Nth frame (balanced approach)
   - Analyze first, middle, and last frames only (fastest, least accurate)

3. **User Workflow Integration**: Should logo detection be:
   - A separate step before video processing?
   - Integrated into the batch processing workflow?
   - Available as both a manual tool and automatic pre-processing step?

## Risks & Mitigations *(if applicable)*

| Risk | Impact | Mitigation |
|------|--------|------------|
| Executable size too large (>500MB) makes distribution difficult | Medium | Use PyInstaller optimization flags, exclude unnecessary dependencies, consider separate FFmpeg download |
| Logo detection accuracy below 80% frustrates users | High | Implement adjustable sensitivity, allow manual correction, start with common logo patterns and improve iteratively |
| Detection too slow (>5 minutes per video) | Medium | Implement frame sampling, use GPU acceleration if available, provide cancel option and progress indication |
| AI model requires dependencies that bloat executable | Medium | Use lightweight models (OpenCV algorithms or MobileNet), avoid heavy ML frameworks like TensorFlow if possible |
| Users expect perfect detection without review | Low | Clear UI messaging that detection is a "suggestion" tool requiring user confirmation |
| Cross-platform expectations after Windows release | Low | Clearly communicate Windows-only support in documentation and release notes |

## Notes

This feature significantly improves accessibility and usability by addressing two major pain points:

1. **Accessibility Barrier**: Current Python-based workflow limits users to those comfortable with command-line tools
2. **Manual Labor**: Finding logo coordinates manually is tedious and error-prone

The standalone executable (P1) is the critical foundation that must be implemented first. Logo detection (P2-P3) provides substantial value but can be implemented incrementally after the executable is working.

For logo detection, we're targeting "good enough" accuracy (80%+) with user review rather than perfect automatic detection. This balances implementation complexity with user value.
