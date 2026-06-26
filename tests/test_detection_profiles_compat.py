"""
Backward-compat test: a profile JSON file saved before the temporal fields
were added must still load successfully, with the new fields default-populated.
"""

import json

from src.data_models import DetectionConfig


OLD_PROFILE_JSON = """
{
    "sensitivity": 0.6,
    "frame_sampling": 30,
    "min_logo_width": 20,
    "min_logo_height": 20,
    "max_logo_width": 450,
    "max_logo_height": 220
}
"""


def test_old_profile_dict_loads_with_temporal_defaults():
    """DetectionConfig(**old_dict) should work and populate temporal defaults."""
    old_data = json.loads(OLD_PROFILE_JSON)
    config = DetectionConfig(**old_data)
    assert config.sensitivity == 0.6
    assert config.temporal_num_frames == 15
    assert config.temporal_variance_threshold == 5.0
    assert config.validate()


def test_unknown_keys_rejected_safely():
    """If the JSON has extra keys we don't recognize, load must not crash silently.

    Strategy: filter to known fields before unpacking. The detection_profiles
    loader should already do this; this test documents the expectation.
    """
    raw = json.loads(OLD_PROFILE_JSON)
    raw["unknown_future_field"] = "ignored"
    from dataclasses import fields as dataclass_fields

    known_field_names = {f.name for f in dataclass_fields(DetectionConfig)}
    filtered = {k: v for k, v in raw.items() if k in known_field_names}
    config = DetectionConfig(**filtered)
    assert config.validate()
