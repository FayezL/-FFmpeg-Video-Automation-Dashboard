# Tasks: CPU Limiting and Enhanced Processing Options

**Input**: Design documents from `/specs/003-cpu-limit-options/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks are included per constitution Principle V (Testing for Critical Paths). Video processing logic and data integrity operations require automated tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- All paths are relative to repository root: `C:/Users/Administrator/Documents/GitHub/-FFmpeg-Video-Automation-Dashboard/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [ ] T001 Add new dependencies to requirements.txt (psutil>=5.9.0, scipy>=1.9.0, pydantic>=2.0.0)
- [ ] T002 Create settings directory structure at ~/.magictvbox/ or AppData/Local/MagicTVBox/
- [ ] T003 [P] Create detection_profiles/ subdirectory for intro/outro pattern storage
- [ ] T004 [P] Create settings.json template with default ApplicationSettings structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data structures and state extensions that all stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Extend AppState with CPULimitConfig in src/state.py
- [ ] T006 [P] Add CPUMetrics dataclass to src/state.py
- [ ] T007 [P] Add ApplicationSettings Pydantic models to src/state.py
- [ ] T008 [P] Add DetectionProfile and DetectionResult dataclasses to src/state.py
- [ ] T009 Add detection_profiles dictionary and detection_enabled flag to AppState in src/state.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU Usage Control (Priority: P1) 🎯 MVP

**Goal**: Allow users to enable/disable CPU limiting with percentage slider (20-95%) and see real-time CPU usage during processing

**Independent Test**: Enable CPU limiting at 50%, start video processing, monitor that CPU usage stays at or below 50% (±5% variance), and verify UI displays current CPU percentage

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Create test_cpu_limiter.py with test_thread_calculation_ranges in tests/unit/
- [ ] T011 [P] [US1] Add test_cpu_monitoring_accuracy to tests/unit/test_cpu_limiter.py
- [ ] T012 [P] [US1] Add test_priority_setting_cross_platform to tests/unit/test_cpu_limiter.py
- [ ] T013 [P] [US1] Create test_cpu_limited_processing.py integration test in tests/integration/

### Implementation for User Story 1

- [ ] T014 [US1] Create CPULimiter class in src/cpu_limiter.py with calculate_threads() method
- [ ] T015 [US1] Add apply_priority() method to CPULimiter in src/cpu_limiter.py for process priority control
- [ ] T016 [US1] Add start_monitoring() and stop_monitoring() methods to CPULimiter in src/cpu_limiter.py
- [ ] T017 [US1] Add get_current_metrics() method to CPULimiter in src/cpu_limiter.py
- [ ] T018 [US1] Add update_config() method for dynamic CPU limit changes in src/cpu_limiter.py
- [ ] T019 [US1] Integrate CPULimiter into VideoProcessor._process_with_subprocess() in src/video_processor.py
- [ ] T020 [US1] Add CPU limiting UI section to settings panel in src/ui/settings_panel.py
- [ ] T021 [US1] Add real-time CPU meter to single processor UI in src/ui/single_processor.py
- [ ] T022 [US1] Add real-time CPU meter to batch processor UI in src/ui/batch_processor.py
- [ ] T023 [US1] Add CPU limit percentage validation and error handling in src/ui/settings_panel.py
- [ ] T024 [US1] Add logging for CPU limit changes and monitoring metrics in src/cpu_limiter.py

**Checkpoint**: At this point, CPU limiting should be fully functional - users can set limit, processing respects it, UI shows real-time usage

---

## Phase 4: User Story 2 - Enhanced Settings Panel (Priority: P2)

**Goal**: Provide categorized settings panel with Performance, Output, Quality, and Advanced tabs, with at least 15 configurable options that persist across sessions

**Independent Test**: Modify settings in each tab, close and reopen application, verify all settings restored correctly

### Tests for User Story 2

- [ ] T025 [P] [US2] Create test_settings_manager.py with test_save_and_load_cycle in tests/unit/
- [ ] T026 [P] [US2] Add test_validation_rejects_invalid_values to tests/unit/test_settings_manager.py
- [ ] T027 [P] [US2] Add test_migration_from_legacy_format to tests/unit/test_settings_manager.py
- [ ] T028 [P] [US2] Add test_recovery_from_corrupt_json to tests/unit/test_settings_manager.py

### Implementation for User Story 2

