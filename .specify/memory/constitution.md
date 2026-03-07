<!--
Sync Impact Report:
- Version: NONE → 1.0.0 (Initial ratification)
- Modified principles: N/A (initial creation)
- Added sections: All (initial creation)
- Removed sections: None
- Templates requiring updates:
  ✅ plan-template.md - reviewed, Constitution Check section aligns
  ✅ spec-template.md - reviewed, user scenarios and requirements align
  ✅ tasks-template.md - reviewed, testing and organization principles align
- Follow-up TODOs: None
-->

# MagicTVBox Constitution

## Core Principles

### I. User-First Design

**Rule**: Every feature MUST be accessible to non-technical users without requiring command-line knowledge or deep FFmpeg understanding.

**Requirements**:
- UI elements must use clear, plain-language labels (no technical jargon)
- Error messages must be actionable (tell users what to do, not just what went wrong)
- Default settings must work out-of-the-box for common use cases
- Real-time progress feedback required for all long-running operations

**Rationale**: The application's purpose is to make FFmpeg automation accessible. Technical barriers defeat this core mission.

### II. Robust Video Processing

**Rule**: FFmpeg operations MUST be reliable, validated, and recoverable. Video processing failures MUST NOT corrupt source files or leave users with incomplete outputs.

**Requirements**:
- Always validate input files before processing (format, accessibility, corruption)
- Use safe FFmpeg parameters (no overwrite without confirmation, atomic operations)
- Implement proper error handling with cleanup of partial outputs on failure
- Log all FFmpeg commands and outputs for debugging
- Preserve original files (never modify in-place)

**Rationale**: Video files represent significant user investment (time, content). Data loss or corruption is unacceptable.

### III. Real-time Feedback & Transparency

**Rule**: Users MUST have visibility into what the application is doing at all times. No black-box operations.

**Requirements**:
- Display real-time progress for all processing operations (percentage, time estimates)
- Show FFmpeg output in logs panel (not hidden)
- Provide queue status for batch operations
- Indicate processing state clearly (idle, processing, complete, error)
- Enable users to inspect settings before execution

**Rationale**: Long video processing operations create anxiety. Transparency builds trust and enables users to diagnose issues.

### IV. Code Quality & Maintainability

**Rule**: Code MUST be readable, maintainable, and follow Python best practices. Complexity must be justified.

**Requirements**:
- Follow PEP 8 style guidelines
- Use type hints for function signatures and complex data structures
- Keep functions focused and small (single responsibility)
- Use meaningful names for variables, functions, and classes
- Add docstrings to classes and non-trivial functions
- Prefer explicit over implicit (readability over cleverness)

**Rationale**: This is a community project. Code quality directly impacts maintainability and contributor experience.

### V. Testing for Critical Paths

**Rule**: Video processing logic and data integrity operations MUST have automated tests. UI-only changes may skip tests unless they affect processing logic.

**Requirements**:
- Test video processor functions (cutting, filtering, format conversion)
- Test FFmpeg command generation and parameter validation
- Test state management for settings and queue
- Test file handling (path validation, extension detection, output naming)
- Integration tests for complete processing workflows (when requested)
- UI tests are OPTIONAL unless specifically required

**Rationale**: Manual testing of video processing is time-consuming and error-prone. Automated tests catch regressions early.

### VI. Performance & Responsiveness

**Rule**: UI MUST remain responsive during all operations. Long-running FFmpeg processes MUST NOT block the UI thread.

**Requirements**:
- Run FFmpeg operations in background threads
- Use threading for batch queue processing
- Update UI from worker threads via thread-safe mechanisms
- Provide cancel/abort functionality for long operations
- Avoid unnecessary file I/O on UI thread

**Rationale**: A frozen UI during processing creates a poor user experience and makes the application appear broken.

### VII. Simplicity & Focus

**Rule**: Keep the application focused on its core mission (FFmpeg automation). Resist feature bloat. Prefer simple, direct solutions.

