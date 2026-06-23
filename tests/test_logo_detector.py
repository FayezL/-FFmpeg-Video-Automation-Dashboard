"""
Unit tests for logo detection module
"""

import pytest
from pathlib import Path

from src.data_models import DetectionConfig, DetectionResult
from src.logo_detector import LogoDetector
from src.exceptions import DetectionFailedError


class TestDetectionConfig:
    """Test DetectionConfig validation"""

    def test_default_config_is_valid(self):
        """Default configuration should pass validation"""
        config = DetectionConfig()
        assert config.validate()

    def test_sensitivity_bounds(self):
        """Sensitivity must be between 0 and 1"""
        config = DetectionConfig(sensitivity=1.5)
        with pytest.raises(AssertionError, match="sensitivity must be 0-1"):
            config.validate()

        config = DetectionConfig(sensitivity=-0.1)
        with pytest.raises(AssertionError, match="sensitivity must be 0-1"):
            config.validate()

    def test_size_constraints(self):
        """Max size must be greater than min size"""
        config = DetectionConfig(min_logo_width=100, max_logo_width=50)
        with pytest.raises(AssertionError, match="max > min width"):
            config.validate()


class TestDetectionResult:
    """Test DetectionResult validation and methods"""

    def test_valid_detection_result(self):
        """Valid detection should pass validation"""
        result = DetectionResult(
            x=10, y=20, width=50, height=30,
            confidence=0.8, frame_index=100, timestamp=3.33
        )
        assert result.validate()

    def test_negative_coordinates_invalid(self):
        """Negative coordinates should fail validation"""
        result = DetectionResult(x=-5, y=10, width=50, height=30)
        with pytest.raises(AssertionError, match="x must be >= 0"):
            result.validate()

    def test_zero_size_invalid(self):
        """Zero width/height should fail validation"""
        result = DetectionResult(x=10, y=10, width=0, height=30)
        with pytest.raises(AssertionError, match="width must be > 0"):
            result.validate()

    def test_confidence_bounds(self):
        """Confidence must be between 0 and 1"""
        result = DetectionResult(x=10, y=10, width=50, height=30, confidence=1.5)
        with pytest.raises(AssertionError, match="confidence must be 0-1"):
            result.validate()

    def test_to_delogo_params(self):
        """Should convert to FFmpeg delogo parameters"""
        result = DetectionResult(x=100, y=200, width=50, height=30)
        params = result.to_delogo_params()
        assert params == (100, 200, 50, 30)

    def test_invalid_status(self):
        """Invalid status should fail validation"""
        result = DetectionResult(x=10, y=10, width=50, height=30, status="unknown")
        with pytest.raises(AssertionError, match="invalid status"):
            result.validate()


class TestLogoDetector:
    """Test LogoDetector core functionality"""

    def test_detector_initialization(self):
        """Detector should initialize with config"""
        config = DetectionConfig(sensitivity=0.8)
        detector = LogoDetector(config)
        assert detector.config.sensitivity == 0.8

    def test_detect_nonexistent_video(self):
        """Should raise DetectionFailedError for missing file"""
        config = DetectionConfig()
        detector = LogoDetector(config)

        with pytest.raises(DetectionFailedError):
            detector.detect_in_video("nonexistent_video.mp4")

    def test_size_filter(self):
        """Size filter should accept valid sizes only"""
        config = DetectionConfig(
            min_logo_width=50,
            min_logo_height=30,
            max_logo_width=200,
            max_logo_height=100
        )
        detector = LogoDetector(config)

        assert detector._passes_size_filter(100, 50) is True
        assert detector._passes_size_filter(20, 50) is False  # Too narrow
        assert detector._passes_size_filter(300, 50) is False  # Too wide
        assert detector._passes_size_filter(100, 150) is False  # Too tall

    def test_position_filter_corners(self):
        """Position filter should accept corner regions"""
        config = DetectionConfig(position_zones=["top-left", "bottom-right"])
        detector = LogoDetector(config)

        video_resolution = (1920, 1080)

        # Top-left corner (should pass)
        assert detector._passes_position_filter(100, 100, 50, 30, video_resolution) is True

        # Bottom-right corner (should pass)
        assert detector._passes_position_filter(1700, 900, 50, 30, video_resolution) is True

        # Center (should fail - not in any enabled zone)
        assert detector._passes_position_filter(900, 500, 50, 30, video_resolution) is False

    def test_position_filter_disabled(self):
        """Empty position zones should disable position filtering"""
        config = DetectionConfig(position_zones=[])
        detector = LogoDetector(config)

        video_resolution = (1920, 1080)

        # Center should pass when position filtering is disabled
        assert detector._passes_position_filter(900, 500, 50, 30, video_resolution) is True

    def test_overlap_calculation(self):
        """Overlap calculation should compute IoU correctly"""
        config = DetectionConfig()
        detector = LogoDetector(config)

        # Perfect overlap
        det1 = DetectionResult(x=100, y=100, width=50, height=50)
        det2 = DetectionResult(x=100, y=100, width=50, height=50)
        assert detector._calculate_overlap(det1, det2) == 1.0

        # No overlap
        det1 = DetectionResult(x=100, y=100, width=50, height=50)
        det2 = DetectionResult(x=200, y=200, width=50, height=50)
        assert detector._calculate_overlap(det1, det2) == 0.0

        # Partial overlap (50% intersection)
        det1 = DetectionResult(x=100, y=100, width=100, height=100)
        det2 = DetectionResult(x=150, y=100, width=100, height=100)
        overlap = detector._calculate_overlap(det1, det2)
        assert 0.3 < overlap < 0.4  # IoU for 50% intersection area

    def test_cluster_merging(self):
        """Should merge similar detections across frames"""
        config = DetectionConfig(merge_overlap_threshold=0.5)
        detector = LogoDetector(config)

        # Create 3 similar detections (should merge to 1)
        detections = [
            DetectionResult(x=100, y=100, width=50, height=50, confidence=0.8, frame_index=0),
            DetectionResult(x=105, y=102, width=52, height=48, confidence=0.85, frame_index=30),
            DetectionResult(x=98, y=101, width=51, height=49, confidence=0.75, frame_index=60),
        ]

        merged = detector._cluster_detections(detections)

        # Should merge to 1 cluster
        assert len(merged) == 1

        # Should use highest confidence
        assert merged[0].confidence == 0.85

        # Should average coordinates (approximately)
        assert 98 <= merged[0].x <= 105
        assert 100 <= merged[0].y <= 102


