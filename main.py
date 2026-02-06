#!/usr/bin/env python3
"""
MagicTVBox - FFmpeg Video Automation Dashboard
Python Desktop Application
"""

import customtkinter as ctk
import tkinter.filedialog as filedialog
import threading
import os
from pathlib import Path
from typing import List, Optional, Dict
import json

from src.video_processor import VideoProcessor
from src.ui.batch_processor import BatchProcessorFrame
from src.ui.single_processor import SingleProcessorFrame
from src.ui.logs_panel import LogsPanel
from src.ui.settings_panel import SettingsPanel
from src.state import AppState

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MagicTVBoxApp:
    """Main application class"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("MagicTVBox - FFmpeg Video Automation")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Initialize state
        self.state = AppState()
        
        # Initialize video processor
        self.video_processor = VideoProcessor(self.state)
        
        # Create UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the main UI layout"""
        # Main container
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Sidebar
        self.sidebar = self._create_sidebar()
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        
        # Content area
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="#0f172a")
        self.content_frame.pack(side="right", fill="both", expand=True, padx=0, pady=0)
        
        # Create views
        self.views = {}
        self.current_view = None
        
        # Initialize views
        self.views['batch'] = BatchProcessorFrame(
            self.content_frame, 
            self.state, 
            self.video_processor
        )
        self.views['single'] = SingleProcessorFrame(
            self.content_frame, 
            self.state, 
            self.video_processor
        )
        self.views['logs'] = LogsPanel(self.content_frame, self.state)
        self.views['settings'] = SettingsPanel(self.content_frame, self.state)
        
        # Show default view
        self._switch_view('batch')
        
    def _create_sidebar(self) -> ctk.CTkFrame:
        """Create the sidebar navigation"""
        sidebar = ctk.CTkFrame(
            self.main_container, 
            width=250, 
            fg_color="#1e293b",
            corner_radius=0
        )
        
        # Header
        header = ctk.CTkFrame(sidebar, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        title = ctk.CTkLabel(
            header, 
            text="MagicTVBox", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            header, 
            text="FFmpeg Automation", 
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        )
        subtitle.pack(anchor="w", pady=(5, 0))
        
        # Navigation buttons
        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=10, pady=10)
        
        nav_items = [
            ("batch", "📊 Batch Processor"),
            ("single", "🎬 Single File"),
            ("settings", "⚙️ Settings"),
            ("logs", "📝 Logs"),
        ]
        
        self.nav_buttons = {}
        for view_id, label in nav_items:
            btn = ctk.CTkButton(
                nav_frame,
                text=label,
                command=lambda v=view_id: self._switch_view(v),
                fg_color="transparent",
                hover_color="#334155",
                anchor="w",
                height=45,
                font=ctk.CTkFont(size=14)
            )
            btn.pack(fill="x", padx=5, pady=2)
            self.nav_buttons[view_id] = btn
        
        return sidebar
    
    def _switch_view(self, view_id: str):
        """Switch between different views"""
        if self.current_view:
            self.views[self.current_view].pack_forget()
        
        # Update button states
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == view_id:
                btn.configure(fg_color="#2563eb", hover_color="#1d4ed8")
            else:
                btn.configure(fg_color="transparent", hover_color="#334155")
        
        # Show new view
        self.views[view_id].pack(fill="both", expand=True, padx=20, pady=20)
        self.current_view = view_id
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    """Entry point"""
    app = MagicTVBoxApp()
    app.run()


if __name__ == "__main__":
    main()