**Requirements**:
- New features must align with core mission (video automation for TV/iOS)
- Prefer configuration over code when adding options
- Avoid premature abstraction (three uses before abstracting)
- Don't add features speculatively (YAGNI)
- Remove unused code instead of commenting it out

**Rationale**: Scope creep kills projects. A focused tool that does its job well beats a bloated tool that does everything poorly.

## Technical Standards

### Stack Constraints

- **Language**: Python 3.8+ (for compatibility with older systems)
- **UI Framework**: CustomTkinter 5.0+ (modern, cross-platform)
- **Video Processing**: FFmpeg 4.0+ (external dependency, must be in PATH)
- **Computer Vision**: OpenCV 4.x (cv2) for logo detection features
- **Packaging**: PyInstaller 5.x for executable distribution

### Dependency Management

- Minimize external dependencies (fewer things to break)
- Pin major versions in requirements.txt
- Document system dependencies (FFmpeg, Python version)
- Provide clear installation instructions for all platforms (Windows, macOS, Linux)

### File Organization

```
src/              # Application source code
├── ui/           # UI components (CustomTkinter panels)
├── video_processor.py  # FFmpeg processing logic
├── state.py      # Application state management
└── exceptions.py # Custom exceptions

tests/            # Automated tests
├── unit/         # Unit tests for processing logic
└── integration/  # End-to-end workflow tests

specs/            # Feature specifications (speckit)
.specify/         # Speckit templates and memory
```

### Platform Support

- **Primary**: Windows (main user base)
- **Secondary**: macOS, Linux (community support)
- Use cross-platform path handling (pathlib, not os.path)
- Test FFmpeg commands across platforms when possible

## Development Workflow

### Feature Development

1. **Specify**: Use `/speckit.specify` to create feature specification
2. **Plan**: Use `/speckit.plan` for technical design
3. **Tasks**: Use `/speckit.tasks` to generate implementation tasks
4. **Implement**: Follow task order, test as you go
5. **Validate**: Run tests, manual smoke test, check against spec

### Code Review Standards

- All code changes require review (no direct commits to main)
- Reviewer must verify:
  - Follows constitution principles
  - Includes tests for processing logic (if applicable)
  - UI remains responsive (if UI changes)
  - Error handling is present and tested
  - Documentation updated (if public API changed)

### Quality Gates

Before merging to main:
- [ ] All tests pass
- [ ] No regressions in existing features (smoke test)
- [ ] Code follows PEP 8 (use ruff or black)
- [ ] Type hints present for new functions
- [ ] Processing logic has tests (if applicable)
- [ ] UI remains responsive (if long operations added)

### Commit Practices

- Use conventional commit messages: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- Reference issue/feature numbers when applicable
- Keep commits focused (one logical change per commit)
- Don't commit commented-out code or debug prints

## Governance

### Constitution Authority

This constitution supersedes all other development practices. When in conflict, constitution principles take precedence. Team members must justify exceptions with documented rationale in plan.md "Complexity Tracking" section.

### Amendment Process

1. Propose changes with clear rationale (why current principle insufficient)
2. Discuss impact on existing code and templates
3. Update constitution with version bump
4. Propagate changes to dependent templates (plan, spec, tasks)
5. Document in commit message and Sync Impact Report

### Versioning Policy

- **MAJOR** (X.0.0): Principle removed, redefined, or made stricter (breaking change)
- **MINOR** (x.Y.0): New principle added or existing principle expanded
- **PATCH** (x.y.Z): Clarifications, wording fixes, non-semantic changes

### Compliance Review

- Constitution check required in Phase 0 of `/speckit.plan` workflow
- Re-check after Phase 1 design if architecture changes
- Violations must be justified in "Complexity Tracking" table
- Unjustified violations block feature approval

### Runtime Guidance

For day-to-day development guidance, consult `CLAUDE.md` in the repository root. This file contains active technologies, commands, and recent changes. The constitution defines non-negotiable principles; CLAUDE.md provides practical implementation guidance.

**Version**: 1.0.0 | **Ratified**: 2026-03-06 | **Last Amended**: 2026-03-06
