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
src/  (main.py is the entry point, at repo root)
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
