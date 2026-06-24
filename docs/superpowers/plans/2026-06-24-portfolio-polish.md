# VideoForge Portfolio Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the repository professional and portfolio-ready: clean git hygiene, remove junk, consolidate docs, rename consistently to "VideoForge", and rewrite README/CLAUDE.md to reflect the full feature set.

**Architecture:** No application logic changes. Work is file operations (`git rm`, `git mv`, edits), config edits, and documentation rewrites. Each task produces one logical commit. "Verification" steps replace TDD tests because there is no new code behavior to test — instead we assert repo state via commands.

**Tech Stack:** Python 3.8+, CustomTkinter, FFmpeg, OpenCV, NumPy, Pillow, PyInstaller. Tests: pytest. Lint: ruff.

**Key context discovered (read before starting):**
- The code is **already renamed to VideoForge**: `main.py` uses `VideoForgeApp`, window title "VideoForge"; `detection_profiles.py` writes to `%APPDATA%/VideoForge/profiles`; `templates.py` uses `~/.videoforge/`; the packaging spec is `src/packaging/VideoForge.spec` with `name='VideoForge'`.
- The ONLY remaining code-level `MagicTVBox` reference is `main.py:30` — and it is an **active bug**: line 30 creates `MagicTVBox.lock` but line 325 removes `VideoForge.lock`, so the lock file is never cleaned up. Fixing line 30 completes the rename AND fixes the bug.
- `setup.py` and `pyproject.toml` still use package name `magic-tv-box` and console script `magic-tv-box`.
- `specs/` are **historical** design docs and reference "MagicTVBox" throughout — they are left UNTOUCHED (rewriting history docs is misleading and out of scope).
- No `LICENSE` file exists. No screenshots exist.

---

## File Structure (what changes)

**Delete (git rm):** `=1.24.0`, `=4.8.0`, empty `electron/`, all 28 tracked `.pyc`/`__pycache__` under `src/`, all `.claude/commands/speckit.*.md`, all `.opencode/command/speckit.*.md`, the entire `.specify/` tree, `.claude/settings.local.json` (untrack only).

**Move (git mv) into `docs/`:** `BUILDING.md`, `PACKAGE_GUIDE.md`, `TRIM_MODES_GUIDE.md`, `HOURS_SUPPORT_VERIFICATION.md`, `UI_HOURS_FIELDS_REFERENCE.md`.

**Create:** `LICENSE`, `docs/screenshots/.gitkeep`.

**Rewrite:** `README.md`, `CLAUDE.md`, `.gitignore`.

**Edit:** `main.py:30`, `setup.py`, `pyproject.toml`, `docs/BUILDING.md`, `docs/PACKAGE_GUIDE.md`, `docs/HOURS_SUPPORT_VERIFICATION.md` (MagicTVBox → VideoForge references in active docs).

---

### Task 1: Resolve merge state and remove tracked build artifacts / junk

**Files:**
- Delete: `=1.24.0`, `=4.8.0`, all `src/**/__pycache__/*.pyc`

- [ ] **Step 1: Remove the unmerged `.pyc` files from the index (resolves the conflicted merge state)**

`git rm -f` on an unmerged path resolves the conflict by deleting the entry. Force-remove every tracked `.pyc` (covers both unmerged and non-unmerged), then clear the local cache dirs (disposable build artifacts):
```bash
git ls-files '*.pyc' | xargs -r git rm -f
find src -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null; true
```

- [ ] **Step 2: Delete the stray pip-redirect junk files**

Run:
```bash
git rm -f '=1.24.0' '=4.8.0'
```

- [ ] **Step 3: Verify no tracked `.pyc` remain and no unmerged paths remain**