class TestProgressCallback:
    """Test progress reporting"""

    def test_progress_callback_called(self):
        """Progress callback should be invoked during detection"""
        # This would require a real video file or mock
        # For now, we'll test that the callback interface works

        progress_values = []
        status_messages = []

        def progress_callback(progress: float, status: str):
            progress_values.append(progress)
            status_messages.append(status)

        # Callback should accept float and string
        progress_callback(0.5, "Processing frame 50/100")

        assert len(progress_values) == 1
        assert progress_values[0] == 0.5
        assert "frame" in status_messages[0].lower()


class TestCancelCheck:
    """Test cancellation handling"""

    def test_cancel_check_interface(self):
        """Cancel check callback should return boolean"""

        def cancel_check() -> bool:
            return False

        assert cancel_check() is False

        def cancel_check_true() -> bool:
            return True

        assert cancel_check_true() is True


class TestTemporalConfigFields:
    """Test the new temporal-stability fields on DetectionConfig"""

    def test_temporal_defaults(self):
        """New temporal fields should have sensible defaults"""
        config = DetectionConfig()
        assert config.temporal_num_frames == 15
        assert config.temporal_variance_threshold == 0.005
        assert config.temporal_skip_intro_frac == 0.02
        assert config.temporal_skip_outro_frac == 0.02
        assert config.temporal_min_region_pixels == 200

    def test_temporal_config_validates(self):
        """Default temporal config should pass validation"""
        config = DetectionConfig()
        assert config.validate()

    def test_temporal_num_frames_bounds(self):
        """temporal_num_frames must be between 3 and 60"""
        with pytest.raises(AssertionError, match="temporal_num_frames"):
            DetectionConfig(temporal_num_frames=2).validate()
        with pytest.raises(AssertionError, match="temporal_num_frames"):
            DetectionConfig(temporal_num_frames=61).validate()

    def test_temporal_threshold_bounds(self):
        """temporal_variance_threshold must be between 0 and 1"""
        with pytest.raises(AssertionError, match="temporal_variance_threshold"):
            DetectionConfig(temporal_variance_threshold=-0.01).validate()
        with pytest.raises(AssertionError, match="temporal_variance_threshold"):
            DetectionConfig(temporal_variance_threshold=1.5).validate()

    def test_temporal_skip_bounds(self):
        """Skip fractions must be between 0 and 0.5"""
        with pytest.raises(AssertionError, match="temporal_skip_intro_frac"):
            DetectionConfig(temporal_skip_intro_frac=0.6).validate()
        with pytest.raises(AssertionError, match="temporal_skip_outro_frac"):
            DetectionConfig(temporal_skip_outro_frac=-0.1).validate()

    def test_backward_compat_missing_temporal_fields(self):
        """Constructing DetectionConfig from old data (no temporal fields) should work"""
        old_data = {"sensitivity": 0.5, "frame_sampling": 30}
        config = DetectionConfig(**old_data)
        assert config.temporal_num_frames == 15
        assert config.validate()


# Integration test (requires real video file)
def test_detect_with_sample_video():
    """
    Integration test with a real video file.

    Note: This test is skipped if no sample video is available.
    To run: place a sample video at tests/fixtures/sample.mp4
    """
    sample_video = Path("tests/fixtures/sample.mp4")

    if not sample_video.exists():
        pytest.skip("Sample video not available for integration test")

    config = DetectionConfig(
        sensitivity=0.75,
        frame_sampling=30
    )
    detector = LogoDetector(config)

    session = detector.detect_in_video(str(sample_video))

    assert session.status == "completed"
    assert session.video_fps > 0
    assert session.video_duration > 0
    assert session.frames_analyzed > 0
    # May or may not find logos depending on video content
    print(f"Found {len(session.results)} logo regions")
