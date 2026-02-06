"""
Settings Panel UI Component
"""

import customtkinter as ctk

from src.state import AppState


class SettingsPanel(ctk.CTkScrollableFrame):
    """Settings panel view"""
    
    def __init__(self, parent, state: AppState):
        super().__init__(parent, fg_color="#0f172a")
        self.state = state
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI components"""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        title = ctk.CTkLabel(
            header,
            text="Settings",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            header,
            text="Configure application settings",
            font=ctk.CTkFont(size=14),
            text_color="#94a3b8"
        )
        subtitle.pack(anchor="w", pady=(5, 0))
        
        # FFmpeg Settings Section
        self._create_ffmpeg_section()
        
        # About Section
        self._create_about_section()
    
    def _create_ffmpeg_section(self):
        """Create FFmpeg settings section"""
        ffmpeg_frame = ctk.CTkFrame(self, fg_color="#1e293b")
        ffmpeg_frame.pack(fill="x", pady=(0, 20))
        
        title = ctk.CTkLabel(
            ffmpeg_frame,
            text="FFmpeg Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(anchor="w", padx=20, pady=(20, 15))
        
        content = ctk.CTkFrame(ffmpeg_frame, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=(0, 20))
        
        info_text = (
            "FFmpeg settings are currently hardcoded to ensure compatibility:\n\n"
            "• Video Codec: libx264\n"
            "• Preset: fast\n"
            "• CRF: 23\n"
            "• Pixel Format: yuv420p\n"
            "• Audio Codec: AAC\n"
            "• Audio Bitrate: 192k\n"
            "• Faststart: Enabled\n\n"
            "These settings provide a good balance between quality and file size,\n"
            "ensuring compatibility with iOS devices and TV boxes."
        )
        
        info_label = ctk.CTkLabel(
            content,
            text=info_text,
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8",
            justify="left",
            anchor="w"
        )
        info_label.pack(anchor="w", pady=10)
    
    def _create_about_section(self):
        """Create about section"""
        about_frame = ctk.CTkFrame(self, fg_color="#1e293b")
        about_frame.pack(fill="x", pady=(0, 20))
        
        title = ctk.CTkLabel(
            about_frame,
            text="About",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(anchor="w", padx=20, pady=(20, 15))
        
        content = ctk.CTkFrame(about_frame, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=(0, 20))
        
        about_text = (
            "MagicTVBox - FFmpeg Video Automation Dashboard\n\n"
            "Version: 1.0.0\n"
            "A modern desktop application for automating video processing tasks.\n\n"
            "Features:\n"
            "• Batch processing of video files\n"
            "• Automatic cutting of last 5 minutes\n"
            "• Delogo filter for removing watermarks\n"
            "• Real-time progress tracking\n"
            "• Modern dark-themed UI\n\n"
            "Built with Python and CustomTkinter"
        )
        
        about_label = ctk.CTkLabel(
            content,
            text=about_text,
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8",
            justify="left",
            anchor="w"
        )
        about_label.pack(anchor="w", pady=10)


