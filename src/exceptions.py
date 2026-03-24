"""
Exception hierarchy for VideoForge application

This module defines custom exceptions for error handling throughout
the application, particularly for logo detection features.
"""


class DetectionError(Exception):
    """Base exception for all detection-related errors"""

    pass


class VideoReadError(DetectionError):
    """Cannot read or parse video file"""

    def __init__(self, video_path: str, reason: str):
        self.video_path = video_path
        self.reason = reason
        super().__init__(f"Cannot read {video_path}: {reason}")


class InvalidVideoFormatError(VideoReadError):
    """Video format is not supported"""

    pass


class DetectionFailedError(DetectionError):
    """Detection process failed"""

    pass


class DetectionTimeoutError(DetectionFailedError):
    """Detection took too long (>5 minutes)"""

    def __init__(self, elapsed_time: float):
        self.elapsed_time = elapsed_time
        super().__init__(f"Detection timeout after {elapsed_time:.1f} seconds")


class DetectionCancelledError(DetectionFailedError):
    """User cancelled detection"""

    def __init__(self, frames_processed: int = 0, total_frames: int = 0):
        self.frames_processed = frames_processed
        self.total_frames = total_frames
        super().__init__(
            f"Detection cancelled ({frames_processed}/{total_frames} frames processed)"
        )


class ProfileError(DetectionError):
    """Base exception for profile-related errors"""

    pass


class ProfileValidationError(ProfileError):
    """Profile data is invalid"""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"Invalid profile field '{field}': {reason}")


class ProfileVersionError(ProfileError):
    """Profile version is not supported"""

    def __init__(self, version: str):
        self.version = version
        super().__init__(f"Unsupported profile version: {version}")


class DuplicateProfileError(ProfileError):
    """Profile with this name already exists"""

    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        super().__init__(f"Profile '{profile_name}' already exists")


class FrameNotFoundError(VideoReadError):
    """Requested frame index is invalid for the video"""

    def __init__(self, frame_index: int, total_frames: int):
        self.frame_index = frame_index
        self.total_frames = total_frames
        super().__init__(
            f"Frame {frame_index} not found (video has {total_frames} frames)",
            "Invalid frame index",
        )
