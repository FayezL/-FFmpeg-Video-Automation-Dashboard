# Implementation Plan: Enhanced Workflow & Performance

**Branch**: `001-enhanced-workflow` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)

## Summary

This feature enhances MagicTVBox with **drag-and-drop file loading**, **parallel batch processing** (2-4 simultaneous encodes), **configuration templates**, **hardware-accelerated encoding** (NVENC/QuickSync), **video metadata validation**, **additional filters** (rotate, crop, scale, brightness), **batch recovery**, and **user-friendly error messages**.

**Primary Goal**: Improve user productivity by 60-75% through parallel processing and streamline workflows with one-click templates.

**Technical Approach**: Add threading-based parallel processor, JSON template persistence, hardware encoder detection via FFmpeg output parsing, and FFmpeg filter chain building.

---

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**: CustomTkinter 5.0+, FFmpeg 4.0+, threading, subprocess, pathlib, json, dataclasses
**Storage**: JSON files in `~/.magictvbox/` for templates and batch states
**Testing**: pytest with 80%+ coverage target, manual UI testing
**Target Platform**: Windows/macOS desktop (x86-64)
**Project Type**: Single desktop application
**Performance Goals**:
- UI responsive <200ms during processing
- Parallel processing: 2-4 simultaneous encodes
- Metadata probing: <1 second per file
- Hardware encoding: 8-15x faster than CPU

**Constraints**:
- Max 8 parallel processes (default 2-4)
- 2GB RAM per active encode process
- Template/profile names: 50 characters max
- Handle 100+ video batches without crashes

**Scale/Scope**: 8 user stories, 50 functional requirements, 10-week implementation

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ✅ No constitution file exists - proceeding without restrictions

Since `.specify/memory/constitution.md` is a template only, no specific gates apply to this feature. Standard Python best practices and the project's existing patterns will be followed.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-enhanced-workflow/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - technical decisions (2,504 lines)
├── data-model.md        # Phase 1 output - data structures
├── quickstart.md        # Phase 1 output - developer guide
├── contracts/           # Phase 1 output - service interfaces
│   └── interfaces.md
├── checklists/
│   └── requirements.md  # Spec quality validation
├── spec.md              # Feature specification
├── implementation-plan.md  # Detailed implementation roadmap
└── plan-summary.txt     # Quick reference guide
```

### Source Code (repository root)

**Option 1: Single project** *(SELECTED)*

```text
MagicTVBox/
├── main.py                     # Application entry point
├── src/
│   ├── state.py               # Central state management (AppState)
│   ├── video_processor.py      # FFmpeg subprocess handling
│   ├── templates.py           # [NEW] Template persistence
│   ├── parallel_processor.py   # [NEW] Parallel batch processing
│   ├── hardware_encoders.py    # [NEW] GPU encoder detection
│   ├── video_metadata.py       # [NEW] Metadata extraction & caching
│   ├── video_filters.py        # [NEW] Filter chain building
│   ├── batch_state.py          # [NEW] Batch state checkpoints
│   ├── error_handler.py        # [NEW] Error message parsing
│   └── ui/
│       ├── main_window.py      # Window management
│       ├── batch_processor.py  # [MODIFY] Add drag-drop, templates, metadata UI
│       ├── single_processor.py # [MODIFY] Add template selector
│       ├── settings_panel.py   # [MODIFY] Add parallelism slider, show GPU encoders
│       ├── logs_panel.py       # Log viewer
│       ├── drag_drop.py        # [NEW] Drag-drop handler
│       ├── preview_modal.py    # [NEW] Video preview modal
│       └── error_dialog.py     # [NEW] Error dialog with action buttons
└── tests/
    ├── test_templates.py               # [NEW]
    ├── test_parallel_processor.py       # [NEW]
    ├── test_hardware_encoders.py        # [NEW]
    ├── test_video_metadata.py           # [NEW]
    ├── test_video_filters.py            # [NEW]
    ├── test_batch_state.py              # [NEW]
    └── test_error_handler.py            # [NEW]
