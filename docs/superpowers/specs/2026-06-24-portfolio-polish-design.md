# VideoForge Portfolio Polish — Design

**Date:** 2026-06-24
**Status:** Approved
**Goal:** Make the repository professional and portfolio-ready by fixing git hygiene, removing junk, consolidating docs, and rewriting the README/CLAUDE.md to accurately reflect the current feature set.

## Context

The application has grown well beyond its documentation. Recent work added temporal-stability logo detection, vision-based detection, flexible cut units (Time/Percent/Frames), parallel processing, drag-and-drop, detection profiles, templates, and PyInstaller `.exe` packaging — none of which appear in the README. The project is also named inconsistently ("MagicTVBox" in README, "VideoForge" in packaging) and contains committed build artifacts and stray files.

## Problems Identified

1. **Merge conflict in progress** on 28 committed `.pyc` files in `__pycache__/` (these are gitignored but were committed before the rules existed).
2. **Stray junk files** `=1.24.0` and `=4.8.0` (artifacts of a `pip install pkg>=X` shell redirection mistake) tracked in git.
3. **Dead `electron/` directory** (empty) and irrelevant Electron/Node `.gitignore` blocks.
4. **Inconsistent naming**: "MagicTVBox" vs "VideoForge".
5. **CLAUDE.md** is a broken auto-generated placeholder (`[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]` repeated).
6. **Cluttered root**: 5 separate top-level guide `.md` files.
7. **README structure section** is outdated (missing most of `src/`).
8. **Speckit tooling noise**: `.claude/commands/`, `.opencode/command/`, `.specify/` (scripts/templates/memory) committed; local config (`.claude/settings.local.json`) tracked.

## Design

### 1. Fix git state & remove junk
- Resolve the in-progress merge by `git rm`-ing all tracked `.pyc` / `__pycache__` files (already gitignored; remove from history going forward).
- Delete stray artifacts `=1.24.0`, `=4.8.0`.
- Delete dead `electron/` directory.
- Remove speckit tooling files: `.claude/commands/`, `.opencode/command/`, `.specify/`.
- Untrack `.claude/settings.local.json` and any local `.opencode/` config; add to `.gitignore`.
- Clean `.gitignore`: drop Electron/Node sections, keep Python + tooling ignores.

**Keep:** `specs/` and `docs/superpowers/` (real design content demonstrates engineering process).

### 2. Consolidate docs
Move into `docs/`: `BUILDING.md`, `PACKAGE_GUIDE.md`, `TRIM_MODES_GUIDE.md`, `HOURS_SUPPORT_VERIFICATION.md`, `UI_HOURS_FIELDS_REFERENCE.md`. Add `docs/screenshots/` placeholder (with `.gitkeep`) for future images. Root retains only `README.md`, `CLAUDE.md`, `LICENSE`.

### 3. Rewrite README.md → "VideoForge"
Structure: title + tagline + badges → hero summary → Features (grouped by capability) → tech-stack table → accurate architecture tree → Getting Started → Usage → Packaging → Testing (`pytest`, `ruff`) → Project Structure → License. Rename "MagicTVBox" → "VideoForge".

### 4. Rewrite CLAUDE.md
Clean, accurate dev guide: real commands, stack, structure, conventions.

### 5. Consistency pass
Rename "MagicTVBox" → "VideoForge" in `setup.py`, `pyproject.toml`, `main.py`, packaging spec, and any remaining references. Add a `LICENSE` file (MIT) at root.

## Out of Scope (YAGNI)
- No application code/logic changes.
- No new features.
- No test rewrites.
- No screenshot generation (placeholder folder only; user adds images later).

## Risks & Mitigations
- **Rename breakage**: console-script/package name change could affect `pip install -e .`. Mitigation: update `setup.py`/`pyproject.toml` console script to `videoforge` consistently and verify import paths unchanged.
- **Merge state**: committing during a merge finalizes it. Mitigation: resolve `.pyc` conflict first, then commit.
