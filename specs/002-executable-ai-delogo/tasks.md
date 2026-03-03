# Tasks: Standalone Executable & AI Logo Detection

**Input**: Design documents from `/specs/002-executable-ai-delogo/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test tasks are included per the existing project pattern (tests/ directory with pytest)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project structure: `src/`, `tests/` at repository root
- All paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize build infrastructure and packaging setup for executable generation

- [x] T001 Create packaging directory structure at src/packaging/
- [x] T002 Add PyInstaller to requirements: pip install pyinstaller==5.13.0
- [x] T003 [P] Create application icon file at src/packaging/icon.ico (note: using default icon for MVP, custom icon optional)
- [x] T004 [P] Create Windows version info file at src/packaging/version_info.txt

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Verify FFmpeg binary location and prepare for bundling (identify path for PyInstaller spec) - Found at C:\ffmpeg\bin\ffmpeg.exe
- [x] T006 [P] Create base data model file with dataclass imports at src/data_models.py
- [x] T007 [P] Extend AppState in src/state.py with detection-related fields (detection_enabled, detection_results, active_profile, detection_progress, detection_status)
- [x] T008 Create base exception hierarchy in src/exceptions.py (DetectionError, VideoReadError, ProfileError, etc.)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Standalone Application Launch (Priority: P1) 🎯 MVP

**Goal**: Users can double-click an executable to launch the application without Python installation

**Independent Test**: Copy MagicTVBox.exe to a Windows machine without Python, double-click, verify application launches in <5 seconds with full UI

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T009 [P] [US1] Create executable test file at tests/test_executable.py to verify build output
- [x] T010 [P] [US1] Create integration test for application startup time at tests/integration/test_startup.py (basic placeholder created)
- [x] T011 [P] [US1] Create test for single-instance behavior at tests/integration/test_single_instance.py

### Implementation for User Story 1

- [x] T012 [US1] Create PyInstaller spec file at src/packaging/MagicTVBox.spec with Analysis configuration
- [x] T013 [US1] Configure hiddenimports in spec file (customtkinter, PIL._tkinter_finder, cv2, numpy.core._multiarray_umath)
- [x] T014 [US1] Configure binaries in spec file to bundle FFmpeg executable
- [x] T015 [US1] Configure datas in spec file to include UI assets from src/packaging/assets
- [x] T016 [US1] Configure excludes in spec file (matplotlib, scipy, pandas, IPython, jupyter)
- [x] T017 [US1] Configure EXE options (upx=True, console=False, icon, version_file)
- [x] T018 [US1] Create automated build script at src/packaging/build_exe.py
- [x] T019 [US1] Implement single-instance check in main.py using file lock
- [x] T020 [US1] Add startup performance optimization (lazy imports, deferred initialization) in main.py
- [x] T021 [US1] Test build on development machine: python src/packaging/build_exe.py (requires: pip install -r requirements.txt first)
- [ ] T022 [US1] Test executable size is under 500MB (should be 180-220MB with UPX) - Manual test after build
- [ ] T023 [US1] Test executable on clean Windows machine without Python - Manual test after build
- [x] T024 [US1] Add error handling for missing FFmpeg with user-friendly message in main.py
- [x] T025 [US1] Document build process in BUILDING.md

**Checkpoint**: At this point, User Story 1 should be fully functional - executable launches without Python, all existing features work

---

## Phase 4: User Story 2 - Automatic Logo Detection (Priority: P2)

**Goal**: Users can automatically detect logo regions using AI, review results, and accept coordinates for delogo processing

**Independent Test**: Load a video with visible logo, click "Detect Logos", verify detection completes in <2 minutes, shows preview with bounding boxes, allows accept/reject, auto-populates delogo parameters

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T026 [P] [US2] Create test fixtures directory at tests/fixtures/ with sample videos
- [ ] T027 [P] [US2] Add sample video with known logo to tests/fixtures/sample_with_logo.mp4
- [ ] T028 [P] [US2] Create contract test for detect_logos() API at tests/contract/test_detection_api.py
- [ ] T029 [P] [US2] Create integration test for full detection workflow at tests/integration/test_logo_workflow.py
- [ ] T030 [P] [US2] Create unit test for frame sampling at tests/unit/test_logo_detector.py
- [ ] T031 [P] [US2] Create unit test for confidence scoring at tests/unit/test_logo_detector.py

### Implementation for User Story 2

**Data Models (can run in parallel)**:

- [ ] T032 [P] [US2] Create DetectionResult dataclass in src/data_models.py
- [ ] T033 [P] [US2] Create DetectionSession dataclass in src/data_models.py
- [ ] T034 [P] [US2] Create DetectionConfig dataclass with defaults in src/data_models.py

**Core Detection Logic**:

- [ ] T035 [US2] Create logo detector module at src/logo_detector.py (depends on T032-T034)
- [ ] T036 [US2] Implement frame sampling function (every 30th frame) in src/logo_detector.py
- [ ] T037 [US2] Implement frame preprocessing (grayscale, blur, normalize) in src/logo_detector.py
- [ ] T038 [US2] Implement Canny edge detection algorithm in src/logo_detector.py
- [ ] T039 [US2] Implement Harris corner detection algorithm in src/logo_detector.py
- [ ] T040 [US2] Implement region filtering (size, aspect ratio, position) in src/logo_detector.py
- [ ] T041 [US2] Implement region clustering (merge overlapping detections) in src/logo_detector.py
- [ ] T042 [US2] Implement confidence scoring algorithm in src/logo_detector.py
- [ ] T043 [US2] Implement detect_logos() main function with progress callbacks in src/logo_detector.py
- [ ] T044 [US2] Implement preview_detection() function with bounding box overlay in src/logo_detector.py
- [ ] T045 [US2] Add error handling and timeout (5 minute max) in src/logo_detector.py
- [ ] T046 [US2] Add cancellation support via threading.Event in src/logo_detector.py

**UI Integration**:

- [ ] T047 [US2] Create logo preview widget at src/ui/logo_preview.py for displaying detection results
- [ ] T048 [US2] Implement bounding box drawing with confidence labels in src/ui/logo_preview.py
- [ ] T049 [US2] Add "Detect Logos" button to delogo section in src/ui/batch_processor.py
- [ ] T050 [US2] Add progress bar for detection progress in src/ui/batch_processor.py
- [ ] T051 [US2] Add "Cancel" button for detection in src/ui/batch_processor.py
- [ ] T052 [US2] Implement threaded detection controller in src/ui/batch_processor.py (background thread + UI updates via queue)
- [ ] T053 [US2] Implement detection result list/grid UI in src/ui/batch_processor.py
- [ ] T054 [US2] Implement accept/reject buttons for each detection result in src/ui/batch_processor.py
- [ ] T055 [US2] Implement auto-population of delogo X, Y, W, H parameters on accept in src/ui/batch_processor.py
- [ ] T056 [US2] Add status messages ("Detecting...", "Found 3 regions", "No logos detected") in src/ui/batch_processor.py
- [ ] T057 [US2] Add error display for detection failures in src/ui/batch_processor.py

**Utility Functions**:

- [ ] T058 [P] [US2] Implement estimate_detection_time() function in src/logo_detector.py
- [ ] T059 [P] [US2] Implement validate_video() function in src/logo_detector.py

**Integration**:

- [ ] T060 [US2] Integrate detection results with existing delogo workflow in src/video_processor.py
- [ ] T061 [US2] Test detection with various video formats (MP4, MKV, AVI) and resolutions
- [ ] T062 [US2] Test detection accuracy on sample videos (target: 80%+ accuracy)
- [ ] T063 [US2] Test detection performance (target: <2 minutes for 1-hour video)
- [ ] T064 [US2] Test UI responsiveness during detection (progress updates, cancel works)

**Checkpoint**: At this point, User Story 2 should be fully functional - logo detection finds regions, user can review and accept, coordinates auto-populate

---

## Phase 5: User Story 3 - Logo Detection Refinement (Priority: P3)

**Goal**: Users can adjust detection sensitivity, save/load detection profiles, and reuse configurations for recurring logo patterns

**Independent Test**: Adjust sensitivity slider, verify detection re-runs with different results; save profile with custom name, close app, reopen, load profile, verify settings restored

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T065 [P] [US3] Create test for profile save/load at tests/unit/test_detection_profiles.py
- [ ] T066 [P] [US3] Create test for profile validation at tests/unit/test_detection_profiles.py
- [ ] T067 [P] [US3] Create test for sensitivity adjustment at tests/integration/test_sensitivity.py
- [ ] T068 [P] [US3] Create test profile fixtures at tests/fixtures/sample_profile.json

### Implementation for User Story 3

**Data Models**:

- [ ] T069 [P] [US3] Create DetectionProfile dataclass in src/data_models.py
- [ ] T070 [P] [US3] Create LogoPattern dataclass in src/data_models.py
- [ ] T071 [P] [US3] Create ProfileStatistics dataclass in src/data_models.py

**Profile Management**:

- [ ] T072 [US3] Create detection profiles module at src/detection_profiles.py (depends on T069-T071)
- [ ] T073 [US3] Implement save_profile() function with JSON serialization in src/detection_profiles.py
- [ ] T074 [US3] Implement load_profile() function with validation in src/detection_profiles.py
- [ ] T075 [US3] Implement list_profiles() function with metadata extraction in src/detection_profiles.py
- [ ] T076 [US3] Implement delete_profile() function with confirmation in src/detection_profiles.py
- [ ] T077 [US3] Implement profile filename sanitization (spaces to underscores, lowercase) in src/detection_profiles.py
- [ ] T078 [US3] Create profiles directory at %APPDATA%/MagicTVBox/profiles/ on first run in src/detection_profiles.py
- [ ] T079 [US3] Add profile version migration support (future-proofing) in src/detection_profiles.py

**Sensitivity Adjustment**:

- [ ] T080 [US3] Add sensitivity slider to detection UI in src/ui/batch_processor.py
- [ ] T081 [US3] Implement sensitivity change handler (re-run detection with new threshold) in src/ui/batch_processor.py
- [ ] T082 [US3] Update DetectionConfig when sensitivity changes in src/logo_detector.py

**Template Matching (Optional Enhancement)**:

- [ ] T083 [P] [US3] Implement template matching algorithm in src/logo_detector.py
- [ ] T084 [P] [US3] Add enable_template_matching option to DetectionConfig in src/data_models.py
- [ ] T085 [US3] Integrate template matching with main detection pipeline in src/logo_detector.py

**UI - Profile Management**:

- [ ] T086 [US3] Add "Save Profile" button to detection UI in src/ui/batch_processor.py
- [ ] T087 [US3] Add "Load Profile" dropdown to detection UI in src/ui/batch_processor.py
- [ ] T088 [US3] Implement profile name input dialog in src/ui/batch_processor.py
- [ ] T089 [US3] Implement "Manage Profiles" dialog (list, view stats, delete) in src/ui/batch_processor.py
- [ ] T090 [US3] Add profile description and tags input fields in src/ui/batch_processor.py
- [ ] T091 [US3] Populate profile dropdown on app startup in src/ui/batch_processor.py
- [ ] T092 [US3] Apply loaded profile to detection config in src/ui/batch_processor.py

**Profile Statistics**:

- [ ] T093 [US3] Update profile statistics after each detection (videos_processed, accuracy) in src/detection_profiles.py
- [ ] T094 [US3] Display profile statistics in "Manage Profiles" dialog in src/ui/batch_processor.py
- [ ] T095 [US3] Track accepted vs rejected detections for accuracy calculation in src/logo_detector.py

**User Feedback (Future Enhancement)**:

- [ ] T096 [P] [US3] Add "Not a Logo" button to mark false positives in src/ui/batch_processor.py
- [ ] T097 [P] [US3] Store false positive examples in profile for future learning in src/detection_profiles.py

**Integration & Testing**:

- [ ] T098 [US3] Test profile save/load cycle with various configurations
- [ ] T099 [US3] Test sensitivity adjustment affects detection results
- [ ] T100 [US3] Test profile management UI (create, load, delete, view stats)
- [ ] T101 [US3] Test profile sharing (export JSON, import on another machine)

**Checkpoint**: All user stories should now be independently functional - users can detect logos, adjust settings, save profiles for reuse

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories or finalize the features

- [ ] T102 [P] Update HOURS_SUPPORT_VERIFICATION.md with executable build instructions
- [ ] T103 [P] Update UI_HOURS_FIELDS_REFERENCE.md with logo detection UI screenshots
- [ ] T104 [P] Create BUILDING.md with detailed executable build guide
- [ ] T105 [P] Add logo detection section to main README.md
- [ ] T106 Code cleanup: Remove debug logging, unused imports across all new files
- [ ] T107 Performance optimization: Profile detection algorithm for bottlenecks
- [ ] T108 [P] Add comprehensive logging for debugging detection issues in src/logo_detector.py
- [ ] T109 Memory profiling: Verify detection stays under 2GB RAM usage
- [ ] T110 [P] Add keyboard shortcuts for detection workflow (Enter=accept, Delete=reject, etc.)
- [ ] T111 [P] Create user guide document at docs/LOGO_DETECTION_GUIDE.md
- [ ] T112 Run quickstart.md validation: Build executable and test all workflows
- [ ] T113 Security review: Validate profile JSON parsing (no code execution risks)
- [ ] T114 [P] Add detection performance metrics to logs (frames/second, total time)
- [ ] T115 Accessibility: Ensure all new UI elements have proper focus indicators and tab order

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on Foundational completion - Can start in parallel with US1 if separate developers
- **User Story 3 (Phase 5)**: Depends on Foundational + User Story 2 completion (needs detection working first)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - No dependencies on US1 (detection works independently)
- **User Story 3 (P3)**: Depends on User Story 2 completion (enhances detection features)

### Within Each User Story

**User Story 1 (Executable)**:
1. Tests first (T009-T011)
2. PyInstaller spec file configuration (T012-T017)
3. Build scripts and optimizations (T018-T020)
4. Testing and validation (T021-T024)
5. Documentation (T025)

**User Story 2 (Detection)**:
1. Tests first (T026-T031)
2. Data models in parallel (T032-T034)
3. Core detection logic sequentially (T035-T046)
4. UI components in parallel after core (T047-T057)
5. Utility functions in parallel (T058-T059)
6. Integration and testing (T060-T064)

**User Story 3 (Refinement)**:
1. Tests first (T065-T068)
2. Data models in parallel (T069-T071)
3. Profile management core (T072-T079)
4. Sensitivity features (T080-T082)
5. Template matching in parallel (T083-T085)
6. UI integration (T086-T092)
7. Statistics tracking (T093-T095)
8. Optional enhancements (T096-T097)
9. Testing (T098-T101)

### Parallel Opportunities

**Within Setup (Phase 1)**:
- T003 (icon) and T004 (version info) can run in parallel

**Within Foundational (Phase 2)**:
- T006 (data models) and T007 (state) and T008 (exceptions) can all run in parallel

**Within User Story 1**:
- T009, T010, T011 (all tests) can run in parallel
- T013-T017 (spec file configs) can run in parallel after T012

**Within User Story 2**:
- T026-T031 (all tests) can run in parallel
- T032-T034 (data models) can run in parallel
- T047-T051 (UI components) can run in parallel after core detection
- T058-T059 (utilities) can run in parallel
- T061-T064 (testing) can run in parallel

**Within User Story 3**:
- T065-T068 (all tests) can run in parallel
- T069-T071 (data models) can run in parallel
- T083-T085 (template matching) can run in parallel
- T096-T097 (feedback features) can run in parallel
- T098-T101 (testing) can run in parallel

**Across User Stories** (if multiple developers):
- US1 and US2 can be developed in parallel after Foundational phase
- US3 must wait for US2 to complete

---

## Parallel Example: User Story 2 (Detection)

```bash
# Step 1: Launch all tests together
Task: "Create contract test for detect_logos() API at tests/contract/test_detection_api.py"
Task: "Create integration test for full detection workflow at tests/integration/test_logo_workflow.py"
Task: "Create unit test for frame sampling at tests/unit/test_logo_detector.py"
Task: "Create unit test for confidence scoring at tests/unit/test_logo_detector.py"

