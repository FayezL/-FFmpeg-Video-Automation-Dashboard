# Tasks: Enhanced Workflow & Performance

**Input**: Design documents from `/specs/001-enhanced-workflow/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/interfaces.md

**Tests**: Test tasks included per feature spec requirements

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create templates directory structure at ~/.magictvbox/templates/
- [X] T002 Create batch_states directory structure at ~/.magictvbox/batch_states/
- [X] T003 [P] Update requirements.txt with new dependencies: pytest, pytest-cov
- [X] T004 [P] Create tests/test_templates.py file structure
- [X] T005 [P] Create tests/test_parallel_processor.py file structure
- [X] T006 [P] Create tests/test_hardware_encoders.py file structure
- [X] T007 [P] Create tests/test_video_metadata.py file structure
- [X] T008 [P] Create tests/test_video_filters.py file structure
- [X] T009 [P] Create tests/test_batch_state.py file structure
- [X] T010 [P] Create tests/test_error_handler.py file structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T011 Extend AppState in src/state.py to add current_template field
- [X] T012 Extend AppState in src/state.py to add template_modified field
- [X] T013 Extend AppState in src/state.py to add parallel_config field (ParallelProcessingConfig)
- [X] T014 Extend AppState in src/state.py to add active_processes list
- [X] T015 Extend AppState in src/state.py to add detected_encoders list
- [X] T016 Extend AppState in src/state.py to add use_hardware_encoding field
- [X] T017 Extend AppState in src/state.py to add selected_encoder field
- [X] T018 Extend AppState in src/state.py to add filter_chain field (FilterChain)
- [X] T019 Extend AppState in src/state.py to add _metadata_cache dictionary
- [X] T020 Extend AppState in src/state.py to add current_batch_state field
- [X] T021 Create ParallelProcessingConfig dataclass in src/state.py
- [X] T022 Add calculate_optimal_workers() method to ParallelProcessingConfig in src/state.py
- [X] T023 Add estimate_memory_usage() method to ParallelProcessingConfig in src/state.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Drag-and-Drop File Loading (Priority: P1) 🎯 MVP

**Goal**: Enable users to quickly add videos by dragging files/folders directly onto the application window instead of clicking through file dialogs

**Independent Test**: Drag a folder of 10 videos onto the app window and verify they all appear in the file list with correct metadata. Success = All files load in under 5 seconds with visual feedback during drag.

### Implementation for User Story 1

- [X] T024 [P] [US1] Create DragDropHandler class in src/ui/drag_drop.py with __init__ method
- [X] T025 [P] [US1] Implement enable() method in DragDropHandler at src/ui/drag_drop.py
- [X] T026 [P] [US1] Implement disable() method in DragDropHandler at src/ui/drag_drop.py
- [X] T027 [P] [US1] Implement set_drop_callback() method in DragDropHandler at src/ui/drag_drop.py
- [X] T028 [US1] Implement filter_video_files() method with folder recursion in DragDropHandler at src/ui/drag_drop.py
- [X] T029 [US1] Implement _handle_drag_enter() internal method for visual feedback in src/ui/drag_drop.py
- [X] T030 [US1] Implement _handle_drag_leave() internal method in src/ui/drag_drop.py
- [X] T031 [US1] Implement _handle_drop() internal method with file path parsing in src/ui/drag_drop.py
- [X] T032 [US1] Add drag-drop zone initialization in BatchProcessor.__init__ at src/ui/batch_processor.py
- [X] T033 [US1] Add _on_files_dropped() callback method in BatchProcessor at src/ui/batch_processor.py
- [X] T034 [US1] Add visual highlight CSS/styling for drag-over state in BatchProcessor at src/ui/batch_processor.py
- [X] T035 [US1] Add duplicate file detection logic in BatchProcessor._on_files_dropped() at src/ui/batch_processor.py
- [X] T036 [US1] Add user warning dialog for duplicate files in src/ui/batch_processor.py
- [X] T037 [US1] Update file list display to show dropped files in src/ui/batch_processor.py
- [X] T038 [US1] Add fallback file dialog button if drag-drop unavailable in src/ui/batch_processor.py

**Tests for User Story 1**

- [X] T039 [P] [US1] Unit test for filter_video_files() with mixed file types in tests/test_drag_drop.py
- [X] T040 [P] [US1] Unit test for filter_video_files() with folder recursion in tests/test_drag_drop.py
- [X] T041 [P] [US1] Unit test for duplicate file detection in tests/test_drag_drop.py
- [ ] T042 [P] [US1] Integration test: drag 5 files, verify all appear in queue in tests/test_drag_drop.py
- [ ] T043 [P] [US1] Integration test: drag folder with 20 videos, verify recursive scan in tests/test_drag_drop.py

**Checkpoint**: At this point, User Story 1 should be fully functional - drag-drop works with visual feedback

---

## Phase 4: User Story 2 - Parallel Batch Processing (Priority: P1) 🎯 MVP

**Goal**: Enable simultaneous processing of 2-4 videos to reduce total batch time by 60-75% on multi-core systems

**Independent Test**: Process a batch of 20 short videos (1 minute each) and verify total completion time is ~25% of serial processing time. Verify all videos complete successfully.

### Implementation for User Story 2

- [ ] T044 [P] [US2] Create ParallelProcessor class in src/parallel_processor.py with __init__ method
- [ ] T045 [P] [US2] Implement process_batch() method in ParallelProcessor at src/parallel_processor.py
- [ ] T046 [P] [US2] Implement stop() method with graceful shutdown in ParallelProcessor at src/parallel_processor.py
- [ ] T047 [P] [US2] Implement is_processing() method in ParallelProcessor at src/parallel_processor.py
- [ ] T048 [P] [US2] Implement get_active_count() method in ParallelProcessor at src/parallel_processor.py
- [ ] T049 [P] [US2] Implement get_queue_size() method in ParallelProcessor at src/parallel_processor.py
- [ ] T050 [US2] Implement _worker_thread() internal method for encoding in src/parallel_processor.py
- [ ] T051 [US2] Implement _queue_manager() internal method for worker dispatch in src/parallel_processor.py
- [ ] T052 [US2] Add thread-safe file queue management in src/parallel_processor.py
- [ ] T053 [US2] Add FFmpeg subprocess termination logic in ParallelProcessor.stop() at src/parallel_processor.py
- [ ] T054 [US2] Add progress tracking for multiple active files in src/parallel_processor.py
- [ ] T055 [US2] Update VideoProcessor to support parallel execution mode at src/video_processor.py
- [ ] T056 [US2] Add process_id parameter to VideoProcessor.process_video() at src/video_processor.py
- [ ] T057 [US2] Update BatchProcessor to use ParallelProcessor instead of serial loop at src/ui/batch_processor.py
- [ ] T058 [US2] Add parallelism slider (1-8 workers) to SettingsPanel at src/ui/settings_panel.py
- [ ] T059 [US2] Add auto-adjust checkbox for optimal worker count in SettingsPanel at src/ui/settings_panel.py
- [ ] T060 [US2] Update batch progress UI to show multiple active files in src/ui/batch_processor.py
- [ ] T061 [US2] Add individual progress bars for each active file in src/ui/batch_processor.py
- [ ] T062 [US2] Update Stop button to terminate all workers in src/ui/batch_processor.py
- [ ] T063 [US2] Add worker count display (e.g., "Processing 3 of 20 files") in src/ui/batch_processor.py

**Tests for User Story 2**

- [ ] T064 [P] [US2] Unit test for calculate_optimal_workers() with various CPU counts in tests/test_parallel_processor.py
- [ ] T065 [P] [US2] Unit test for queue management (add files while processing) in tests/test_parallel_processor.py
- [ ] T066 [P] [US2] Unit test for graceful stop with timeout in tests/test_parallel_processor.py
- [ ] T067 [P] [US2] Integration test: process 10 files with 2 workers, verify parallelism in tests/test_parallel_processor.py
- [ ] T068 [P] [US2] Integration test: measure speedup vs serial processing in tests/test_parallel_processor.py
- [ ] T069 [P] [US2] Integration test: stop processing mid-batch, verify clean shutdown in tests/test_parallel_processor.py

**Checkpoint**: At this point, User Story 2 should be fully functional - parallel processing works with configurable workers

---

## Phase 5: User Story 3 - Configuration Presets & Templates (Priority: P1) 🎯 MVP

**Goal**: Enable users to save/load processing settings as named templates to eliminate repetitive configuration

**Independent Test**: Configure trim settings + profile, save as "Meeting Clips" template, close app, reopen, load template, and verify all settings restore correctly. Success = Configuration restored in under 5 seconds.

### Implementation for User Story 3

- [ ] T070 [P] [US3] Create Template dataclass in src/templates.py with all fields from data-model.md
- [ ] T071 [P] [US3] Implement Template.to_dict() serialization method in src/templates.py
- [ ] T072 [P] [US3] Implement Template.from_dict() deserialization method in src/templates.py
- [ ] T073 [P] [US3] Create TemplateManager class in src/templates.py with __init__ method
- [ ] T074 [P] [US3] Implement save_template() method in TemplateManager at src/templates.py
- [ ] T075 [P] [US3] Implement load_template() method in TemplateManager at src/templates.py
- [ ] T076 [P] [US3] Implement list_templates() method in TemplateManager at src/templates.py
- [ ] T077 [P] [US3] Implement delete_template() method in TemplateManager at src/templates.py
- [ ] T078 [P] [US3] Implement template_exists() method in TemplateManager at src/templates.py
- [ ] T079 [P] [US3] Implement export_template() method in TemplateManager at src/templates.py
- [ ] T080 [P] [US3] Implement import_template() method in TemplateManager at src/templates.py
- [ ] T081 [US3] Add template name validation (_is_valid_name) in TemplateManager at src/templates.py
- [ ] T082 [US3] Add atomic write (temp file + rename) for template saves in src/templates.py
- [ ] T083 [US3] Add template dropdown selector to BatchProcessor UI at src/ui/batch_processor.py
- [ ] T084 [US3] Add "Save as Template" button to BatchProcessor at src/ui/batch_processor.py
- [ ] T085 [US3] Add "Update Template" button (enabled when template loaded) to BatchProcessor at src/ui/batch_processor.py
- [ ] T086 [US3] Add template name input dialog for save operation in src/ui/batch_processor.py
- [ ] T087 [US3] Implement _save_current_as_template() method in BatchProcessor at src/ui/batch_processor.py
- [ ] T088 [US3] Implement _load_template() method to restore settings in BatchProcessor at src/ui/batch_processor.py
- [ ] T089 [US3] Add asterisk (*) indicator when settings differ from loaded template in src/ui/batch_processor.py
- [ ] T090 [US3] Add template dropdown selector to SingleProcessor UI at src/ui/single_processor.py
- [ ] T091 [US3] Implement _load_template() method in SingleProcessor at src/ui/single_processor.py
- [ ] T092 [US3] Add template preview tooltip (shows key settings) in src/ui/batch_processor.py
- [ ] T093 [US3] Add template management dialog (list, delete, export/import) in src/ui/batch_processor.py

**Tests for User Story 3**

- [ ] T094 [P] [US3] Unit test for Template.to_dict() and from_dict() round-trip in tests/test_templates.py
- [ ] T095 [P] [US3] Unit test for template name validation with invalid characters in tests/test_templates.py
- [ ] T096 [P] [US3] Unit test for save_template() with atomic write in tests/test_templates.py
- [ ] T097 [P] [US3] Unit test for load_template() with missing file raises FileNotFoundError in tests/test_templates.py
- [ ] T098 [P] [US3] Unit test for list_templates() returns sorted list in tests/test_templates.py
- [ ] T099 [P] [US3] Integration test: save template, close app, load template, verify settings match in tests/test_templates.py
- [ ] T100 [P] [US3] Integration test: modify loaded template, verify asterisk appears in tests/test_templates.py

**Checkpoint**: At this point, User Story 3 should be fully functional - templates save/load correctly

---

## Phase 6: User Story 4 - Hardware-Accelerated Encoding (Priority: P2)

**Goal**: Enable users with GPU hardware to use hardware encoding for 5-20x faster processing

**Independent Test**: On a system with NVIDIA GPU, select "GPU Accelerated" profile and verify FFmpeg uses h264_nvenc encoder and encoding completes 10x faster than CPU. Success = GPU profile appears only on compatible systems.

### Implementation for User Story 4

- [ ] T101 [P] [US4] Create HardwareEncoder dataclass in src/hardware_encoders.py with all fields from data-model.md
- [ ] T102 [P] [US4] Implement get_codec_for_profile() method in HardwareEncoder at src/hardware_encoders.py
- [ ] T103 [P] [US4] Implement create_gpu_profile_variant() method in HardwareEncoder at src/hardware_encoders.py
- [ ] T104 [P] [US4] Create HardwareEncoderDetector class in src/hardware_encoders.py with __init__ method
- [ ] T105 [P] [US4] Implement detect_encoders() method in HardwareEncoderDetector at src/hardware_encoders.py
- [ ] T106 [US4] Add FFmpeg encoder parsing logic (_parse_encoders_output) in src/hardware_encoders.py
- [ ] T107 [US4] Add encoder-specific detection (NVENC, QuickSync, AMF, VideoToolbox) in src/hardware_encoders.py
- [ ] T108 [US4] Implement test_encoder() method with 1-second test encode in src/hardware_encoders.py
- [ ] T109 [US4] Implement create_gpu_profiles() method in HardwareEncoderDetector at src/hardware_encoders.py
- [ ] T110 [US4] Implement get_recommended_encoder() method with priority ranking in src/hardware_encoders.py
- [ ] T111 [US4] Add GPU encoder detection on app startup in main.py
- [ ] T112 [US4] Store detected encoders in AppState at main.py
- [ ] T113 [US4] Add GPU profile variants to profile selector in SettingsPanel at src/ui/settings_panel.py
- [ ] T114 [US4] Add GPU encoder status display (e.g., "NVIDIA NVENC detected") in SettingsPanel at src/ui/settings_panel.py
- [ ] T115 [US4] Add tooltip for GPU profiles explaining hardware requirements in src/ui/settings_panel.py
- [ ] T116 [US4] Hide GPU profiles if no compatible hardware detected in src/ui/settings_panel.py
- [ ] T117 [US4] Update VideoProcessor to use hardware encoder codec when GPU profile selected at src/video_processor.py
- [ ] T118 [US4] Add fallback to CPU encoding if GPU encoding fails in src/video_processor.py
- [ ] T119 [US4] Add GPU encoding failure detection and warning log in src/video_processor.py

**Tests for User Story 4**

- [ ] T120 [P] [US4] Unit test for _parse_encoders_output() with sample FFmpeg output in tests/test_hardware_encoders.py
- [ ] T121 [P] [US4] Unit test for get_recommended_encoder() priority ranking in tests/test_hardware_encoders.py
- [ ] T122 [P] [US4] Unit test for create_gpu_profile_variant() codec substitution in tests/test_hardware_encoders.py
- [ ] T123 [P] [US4] Integration test: detect encoders on test system in tests/test_hardware_encoders.py
- [ ] T124 [P] [US4] Integration test: GPU encoding with fallback to CPU on failure in tests/test_hardware_encoders.py

**Checkpoint**: At this point, User Story 4 should be fully functional - GPU encoding works with auto-fallback

---

## Phase 7: User Story 5 - Video Preview & Metadata Validation (Priority: P2)

**Goal**: Display video metadata (duration, resolution, codec) before processing and enable quick preview to catch issues early

**Independent Test**: Add a 4K video to queue and verify UI displays "3840x2160, H.264, 2.5GB, 12:34 duration". Select 1080p profile and verify warning appears: "Video will be downscaled". Right-click file and preview first 5 seconds.

### Implementation for User Story 5

- [ ] T125 [P] [US5] Create VideoMetadata dataclass in src/video_metadata.py with all fields from data-model.md
- [ ] T126 [P] [US5] Implement exceeds_resolution() method in VideoMetadata at src/video_metadata.py
- [ ] T127 [P] [US5] Implement get_resolution_string() method in VideoMetadata at src/video_metadata.py
- [ ] T128 [P] [US5] Implement get_file_size_mb() method in VideoMetadata at src/video_metadata.py
- [ ] T129 [P] [US5] Implement get_duration_string() method in VideoMetadata at src/video_metadata.py
- [ ] T130 [P] [US5] Create VideoMetadataExtractor class in src/video_metadata.py with __init__ method
- [ ] T131 [US5] Implement extract_metadata() method using ffprobe in src/video_metadata.py
- [ ] T132 [US5] Add LRU cache implementation for metadata results in src/video_metadata.py
- [ ] T133 [US5] Implement validate_against_profile() method in VideoMetadataExtractor at src/video_metadata.py
- [ ] T134 [US5] Add resolution limit validation logic in src/video_metadata.py
- [ ] T135 [US5] Add codec compatibility validation in src/video_metadata.py
- [ ] T136 [US5] Implement clear_cache() method in VideoMetadataExtractor at src/video_metadata.py
- [ ] T137 [US5] Implement get_cache_stats() method in VideoMetadataExtractor at src/video_metadata.py
- [ ] T138 [US5] Create PreviewModal class in src/ui/preview_modal.py for video preview
- [ ] T139 [US5] Implement show_preview() method with 5-second clip playback in src/ui/preview_modal.py
- [ ] T140 [US5] Add FFmpeg subprocess for preview clip extraction in src/ui/preview_modal.py
- [ ] T141 [US5] Update BatchProcessor to extract metadata on file add at src/ui/batch_processor.py
- [ ] T142 [US5] Update file list to display duration, resolution, codec, file size in src/ui/batch_processor.py
- [ ] T143 [US5] Add validation warning icons next to files in BatchProcessor at src/ui/batch_processor.py
- [ ] T144 [US5] Add tooltip showing validation warnings on hover in src/ui/batch_processor.py
- [ ] T145 [US5] Add "Validate All" button to BatchProcessor UI at src/ui/batch_processor.py
- [ ] T146 [US5] Add right-click context menu with "Preview" option in src/ui/batch_processor.py
- [ ] T147 [US5] Implement _on_preview_file() callback to open PreviewModal in src/ui/batch_processor.py
- [ ] T148 [US5] Add error status for corrupted/unreadable files in src/ui/batch_processor.py

**Tests for User Story 5**

- [ ] T149 [P] [US5] Unit test for extract_metadata() with valid video file in tests/test_video_metadata.py
- [ ] T150 [P] [US5] Unit test for extract_metadata() with corrupted file raises ValueError in tests/test_video_metadata.py
- [ ] T151 [P] [US5] Unit test for validate_against_profile() with 4K video and 1080p profile in tests/test_video_metadata.py
- [ ] T152 [P] [US5] Unit test for LRU cache eviction after 1000 entries in tests/test_video_metadata.py
- [ ] T153 [P] [US5] Integration test: add file, verify metadata appears in UI in tests/test_video_metadata.py
- [ ] T154 [P] [US5] Integration test: preview video, verify 5-second clip plays in tests/test_video_metadata.py

**Checkpoint**: At this point, User Story 5 should be fully functional - metadata and preview work

---

## Phase 8: User Story 6 - Additional Video Filters (Priority: P3)

**Goal**: Provide additional video transformation filters beyond delogo (rotate, crop, scale, brightness/contrast, saturation, deinterlace)

**Independent Test**: Enable "Brightness +20%" filter, process a video, and verify the output is visibly brighter. Chain multiple filters (Rotate 90° + Crop + Brightness) and verify all apply correctly in order.

### Implementation for User Story 6

- [ ] T155 [P] [US6] Create VideoFilter dataclass in src/video_filters.py
- [ ] T156 [P] [US6] Implement to_ffmpeg_string() method for rotate filter in VideoFilter at src/video_filters.py
- [ ] T157 [P] [US6] Implement to_ffmpeg_string() method for crop filter in VideoFilter at src/video_filters.py
- [ ] T158 [P] [US6] Implement to_ffmpeg_string() method for scale filter in VideoFilter at src/video_filters.py
- [ ] T159 [P] [US6] Implement to_ffmpeg_string() method for brightness filter in VideoFilter at src/video_filters.py
- [ ] T160 [P] [US6] Implement to_ffmpeg_string() method for contrast filter in VideoFilter at src/video_filters.py
- [ ] T161 [P] [US6] Implement to_ffmpeg_string() method for saturation filter in VideoFilter at src/video_filters.py
- [ ] T162 [P] [US6] Implement to_ffmpeg_string() method for deinterlace filter in VideoFilter at src/video_filters.py
- [ ] T163 [P] [US6] Implement to_ffmpeg_string() method for delogo filter in VideoFilter at src/video_filters.py
- [ ] T164 [P] [US6] Create FilterChain dataclass in src/video_filters.py
- [ ] T165 [US6] Implement add_filter() method in FilterChain at src/video_filters.py
- [ ] T166 [US6] Implement to_ffmpeg_string() with fixed filter ordering in FilterChain at src/video_filters.py
- [ ] T167 [US6] Implement is_empty() method in FilterChain at src/video_filters.py
- [ ] T168 [US6] Create FilterChainBuilder class in src/video_filters.py
- [ ] T169 [US6] Implement build_filter_string() static method in FilterChainBuilder at src/video_filters.py
- [ ] T170 [US6] Implement validate_filter_params() static method in FilterChainBuilder at src/video_filters.py
- [ ] T171 [US6] Implement get_filter_defaults() static method in FilterChainBuilder at src/video_filters.py
- [ ] T172 [US6] Add "Video Filters" collapsible section to BatchProcessor UI at src/ui/batch_processor.py
- [ ] T173 [US6] Add Rotate filter controls (90/180/270 dropdown) in src/ui/batch_processor.py
- [ ] T174 [US6] Add Crop filter controls (top/bottom/left/right spinboxes) in src/ui/batch_processor.py
- [ ] T175 [US6] Add Scale filter controls (width/height input) in src/ui/batch_processor.py
- [ ] T176 [US6] Add Brightness slider (-1.0 to 1.0) in src/ui/batch_processor.py
- [ ] T177 [US6] Add Contrast slider (0.0 to 3.0) in src/ui/batch_processor.py
- [ ] T178 [US6] Add Saturation slider (0.0 to 3.0) in src/ui/batch_processor.py
- [ ] T179 [US6] Add Deinterlace checkbox in src/ui/batch_processor.py
- [ ] T180 [US6] Update existing delogo controls to integrate with filter system in src/ui/batch_processor.py
- [ ] T181 [US6] Add enable/disable checkboxes for each filter in src/ui/batch_processor.py
- [ ] T182 [US6] Update VideoProcessor to apply filter chain from AppState at src/video_processor.py
- [ ] T183 [US6] Integrate FilterChain.to_ffmpeg_string() into FFmpeg command building in src/video_processor.py

**Tests for User Story 6**

- [ ] T184 [P] [US6] Unit test for VideoFilter.to_ffmpeg_string() for each filter type in tests/test_video_filters.py
- [ ] T185 [P] [US6] Unit test for FilterChain.to_ffmpeg_string() with multiple filters in tests/test_video_filters.py
- [ ] T186 [P] [US6] Unit test for filter ordering (rotate→crop→scale→color) in tests/test_video_filters.py
- [ ] T187 [P] [US6] Unit test for validate_filter_params() with invalid values in tests/test_video_filters.py
- [ ] T188 [P] [US6] Integration test: apply brightness filter, verify output is brighter in tests/test_video_filters.py
- [ ] T189 [P] [US6] Integration test: chain 3 filters, verify all apply in order in tests/test_video_filters.py

**Checkpoint**: At this point, User Story 6 should be fully functional - filters apply correctly

---

## Phase 9: User Story 7 - Resume Failed Batch Processing (Priority: P3)

**Goal**: Enable users to resume interrupted batches from where they left off instead of restarting

**Independent Test**: Start a 20-file batch, stop after 8 complete, close app, reopen, and verify prompt "Resume previous batch? (8 of 20 completed)". Resume and verify processing continues from file 9.

### Implementation for User Story 7

- [ ] T190 [P] [US7] Create BatchState dataclass in src/batch_state.py with all fields from data-model.md
- [ ] T191 [P] [US7] Implement to_dict() serialization method in BatchState at src/batch_state.py
- [ ] T192 [P] [US7] Implement from_dict() deserialization method in BatchState at src/batch_state.py
- [ ] T193 [P] [US7] Implement is_complete() method in BatchState at src/batch_state.py
- [ ] T194 [P] [US7] Implement get_pending_files() method in BatchState at src/batch_state.py
- [ ] T195 [P] [US7] Create BatchStateManager class in src/batch_state.py with __init__ method
- [ ] T196 [P] [US7] Implement create_batch() method in BatchStateManager at src/batch_state.py
- [ ] T197 [P] [US7] Implement save_checkpoint() method in BatchStateManager at src/batch_state.py
- [ ] T198 [P] [US7] Implement load_batch() method in BatchStateManager at src/batch_state.py
- [ ] T199 [P] [US7] Implement find_incomplete_batches() method in BatchStateManager at src/batch_state.py
- [ ] T200 [P] [US7] Implement delete_batch() method in BatchStateManager at src/batch_state.py
- [ ] T201 [US7] Implement verify_output_files() method in BatchStateManager at src/batch_state.py
- [ ] T202 [US7] Add checkpoint saving after each file completion in ParallelProcessor at src/parallel_processor.py
- [ ] T203 [US7] Add batch state initialization when processing starts in src/ui/batch_processor.py
- [ ] T204 [US7] Add incomplete batch detection on app startup in main.py
- [ ] T205 [US7] Create resume batch dialog with (X of Y completed) message in src/ui/batch_processor.py
- [ ] T206 [US7] Add "Resume" and "Start New" buttons to resume dialog in src/ui/batch_processor.py
- [ ] T207 [US7] Implement _resume_batch() method in BatchProcessor at src/ui/batch_processor.py
- [ ] T208 [US7] Add settings mismatch detection (compare current vs snapshot) in src/ui/batch_processor.py
- [ ] T209 [US7] Add settings choice dialog if mismatch detected in src/ui/batch_processor.py
- [ ] T210 [US7] Add output file verification before skipping completed files in src/ui/batch_processor.py
- [ ] T211 [US7] Add batch state cleanup on successful completion in src/ui/batch_processor.py

**Tests for User Story 7**

- [ ] T212 [P] [US7] Unit test for BatchState.is_complete() with various states in tests/test_batch_state.py
- [ ] T213 [P] [US7] Unit test for BatchState.get_pending_files() in tests/test_batch_state.py
- [ ] T214 [P] [US7] Unit test for save_checkpoint() and load_batch() round-trip in tests/test_batch_state.py
- [ ] T215 [P] [US7] Unit test for find_incomplete_batches() returns sorted results in tests/test_batch_state.py
- [ ] T216 [P] [US7] Integration test: interrupt batch, restart app, verify resume prompt in tests/test_batch_state.py
- [ ] T217 [P] [US7] Integration test: resume batch, verify skips completed files in tests/test_batch_state.py

**Checkpoint**: At this point, User Story 7 should be fully functional - batch resume works correctly

---

## Phase 10: User Story 8 - Smart Error Messages & Recovery (Priority: P3)

**Goal**: Parse FFmpeg errors into user-friendly messages with suggested fixes instead of raw technical output

**Independent Test**: Attempt to encode with GPU profile when NVENC drivers are missing. Verify error message says "GPU encoding unavailable. Please update NVIDIA drivers or use a CPU profile." with clickable action buttons.

### Implementation for User Story 8

- [ ] T218 [P] [US8] Create ErrorMessageParser class in src/error_handler.py
- [ ] T219 [P] [US8] Implement parse_ffmpeg_error() static method in ErrorMessageParser at src/error_handler.py
- [ ] T220 [US8] Add GPU unavailable error pattern and user message in src/error_handler.py
- [ ] T221 [US8] Add corrupted file error pattern and user message in src/error_handler.py
- [ ] T222 [US8] Add insufficient disk space error pattern and user message in src/error_handler.py
- [ ] T223 [US8] Add missing codec error pattern and user message in src/error_handler.py
- [ ] T224 [US8] Add GPU out of memory error pattern and user message in src/error_handler.py
- [ ] T225 [US8] Add invalid resolution error pattern and user message in src/error_handler.py
- [ ] T226 [US8] Implement get_known_error_patterns() static method in ErrorMessageParser at src/error_handler.py
- [ ] T227 [US8] Implement extract_relevant_output() static method in ErrorMessageParser at src/error_handler.py
- [ ] T228 [US8] Add fallback generic message for unknown error patterns in src/error_handler.py
- [ ] T229 [US8] Create ErrorDialog class in src/ui/error_dialog.py
- [ ] T230 [US8] Add user-friendly message display in ErrorDialog at src/ui/error_dialog.py
- [ ] T231 [US8] Add "Show Details" expandable section for raw FFmpeg output in src/ui/error_dialog.py
- [ ] T232 [US8] Add action buttons (Retry, Skip File, Choose Different Profile) in src/ui/error_dialog.py
- [ ] T233 [US8] Implement action button callbacks in ErrorDialog at src/ui/error_dialog.py
- [ ] T234 [US8] Update VideoProcessor to use ErrorMessageParser on FFmpeg failures at src/video_processor.py
- [ ] T235 [US8] Update ParallelProcessor to display ErrorDialog on file failure at src/parallel_processor.py
- [ ] T236 [US8] Add error logging to LogsPanel with timestamp in src/ui/logs_panel.py
- [ ] T237 [US8] Add error count summary in BatchProcessor status bar in src/ui/batch_processor.py

**Tests for User Story 8**

- [ ] T238 [P] [US8] Unit test for parse_ffmpeg_error() with GPU unavailable output in tests/test_error_handler.py
- [ ] T239 [P] [US8] Unit test for parse_ffmpeg_error() with disk full output in tests/test_error_handler.py
- [ ] T240 [P] [US8] Unit test for parse_ffmpeg_error() with corrupted file output in tests/test_error_handler.py
- [ ] T241 [P] [US8] Unit test for parse_ffmpeg_error() with unknown error falls back to generic in tests/test_error_handler.py
- [ ] T242 [P] [US8] Unit test for extract_relevant_output() truncates to max lines in tests/test_error_handler.py
- [ ] T243 [P] [US8] Integration test: trigger GPU error, verify user-friendly message appears in tests/test_error_handler.py

**Checkpoint**: At this point, User Story 8 should be fully functional - errors show helpful messages

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T244 [P] Update README.md with new features documentation
- [ ] T245 [P] Update quickstart.md with setup instructions for new dependencies
- [ ] T246 [P] Add inline code comments for complex logic in ParallelProcessor
- [ ] T247 [P] Add inline code comments for filter chain building in FilterChainBuilder
- [ ] T248 [P] Add docstrings for all public methods in TemplateManager
- [ ] T249 [P] Add docstrings for all public methods in HardwareEncoderDetector
- [ ] T250 [P] Add docstrings for all public methods in VideoMetadataExtractor
- [ ] T251 [P] Add docstrings for all public methods in BatchStateManager
- [ ] T252 [P] Add docstrings for all public methods in ErrorMessageParser
- [ ] T253 Performance benchmark: measure parallel processing speedup with 2/4/8 workers
- [ ] T254 Performance benchmark: measure hardware encoding speedup vs CPU
- [ ] T255 Performance benchmark: measure template load time
- [ ] T256 Performance benchmark: measure metadata extraction time for 100 files
- [ ] T257 Memory profiling: verify no leaks in 100+ file batches
- [ ] T258 Memory profiling: verify metadata cache eviction works correctly
- [ ] T259 Code cleanup: remove debug print statements across all new files
- [ ] T260 Code cleanup: consistent error handling patterns across services
- [ ] T261 UI polish: consistent button styling across all dialogs
- [ ] T262 UI polish: consistent error message formatting
- [ ] T263 UI polish: keyboard shortcuts for common actions (Ctrl+S for save template)
- [ ] T264 Security: validate template JSON to prevent code injection
- [ ] T265 Security: sanitize file paths to prevent directory traversal
- [ ] T266 Run full test suite with coverage report (target 80%+)
- [ ] T267 Manual testing: drag-drop on Windows
- [ ] T268 Manual testing: drag-drop on macOS
- [ ] T269 Manual testing: parallel processing with 1/2/4/8 workers
- [ ] T270 Manual testing: hardware encoding on NVIDIA GPU system
- [ ] T271 Manual testing: hardware encoding fallback when GPU fails
- [ ] T272 Manual testing: template save/load across app restarts
- [ ] T273 Manual testing: batch resume after crash
- [ ] T274 Manual testing: all filter types apply correctly
- [ ] T275 Manual testing: error messages for all common failure scenarios
- [ ] T276 Validate quickstart.md by having fresh developer follow it

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-10)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1) - Drag-Drop**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1) - Parallel Processing**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P1) - Templates**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P2) - Hardware Encoding**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 5 (P2) - Metadata/Preview**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 6 (P3) - Filters**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 7 (P3) - Batch Resume**: Depends on US2 (Parallel Processing) being complete
- **User Story 8 (P3) - Error Messages**: Can start after Foundational (Phase 2) - Works across all stories

### Within Each User Story

- Tests can be written in parallel with implementation (or before, if TDD)
- Models/dataclasses before services
- Services before UI integration
- Core implementation before integration with other stories
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003-T010)
- All Foundational state extension tasks (T011-T023) can run in parallel
- Once Foundational phase completes, US1, US2, US3 can all start in parallel (if team capacity allows)
- US4, US5, US6 can start in parallel after Foundational
- Within each story, tasks marked [P] can run in parallel (different files)
- All test tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1 (Drag-Drop)

```bash
# After Foundational phase completes, launch these in parallel:

