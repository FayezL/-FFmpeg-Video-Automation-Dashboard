# Developer Quickstart: CPU Limiting and Enhanced Processing Options

**Feature**: 003-cpu-limit-options
**Date**: 2026-03-07
**For**: Developers implementing or integrating this feature

## Overview

This guide helps you quickly understand and integrate the CPU limiting, enhanced settings, and intro/outro detection features into the FFmpeg Video Automation Dashboard.

---

## Prerequisites

1. **Development Environment**:
   ```bash
   # Clone and navigate to repo
   cd -FFmpeg-Video-Automation-Dashboard

   # Install dependencies (includes new ones)
   pip install -r requirements.txt

   # New dependencies added:
   # - psutil>=5.9.0 (CPU monitoring)
   # - scipy>=1.9.0 (perceptual hashing)
   # - pydantic>=2.0.0 (settings validation)
   ```

2. **Review Key Documents**:
   - [spec.md](spec.md) - Feature requirements
   - [research.md](research.md) - Technical decisions
   - [data-model.md](data-model.md) - Data structures

---

## Quick Integration Guide

### 1. CPU Limiting (5 minutes)

**Add to video processing**:

```python
# src/video_processor.py

from src.cpu_limiter import CPULimiter

class VideoProcessor:
    def _process_with_subprocess(self, input_path, output_path, on_progress, on_log):
        # ... existing FFmpeg command building ...

        # ADD: CPU limiting integration
        limiter = None
        if self.state.cpu_limit_config.enabled:
            limiter = CPULimiter(self.state.cpu_limit_config)
            threads = limiter.calculate_threads()
            cmd.extend(["-threads", str(threads)])
            if on_log:
                on_log(f"CPU limit: {self.state.cpu_limit_config.limit_percent}% ({threads} threads)")

        process = subprocess.Popen(cmd, ...)

        # ADD: Apply priority and start monitoring
        if limiter:
            limiter.apply_priority(process)

            def cpu_callback(metrics):
                self.state.current_cpu_metrics = metrics
                # Optional: log CPU usage
                if on_log:
                    on_log(f"CPU: {metrics.process_cpu_percent:.1f}%")

            limiter.start_monitoring(process, cpu_callback)

        # ... existing progress monitoring loop ...

        process.wait()

        # ADD: Clean up monitoring
        if limiter:
            limiter.stop_monitoring()

        return success, error_msg
```

**Add UI controls** (src/ui/settings_panel.py):

```python
# Add to Performance section
cpu_frame = ctk.CTkFrame(performance_section, fg_color="transparent")
cpu_frame.pack(fill="x", pady=10)

cpu_checkbox = ctk.CTkCheckBox(
    cpu_frame,
    text="Enable CPU Limiting",
    command=lambda: self._on_cpu_toggle(cpu_checkbox, cpu_slider)
)
cpu_checkbox.pack(anchor="w")

cpu_slider = ctk.CTkSlider(
    cpu_frame,
    from_=20,
    to=95,
    number_of_steps=15,  # 5% increments
    command=lambda v: self._on_cpu_slider_change(int(v))
)
cpu_slider.set(self.state.cpu_limit_config.limit_percent)
cpu_slider.pack(fill="x", padx=20, pady=5)

def _on_cpu_toggle(self, checkbox, slider):
    enabled = checkbox.get() == 1
    self.state.cpu_limit_config.enabled = enabled
    slider.configure(state="normal" if enabled else "disabled")

def _on_cpu_slider_change(self, value):
    # Round to nearest 5%
    value = round(value / 5) * 5
    self.state.cpu_limit_config.limit_percent = value
```

### 2. Enhanced Settings (10 minutes)

**Create settings manager** (src/settings_manager.py):