# Step 2: Launch all data models together
Task: "Create DetectionResult dataclass in src/data_models.py"
Task: "Create DetectionSession dataclass in src/data_models.py"
Task: "Create DetectionConfig dataclass in src/data_models.py"

# Step 3: Core detection (sequential due to dependencies)
Task: "Create logo detector module at src/logo_detector.py"
Task: "Implement frame sampling function in src/logo_detector.py"
... (continue sequentially)

# Step 4: Launch UI components together after core is done
Task: "Create logo preview widget at src/ui/logo_preview.py"
Task: "Implement bounding box drawing in src/ui/logo_preview.py"
Task: "Add 'Detect Logos' button in src/ui/batch_processor.py"
Task: "Add progress bar in src/ui/batch_processor.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

**Goal**: Deliver a working standalone executable first

1. Complete Phase 1: Setup (T001-T004) → ~1 hour
2. Complete Phase 2: Foundational (T005-T008) → ~2 hours
3. Complete Phase 3: User Story 1 (T009-T025) → ~2-3 days
4. **STOP and VALIDATE**: Build executable, test on clean machine, verify <5s startup
5. Deploy/demo if ready → **MVP Delivered!**

**Value**: Users can now run the app without Python - immediate accessibility improvement

### Incremental Delivery

**Phase 1**: Setup + Foundational → Foundation ready (~3 hours)