- [ ] T029 [P] [US2] Create PerformanceSettings Pydantic model in src/state.py
- [ ] T030 [P] [US2] Create OutputSettings Pydantic model in src/state.py
- [ ] T031 [P] [US2] Create QualitySettings Pydantic model in src/state.py
- [ ] T032 [P] [US2] Create AdvancedSettings Pydantic model in src/state.py
- [ ] T033 [US2] Create SettingsManager class with load() method in src/settings_manager.py
- [ ] T034 [US2] Add save() method with atomic write and backup to SettingsManager in src/settings_manager.py
- [ ] T035 [US2] Add update() method for individual setting changes in src/settings_manager.py
- [ ] T036 [US2] Add migrate_legacy_settings() function for version migration in src/settings_manager.py
- [ ] T037 [US2] Replace existing settings panel with CTkTabview in src/ui/settings_panel.py
- [ ] T038 [US2] Create Performance tab with CPU limiting and parallel jobs settings in src/ui/settings_panel.py
- [ ] T039 [US2] Create Output tab with naming pattern and folder settings in src/ui/settings_panel.py
- [ ] T040 [US2] Create Quality tab with profile and bitrate settings in src/ui/settings_panel.py
- [ ] T041 [US2] Create Advanced tab with FFmpeg params and logging settings in src/ui/settings_panel.py
- [ ] T042 [US2] Add Pydantic validation error display to settings UI in src/ui/settings_panel.py
- [ ] T043 [US2] Integrate SettingsManager into main.py initialization
- [ ] T044 [US2] Update all UI components to read settings from SettingsManager instead of direct AppState

**Checkpoint**: At this point, enhanced settings should be fully functional - users can configure all options, settings persist, validation works

---

## Phase 5: User Story 3 - Intro/Outro Detection (Priority: P3)

**Goal**: Automatically detect intro/outro segments in video files with 85%+ accuracy, display confidence scores, and learn from user corrections

**Independent Test**: Process video with known intro, verify system detects segment with time range and confidence score, user can confirm/correct, subsequent episodes use learned pattern

### Tests for User Story 3

- [ ] T045 [P] [US3] Create test_intro_outro_detector.py with test_perceptual_hash_computation in tests/unit/
- [ ] T046 [P] [US3] Add test_pattern_matching_accuracy to tests/unit/test_intro_outro_detector.py
- [ ] T047 [P] [US3] Add test_confidence_scoring to tests/unit/test_intro_outro_detector.py
- [ ] T048 [P] [US3] Add test_user_correction_learning to tests/unit/test_intro_outro_detector.py
- [ ] T049 [P] [US3] Create test_intro_outro_workflow.py integration test in tests/integration/
- [ ] T050 [P] [US3] Add test_detection_time_under_10_percent to tests/integration/test_intro_outro_workflow.py

### Implementation for User Story 3

- [ ] T051 [P] [US3] Create SegmentPattern dataclass in src/state.py
- [ ] T052 [P] [US3] Add DetectedSegment dataclass to src/state.py
- [ ] T053 [US3] Create IntroOutroDetector class with analyze_video() method in src/intro_outro_detector.py
- [ ] T054 [US3] Add compute_perceptual_hash() method using DCT in src/intro_outro_detector.py
- [ ] T055 [US3] Add _detect_intro() method with frame sampling and hashing in src/intro_outro_detector.py
- [ ] T056 [US3] Add _detect_outro() method with pattern matching in src/intro_outro_detector.py
- [ ] T057 [US3] Add similarity_score() method to SegmentPattern in src/state.py
- [ ] T058 [US3] Add load_profile() and save_profile() methods in src/intro_outro_detector.py
- [ ] T059 [US3] Add learn_from_correction() method to update profiles in src/intro_outro_detector.py
- [ ] T060 [US3] Create intro/outro detection UI panel in src/ui/intro_outro_panel.py
- [ ] T061 [US3] Add detection results display with confidence scores to UI panel
- [ ] T062 [US3] Add user review UI (confirm/correct buttons) to intro_outro_panel.py
- [ ] T063 [US3] Add detection enable/disable checkbox to single processor in src/ui/single_processor.py
- [ ] T064 [US3] Add detection enable/disable checkbox to batch processor in src/ui/batch_processor.py
- [ ] T065 [US3] Integrate detection as optional preprocessing step in VideoProcessor.process_video()
- [ ] T066 [US3] Add FFmpeg -ss and -t parameters for skipping detected segments in src/video_processor.py
- [ ] T067 [US3] Add detection progress indicator to UI in src/ui/intro_outro_panel.py
- [ ] T068 [US3] Add logging for detection results and confidence scores

**Checkpoint**: At this point, intro/outro detection should be fully functional - users can enable detection, review results, correct mistakes, and processing skips confirmed segments

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, error handling improvements, performance optimization