```python
from pydantic import ValidationError
from src.state import ApplicationSettings
import json
from pathlib import Path

class SettingsManager:
    def __init__(self, settings_path: Path):
        self.settings_path = settings_path
        self.settings = self.load()

    def load(self) -> ApplicationSettings:
        """Load settings from disk or create defaults"""
        if self.settings_path.exists():
            try:
                data = json.loads(self.settings_path.read_text())
                return ApplicationSettings(**data)
            except (json.JSONDecodeError, ValidationError) as e:
                # Backup corrupt file
                backup = self.settings_path.with_suffix('.json.corrupt')
                self.settings_path.rename(backup)
                return ApplicationSettings()  # Defaults
        return ApplicationSettings()

    def save(self) -> None:
        """Atomically save settings with backup"""
        # Create backup
        if self.settings_path.exists():
            backup = self.settings_path.with_suffix('.json.backup')
            self.settings_path.replace(backup)

        # Write new settings
        self.settings_path.write_text(
            self.settings.model_dump_json(indent=2)
        )

    def update(self, category: str, key: str, value):
        """Update a specific setting"""
        category_obj = getattr(self.settings, category)
        setattr(category_obj, key, value)
        self.save()
```

**Integrate in main.py**:

```python
class MagicTVBoxApp:
    def __init__(self):
        # ... existing code ...

        # NEW: Initialize settings manager
        settings_path = Path.home() / ".magictvbox" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_manager = SettingsManager(settings_path)

        # Load settings into state
        self.state.cpu_limit_config = CPULimitConfig(
            enabled=self.settings_manager.settings.performance.cpu_limiting_enabled,
            limit_percent=self.settings_manager.settings.performance.cpu_limit_percent,
            priority_level=self.settings_manager.settings.performance.ffmpeg_priority
        )
```

### 3. Intro/Outro Detection (20 minutes)

**Basic detector** (src/intro_outro_detector.py):

```python
import cv2
import numpy as np
from typing import List, Optional
from src.state import DetectionResult, DetectedSegment

class IntroOutroDetector:
    def __init__(self, profiles_dir: Path):
        self.profiles_dir = profiles_dir
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def analyze_video(
        self,
        video_path: str,
        series_name: Optional[str] = None,
        progress_callback = None
    ) -> DetectionResult:
        """
        Analyze video for intro/outro segments.

        Args:
            video_path: Path to video file
            series_name: Optional series name for profile lookup
            progress_callback: Optional callback(percent: float)

        Returns:
            DetectionResult with detected segments
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return DetectionResult(
                file_path=video_path,
                error="Could not open video file"
            )

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps

        # Sample first 2 minutes for intro detection
        intro = self._detect_intro(cap, fps, total_frames, progress_callback)

        # Reset and sample last 2 minutes for outro
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames - int(2 * 60 * fps)))
        outro = self._detect_outro(cap, fps, total_frames, progress_callback)

        cap.release()

        return DetectionResult(
            file_path=video_path,
            series_id=self._get_series_id(series_name) if series_name else None,
            intro=intro,
            outro=outro,
            analysis_duration=0.0  # TODO: track actual time
        )

    def _detect_intro(self, cap, fps, total_frames, progress_callback):
        """Detect intro segment (simplified)"""
        # TODO: Implement perceptual hashing and pattern matching
        # For now, return placeholder
        return DetectedSegment(
            segment_type="intro",
            start_time=0.0,
            end_time=30.0,  # Assume 30 second intro
            confidence=0.60,  # Low confidence - needs review
            method="placeholder"
        )

    def _detect_outro(self, cap, fps, total_frames, progress_callback):
        """Detect outro segment (simplified)"""
        # TODO: Implement perceptual hashing and pattern matching
        return None  # No outro detected

    def _get_series_id(self, series_name: str) -> str:
        """Generate consistent series ID from name"""
        import hashlib
        return hashlib.md5(series_name.encode()).hexdigest()[:16]
```

**Add to UI** (src/ui/single_processor.py):

