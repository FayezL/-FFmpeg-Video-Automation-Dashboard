# Implementation Plan: Standalone Executable & AI Logo Detection

**Branch**: `002-executable-ai-delogo` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-executable-ai-delogo/spec.md`

## Summary

This feature transforms the MagicTVBox video processing tool into a user-friendly standalone Windows application with AI-powered logo detection. The primary requirement is to package the existing Python application as a double-clickable executable that includes all dependencies, eliminating the need for Python installation. The secondary requirement is to add automatic logo detection using computer vision to identify watermarks and station logos, replacing the current manual coordinate entry workflow.

**Technical Approach** (from research):
- Use PyInstaller to bundle Python runtime, dependencies, and application code
- Leverage OpenCV for lightweight logo detection using template matching and edge detection algorithms
- Extend existing CustomTkinter UI with detection preview and controls
- Store detection profiles as JSON files for easy sharing and version control

## Technical Context

**Language/Version**: Python 3.8+ (existing codebase standard)
**Primary Dependencies**: PyInstaller 5.x, CustomTkinter 5.0+, FFmpeg 4.0+, OpenCV 4.x (cv2), NumPy, Pillow (PIL)
**Storage**: File-based - JSON for detection profiles, existing state management for application settings
**Testing**: pytest with fixtures for video processing, mock detection results, UI component testing
**Target Platform**: Windows 10+ (64-bit), minimum 4GB RAM, optional GPU acceleration
**Project Type**: Single desktop application (existing `src/` structure extended)
**Performance Goals**: Application startup <5s, logo detection <2min per video, frame processing <100ms per frame
**Constraints**: Executable size <500MB, detection accuracy ≥80%, memory usage <2GB during detection
**Scale/Scope**: Single-user desktop application, process videos up to 4K resolution, detect up to 10 logo regions per video

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: The project does not have a ratified constitution file yet (`.specify/memory/constitution.md` contains only template placeholders). This implementation will follow general best practices:

### Assumed Principles (to be ratified later)

- ✅ **Modularity**: Logo detection implemented as standalone module (`src/logo_detector.py`) that can be tested independently
- ✅ **Testing**: Tests written before implementation per existing project pattern (see `tests/` directory)
- ✅ **Backward Compatibility**: Executable packaging doesn't break existing Python-based workflow
- ✅ **User Data Safety**: Detection profiles stored in user-accessible location, no automatic data loss

### Gates

- ✅ **No Breaking Changes**: Existing video processing functionality remains intact
- ✅ **Testability**: Detection logic separated from UI for unit testing
- ✅ **Documentation**: Quickstart guide for building executable and using logo detection
- ⚠️ **Dependency Review**: OpenCV adds ~100MB to executable size (justified by logo detection requirement)

**Status**: PASSED - No constitution violations. Dependency size justified by core feature requirement.

## Project Structure

### Documentation (this feature)

```text
specs/002-executable-ai-delogo/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - technology choices and patterns
├── data-model.md        # Phase 1 output - detection result entities
├── quickstart.md        # Phase 1 output - building and using the features
├── contracts/           # Phase 1 output - detection API contracts
│   └── logo-detection-api.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created yet)
```

### Source Code (repository root)

```text
src/
├── models/                 # [EXISTING] Data models
├── services/               # [EXISTING] Business logic
├── ui/                     # [EXISTING] UI components
│   ├── batch_processor.py  # [EXTEND] Add logo detection UI
│   └── logo_preview.py     # [NEW] Detection result preview widget
├── logo_detector.py        # [NEW] Core logo detection logic
├── detection_profiles.py   # [NEW] Profile save/load management
├── packaging/              # [NEW] Executable build scripts
│   ├── build_exe.py        # PyInstaller configuration
│   ├── icon.ico            # Application icon
│   └── assets/             # Bundled assets for executable
├── state.py                # [EXTEND] Add detection state
└── main.py                 # [EXISTING] Application entry point

tests/
├── contract/               # [NEW] Logo detection API contract tests
│   └── test_detection_api.py
├── integration/            # [EXTEND] Full workflow tests
│   └── test_logo_workflow.py
├── unit/                   # [NEW] Detection algorithm tests
│   ├── test_logo_detector.py
│   ├── test_detection_profiles.py
│   └── fixtures/           # Test videos with known logos
│       └── sample_logo.mp4
└── test_executable.py      # [NEW] Executable packaging tests