- [ ] T069 [P] Add error handling for psutil PermissionError in src/cpu_limiter.py
- [ ] T070 [P] Add error handling for OpenCV video open failures in src/intro_outro_detector.py
- [ ] T071 [P] Add error handling for corrupt settings.json with backup restoration in src/settings_manager.py
- [ ] T072 [P] Update README.md with new feature documentation
- [ ] T073 [P] Add user guide section for CPU limiting to docs/
- [ ] T074 [P] Add user guide section for enhanced settings to docs/
- [ ] T075 [P] Add user guide section for intro/outro detection to docs/
- [ ] T076 Optimize frame sampling rate for intro/outro detection (target <10% analysis time)
- [ ] T077 Add parallel frame processing for faster detection in src/intro_outro_detector.py
- [ ] T078 Add detection profile caching to reduce redundant analysis
- [ ] T079 Run full integration test suite across all three user stories
- [ ] T080 Perform cross-platform testing (Windows, macOS, Linux) for CPU limiting

---

## Dependencies & Execution Order

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3, 4, 5 can run in PARALLEL
                                              ↓
                                           Phase 6 (Polish)
```

**Independent Stories**:
- ✅ US1 (CPU Limiting) - No dependencies on US2 or US3
- ✅ US2 (Enhanced Settings) - No dependencies on US1 or US3
- ✅ US3 (Intro/Outro Detection) - No dependencies on US1 or US2

**Critical Path**: Phase 1 → Phase 2 → Phase 3 (MVP) → Phase 6

**Parallel Opportunities**:
- After Phase 2, all three user stories (US1, US2, US3) can be developed in parallel by different team members
- Within each user story, tasks marked [P] can run in parallel
- Test tasks (T010-T013, T025-T028, T045-T050) can all run in parallel after Phase 2

### Parallel Execution Examples

**After Phase 2 completes:**

```
Developer A: T014-T024 (US1 - CPU Limiting)
Developer B: T029-T044 (US2 - Enhanced Settings)
Developer C: T051-T068 (US3 - Intro/Outro Detection)
```

**Within US1 (CPU Limiting):**

```
Parallel:
- T010, T011, T012, T013 (all test files, independent)
- T020, T021, T022 (UI updates in different files)

Sequential:
- T014 → T015 → T016 → T017 → T018 (CPULimiter methods build on each other)
- T019 (VideoProcessor integration depends on T014-T018 complete)
```

**Within US2 (Enhanced Settings):**

```
Parallel:
- T025, T026, T027, T028 (all test files, independent)
- T029, T030, T031, T032 (Pydantic models, independent)
- T038, T039, T040, T041 (UI tabs, independent)

Sequential:
- T033 → T034 → T035 → T036 (SettingsManager methods build on each other)
- T037 → T038-T041 (UI tabs depend on TabView creation)
- T043 → T044 (Integration depends on SettingsManager complete)
```

**Within US3 (Intro/Outro Detection):**

```
Parallel:
- T045, T046, T047, T048, T049, T050 (all test files, independent)
- T051, T052 (dataclasses, independent)
- T063, T064 (UI checkboxes in different files)

Sequential:
- T053 → T054 → T055 → T056 (Detector methods build on each other)
- T057 → T058 → T059 (Profile management depends on similarity scoring)
- T060 → T061 → T062 → T067 (UI panel components build on each other)
- T065 → T066 (FFmpeg integration depends on detector complete)
```

---

## Implementation Strategy

### MVP Scope (Recommended First Delivery)

**Phase 3 Only (User Story 1 - CPU Limiting)**:
- Tasks T001-T024 (Setup + Foundational + US1)
- Delivers: Users can limit CPU usage during processing and see real-time metrics
- Testable: Enable 50% limit, process video, verify CPU stays ≤50%
- Value: Immediate improvement to user experience during processing

### Incremental Delivery Path

1. **Sprint 1** (MVP): T001-T024 → Deliver CPU limiting
2. **Sprint 2**: T025-T044 → Deliver enhanced settings
3. **Sprint 3**: T045-T068 → Deliver intro/outro detection
4. **Sprint 4**: T069-T080 → Polish and optimization

Each sprint delivers an independently testable, valuable feature increment.

---

## Task Summary

**Total Tasks**: 80

**Task Breakdown by Phase**:
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 5 tasks
- Phase 3 (US1 - CPU Limiting): 15 tasks (4 tests + 11 implementation)
- Phase 4 (US2 - Enhanced Settings): 20 tasks (4 tests + 16 implementation)
- Phase 5 (US3 - Intro/Outro Detection): 24 tasks (6 tests + 18 implementation)
- Phase 6 (Polish): 12 tasks

**Parallel Opportunities**: 37 tasks marked [P] can run in parallel within their phase

**Independent Test Criteria**:
- US1: Start processing with CPU limit enabled → verify CPU usage ≤ target ± 5%
- US2: Modify settings → restart app → verify settings persisted
- US3: Process video with intro → verify detection shows time range and confidence

**Format Validation**: ✅ All 80 tasks follow strict checklist format with checkbox, ID, optional [P] and [Story] labels, and file paths