# Group 1: Core DragDropHandler methods (all in same file, sequential)
T024 → T025 → T026 → T027 → T028 → T029 → T030 → T031

# Group 2: BatchProcessor integration (same file, sequential)
T032 → T033 → T034 → T035 → T036 → T037 → T038

# Group 3: Tests (different file, can start in parallel with implementation)
T039, T040, T041, T042, T043 (all parallel)
```

---

## Parallel Example: User Story 2 (Parallel Processing)

```bash
# After Foundational phase completes, launch these in parallel:

# Group 1: ParallelProcessor service (src/parallel_processor.py, sequential within file)
T044 → T045 → T046 → T047 → T048 → T049 → T050 → T051 → T052 → T053 → T054

# Group 2: VideoProcessor updates (src/video_processor.py, parallel with Group 1)
T055 → T056

# Group 3: BatchProcessor UI (src/ui/batch_processor.py, parallel with Group 1)
T057 → T060 → T061 → T062 → T063

# Group 4: SettingsPanel UI (src/ui/settings_panel.py, parallel with all above)
T058 → T059

# Group 5: Tests (tests/test_parallel_processor.py, parallel with all above)
T064, T065, T066, T067, T068, T069 (all parallel)
```

---

## Parallel Example: Phase 2 (Foundational) - All Stories Can Start After This

```bash
# All Foundational tasks can run in parallel (different aspects of AppState):
T011 (current_template) [P]
T012 (template_modified) [P]
T013 (parallel_config) [P]
T014 (active_processes) [P]
T015 (detected_encoders) [P]
T016 (use_hardware_encoding) [P]
T017 (selected_encoder) [P]
T018 (filter_chain) [P]
T019 (_metadata_cache) [P]
T020 (current_batch_state) [P]
T021 (ParallelProcessingConfig dataclass) [P]
T022 (calculate_optimal_workers) [P]
T023 (estimate_memory_usage) [P]

