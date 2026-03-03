# Developer Quickstart: Enhanced Workflow & Performance

**Feature**: 001-enhanced-workflow
**Target Audience**: Developers implementing the feature
**Prerequisites**: Python 3.8+, Git, FFmpeg installed

---

## Quick Setup (5 minutes)

### 1. Branch Setup

```bash
# Already on the feature branch (created by /speckit.specify)
git status
# Should show: On branch 001-enhanced-workflow

# Pull latest from main if needed
git fetch origin main
git merge origin/main
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install customtkinter>=5.0
pip install ffmpeg-python  # Optional but recommended

# Verify FFmpeg installation
ffmpeg -version
ffprobe -version
```

### 3. Run the Application

```bash
# From repo root
python main.py
```

---

## Architecture Overview (3 minute read)

### Current Structure

```
MagicTVBox/
├── main.py                     # Entry point - creates MagicTVBoxApp
├── src/
│   ├── state.py               # AppState singleton - central state management
│   ├── video_processor.py      # FFmpeg subprocess handling
│   └── ui/
│       ├── batch_processor.py  # Batch processing UI
│       ├── single_processor.py # Single file processing UI
│       ├── settings_panel.py   # Settings display
│       └── logs_panel.py       # Log viewer
```

### Key Patterns

1. **Singleton State**: `AppState` holds all configuration
   ```python
   from src.state import AppState
   state = AppState()
   state.cut_mode = CutMode.CUT_LAST
   state.cut_minutes = 5.0
   ```

2. **Callback-Based Progress**: Processing uses callbacks for events
   ```python
   video_processor.process_video(
       input_path, output_path,
       on_progress=lambda pct: print(f"{pct}%"),
       on_log=lambda msg: print(msg)
   )
   ```

3. **Threading**: Background threads for non-blocking UI
   ```python
   thread = threading.Thread(target=self._start_processing)
   thread.start()
   ```

---

## Feature Implementation Phases

### Phase 1: Core Infrastructure (Weeks 1-2)

**Goal**: Parallel processing + templates + hardware detection

**New Files**:
- `src/parallel_processor.py` - Multi-threaded batch processor
- `src/templates.py` - Template save/load
- `src/hardware_encoders.py` - GPU encoder detection

**Modified Files**:
- `src/state.py` - Add template/parallel/hardware fields
- `src/video_processor.py` - Add GPU encoder support

**Test Command**:
```bash
python -m pytest tests/test_parallel_processor.py -v
python -m pytest tests/test_templates.py -v
```

**Manual Test**:
1. Run app, add 5 videos to batch
2. Start processing - should see 2-3 processing simultaneously
3. Save current settings as "Test Template"
4. Close app, reopen, load "Test Template"

---

### Phase 2: Drag-Drop & UI (Weeks 2-3)

**Goal**: Drag-drop files, template selector UI

**New Files**:
- `src/ui/drag_drop.py` - Drag-drop handler

**Modified Files**:
- `src/ui/batch_processor.py` - Enable drag-drop zone, add template dropdown
- `src/ui/single_processor.py` - Add template dropdown

**Test Command**:
```bash
# Manual testing required for drag-drop
python main.py
```

**Manual Test**:
1. Drag 10 video files from File Explorer onto batch processor window
2. Files should appear in list immediately
3. Try dragging a folder - should recursively add all videos

---

### Phase 3: Metadata & Validation (Weeks 3-4)

**Goal**: Video preview, metadata display, validation warnings

**New Files**:
- `src/video_metadata.py` - Metadata extraction & caching
- `src/ui/preview_modal.py` - Video preview modal

**Modified Files**:
- `src/ui/batch_processor.py` - Show duration, resolution, codec in file list

**Test Command**:
```bash
python -m pytest tests/test_video_metadata.py -v
```

**Manual Test**:
1. Add a 4K video with "Universal" profile (max 1080p)
2. Should see warning icon: "Video will be downscaled to 1920x1080"
3. Right-click video → "Preview" → modal shows first 5 seconds

---

### Phase 4: Hardware Encoding (Week 4)

**Goal**: GPU-accelerated encoding profiles

**Modified Files**:
- `src/ui/settings_panel.py` - Show detected hardware encoders
- `src/ui/batch_processor.py` - Add GPU profiles to dropdown

**Test Command**:
```bash
# Test GPU detection (requires compatible hardware)
python -c "from src.hardware_encoders import HardwareEncoderDetector; print(HardwareEncoderDetector().detect_encoders())"
```