```

**Structure Decision**: MagicTVBox uses a single-project structure with clear `src/` and `tests/` separation. New service classes are added to `src/` root, UI components in `src/ui/`. This maintains consistency with existing codebase structure.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution violations. This feature adds necessary complexity to address critical user needs (parallel processing, templates, hardware acceleration) without unnecessary abstraction layers.

---

## Phase 0: Research & Technical Decisions

**Status**: ✅ COMPLETED

**Output**: [research.md](./research.md) (2,504 lines, 80KB)

**Key Decisions Documented**:
1. **Threading vs Multiprocessing**: Threading chosen (simpler state sharing, FFmpeg is subprocess)
2. **Drag-Drop Strategy**: Hybrid tkinterdnd2 + file dialog fallback
3. **Template Storage**: JSON in `~/.magictvbox/templates/` with inline profile settings
4. **Hardware Detection**: Parse `ffmpeg -encoders` output, test with 1-second encode
5. **Filter Ordering**: Fixed order (rotate→crop→scale→color→deinterlace→delogo) to prevent artifacts
6. **Worker Count Formula**: `max(1, min(4, (cores-1)//2))` default, user-adjustable 1-8
7. **Batch Checkpointing**: Save after each file completes, detect on startup
8. **Error Patterns**: Regex-based parsing for common errors (GPU unavailable, disk full, corrupted file)

**Research Topics Covered**:
- Drag-and-drop implementation in CustomTkinter/Tkinter
- Parallel processing patterns with Python threading
- Hardware encoder detection and testing
- Template/config persistence (cross-platform paths)
- Video metadata extraction and caching
- FFmpeg filter chains and parameter syntax
- Batch state persistence and recovery
- Error message parsing and translation

---

## Phase 1: Design & Contracts

**Status**: ✅ COMPLETED

**Output**:
- [data-model.md](./data-model.md) - 6 core entities (Template, BatchState, VideoMetadata, FilterChain, HardwareEncoder, ParallelProcessingConfig)
- [contracts/interfaces.md](./contracts/interfaces.md) - 8 service interfaces with method signatures
- [quickstart.md](./quickstart.md) - Developer onboarding guide

**Key Entities**:
1. **Template**: Saved configuration preset (trim settings, profile, filters, output options)
2. **BatchState**: In-progress batch state for recovery (files, completed, settings snapshot)
3. **VideoMetadata**: Cached video properties (duration, resolution, codec, bitrate)
4. **FilterChain**: Ordered video filters with FFmpeg string generation
5. **HardwareEncoder**: Detected GPU encoder with capability info
6. **ParallelProcessingConfig**: Worker pool configuration

**Service Interfaces**:
1. **TemplateManager**: Template CRUD operations
2. **ParallelProcessor**: Thread-pooled batch processing
3. **HardwareEncoderDetector**: GPU encoder detection and profile creation
4. **VideoMetadataExtractor**: Metadata extraction with caching
5. **FilterChainBuilder**: FFmpeg filter string building
6. **BatchStateManager**: Checkpoint persistence and recovery
7. **ErrorMessageParser**: User-friendly error translation
8. **DragDropHandler**: Drag-drop event handling

**Agent Context**: Will be updated after this phase (see next section)

---

## Phase 2: Implementation Roadmap

**Full Details**: See [implementation-plan.md](./implementation-plan.md) for complete 10-week schedule

**Summary**:

| Phase | Duration | Deliverables | Priority |
|-------|----------|--------------|----------|
| Phase 1 | Weeks 1-2 | Core infrastructure (ParallelProcessor, TemplateManager, HardwareEncoderDetector) | P1 |
| Phase 2 | Weeks 2-3 | Drag-drop UI, template selector, UI improvements | P1 |
| Phase 3 | Weeks 3-4 | Metadata extraction, validation, preview modal | P2 |
| Phase 4 | Week 4 | Hardware encoder detection, GPU profiles | P2 |
| Phase 5 | Week 5 | Video filters (rotate, crop, scale, brightness) | P3 |
| Phase 6 | Weeks 5-6 | Error handling, batch recovery | P3 |
| Phase 7 | Weeks 6-7 | Testing, benchmarking, performance optimization, polish | All |

**Critical Path**:
1. ParallelProcessor (enables all parallel features)
2. TemplateManager (enables workflow efficiency)
3. HardwareEncoderDetector (enables GPU speedup)
4. DragDropHandler (enables modern file selection)

---

## Feature Dependencies

### Internal Dependencies

- **ParallelProcessor** depends on **VideoProcessor** (existing)
- **TemplateManager** depends on **AppState** (existing)
- **HardwareEncoderDetector** depends on **ProcessingProfile** (existing in state.py)
- **VideoMetadataExtractor** depends on **ProcessingProfile** for validation
- **FilterChainBuilder** depends on **VideoProcessor** for filter application
- **BatchStateManager** depends on **ParallelProcessor** for multi-process tracking

### External Dependencies

- **FFmpeg 4.0+**: Video processing binary (user must install)
- **CustomTkinter 5.0+**: GUI framework (`pip install customtkinter`)
- **tkinterdnd2** (optional): Drag-drop support (`pip install tkinterdnd2`)
- **ffmpeg-python** (optional): Python FFmpeg wrapper (`pip install ffmpeg-python`)
- **pytest**: Testing framework (`pip install pytest pytest-cov`)

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Drag-drop not working on all systems | Medium | Medium | Provide file dialog fallback |
| Hardware encoding fails or unavailable | High | Medium | Auto-fallback to CPU encoding with warning |
| Parallel processing causes crashes | Low | High | Careful threading, resource limits, extensive testing |
| Template corruption loses user config | Low | High | Atomic writes, backup on update, validation on load |
| Batch recovery fails after app crash | Medium | Medium | Checkpoint after each file, validate on resume |
| Performance degrades with 100+ files | Medium | Low | Warn user, recommend smaller batches |
| FFmpeg output parsing breaks | Low | Medium | Graceful fallback to raw output for unknown patterns |

---

## Success Metrics

**Usability**:
- SC-001: Add 20 videos via drag-drop in <5 seconds (vs 30+ sec with dialogs)
- SC-002: Load template in <10 seconds (vs 2-3 min manual configuration)
- SC-003: 90% user success rate on first drag-drop attempt

**Performance**:
- SC-005: 20-video batch in 25-30% of serial time (2-4 workers)
- SC-006: Hardware encoding 8-15x faster than CPU
- SC-007: UI responsive (<200ms) during parallel processing
- SC-008: Metadata probing <1 second per file

**Quality & Reliability**:
- SC-009: 95% of FFmpeg errors show user-friendly messages
- SC-010: Resume interrupted batch in <15 seconds
- SC-011: Pre-processing validation catches 90% of issues
- SC-016: Handle 100+ batches without crashes
- SC-017: Template save/load 99.9% success rate
- SC-018: Batch resume 99% success rate

**Adoption**:
- SC-013: 60% of users create template in first week
- SC-014: 40% of GPU users leverage acceleration for 50% of jobs

---

## Definition of Done

### Code Complete

- [ ] All 7 new service classes implemented with interfaces matching contracts/
- [ ] All 3 UI components modified with new features
- [ ] All state extensions added to AppState
- [ ] No [NEEDS CLARIFICATION] markers remain in code

### Testing Complete

- [ ] Unit tests for all services (80%+ coverage)
- [ ] Integration tests for service interactions
- [ ] Manual testing of all 8 user stories
- [ ] Performance benchmarks meet success criteria
- [ ] Tested on Windows and macOS

### Documentation Complete

- [ ] All public methods have docstrings
- [ ] README updated with new features
- [ ] quickstart.md validated by fresh developer
- [ ] Inline comments for complex logic

### UX Complete

- [ ] All UI text reviewed for clarity
- [ ] Error messages tested with real failures
- [ ] Drag-drop tested with various file types
- [ ] Template loading tested with edge cases
- [ ] Parallel processing tested with 1-8 workers

### Performance Validated

- [ ] Parallel processing achieves 60-75% time reduction
- [ ] Hardware encoding achieves 8-15x speedup
- [ ] UI remains responsive during processing
- [ ] No memory leaks in 100+ video batches

---

## Next Steps

1. ✅ Review spec.md (user requirements)
2. ✅ Review research.md (technical decisions)
3. ✅ Review data-model.md (entities and schemas)
4. ✅ Review contracts/interfaces.md (service APIs)
5. ⬜ Read quickstart.md (developer setup)
6. ⬜ Run `/speckit.tasks` to generate actionable task list
7. ⬜ Begin Phase 1 implementation (ParallelProcessor + TemplateManager)

---

**Plan Complete** | **Ready for `/speckit.tasks` command**