**Phase 2**: Add User Story 1 (Executable) → Test independently → Deploy/Demo (~3 days)
- **Value**: Standalone executable working
- **Test**: Copy to machine without Python, launch successfully

**Phase 3**: Add User Story 2 (Detection) → Test independently → Deploy/Demo (~7-10 days)
- **Value**: AI logo detection working
- **Test**: Detect logos in test video, accept region, verify coordinates auto-populated

**Phase 4**: Add User Story 3 (Refinement) → Test independently → Deploy/Demo (~4-6 days)
- **Value**: Profile save/load, sensitivity adjustment
- **Test**: Save profile, reload, verify settings restored

**Phase 5**: Polish → Final validation → Release (~2-3 days)

**Total Estimate**: ~3 weeks for complete implementation

### Parallel Team Strategy

With 2-3 developers:

1. **Week 1**: Everyone completes Setup + Foundational together (~1 day)
   - Then split:
     - Developer A: User Story 1 (Executable) → 3 days
     - Developer B: User Story 2 (Detection core) → 3 days
     - Developer C: User Story 2 (Detection UI) → 3 days (after B completes core)

2. **Week 2**:
   - Developer A: Finish US1, help with US2 integration
   - Developer B + C: Complete US2 integration and testing

3. **Week 3**:
   - Developer A: User Story 3 (Profiles)
   - Developer B: User Story 3 (Sensitivity)
   - Developer C: Polish and documentation

