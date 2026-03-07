# Implementation Plan: CPU Limiting and Enhanced Processing Options

**Branch**: `003-cpu-limit-options` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-cpu-limit-options/spec.md`

## Summary

Add CPU limiting controls, enhanced settings panel, and intro/outro detection to the FFmpeg video automation application. Primary requirement is allowing users to throttle CPU usage during video processing to maintain system responsiveness for multitasking. Secondary features include expanded configuration options and automated intro/outro segment detection for series content.

**Technical Approach**: Implement CPU throttling through FFmpeg threading controls and process priority management. Enhance settings UI with categorized options tabs. Integrate OpenCV-based video frame analysis for intro/outro pattern detection with confidence scoring and user feedback loop.

## Technical Context

**Language/Version**: Python 3.8+ (existing codebase standard)
**Primary Dependencies**: CustomTkinter 5.0+, FFmpeg 4.0+, OpenCV 4.x (cv2), NumPy, Pillow (PIL), psutil (for CPU monitoring)
**Storage**: JSON files for settings persistence, detection profiles cache
**Testing**: pytest for unit and integration tests
**Target Platform**: Windows (primary), macOS/Linux (secondary)
**Project Type**: Single desktop application
**Performance Goals**: CPU limiting maintains <5% variance from target, intro/outro detection completes within 10% of video duration, UI remains responsive (<100ms freeze time)
**Constraints**: All FFmpeg operations in background threads, no UI blocking, settings persist across sessions
**Scale/Scope**: Single-user desktop application, batch processing up to 100 files, detection profiles for 50+ series

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: User-First Design
- ✅ **CPU limiting**: Simple on/off toggle with percentage slider (20-95%)
- ✅ **Enhanced settings**: Categorized tabs (Performance, Output, Quality, Advanced)
- ✅ **Intro/outro detection**: Clear UI showing detected segments with confidence scores
- ✅ **Error messages**: Specific validation messages for invalid CPU limits or settings
- ✅ **Real-time feedback**: CPU usage meter during processing, detection progress indicator

### Principle II: Robust Video Processing
- ✅ **No source modification**: All processing preserves originals
- ✅ **Validation**: Check CPU limit ranges, validate custom FFmpeg parameters
- ✅ **Error handling**: Graceful degradation if detection fails, fallback to full video processing
- ✅ **Logging**: Log CPU limit changes, detection results, FFmpeg commands with parameters
- ✅ **Cleanup**: Remove partial outputs on detection or processing failure

### Principle III: Real-time Feedback & Transparency
- ✅ **CPU monitoring**: Live CPU usage percentage display during processing
- ✅ **Detection visibility**: Show frame analysis progress, detected segments, confidence scores
- ✅ **Settings preview**: Display current settings before processing starts
- ✅ **Queue status**: Indicate when CPU limiting affects queue processing speed
- ✅ **Logs integration**: Output detection results and CPU metrics to logs panel

### Principle IV: Code Quality & Maintainability
- ✅ **Type hints**: All new functions include type annotations
- ✅ **Single responsibility**: CPULimiter, SettingsManager, IntroOutroDetector as separate classes
- ✅ **PEP 8**: Follow existing codebase style conventions
- ✅ **Docstrings**: Document detection algorithms, CPU throttling mechanisms
- ✅ **Meaningful names**: `apply_cpu_limit()`, `detect_intro_pattern()`, `persist_settings()`

### Principle V: Testing for Critical Paths
- ✅ **CPU limiting**: Test percentage enforcement, real-time adjustments, thread safety
- ✅ **Settings persistence**: Test save/load cycles, default handling, validation
- ✅ **Detection accuracy**: Test with known intro/outro samples, edge cases (no intro, variable length)
- ✅ **FFmpeg integration**: Test CPU-limited command generation, parameter injection
- ✅ **Integration tests**: Complete workflow from CPU limit enable to processing complete

### Principle VI: Performance & Responsiveness
- ✅ **Background threads**: CPU monitoring, intro/outro detection in worker threads
- ✅ **UI updates**: Thread-safe callbacks for progress updates, CPU metrics
- ✅ **Cancel support**: Allow cancellation of detection analysis, revert to full processing
- ✅ **No blocking I/O**: Async settings persistence, non-blocking profile cache reads

### Principle VII: Simplicity & Focus
- ✅ **Core mission alignment**: CPU limiting improves user experience during video processing
- ✅ **Enhanced settings**: Configuration over code, expand existing settings framework
- ✅ **Intro/outro detection**: Optional feature, doesn't complicate core processing flow
- ✅ **No premature abstraction**: Implement detection for single use case first, abstract if needed later
- ✅ **Clean removal**: Commented code removed, clear separation of optional features

**Status**: ✅ All gates passed. No constitution violations. Feature aligns with all principles.

## Project Structure

### Documentation (this feature)

```text
specs/003-cpu-limit-options/
├── plan.md              # This file
├── research.md          # Phase 0: Technical research and decisions
├── data-model.md        # Phase 1: Data structures and entities
├── quickstart.md        # Phase 1: Developer setup and integration guide
├── contracts/           # Phase 1: API contracts (if applicable)
├── checklists/          # Quality validation checklists
│   └── requirements.md  # Spec quality checklist (complete)
└── tasks.md             # Phase 2: Implementation tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── ui/
│   ├── single_processor.py      # Add CPU limiting UI controls
│   ├── batch_processor.py        # Add CPU limiting UI controls
│   ├── settings_panel.py         # Enhance with categorized tabs
│   └── intro_outro_panel.py      # NEW: Intro/outro detection UI
├── video_processor.py            # Integrate CPU limiting in FFmpeg execution
├── cpu_limiter.py                # NEW: CPU throttling and monitoring
├── intro_outro_detector.py       # NEW: Video segment detection logic
├── settings_manager.py           # NEW: Enhanced settings persistence
├── state.py                      # Add CPU limit, detection settings to AppState
└── exceptions.py                 # Add CPU limiting, detection exceptions

tests/
├── unit/
│   ├── test_cpu_limiter.py       # NEW: CPU throttling tests
│   ├── test_intro_outro_detector.py  # NEW: Detection algorithm tests
│   ├── test_settings_manager.py  # NEW: Settings persistence tests
│   └── test_video_processor.py   # UPDATE: CPU-limited FFmpeg tests
└── integration/
    ├── test_cpu_limited_processing.py  # NEW: End-to-end CPU limiting workflow
    └── test_intro_outro_workflow.py    # NEW: Detection + processing workflow
```

**Structure Decision**: Single desktop application structure (Option 1). New modules added to existing `src/` directory following current organization. UI components extend existing panel framework. Tests follow established `unit/` and `integration/` structure.

## Complexity Tracking

No constitution violations requiring justification. All features align with existing principles and technical standards.