**Manual Test**:
1. Launch app on system with NVIDIA GPU
2. Profile dropdown should show "Universal - GPU (NVENC)"
3. Process video with GPU profile - should complete 10x faster than CPU

---

### Phase 5: Video Filters (Week 5)

**Goal**: Rotate, crop, scale, brightness adjustments

**New Files**:
- `src/video_filters.py` - Filter chain builder

**Modified Files**:
- `src/ui/batch_processor.py` - Add "Video Filters" section with checkboxes/sliders

**Test Command**:
```bash
python -m pytest tests/test_video_filters.py -v
```

**Manual Test**:
1. Enable "Rotate 90°" filter
2. Process a video - output should be rotated
3. Enable "Crop" + "Brightness +20%" - both should apply

---

### Phase 6: Recovery & Errors (Weeks 5-6)

**Goal**: Batch resume, user-friendly errors

**New Files**:
- `src/batch_state.py` - Batch state checkpointing
- `src/error_handler.py` - Error message parser
- `src/ui/error_dialog.py` - Error dialog with action buttons

**Test Command**:
```bash
python -m pytest tests/test_batch_state.py -v
python -m pytest tests/test_error_handler.py -v
```

**Manual Test**:
1. Start 20-file batch
2. After 5 files complete, close app forcefully (Task Manager)
3. Reopen app - should prompt "Resume previous batch? (5 of 20 completed)"
4. Click "Resume" - should continue from file 6

---

## Development Workflow

### 1. Create New Service

```bash
# Create service file
cat > src/my_service.py << 'EOF'
"""My service description"""
from dataclasses import dataclass
from typing import List, Optional

class MyService:
    """Service to do X"""

    def __init__(self, dependency):
        self.dependency = dependency

    def do_something(self, arg: str) -> str:
        """Do something with arg"""
        return f"Processed: {arg}"
EOF

# Create test file
cat > tests/test_my_service.py << 'EOF'
import pytest
from src.my_service import MyService

def test_do_something():
    service = MyService(dependency=None)
    result = service.do_something("test")
    assert result == "Processed: test"
EOF

# Run tests
python -m pytest tests/test_my_service.py -v
```

### 2. Update UI Component

```python
# In src/ui/batch_processor.py

def _create_my_section(self):
    """Create my new UI section"""
    frame = ctk.CTkFrame(self, fg_color="#1e293b")
    frame.pack(fill="x", pady=(0, 12))

    title = ctk.CTkLabel(
        frame,
        text="My Section",
        font=ctk.CTkFont(size=16, weight="bold")
    )
    title.pack(anchor="w", padx=16, pady=(16, 12))

    # Add widgets...
```

### 3. Add State Field

```python
# In src/state.py, add to AppState.__init__()

self.my_new_setting: bool = False
self.my_value: float = 1.0
```

### 4. Test UI Changes

```bash
# Run app and manually verify
python main.py

# Or use interactive testing
python
>>> from main import MagicTVBoxApp
>>> app = MagicTVBoxApp()
>>> # Inspect/test components interactively
```

---

## Common Tasks

### Add a New Processing Profile

```python
# In src/state.py, add to PROCESSING_PROFILES dict

"my_profile": ProcessingProfile(
    name="My Custom Profile",
    description="Description of what this profile does",
    video_codec="libx264",
    video_preset="medium",
    video_crf=23,
    pixel_format="yuv420p",
    audio_codec="aac",
    audio_bitrate="192k",
    use_faststart=True
)
```

### Add a Callback to AppState

```python
# In src/state.py

def __init__(self):
    # ...
    self.my_callbacks: List[Callable[[str], None]] = []

def register_my_callback(self, callback: Callable[[str], None]):
    """Register callback for my events"""
    self.my_callbacks.append(callback)

def trigger_my_event(self, message: str):
    """Trigger callbacks with message"""
    for callback in self.my_callbacks:
        callback(message)
```

### Debug FFmpeg Command

```python
# In src/video_processor.py, add before subprocess.run():

print("FFmpeg command:")
print(" ".join(ffmpeg_cmd))

# Or log to file:
with open("ffmpeg_debug.txt", "w") as f:
    f.write(" ".join(ffmpeg_cmd))
```

---

## Troubleshooting

### Issue: "FFmpeg not found"

```bash
# Windows: Add FFmpeg to PATH
setx PATH "%PATH%;C:\path\to\ffmpeg\bin"

# macOS: Install via Homebrew
brew install ffmpeg

# Verify
ffmpeg -version
```