Run: `git ls-files | grep -cE '\.pyc$' || true`
Expected: `0`
Run: `git diff --name-only --diff-filter=U`
Expected: empty output

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove tracked build artifacts and stray junk files"
```

---

### Task 2: Remove empty electron dir, speckit tooling noise, and untrack local config

**Files:**
- Delete: `electron/` (empty), `.claude/commands/`, `.opencode/command/`, `.specify/`
- Untrack (keep locally): `.claude/settings.local.json`

- [ ] **Step 1: Remove the empty electron directory from the tree**

Run:
```bash
rmdir electron 2>/dev/null || git rm -r --cached electron 2>/dev/null; true
```
(`electron/` is empty and not tracked, so `rmdir` removes it; the `git rm` is a no-op fallback.)

- [ ] **Step 2: Remove speckit tooling command files and the .specify tooling tree**

Run:
```bash
git rm -r --cached .claude/commands .opencode/command .specify
rm -rf .claude/commands .opencode/command .specify
```

- [ ] **Step 3: Untrack local settings (keep the file on disk for local use)**

Run:
```bash
git rm --cached .claude/settings.local.json 2>/dev/null; true
```

- [ ] **Step 4: Verify only intended items were removed**

Run: `git ls-files | grep -E '^(\.claude|\.opencode|\.specify|electron)' || true`
Expected: empty output (nothing from these paths remains tracked)

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: remove speckit tooling noise and untrack local config"
```

---

### Task 3: Clean up `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Replace the `.gitignore` with a Python-focused version**

Replace the ENTIRE contents of `.gitignore` with:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
env/
ENV/
*.egg-info/
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
.mypy_cache/

# Build / packaging
build/
dist/
*.spec.bak
*.exe
*.dll
*.pyd

# Local agent / editor config (keep local, do not track)
.claude/settings.local.json
.opencode/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project-specific
.specify/memory/agent-context.md
```

- [ ] **Step 2: Verify**

Run: `git check-ignore .claude/settings.local.json`
Expected: prints the path (confirms it is now ignored)

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: simplify .gitignore for Python project"
```

---

### Task 4: Consolidate scattered root docs into `docs/`

**Files:**
- Move: `BUILDING.md`, `PACKAGE_GUIDE.md`, `TRIM_MODES_GUIDE.md`, `HOURS_SUPPORT_VERIFICATION.md`, `UI_HOURS_FIELDS_REFERENCE.md` → `docs/`
- Create: `docs/screenshots/.gitkeep`

- [ ] **Step 1: Move the five root guide files into `docs/` (preserves history)**

Run:
```bash
git mv BUILDING.md docs/BUILDING.md
git mv PACKAGE_GUIDE.md docs/PACKAGE_GUIDE.md
git mv TRIM_MODES_GUIDE.md docs/TRIM_MODES_GUIDE.md
git mv HOURS_SUPPORT_VERIFICATION.md docs/HOURS_SUPPORT_VERIFICATION.md
git mv UI_HOURS_FIELDS_REFERENCE.md docs/UI_HOURS_FIELDS_REFERENCE.md
```

- [ ] **Step 2: Create a screenshots placeholder folder**

Run:
```bash
mkdir -p docs/screenshots
printf '# Place app screenshots here (e.g. main-window.png, batch-processor.png).\n' > docs/screenshots/README.md
```

- [ ] **Step 3: Verify**

Run: `ls docs/*.md | sort`
Expected: lists `BUILDING.md`, `LOGO_DETECTION_AI_OPTIONS.md`, `PACKAGE_GUIDE.md`, `HOURS_SUPPORT_VERIFICATION.md`, `UI_HOURS_FIELDS_REFERENCE.md`, `TRIM_MODES_GUIDE.md`
Run: `ls docs/screenshots/`
Expected: `README.md`

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "docs: consolidate root guides under docs/"
```

---

### Task 5: Complete the VideoForge rename in code & config

**Files:**
- Modify: `main.py:30`
- Modify: `setup.py:2,13,30`
- Modify: `pyproject.toml:6,33`

- [ ] **Step 1: Fix the lock-file bug in `main.py` (completes the rename)**

In `main.py`, change the lock path on line 30 from `MagicTVBox.lock` to `VideoForge.lock`:

Replace:
```python
    lock_path = Path(tempfile.gettempdir()) / "MagicTVBox.lock"
```
with:
```python
    lock_path = Path(tempfile.gettempdir()) / "VideoForge.lock"
```

- [ ] **Step 2: Update `setup.py`**

In `setup.py`:

Replace:
```python
"""
Setup script for MagicTVBox
"""
```
with:
```python
"""
Setup script for VideoForge
"""
```

Replace:
```python
    name="magic-tv-box",
```
with:
```python
    name="videoforge",
```

Replace:
```python
            "magic-tv-box=main:main",
```
with:
```python
            "videoforge=main:main",