```python
# In options section, add detection checkbox
detection_checkbox = ctk.CTkCheckBox(
    options_frame,
    text="Detect and Skip Intro/Outro",
    command=self._on_detection_toggle
)
detection_checkbox.pack(anchor="w", pady=5)

def _on_detection_toggle(self):
    self.state.detection_enabled = self.detection_checkbox.get() == 1

# In processing thread, add detection step
if self.state.detection_enabled:
    detector = IntroOutroDetector(Path.home() / ".magictvbox" / "detection_profiles")
    result = detector.analyze_video(self.selected_file)

    if result.intro and not result.intro.needs_review:
        # Auto-apply high-confidence detection
        cut_start = result.intro.end_time
    elif result.intro:
        # Show review UI for low-confidence
        self._show_detection_review(result)
```

---

## Testing Your Changes

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run specific feature tests
pytest tests/unit/test_cpu_limiter.py -v
pytest tests/unit/test_settings_manager.py -v
pytest tests/unit/test_intro_outro_detector.py -v
```

### Manual Testing

1. **CPU Limiting**:
   ```
   - Enable CPU limiting at 50%
   - Start a video processing task
   - Monitor Task Manager/Activity Monitor
   - Verify CPU usage stays ~50% (±5%)
   - Try changing limit during processing
   ```

2. **Enhanced Settings**:
   ```
   - Modify settings in each tab
   - Close and reopen application
   - Verify settings persist
   - Try invalid values (expect validation errors)
   ```

3. **Intro/Outro Detection**:
   ```
   - Process a video with known intro
   - Verify detection UI shows segment
   - Confirm or correct detection
   - Process another episode of same series
   - Verify improved accuracy
   ```

---

## Common Integration Points

### Where to Add Your Code

| Feature | Primary Files | Secondary Files |
|---------|--------------|-----------------|
| CPU Limiting | `src/cpu_limiter.py` (NEW)<br>`src/video_processor.py` (MODIFY) | `src/state.py`<br>`src/ui/settings_panel.py` |
| Enhanced Settings | `src/settings_manager.py` (NEW)<br>`src/ui/settings_panel.py` (MODIFY) | `src/state.py`<br>`main.py` |
| Intro/Outro Detection | `src/intro_outro_detector.py` (NEW)<br>`src/ui/intro_outro_panel.py` (NEW) | `src/video_processor.py`<br>`src/state.py` |

### State Management

All feature state flows through `AppState`:

```python
# src/state.py modifications
@dataclass
class AppState:
    # NEW fields
    cpu_limit_config: CPULimitConfig = field(default_factory=CPULimitConfig)
    current_cpu_metrics: Optional[CPUMetrics] = None
    settings_manager: Optional[SettingsManager] = None
    detection_profiles: Dict[str, DetectionProfile] = field(default_factory=dict)
    detection_enabled: bool = False
```

---

## Troubleshooting

### CPU Limiting Not Working

1. Check psutil is installed: `pip show psutil`
2. Verify config enabled: `print(state.cpu_limit_config.enabled)`
3. Check FFmpeg command includes `-threads`: Look in logs
4. Platform-specific: Windows requires admin for high priority

### Settings Not Persisting

1. Check settings file location: `~/.magictvbox/settings.json`
2. Verify write permissions
3. Check for validation errors in console
4. Inspect backup file if corrupt: `settings.json.corrupt`

### Detection Not Finding Intros

1. Verify OpenCV can open video: `cv2.VideoCapture(path).isOpened()`
2. Check scipy installed: `pip show scipy`
3. Try with different video file
4. Review confidence threshold (default 0.75)

---

## Next Steps

1. Review [tasks.md](tasks.md) for detailed implementation tasks (generated by `/speckit.tasks`)
2. Check [plan.md](plan.md) for architecture decisions
3. Refer to [contracts/](contracts/) for API specifications
4. Run tests after each module completion

---

## Getting Help

- **Constitution**: `.specify/memory/constitution.md` - Non-negotiable principles
- **CLAUDE.md**: Current technologies and commands
- **Spec**: [spec.md](spec.md) - User requirements and success criteria
- **Research**: [research.md](research.md) - Technical decisions and alternatives

For questions or clarifications, refer to the documents above or reach out to the project maintainer.
