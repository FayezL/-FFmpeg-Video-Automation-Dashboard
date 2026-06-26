"""
Tests for drag-and-drop functionality.

This module tests the DragDropHandler class for proper file filtering,
folder recursion, and duplicate detection.
"""

from src.ui.drag_drop import DragDropHandler


class TestDragDropHandler:
    """Test suite for DragDropHandler class"""

    def test_filter_video_files_with_mixed_types(self, tmp_path):
        """Test filtering with mixed file types"""
        # Create test files
        video_file = tmp_path / "video.mp4"
        text_file = tmp_path / "readme.txt"
        image_file = tmp_path / "image.png"

        video_file.touch()
        text_file.touch()
        image_file.touch()

        handler = DragDropHandler(None, lambda x: None)
        result = handler.filter_video_files([
            str(video_file),
            str(text_file),
            str(image_file)
        ])

        assert len(result) == 1
        assert str(video_file.absolute()) in result

    def test_filter_video_files_with_folder_recursion(self, tmp_path):
        """Test folder recursion for video files"""
        # Create nested directory structure
        subdir = tmp_path / "videos" / "subfolder"
        subdir.mkdir(parents=True)

        video1 = tmp_path / "video1.mp4"
        video2 = tmp_path / "videos" / "video2.mkv"
        video3 = subdir / "video3.avi"
        text_file = subdir / "readme.txt"

        video1.touch()
        video2.touch()
        video3.touch()
        text_file.touch()

        handler = DragDropHandler(None, lambda x: None)
        result = handler.filter_video_files([str(tmp_path)])

        assert len(result) == 3
        assert all(any(v in r for v in ["video1.mp4", "video2.mkv", "video3.avi"]) for r in result)

    def test_filter_video_files_supports_all_extensions(self):
        """Test that all video extensions are supported"""
        handler = DragDropHandler(None, lambda x: None)

        expected_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm'}
        assert expected_extensions.issubset(handler.VIDEO_EXTENSIONS)

    def test_enable_disable(self):
        """Test enabling and disabling drag-drop"""
        handler = DragDropHandler(None, lambda x: None)

        # Should not raise errors even without tkinterdnd2
        handler.enable()
        handler.disable()

        assert True  # If we got here without exceptions, test passes

    def test_set_drop_callback(self):
        """Test updating drop callback"""
        called = []

        def callback1(files):
            called.append(1)

        def callback2(files):
            called.append(2)

        handler = DragDropHandler(None, callback1)
        handler.set_drop_callback(callback2)

        assert handler.on_drop_callback == callback2

    def test_empty_file_list(self):
        """Test handling empty file list"""
        handler = DragDropHandler(None, lambda x: None)
        result = handler.filter_video_files([])

        assert result == []

    def test_nonexistent_path(self):
        """Test handling nonexistent paths"""
        handler = DragDropHandler(None, lambda x: None)
        result = handler.filter_video_files(["/nonexistent/path/video.mp4"])

        assert result == []

    def test_case_insensitive_extensions(self, tmp_path):
        """Test that file extensions are case-insensitive"""
        video_upper = tmp_path / "VIDEO.MP4"
        video_mixed = tmp_path / "video.MkV"
        video_lower = tmp_path / "video.avi"

        video_upper.touch()
        video_mixed.touch()
        video_lower.touch()

        handler = DragDropHandler(None, lambda x: None)
        result = handler.filter_video_files([str(tmp_path)])

        assert len(result) == 3