# Once ALL of these complete, US1-US8 can start in parallel
```

---

## Implementation Strategy

### MVP First (User Stories 1, 2, 3 Only - All P1)

This delivers the most critical features first:

1. **Phase 1: Setup** (T001-T010)
2. **Phase 2: Foundational** (T011-T023) - CRITICAL BLOCKER
3. **Phase 3: US1 - Drag-Drop** (T024-T043) - Modern file selection
4. **Phase 4: US2 - Parallel Processing** (T044-T069) - 60-75% speedup
5. **Phase 5: US3 - Templates** (T070-T100) - Eliminate repetitive config

**STOP and VALIDATE**: At this point, the MVP is complete with:
- Drag-drop file loading (saves 30+ seconds per batch)
- Parallel processing (60-75% time reduction)
- Templates (saves 2-3 minutes per session)

This MVP delivers immediate, measurable value to all users.

### Incremental Delivery (Add P2 Features)

After MVP validation, add P2 features:

6. **Phase 6: US4 - Hardware Encoding** (T101-T124) - 5-20x speedup for GPU users
7. **Phase 7: US5 - Metadata/Preview** (T125-T154) - Catch issues before processing

**VALIDATE**: Core features + performance enhancements complete

### Full Feature Set (Add P3 Features)

Finally, add nice-to-have P3 features:

8. **Phase 8: US6 - Video Filters** (T155-T189) - Additional transformations
9. **Phase 9: US7 - Batch Resume** (T190-T217) - Recovery from interruptions
10. **Phase 10: US8 - Error Messages** (T218-T243) - Better troubleshooting

11. **Phase 11: Polish** (T244-T276) - Documentation, testing, optimization

### Parallel Team Strategy

With multiple developers (e.g., 3 developers):

1. **All team members**: Complete Phase 1 (Setup) and Phase 2 (Foundational) together
2. **Once Foundational is done**, split work:
   - **Developer A**: User Story 1 (Drag-Drop) - T024-T043
   - **Developer B**: User Story 2 (Parallel Processing) - T044-T069
   - **Developer C**: User Story 3 (Templates) - T070-T100
3. **After MVP stories complete**, proceed to P2 stories:
   - **Developer A**: User Story 4 (Hardware Encoding) - T101-T124
   - **Developer B**: User Story 5 (Metadata/Preview) - T125-T154
   - **Developer C**: Start P3 stories or help with testing
4. **Final phase**: All team members work on Polish together

**Key advantage**: Each user story is independent, so developers can work in parallel without merge conflicts or blocking each other.

---

## MVP Recommendation

**Minimum Viable Product**: User Stories 1, 2, 3 (All P1)

**Rationale**:
- **US1 (Drag-Drop)**: Addresses the most common user interaction (file selection) - saves 30+ seconds per session
- **US2 (Parallel Processing)**: Addresses the biggest performance bottleneck - reduces batch time by 60-75%
- **US3 (Templates)**: Addresses repetitive configuration - saves 2-3 minutes per session

**Combined Impact**: An active user processing 3 batches per week sees:
- 90+ seconds saved per week on file selection
- 10+ hours saved per month on batch processing
- 6+ minutes saved per week on configuration

**Timeline**: MVP can be completed in 4-5 weeks with 1 developer, or 2-3 weeks with 3 developers working in parallel.

**Post-MVP**: Add P2 features (US4, US5) for hardware acceleration and quality-of-life improvements, then P3 features (US6, US7, US8) as nice-to-haves.

---

## Task Summary Statistics

- **Total Tasks**: 276
- **Setup Tasks**: 10 (Phase 1)
- **Foundational Tasks**: 13 (Phase 2)
- **User Story Tasks**: 220 (Phases 3-10)
  - US1 (P1): 22 tasks (15 implementation + 7 tests)
  - US2 (P1): 26 tasks (20 implementation + 6 tests)
  - US3 (P1): 31 tasks (24 implementation + 7 tests)
  - US4 (P2): 24 tasks (19 implementation + 5 tests)
  - US5 (P2): 30 tasks (24 implementation + 6 tests)
  - US6 (P3): 35 tasks (29 implementation + 6 tests)
  - US7 (P3): 28 tasks (22 implementation + 6 tests)
  - US8 (P3): 26 tasks (20 implementation + 6 tests)
- **Polish Tasks**: 33 (Phase 11)

**Parallelizable Tasks**: ~140 tasks marked [P] (51% can run in parallel)

**MVP Tasks**: 96 tasks (Setup + Foundational + US1 + US2 + US3)

**Estimated Timeline**:
- MVP (1 developer): 4-5 weeks
- MVP (3 developers in parallel): 2-3 weeks
- Full feature set (1 developer): 10-12 weeks
- Full feature set (3 developers): 5-7 weeks

---

## Notes

- [P] marker indicates tasks that can run in parallel (different files, no dependencies)
- [US#] label maps each task to its user story for traceability
- Each user story is independently completable and testable
- Tests can be written in parallel with implementation (or before, for TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Foundational phase MUST complete before any user story work begins
- After Foundational, all user stories can proceed in parallel (if team capacity allows)
