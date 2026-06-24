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
