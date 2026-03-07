"""
Settings Manager — Persistent application settings with validation.

Loads/saves settings from a JSON file, validates via Pydantic,
and handles migration from legacy AppState format.
"""

import json
import shutil
from pathlib import Path
from typing import Optional

from src.state import PYDANTIC_AVAILABLE

if PYDANTIC_AVAILABLE:
    from src.state import ApplicationSettings


def _default_settings_path() -> Path:
    """Platform-appropriate settings directory."""
    import sys
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Local" / "MagicTVBox"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "MagicTVBox"
    else:
        base = Path.home() / ".config" / "magictvbox"
    base.mkdir(parents=True, exist_ok=True)
    return base / "settings.json"


class SettingsManager:
    """Load, validate, persist, and migrate application settings."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or _default_settings_path()
        self.settings: "ApplicationSettings" = self.load()

    # ------------------------------------------------------------------
    # Core I/O
    # ------------------------------------------------------------------

    def load(self) -> "ApplicationSettings":
        """Load settings from disk. Falls back to defaults on any error."""
        if not PYDANTIC_AVAILABLE:
            from src.state import ApplicationSettings as Fallback
            return Fallback()

        if not self.path.exists():
            return ApplicationSettings()

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return ApplicationSettings(**data)
        except (json.JSONDecodeError, Exception):
            # Backup corrupt file and start fresh
            self._backup(suffix=".corrupt")
            return ApplicationSettings()

    def save(self) -> None:
        """Atomically save settings with a pre-write backup."""
        if not PYDANTIC_AVAILABLE:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Backup current file before overwriting
        if self.path.exists():
            self._backup(suffix=".backup")

        text = self.settings.model_dump_json(indent=2)
        self.path.write_text(text, encoding="utf-8")

    # ------------------------------------------------------------------
    # Granular update
    # ------------------------------------------------------------------

    def update(self, category: str, key: str, value) -> None:
        """Update a single setting, validate, and save.

        Raises ValueError if the new value is invalid.
        """
        if not PYDANTIC_AVAILABLE:
            return

        cat_obj = getattr(self.settings, category, None)
        if cat_obj is None:
            raise ValueError(f"Unknown settings category: {category}")
        if not hasattr(cat_obj, key):
            raise ValueError(f"Unknown setting: {category}.{key}")

        setattr(cat_obj, key, value)
        # Re-validate the whole category by reconstructing it
        cat_class = type(cat_obj)
        try:
            validated = cat_class(**cat_obj.model_dump())
            setattr(self.settings, category, validated)
        except Exception as exc:
            # Roll back the change
            self.settings = self.load()
            raise ValueError(str(exc)) from exc

        self.save()

    # ------------------------------------------------------------------
    # Migration
    # ------------------------------------------------------------------

    def migrate_from_state(self, state) -> None:
        """Import settings from an existing AppState (legacy migration)."""
        if not PYDANTIC_AVAILABLE:
            return

        from src.state import PerformanceSettings, OutputSettings, QualitySettings, AdvancedSettings

        self.settings.performance = PerformanceSettings(
            cpu_limiting_enabled=state.cpu_limit_config.enabled,
            cpu_limit_percent=state.cpu_limit_config.limit_percent,
            max_parallel_jobs=state.parallel_config.max_workers,
            ffmpeg_priority=state.cpu_limit_config.priority_level,
        )
        self.settings.output = OutputSettings(
            prefix=state.output_prefix,
            suffix=state.output_suffix,
            output_format=state.output_format,
            create_subfolder=state.create_output_subfolder,
        )
        self.settings.quality = QualitySettings(
            default_profile=state.processing_profile,
        )
        self.settings.advanced = AdvancedSettings()
        self.save()

    def apply_to_state(self, state) -> None:
        """Push persisted settings back into AppState on startup."""
        if not PYDANTIC_AVAILABLE:
            return

        perf = self.settings.performance
        state.cpu_limit_config.enabled = perf.cpu_limiting_enabled
        state.cpu_limit_config.limit_percent = perf.cpu_limit_percent
        state.cpu_limit_config.priority_level = perf.ffmpeg_priority
        state.parallel_config.max_workers = perf.max_parallel_jobs

        out = self.settings.output
        state.output_prefix = out.prefix
        state.output_suffix = out.suffix
        state.output_format = out.output_format
        state.create_output_subfolder = out.create_subfolder

        qual = self.settings.quality
        # Map display names to dict keys for backward compatibility
        from src.state import PROCESSING_PROFILES
        profile = qual.default_profile
        if profile not in PROCESSING_PROFILES:
            # Legacy settings.json may store display names like "Universal Compatible"
            name_to_key = {p.name: k for k, p in PROCESSING_PROFILES.items()}
            profile = name_to_key.get(profile, "universal")
        state.processing_profile = profile

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _backup(self, suffix: str = ".backup") -> None:
        """Copy current settings file to a backup."""
        backup = self.path.with_suffix(self.path.suffix + suffix)
        try:
            shutil.copy2(self.path, backup)
        except OSError:
            pass