```

- [ ] **Step 3: Update `pyproject.toml`**

In `pyproject.toml`:

Replace:
```toml
name = "magic-tv-box"
```
with:
```toml
name = "videoforge"
```

Replace:
```toml
magic-tv-box = "main:main"
```
with:
```toml
videoforge = "main:main"
```

- [ ] **Step 4: Verify no functional code references the old name**

Run: `grep -rniE "magic[-_ ]?tv[-_ ]?box" --include="*.py" --include="*.toml" --include="*.spec" . | grep -vE '\.git/|__pycache__|specs/' || true`
Expected: empty output (all code/config references gone; `specs/` historical docs are allowed to remain)

- [ ] **Step 5: Verify the app still imports cleanly**

Run: `python -c "import main; print('import OK')"`
Expected: `import OK`

- [ ] **Step 6: Commit**

```bash
git add main.py setup.py pyproject.toml
git commit -m "refactor: complete rename to VideoForge (fix lock-file cleanup)"
```

---

### Task 6: Update active docs (MagicTVBox → VideoForge references)

**Files:**
- Modify: `docs/BUILDING.md`, `docs/PACKAGE_GUIDE.md`, `docs/HOURS_SUPPORT_VERIFICATION.md`

These active guides reference `src/packaging/MagicTVBox.spec` (which no longer exists — it is `VideoForge.spec`) and `dist/MagicTVBox.exe`. Update only product/spec/exe name references. Leave runtime paths like `%APPDATA%/MagicTVBox/profiles` alone IF they appear (they reflect historical user-data locations and are out of scope); however these three files only reference the product/spec/exe names, so a wholesale replace is safe here.

- [ ] **Step 1: Replace product, spec-file, and exe name references in the three moved docs**

Run (replaces `MagicTVBox.spec` → `VideoForge.spec`, `MagicTVBox.exe` → `VideoForge.exe`, and standalone `MagicTVBox` → `VideoForge` in these three files only):
```bash
for f in docs/BUILDING.md docs/PACKAGE_GUIDE.md docs/HOURS_SUPPORT_VERIFICATION.md; do
  sed -i 's/MagicTVBox\.spec/VideoForge.spec/g; s/MagicTVBox\.exe/VideoForge.exe/g; s/MagicTVBox/VideoForge/g' "$f"
done
```

- [ ] **Step 2: Verify**

Run: `grep -rcE "MagicTVBox" docs/BUILDING.md docs/PACKAGE_GUIDE.md docs/HOURS_SUPPORT_VERIFICATION.md`
Expected: `0` for each file

- [ ] **Step 3: Commit**

```bash
git add docs/BUILDING.md docs/PACKAGE_GUIDE.md docs/HOURS_SUPPORT_VERIFICATION.md
git commit -m "docs: update active guides to VideoForge name"
```

---

### Task 7: Add MIT `LICENSE`

**Files:**
- Create: `LICENSE`

- [ ] **Step 1: Create the LICENSE file**

Create `LICENSE` with exactly:

```
MIT License

Copyright (c) 2026 VideoForge Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Commit**

```bash
git add LICENSE
git commit -m "docs: add MIT LICENSE"
```

---

### Task 8: Rewrite `CLAUDE.md` (clean dev guide)

**Files:**
- Modify: `CLAUDE.md` (full rewrite)

- [ ] **Step 1: Replace the broken auto-generated CLAUDE.md**

Replace the ENTIRE contents of `CLAUDE.md` with:

```markdown
# VideoForge — Development Guidelines

VideoForge is a Python desktop application (CustomTkinter) that turns FFmpeg into a point-and-click dashboard for batch-processing TV recordings: automatic logo/watermark detection, flexible trimming, parallel encoding, and one-click `.exe` packaging.

## Tech Stack

- **Language:** Python 3.8+
- **GUI:** CustomTkinter 5.2+, tkinterdnd2 (drag-and-drop)
- **Video:** FFmpeg 4.0+ via `ffmpeg-python` / subprocess
- **Logo detection:** OpenCV (opencv-python-headless) + NumPy — classical CV (temporal-stability + manual). Optional Google Cloud Vision (`requirements-ai.txt`).
- **Packaging:** PyInstaller 6.x
- **Tests:** pytest, pytest-cov
- **Lint:** ruff

## Project Structure

```
src/
  main.py is the entry point (repo root)
  video_processor.py   # FFmpeg orchestration & filters
  parallel_processor.py
  logo_detector_temporal.py  # default CV detector
  logo_detector_vision.py    # optional Cloud Vision
  logo_detector.py           # manual coordinates
  detection_profiles.py      # JSON profile persistence
  templates.py / data_models.py / state.py / exceptions.py
  ui/                        # CustomTkinter frames
  packaging/                 # PyInstaller spec + build_exe.py