**Benefit**: Parallel work reduces calendar time from 3 weeks to 2 weeks

---

## Checkpoints & Validation

### After Phase 1 (Setup)
- ✅ Packaging directory exists with icon and version info
- ✅ PyInstaller dependency installed
- ✅ All setup tasks complete

### After Phase 2 (Foundational)
- ✅ AppState extended with detection fields
- ✅ Exception hierarchy defined
- ✅ Data models file created
- ✅ FFmpeg path identified
- ✅ Foundation ready for all user stories

### After Phase 3 (US1 - Executable)
- ✅ Build script runs without errors
- ✅ Executable size under 500MB
- ✅ Application launches in <5 seconds
- ✅ Works on machine without Python
- ✅ Single-instance behavior works
- ✅ All existing features functional
- **CHECKPOINT**: MVP ready for release

### After Phase 4 (US2 - Detection)
- ✅ Detection finds logos in test videos
- ✅ Preview shows bounding boxes with confidence
- ✅ Accept/reject workflow works
- ✅ Coordinates auto-populate delogo params
- ✅ Progress bar updates correctly
- ✅ Cancel button stops detection
- ✅ Detection completes in <2 minutes
- ✅ Accuracy ≥80% on test videos
- **CHECKPOINT**: Detection feature ready

### After Phase 5 (US3 - Refinement)
- ✅ Sensitivity slider changes results
- ✅ Profile save creates JSON file
- ✅ Profile load restores settings
- ✅ Profile management UI works
- ✅ Statistics update correctly
- **CHECKPOINT**: All features complete

### After Phase 6 (Polish)
- ✅ Documentation updated
- ✅ Code cleaned and optimized
- ✅ Performance meets targets
- ✅ Security review passed
- ✅ Quickstart validation successful
- **CHECKPOINT**: Ready for production release

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US1 and US2 are independent - can be developed in parallel
- US3 depends on US2 - must be sequential
- Avoid: vague tasks, same file conflicts, breaking existing functionality
- Always test executable on clean machine without Python after US1
- Keep detection logic separate from UI for testability
- Profile JSON format must be human-readable and shareable

---

## Total Task Count

- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 4 tasks (BLOCKING)
- **Phase 3 (US1 - Executable)**: 17 tasks (MVP)
- **Phase 4 (US2 - Detection)**: 39 tasks
- **Phase 5 (US3 - Refinement)**: 37 tasks
- **Phase 6 (Polish)**: 14 tasks

**TOTAL**: 115 tasks

**Parallel Opportunities**: 41 tasks marked [P] can run in parallel within their phases

**MVP Scope**: Phases 1-3 (25 tasks) → Standalone executable working

**Full Feature**: All phases (115 tasks) → Complete with AI detection and profiles
