"""
Template management for saving and loading processing configurations.

This module provides template persistence functionality, allowing users to save
and restore common processing configurations as named templates.
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
import time

from src.state import CutMode


@dataclass
class Template:
    """Saved configuration preset"""

    name: str
    description: str
    created_timestamp: float

    # Trim settings
    trim_mode: CutMode
    cut_minutes: float = 0.0
    cut_seconds: float = 0.0
    cut_start_minutes: float = 0.0
    cut_start_seconds: float = 0.0
    cut_end_minutes: Optional[float] = None
    cut_end_seconds: Optional[float] = None

    # Processing options
    processing_profile_key: str = "universal"
    apply_delogo: bool = False
    delogo_x: int = 1635
    delogo_y: int = 240
    delogo_w: int = 176
    delogo_h: int = 147

    # Output options
    output_format: str = "mp4"
    output_suffix: str = ""
    output_prefix: str = ""
    create_output_subfolder: bool = False
    overwrite_existing: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize template to dictionary.

        Returns:
            Dictionary representation of template
        """
        data = asdict(self)
        # Convert enum to string
        data["trim_mode"] = self.trim_mode.value
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Template":
        """
        Deserialize template from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Template object

        Raises:
            ValueError: If data is invalid
        """
        # Convert trim_mode string to enum
        if "trim_mode" in data:
            if isinstance(data["trim_mode"], str):
                data["trim_mode"] = CutMode(data["trim_mode"])

        return Template(**data)


class TemplateManager:
    """Template persistence and retrieval service"""

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize template manager.

        Args:
            templates_dir: Directory for template storage. Defaults to ~/.videoforge/templates/
        """
        if templates_dir is None:
            home = Path.home()
            templates_dir = str(home / ".videoforge" / "templates")

        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def save_template(self, template: Template) -> None:
        """
        Save a template to disk.

        Args:
            template: Template object to save

        Raises:
            ValueError: If template name invalid
            IOError: If unable to write file
        """
        if not self._is_valid_name(template.name):
            raise ValueError(f"Invalid template name: {template.name}")

        file_path = self._get_template_path(template.name)

        try:
            # Atomic write: write to temp file then rename
            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(template.to_dict(), f, indent=2)

            # Rename temp file to actual file (atomic on most systems)
            temp_path.replace(file_path)

        except OSError as e:
            raise IOError(f"Failed to save template: {e}")

    def load_template(self, name: str) -> Template:
        """
        Load a template by name.

        Args:
            name: Template name (without .json extension)

        Returns:
            Template object

        Raises:
            FileNotFoundError: If template doesn't exist
            ValueError: If template JSON is invalid
        """
        file_path = self._get_template_path(name)

        if not file_path.exists():
            raise FileNotFoundError(f"Template '{name}' not found")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Template.from_dict(data)

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise ValueError(f"Invalid template format: {e}")

    def list_templates(self) -> List[Tuple[str, str]]:
        """
        List all available templates.

        Returns:
            List of (name, description) tuples sorted by name
        """
        templates = []

        for file_path in self.templates_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    name = data.get("name", file_path.stem)
                    description = data.get("description", "")
                    templates.append((name, description))
            except:
                # Skip invalid template files
                continue

        return sorted(templates, key=lambda x: x[0].lower())

    def delete_template(self, name: str) -> None:
        """
        Delete a template.

        Args:
            name: Template name to delete

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        file_path = self._get_template_path(name)

        if not file_path.exists():
            raise FileNotFoundError(f"Template '{name}' not found")

        file_path.unlink()

    def template_exists(self, name: str) -> bool:
        """
        Check if a template exists.

        Args:
            name: Template name to check

        Returns:
            True if template exists, False otherwise
        """
        file_path = self._get_template_path(name)
        return file_path.exists()

    def export_template(self, name: str, export_path: str) -> None:
        """
        Export a template to a specific file path.

        Args:
            name: Template name to export
            export_path: Absolute path for exported JSON file

        Raises:
            FileNotFoundError: If template doesn't exist
            IOError: If unable to write export file
        """
        template = self.load_template(name)
        export_path_obj = Path(export_path)

        try:
            with open(export_path_obj, "w", encoding="utf-8") as f:
                json.dump(template.to_dict(), f, indent=2)
        except OSError as e:
            raise IOError(f"Failed to export template: {e}")

    def import_template(
        self, import_path: str, new_name: Optional[str] = None
    ) -> Template:
        """
        Import a template from a file.

        Args:
            import_path: Path to template JSON file
            new_name: Optional new name for imported template

        Returns:
            Imported Template object

        Raises:
            FileNotFoundError: If import file doesn't exist
            ValueError: If template JSON is invalid
        """
        import_path_obj = Path(import_path)

        if not import_path_obj.exists():
            raise FileNotFoundError(f"Import file not found: {import_path}")

        try:
            with open(import_path_obj, "r", encoding="utf-8") as f:
                data = json.load(f)

            template = Template.from_dict(data)

            # Override name if provided
            if new_name:
                template.name = new_name

            # Save to templates directory
            self.save_template(template)

            return template

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise ValueError(f"Invalid template format: {e}")

    def _is_valid_name(self, name: str) -> bool:
        """
        Validate template name.

        Args:
            name: Template name to validate

        Returns:
            True if valid, False otherwise
        """
        if not name or len(name) > 50:
            return False

        # Disallow path separators and special characters
        invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "\0"]
        return not any(char in name for char in invalid_chars)

    def _get_template_path(self, name: str) -> Path:
        """
        Get file path for a template.

        Args:
            name: Template name

        Returns:
            Path object for template file
        """
        return self.templates_dir / f"{name}.json"