tests/                       # unit + integration (pytest)
docs/                        # guides and design specs
specs/                       # historical feature design docs (read-only reference)
```

## Commands

Run from the repository root:

```bash
pip install -r requirements.txt          # core deps
pip install -r requirements-ai.txt       # optional Cloud Vision detector
pytest                                    # run the test suite
pytest tests/unit tests/integration       # scope a subset
ruff check .                              # lint
python main.py                            # run the app
```

## Conventions

- Python 3.8+ syntax. Use type hints. Follow PEP 8 (enforced loosely via ruff).
- Keep functions small and focused; add docstrings to public classes/functions.
- Do not commit `__pycache__/`, `.pyc`, `build/`, or `dist/`.
- `specs/` contains historical design records — do not rewrite them; reference them only.
- Logo-detection runtime data lives under `%APPDATA%/VideoForge/profiles` (Windows) / `~/.videoforge` (templates).
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: replace broken CLAUDE.md with clean dev guide"
```

---

### Task 9: Rewrite `README.md` (centerpiece)

**Files:**
- Modify: `README.md` (full rewrite)

- [ ] **Step 1: Replace the ENTIRE contents of `README.md`**

Replace with:

````markdown
# VideoForge

<p align="center">
  <em>A desktop dashboard that turns FFmpeg into a point-and-click workflow — batch-process TV recordings with automatic logo detection, flexible trimming, and parallel encoding.</em>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.8%2B-blue">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="FFmpeg" src="https://img.shields.io/badge/FFmpeg-4.0%2B-black">
  <img alt="OpenCV" src="https://img.shields.io/badge/OpenCV-classical%20CV-blueviolet">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey">
  <img alt="Tests" src="https://img.shields.io/badge/tests-pytest-brightgreen">
</p>

---

VideoForge is a Python desktop application (built with CustomTkinter) that wraps FFmpeg in a clean, dark-themed UI. Originally built to convert a pile of personal Bash scripts into a reusable tool, it now supports automatic watermark/logo detection, flexible cut units, multi-task batch processing, parallel encoding, and packaging to a standalone Windows `.exe`.

## Highlights

- **Automatic logo detection** — a temporal-stability computer-vision pipeline (OpenCV + NumPy) samples frames, computes per-pixel variance, and locates persistent watermarks automatically. Manual coordinate entry and an optional Google Cloud Vision detector are also available.
- **Multi-task batch processing** — run several task tabs at once, each with its own files and settings, processed sequentially with live per-file progress.
- **Parallel encoding** — a worker pool runs multiple FFmpeg encodes concurrently to use more of your CPU.
- **Flexible trimming** — cut by **Time**, **Percent**, or **Frames**, including one-click "cut last N minutes".
- **Drag-and-drop** — drop files straight into the UI (tkinterdnd2).
- **Detection profiles & templates** — save reusable logo-detection profiles (`%APPDATA%/VideoForge/profiles`) and processing templates for recurring jobs.
- **One-click `.exe`** — PyInstaller packaging ships a double-clickable Windows executable with no Python install required.

## Screenshots

Screenshots live in [`docs/screenshots/`](docs/screenshots). *(Add `main-window.png`, `batch-processor.png`, etc. here.)*

## Tech Stack

| Area | Technology |
| --- | --- |
| Language | Python 3.8+ |
| GUI | CustomTkinter, tkinterdnd2 |
| Video engine | FFmpeg 4.0+ (`ffmpeg-python` / subprocess) |
| Logo detection | OpenCV + NumPy (classical CV); optional Google Cloud Vision |
| Imaging | Pillow |
| Packaging | PyInstaller |
| Tests / lint | pytest, pytest-cov, ruff |

## Prerequisites

- Python 3.8+
- **FFmpeg** installed and on your `PATH`

```bash
# macOS
brew install ffmpeg
# Debian/Ubuntu
sudo apt install ffmpeg
# Windows: download from ffmpeg.org, or: choco install ffmpeg
```

Verify with `ffmpeg -version`.

## Installation

