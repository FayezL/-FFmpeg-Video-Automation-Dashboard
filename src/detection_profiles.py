"""
Detection profile management module

This module handles saving, loading, and managing logo detection profiles.
Profiles store detection settings and learned patterns for recurring logos.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from src.data_models import DetectionProfile, DetectionConfig, ProfileStatistics
from src.exceptions import ProfileError


def get_profiles_dir() -> Path:
    """Get the profiles directory path, creating it if necessary"""
    if os.name == "nt":  # Windows
        base_dir = Path(os.environ.get("APPDATA", "~"))
    else:  # macOS/Linux
        base_dir = Path.home() / ".config"

    profiles_dir = base_dir / "VideoForge" / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    return profiles_dir


def sanitize_filename(name: str) -> str:
    """
    Sanitize profile name for use as filename.

    Converts to lowercase, replaces spaces with underscores,
    removes special characters.
    """
    # Replace spaces with underscores
    sanitized = name.lower().replace(" ", "_")
    # Remove special characters, keep alphanumeric and underscores
    sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")
    # Fallback if empty
    if not sanitized:
        sanitized = "profile"
    return sanitized


def save_profile(profile: DetectionProfile) -> Path:
    """
    Save a detection profile to JSON file.

    Args:
        profile: DetectionProfile object to save

    Returns:
        Path to saved profile file

    Raises:
        ProfileError: If save fails
    """
    try:
        profiles_dir = get_profiles_dir()
        filename = f"{sanitize_filename(profile.name)}.json"
        filepath = profiles_dir / filename

        # Prepare profile data
        profile_data = {
            "profile_id": profile.profile_id,
            "name": profile.name,
            "description": profile.description,
            "config": {
                "sensitivity": profile.config.sensitivity,
                "frame_sampling": profile.config.frame_sampling,
                "max_frames_to_analyze": profile.config.max_frames_to_analyze,
                "detection_scale_max_height": profile.config.detection_scale_max_height,
                "min_logo_width": profile.config.min_logo_width,
                "min_logo_height": profile.config.min_logo_height,
                "max_logo_width": profile.config.max_logo_width,
                "max_logo_height": profile.config.max_logo_height,
                "aspect_ratio_min": profile.config.aspect_ratio_min,
                "aspect_ratio_max": profile.config.aspect_ratio_max,
                "position_zones": profile.config.position_zones,
                "edge_threshold_low": profile.config.edge_threshold_low,
                "edge_threshold_high": profile.config.edge_threshold_high,
                "enable_template_matching": profile.config.enable_template_matching,
                "merge_overlap_threshold": profile.config.merge_overlap_threshold,
                "min_confidence_to_report": profile.config.min_confidence_to_report,
            },
            "created_at": datetime.now().isoformat(),
            "version": 1,
        }

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)

        return filepath

    except Exception as e:
        raise ProfileError(f"Failed to save profile: {e}")


def load_profile(profile_name: str) -> DetectionProfile:
    """
    Load a detection profile from JSON file.

    Args:
        profile_name: Name of profile to load

    Returns:
        DetectionProfile object

    Raises:
        ProfileError: If load fails or profile not found
    """
    try:
        profiles_dir = get_profiles_dir()
        filename = f"{sanitize_filename(profile_name)}.json"
        filepath = profiles_dir / filename

        if not filepath.exists():
            raise ProfileError(f"Profile '{profile_name}' not found")

        with open(filepath, "r", encoding="utf-8") as f:
            profile_data = json.load(f)

        # Validate required fields
        required_fields = ["name", "config"]
        for field in required_fields:
            if field not in profile_data:
                raise ProfileError(f"Invalid profile: missing field '{field}'")

        # Reconstruct DetectionConfig
        config_data = profile_data["config"]
        config = DetectionConfig(
            sensitivity=config_data.get("sensitivity", 0.75),
            frame_sampling=config_data.get("frame_sampling", 30),
            max_frames_to_analyze=config_data.get("max_frames_to_analyze", 5),
            detection_scale_max_height=config_data.get(
                "detection_scale_max_height", 720
            ),
            min_logo_width=config_data.get("min_logo_width", 20),
            min_logo_height=config_data.get("min_logo_height", 20),
            max_logo_width=config_data.get("max_logo_width", 450),
            max_logo_height=config_data.get("max_logo_height", 220),
            aspect_ratio_min=config_data.get("aspect_ratio_min", 0.5),
            aspect_ratio_max=config_data.get("aspect_ratio_max", 5.0),
            position_zones=config_data.get(
                "position_zones",
                ["top-left", "top-right", "bottom-left", "bottom-right"],
            ),
            edge_threshold_low=config_data.get("edge_threshold_low", 50),
            edge_threshold_high=config_data.get("edge_threshold_high", 150),
            enable_template_matching=config_data.get("enable_template_matching", False),
            merge_overlap_threshold=config_data.get("merge_overlap_threshold", 0.5),
            min_confidence_to_report=config_data.get("min_confidence_to_report", 0.35),
        )

        # Create DetectionProfile
        profile = DetectionProfile(
            profile_id=profile_data.get("profile_id", ""),
            name=profile_data["name"],
            description=profile_data.get("description"),
            config=config,
        )

        return profile

    except json.JSONDecodeError as e:
        raise ProfileError(f"Invalid profile JSON: {e}")
    except Exception as e:
        if isinstance(e, ProfileError):
            raise
        raise ProfileError(f"Failed to load profile: {e}")


def list_profiles() -> List[Dict[str, Any]]:
    """
    List all available detection profiles with metadata.

    Returns:
        List of dicts with profile info (name, description, created_at)
    """
    try:
        profiles_dir = get_profiles_dir()
        profiles = []

        for filepath in profiles_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)

                profiles.append(
                    {
                        "name": profile_data.get("name", filepath.stem),
                        "description": profile_data.get("description", ""),
                        "created_at": profile_data.get("created_at", ""),
                        "filepath": str(filepath),
                    }
                )
            except (json.JSONDecodeError, KeyError):
                # Skip invalid profiles
                continue

        # Sort by name
        profiles.sort(key=lambda p: p["name"])

        return profiles

    except Exception as e:
        raise ProfileError(f"Failed to list profiles: {e}")


def delete_profile(profile_name: str) -> None:
    """
    Delete a detection profile file.

    Args:
        profile_name: Name of profile to delete

    Raises:
        ProfileError: If deletion fails or profile not found
    """
    try:
        profiles_dir = get_profiles_dir()
        filename = f"{sanitize_filename(profile_name)}.json"
        filepath = profiles_dir / filename

        if not filepath.exists():
            raise ProfileError(f"Profile '{profile_name}' not found")

        filepath.unlink()

    except Exception as e:
        if isinstance(e, ProfileError):
            raise
        raise ProfileError(f"Failed to delete profile: {e}")


def profile_exists(profile_name: str) -> bool:
    """Check if a profile with the given name exists"""
    profiles_dir = get_profiles_dir()
    filename = f"{sanitize_filename(profile_name)}.json"
    filepath = profiles_dir / filename
    return filepath.exists()