### Issue: "ModuleNotFoundError: No module named 'customtkinter'"

```bash
pip install customtkinter>=5.0
```

### Issue: Drag-drop not working

- **Windows**: Ensure app runs with standard user permissions (not admin)
- **macOS**: Grant app permissions in System Preferences → Security & Privacy

### Issue: GPU encoding fails

```bash
# Check GPU encoder availability
ffmpeg -encoders | grep nvenc  # NVIDIA
ffmpeg -encoders | grep qsv    # Intel
ffmpeg -encoders | grep videotoolbox  # Apple

# If not shown, update drivers or FFmpeg build
```

### Issue: Tests failing

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run with verbose output
python -m pytest -v

# Run specific test
python -m pytest tests/test_my_service.py::test_my_function -v
```

---

## Code Style & Standards

### Python Style

- **PEP 8**: Follow Python style guide
- **Type hints**: Use for all function signatures
- **Docstrings**: Google style for classes and public methods
- **Naming**: snake_case for functions/variables, PascalCase for classes

Example:
```python
from typing import Optional, List

def process_files(
    file_paths: List[str],
    output_dir: str,
    overwrite: bool = False
) -> Optional[str]:
    """
    Process multiple video files.

    Args:
        file_paths: List of input file paths
        output_dir: Output directory path
        overwrite: Whether to overwrite existing files

    Returns:
        Error message if failed, None if successful
    """
    # Implementation...
```

### Testing Standards

- **Coverage**: Aim for 80%+ test coverage
- **Test naming**: `test_<function_name>_<scenario>()`
- **Assertions**: Use pytest's assert, not unittest methods
- **Fixtures**: Use pytest fixtures for setup

Example:
```python
import pytest
from src.templates import TemplateManager

@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for tests"""
    return str(tmp_path)

def test_save_template_creates_file(temp_dir):
    """Test that saving template creates JSON file"""
    manager = TemplateManager(temp_dir)
    template = Template(name="test", description="Test", ...)
    manager.save_template(template)
    assert (Path(temp_dir) / "test.json").exists()
```

---

## Useful Commands

### Run App

```bash
python main.py
```

### Run Tests

```bash
# All tests
python -m pytest

# Specific file
python -m pytest tests/test_templates.py

# With coverage
python -m pytest --cov=src --cov-report=html

# Watch mode (requires pytest-watch)
ptw
```

### Check FFmpeg

```bash
# Version
ffmpeg -version

# Available encoders
ffmpeg -encoders

# Available filters
ffmpeg -filters

# Test encode
ffmpeg -i input.mp4 -t 5 -c:v libx264 -preset ultrafast output.mp4
```

### Profile Performance

```python
import cProfile
import pstats

cProfile.run('my_function()', 'profile_stats')
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative')
stats.print_stats(20)
```

---

## Documentation Links

- **Feature Spec**: [spec.md](./spec.md)
- **Data Model**: [data-model.md](./data-model.md)
- **Service Interfaces**: [contracts/interfaces.md](./contracts/interfaces.md)
- **Research**: [research.md](./research.md)
- **Implementation Plan**: [implementation-plan.md](./implementation-plan.md)

---

## Getting Help

### Questions During Development

1. Check the [research.md](./research.md) for technical decisions
2. Review [contracts/interfaces.md](./contracts/interfaces.md) for interface definitions
3. Look at existing code patterns in `src/video_processor.py` or `src/ui/batch_processor.py`
4. Search the [spec.md](./spec.md) for acceptance criteria

### Debugging Issues

1. Enable verbose logging (add `--verbose` flag or set log level)
2. Check `~/.magictvbox/` for template/state files
3. Inspect FFmpeg commands (see "Debug FFmpeg Command" above)
4. Use Python debugger: `import pdb; pdb.set_trace()`

---

## Next Steps

1. ✅ Read this quickstart (you're done!)
2. ⬜ Skim [spec.md](./spec.md) to understand user requirements
3. ⬜ Review [data-model.md](./data-model.md) for entities
4. ⬜ Start with Phase 1 implementation (parallel processing)
5. ⬜ Write tests first (TDD approach recommended)
6. ⬜ Implement feature incrementally
7. ⬜ Manual test after each phase

**Recommended First Task**: Implement `ParallelProcessor` class with basic thread pooling (see [contracts/interfaces.md](./contracts/interfaces.md#2-parallelprocessor) for interface).

---

**Happy Coding! 🚀**