```bash
git clone <repository-url>
cd VideoForge
python -m venv venv
# Windows: venv\Scripts\activate   |   macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

For the optional Cloud Vision logo detector: `pip install -r requirements-ai.txt` and set `GOOGLE_APPLICATION_CREDENTIALS` (see [`docs/LOGO_DETECTION_AI_OPTIONS.md`](docs/LOGO_DETECTION_AI_OPTIONS.md)).

## Running

```bash
python main.py
```

Or, after `pip install -e .`, use the `videoforge` console command.

## Usage

1. **Batch Processor** — add task tabs, drop or select files, pick an output folder, enable options (trim / cut-units / delogo / auto-detect), and start.
2. **Single File** — process one file with the same options.
3. **Logs** — live FFmpeg output and processing messages.
4. **Settings** — FFmpeg encoding details and app info.

### Encoding defaults

H.264 (`libx264`, preset `fast`, CRF 23, YUV420P) + AAC 192k + faststart — a quality/size balance tuned for iOS devices and TV boxes.

## Packaging a Windows executable

```bash
pyinstaller --clean --noconfirm src/packaging/VideoForge.spec
# → dist/VideoForge.exe
```

See [`docs/BUILDING.md`](docs/BUILDING.md) and [`docs/PACKAGE_GUIDE.md`](docs/PACKAGE_GUIDE.md) for full details.

## Testing & lint

```bash
pytest                 # full suite (unit + integration)
ruff check .           # lint
```

Integration tests run real FFmpeg; ensure FFmpeg is on your `PATH`.

## Project Structure

```
main.py                      # Entry point — VideoForgeApp
src/
├── video_processor.py       # FFmpeg orchestration & filters
├── parallel_processor.py    # Concurrent encode worker pool
├── logo_detector_temporal.py# Temporal-stability CV detector (default)
├── logo_detector_vision.py  # Optional Google Cloud Vision detector
├── logo_detector.py         # Manual-coordinate detector
├── logo_detection_utils.py  # Shared CV filter helpers
├── detection_profiles.py    # JSON logo-detection profiles
├── templates.py             # Processing-profile templates
├── data_models.py           # Config / profile / template dataclasses
├── state.py                 # Application state container
├── exceptions.py            # Domain exception hierarchy
├── packaging/               # PyInstaller spec + build script
└── ui/                      # CustomTkinter frames (batch, single, logs, settings, drag-drop)
tests/                       # Unit + integration tests
docs/                        # Guides and design specs
specs/                       # Historical feature design records
```

## Documentation

- [`docs/BUILDING.md`](docs/BUILDING.md) — building the standalone executable
- [`docs/PACKAGE_GUIDE.md`](docs/PACKAGE_GUIDE.md) — packaging walkthrough
- [`docs/TRIM_MODES_GUIDE.md`](docs/TRIM_MODES_GUIDE.md) — trim modes reference
- [`docs/LOGO_DETECTION_AI_OPTIONS.md`](docs/LOGO_DETECTION_AI_OPTIONS.md) — detection methods & Cloud Vision setup
- [`specs/`](specs) — historical design documents for each feature

## License

[MIT](LICENSE)
````

- [ ] **Step 2: Verify the README renders sanely (no broken internal links to moved files)**

Run: `grep -oE '\]\([^)]*\.md\)' README.md | sort -u`
Expected: links pointing to `docs/BUILDING.md`, `docs/PACKAGE_GUIDE.md`, `docs/TRIM_MODES_GUIDE.md`, `docs/LOGO_DETECTION_AI_OPTIONS.md`, `LICENSE` — all of which now exist.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README as portfolio-ready VideoForge overview"
```

---

### Task 10: Final verification

- [ ] **Step 1: Repo is clean and no junk remains**

Run: `git status`
Expected: `nothing to commit, working tree clean`
Run: `git ls-files | grep -cE '\.pyc$|^='`
Expected: `0`

- [ ] **Step 2: Imports and tests still pass**

Run: `python -c "import main; print('import OK')"`
Expected: `import OK`
Run: `pytest -q`
Expected: test run completes (all passing, or the same baseline as before cleanup).

- [ ] **Step 3: Lint is clean (baseline)**

Run: `ruff check .`
Expected: no new errors introduced by the rename/config changes.

- [ ] **Step 4: Root directory is tidy**

Run: `ls *.md`
Expected: only `CLAUDE.md` and `README.md` at the root.
```
