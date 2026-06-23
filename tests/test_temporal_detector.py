"""
Unit tests for the temporal-stability logo detector.

Most tests use synthetic NumPy frame stacks (no real video files needed).
The end-to-end `detect_in_video` test on a real video lives in
tests/integration/test_temporal_detection.py.
"""

from src.data_models import DetectionConfig
from src.logo_detector_temporal import TemporalLogoDetector


class TestTemporalLogoDetectorSkeleton:
    """Verify the class exists and has the expected interface."""

    def test_can_instantiate_with_config(self):
        config = DetectionConfig()
        detector = TemporalLogoDetector(config)
        assert detector.config is config

    def test_has_detect_in_video_method(self):
        detector = TemporalLogoDetector(DetectionConfig())
        assert callable(getattr(detector, "detect_in_video", None))
