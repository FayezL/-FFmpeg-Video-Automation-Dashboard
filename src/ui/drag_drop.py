"""
Drag-and-drop file handler for CustomTkinter.

This module provides drag-and-drop functionality for video files,
with automatic folder recursion and video file filtering.
"""

import os
from typing import List, Callable, Optional
from pathlib import Path


class DragDropHandler:
    """Handles drag-and-drop events for video files"""

    # Supported video file extensions
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm', '.flv', '.wmv', '.mpg', '.mpeg'}

    def __init__(self, widget, on_drop: Callable[[List[str]], None]):
        """
        Initialize drag-drop handler.

        Args:
            widget: CustomTkinter widget to enable drag-drop on
            on_drop: Callback when files are dropped (receives list of file paths)
        """
        self.widget = widget
        self.on_drop_callback = on_drop
        self._enabled = False
        self._has_tkdnd = False

        # Try to import tkinterdnd2
        try:
            from tkinterdnd2 import DND_FILES, TkinterDnD
            self._has_tkdnd = True
            self._dnd_files = DND_FILES
        except ImportError:
            self._has_tkdnd = False

    def enable(self) -> None:
        """Enable drag-drop on the widget"""
        if self._has_tkdnd:
            self._enable_tkdnd()
        self._enabled = True

    def disable(self) -> None:
        """Disable drag-drop on the widget"""
        if self._has_tkdnd and self._enabled:
            self._disable_tkdnd()
        self._enabled = False

    def set_drop_callback(self, callback: Callable[[List[str]], None]) -> None:
        """
        Update the drop callback function.

        Args:
            callback: New callback function
        """
        self.on_drop_callback = callback

    def filter_video_files(self, file_paths: List[str]) -> List[str]:
        """
        Filter list to only valid video files.

        Args:
            file_paths: List of file or folder paths

        Returns:
            List of video file paths (recursively scans folders)
        """
        video_files = []

        for path_str in file_paths:
            path = Path(path_str)

            if path.is_file():
                # Check if it's a video file
                if path.suffix.lower() in self.VIDEO_EXTENSIONS:
                    video_files.append(str(path.absolute()))

            elif path.is_dir():
                # Recursively scan directory for video files
                for item in path.rglob('*'):
                    if item.is_file() and item.suffix.lower() in self.VIDEO_EXTENSIONS:
                        video_files.append(str(item.absolute()))

        return sorted(video_files)

    def _enable_tkdnd(self) -> None:
        """Enable tkinterdnd2 drag-drop"""
        try:
            self.widget.drop_target_register(self._dnd_files)
            self.widget.dnd_bind('<<Drop>>', self._handle_drop)
            self.widget.dnd_bind('<<DragEnter>>', self._handle_drag_enter)
            self.widget.dnd_bind('<<DragLeave>>', self._handle_drag_leave)
        except Exception as e:
            print(f"Warning: Could not enable drag-drop: {e}")
            self._has_tkdnd = False

    def _disable_tkdnd(self) -> None:
        """Disable tkinterdnd2 drag-drop"""
        try:
            self.widget.dnd_unbind('<<Drop>>')
            self.widget.dnd_unbind('<<DragEnter>>')
            self.widget.dnd_unbind('<<DragLeave>>')
        except:
            pass

    def _handle_drag_enter(self, event) -> str:
        """
        Handle drag enter event for visual feedback.

        Args:
            event: Tkinter event object

        Returns:
            String indicating action (for tkinterdnd2)
        """
        # Visual feedback could be added here (highlight border, change color, etc.)
        return event.action

    def _handle_drag_leave(self, event) -> None:
        """
        Handle drag leave event.

        Args:
            event: Tkinter event object
        """
        # Remove visual feedback here
        pass

    def _handle_drop(self, event) -> str:
        """
        Handle drop event with file path parsing.

        Args:
            event: Tkinter event object containing dropped data

        Returns:
            String indicating action (for tkinterdnd2)
        """
        # Parse dropped file paths
        # tkinterdnd2 returns paths in a space-separated string with curly braces for paths with spaces
        raw_data = event.data

        # Parse the tkinterdnd2 format: {path with spaces} path_without_spaces {another path}
        paths = []
        current = ""
        in_braces = False

        for char in raw_data:
            if char == '{':
                in_braces = True
            elif char == '}':
                in_braces = False
                if current:
                    paths.append(current.strip())
                    current = ""
            elif char == ' ' and not in_braces:
                if current:
                    paths.append(current.strip())
                    current = ""
            else:
                current += char

        # Add last path if exists
        if current:
            paths.append(current.strip())

        # Filter to only video files
        video_files = self.filter_video_files(paths)

        # Call the callback with filtered files
        if video_files and self.on_drop_callback:
            self.on_drop_callback(video_files)

        return event.action