build/                      # [NEW] Build output directory
└── MagicTVBox.exe         # Final executable (gitignored)
```

**Structure Decision**: Single project structure maintained. All new code integrates with existing `src/` layout. The `packaging/` subdirectory is added for executable build configuration to keep build logic separate from application logic.

## Complexity Tracking

> **No violations - this section is empty per template instructions**

## Phase 0: Research & Technology Choices

**Status**: ✅ COMPLETE

### Research Areas

1. **Executable Packaging Tool Selection**
2. **Logo Detection Algorithm Approach**
3. **OpenCV Integration Patterns**
4. **PyInstaller Optimization Strategies**
5. **Detection Profile Storage Format**

**Output**: See [research.md](./research.md) for detailed findings and decisions.

## Phase 1: Design & Contracts

**Status**: ✅ COMPLETE

### Data Models

**Output**: See [data-model.md](./data-model.md) for complete entity definitions:

- `DetectionResult` - Represents a detected logo region
- `DetectionProfile` - Saved detection configuration
- `DetectionProgress` - Real-time progress tracking
- `FrameSample` - Individual frame analysis result

### API Contracts

**Output**: See [contracts/logo-detection-api.md](./contracts/logo-detection-api.md) for:

- `detect_logos(video_path, config)` - Main detection function
- `preview_detection(result, frame_index)` - Generate preview image
- `save_profile(profile, path)` - Persist detection settings
- `load_profile(path)` - Load saved settings

### User Guide

**Output**: See [quickstart.md](./quickstart.md) for:

- Building the executable with PyInstaller
- Using logo detection feature
- Creating and managing detection profiles
- Troubleshooting common issues

## Phase 2: Task Breakdown

**Status**: ⏸️ PENDING - Run `/speckit.tasks` to generate

This phase will create `tasks.md` with actionable, dependency-ordered tasks for implementation.

## Implementation Phases (High-Level)

### Phase 1: Standalone Executable (Priority P1) - ~8-12 tasks

**Goal**: Users can double-click to launch application without Python

**Key Tasks**:
- Configure PyInstaller spec file with all dependencies
- Create application icon and branding assets
- Bundle FFmpeg binaries or create installer
- Implement single-instance application check
- Add startup performance optimization
- Create build script with optimization flags
- Test on clean Windows system without Python
- Document build process

**Success Criteria**: Application launches in <5s, executable size <500MB, works without Python

### Phase 2: Basic Logo Detection (Priority P2) - ~12-16 tasks

**Goal**: Users can automatically detect logo regions with 80%+ accuracy

**Key Tasks**:
- Implement frame extraction every 30th frame
- Create OpenCV-based detection algorithm (edge detection + template matching)
- Build detection result data model
- Add "Detect Logos" button to UI
- Create detection preview widget with bounding boxes
- Implement confidence scoring
- Add progress indication with cancel support
- Integrate with existing delogo parameters
- Handle edge cases (no logos, timeouts, errors)
- Test detection accuracy on sample videos
- Document detection workflow

**Success Criteria**: Detection completes in <2min, 80%+ accuracy, user can accept/reject regions

### Phase 3: Detection Refinement (Priority P3) - ~8-10 tasks

**Goal**: Users can customize detection and save profiles

**Key Tasks**:
- Add sensitivity slider to UI
- Implement profile save/load functionality
- Create profile storage format (JSON)
- Add profile selection dropdown
- Implement user feedback collection (mark as not logo)
- Create profile management UI
- Document profile format for sharing
- Add profile validation

**Success Criteria**: Users can save/load profiles, adjust sensitivity affects results

## Risk Mitigation Strategies

| Risk | Mitigation Implementation |
|------|--------------------------|
| Executable size >500MB | PyInstaller optimization: exclude dev dependencies, use UPX compression, consider FFmpeg external download |
| Detection accuracy <80% | Start with conservative edge detection, allow manual adjustment, collect false positive examples for tuning |
| Detection timeout (>5min) | Implement frame sampling (every 30th frame), add timeout with partial results, show progress with cancel option |
| OpenCV bloat | Use opencv-python-headless (smaller), exclude unused modules, consider lazy loading |
| Single instance fails | Fallback to multi-instance with clear window labeling |

## Dependencies Management

### Required for Executable Packaging

- PyInstaller 5.x - Bundle Python runtime
- pywin32 - Windows-specific functionality
- UPX (optional) - Executable compression

### Required for Logo Detection

- opencv-python-headless ~= 4.8.0 - Core CV functionality without GUI
- numpy ~= 1.24.0 - Array operations for frame processing
- Pillow (PIL) ~= 10.0.0 - Image I/O and preview generation

### Already in Project

- CustomTkinter 5.0+ - UI framework
- FFmpeg 4.0+ - Video processing (external binary)
- pytest - Testing framework

## Testing Strategy

### Unit Tests (tests/unit/)

- Logo detection algorithm with known logo patterns
- Profile save/load with various configurations
- Frame extraction and sampling logic
- Confidence scoring accuracy

### Integration Tests (tests/integration/)

- Full detection workflow from video → results → UI
- Executable launch and shutdown
- Detection with various video formats and resolutions
- Cancel operation during detection

### Contract Tests (tests/contract/)

- Detection API inputs/outputs
- Profile format validation
- Error handling and edge cases

### Manual Testing Checklist

- [ ] Double-click executable launches app
- [ ] App works on machine without Python
- [ ] Logo detection finds known logos in test videos
- [ ] Preview shows correct bounding boxes
- [ ] Sensitivity adjustment changes results
- [ ] Profile save/load works correctly
- [ ] Cancel stops detection cleanly
- [ ] Executable size is acceptable (<500MB)

## Notes

- **Incremental Delivery**: P1 (executable) can be delivered independently before P2 (detection)
- **OpenCV Choice**: Using opencv-python-headless (no Qt GUI dependencies) saves ~50MB vs full opencv-python
- **Detection Algorithm**: Starting with classical CV (edge detection + template matching) rather than deep learning to avoid TensorFlow/PyTorch dependencies that would add 200-400MB to executable
- **Profile Format**: JSON chosen over pickle for human readability and security (pickle can execute arbitrary code)
- **FFmpeg Bundling**: May need to bundle FFmpeg or provide installer due to licensing (FFmpeg is GPL/LGPL)
