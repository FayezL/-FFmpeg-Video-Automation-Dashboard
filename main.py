#!/usr/bin/env python3
"""
VideoForge - FFmpeg Video Automation Dashboard
Python Desktop Application
"""

import customtkinter as ctk
import os
import sys
import tempfile
import time
from pathlib import Path

# Single-instance check using file lock
_lock_file = None


def check_single_instance():
    """
    Ensure only one instance of the application runs at a time.

    Returns True if this is the first instance, False if another instance is already running.
    """
    global _lock_file

    lock_path = Path(tempfile.gettempdir()) / "VideoForge.lock"

    try:
        if lock_path.exists():
            # Remove stale lock: process that created it is gone, or file is old
            try:
                pid_str = lock_path.read_text().strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    if pid != os.getpid() and not _is_process_running(pid):
                        lock_path.unlink()
                else:
                    # No valid PID; remove if file is older than 1 hour
                    if (time.time() - lock_path.stat().st_mtime) > 3600:
                        lock_path.unlink()
            except (OSError, ValueError):
                try:
                    lock_path.unlink()
                except OSError:
                    pass

        _lock_file = open(lock_path, "x")  # Exclusive creation
        _lock_file.write(str(os.getpid()))
        _lock_file.flush()
        return True

    except FileExistsError:
        return False
    except Exception:
        # If anything goes wrong, allow the app to start
        return True


def _is_process_running(pid: int) -> bool:
    """Return True if a process with the given PID is running."""
    if sys.platform == "win32":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            handle = kernel32.OpenProcess(
                0x1000, False, pid
            )  # PROCESS_QUERY_LIMITED_INFORMATION
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# Lazy imports for faster startup (T020)
# These will be imported when first needed
from src.video_processor import VideoProcessor  # noqa: E402
from src.ui.batch_processor import BatchProcessorFrame  # noqa: E402
from src.ui.single_processor import SingleProcessorFrame  # noqa: E402
from src.ui.logs_panel import LogsPanel  # noqa: E402
from src.ui.settings_panel import SettingsPanel  # noqa: E402
from src.state import AppState  # noqa: E402

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VideoForgeApp:
    """Main application class"""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("VideoForge - FFmpeg Video Automation")
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

        # Batch view: tabbed Task 1, Task 2, + Add task button for more
        self.batch_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.batch_tabview = ctk.CTkTabview(self.batch_container, fg_color="#0f172a")
        self.batch_tabview.pack(fill="both", expand=True)
        self.batch_tabview.add("Task 1")
        self.batch_tabview.add("Task 2")
        self.batch_tabview.set("Task 1")
        self.views["batch_task1"] = BatchProcessorFrame(
            self.batch_tabview.tab("Task 1"),
            self.state,
            self.video_processor,
            task_index=0,
        )
        self.views["batch_task1"].pack(fill="both", expand=True)
        self.views["batch_task2"] = BatchProcessorFrame(
            self.batch_tabview.tab("Task 2"),
            self.state,
            self.video_processor,
            task_index=1,
        )
        self.views["batch_task2"].pack(fill="both", expand=True)
        # Button row: Add task
        self.batch_btn_row = ctk.CTkFrame(self.batch_container, fg_color="transparent")
        self.batch_btn_row.pack(fill="x", pady=(8, 0))
        self.add_task_btn = ctk.CTkButton(
            self.batch_btn_row,
            text="＋ Add task tab",
            command=self._add_batch_task_tab,
            fg_color="#1e40af",
            hover_color="#2563eb",
            width=140,
            height=32,
        )
        self.add_task_btn.pack(side="left")
        self.batch_extra_frames = []  # Task 3, 4, ... frames
        self.views["batch"] = self.batch_container

        self.views["single"] = SingleProcessorFrame(
            self.content_frame, self.state, self.video_processor
        )
        self.views["logs"] = LogsPanel(self.content_frame, self.state)
        self.views["settings"] = SettingsPanel(self.content_frame, self.state)

        # Show default view
        self._switch_view("batch")

    def _create_sidebar(self) -> ctk.CTkFrame:
        """Create the sidebar navigation"""
        sidebar = ctk.CTkFrame(
            self.main_container, width=250, fg_color="#1e293b", corner_radius=0
        )

        # Header
        header = ctk.CTkFrame(sidebar, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)

        title = ctk.CTkLabel(
            header, text="VideoForge", font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header,
            text="FFmpeg Automation",
            font=ctk.CTkFont(size=12),
            text_color="#60a5fa",
        )
        subtitle.pack(anchor="w", pady=(5, 0))

        # Navigation buttons
        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=10, pady=10)

        nav_items = [
            ("batch", "▤  Batch Processor"),
            ("single", "▷  Single File"),
            ("settings", "⚙  Settings"),
            ("logs", "☰  Logs"),
        ]

        self.nav_buttons = {}
        for view_id, label in nav_items:
            btn = ctk.CTkButton(
                nav_frame,
                text=label,
                command=lambda v=view_id: self._switch_view(v),
                fg_color="transparent",
                hover_color="#1e40af",
                anchor="w",
                height=45,
                font=ctk.CTkFont(size=14),
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
                btn.configure(fg_color="#2563eb", hover_color="#3b82f6")
            else:
                btn.configure(fg_color="transparent", hover_color="#1e40af")

        # Show new view
        self.views[view_id].pack(fill="both", expand=True, padx=20, pady=20)
        self.current_view = view_id

    def _add_batch_task_tab(self):
        """Add a new task tab (Task 3, 4, ...)."""
        self.state.extra_task_slots.append(
            {
                "files": [],
                "output_folder": None,
                "processing": False,
            }
        )
        n = len(self.state.extra_task_slots)
        task_num = 2 + n  # Task 3, 4, 5 ...
        tab_name = f"Task {task_num}"
        self.batch_tabview.add(tab_name)
        task_index = 1 + n  # 2 for first extra, 3 for second, ...
        frame = BatchProcessorFrame(
            self.batch_tabview.tab(tab_name),
            self.state,
            self.video_processor,
            task_index=task_index,
        )
        frame.pack(fill="both", expand=True)
        self.batch_extra_frames.append(frame)
        self.batch_tabview.set(tab_name)

    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    """Entry point"""
    # T019: Single-instance check
    if not check_single_instance():
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            "VideoForge Already Running",
            "Another instance of VideoForge is already running.\n\n"
            "Please use the existing window or close it first.",
        )
        root.destroy()
        sys.exit(0)

    # T024: Check FFmpeg availability
    import shutil

    if not shutil.which("ffmpeg"):
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        result = messagebox.askyesno(
            "FFmpeg Not Found",
            "FFmpeg is required for video processing but was not found.\n\n"
            "The application can still launch, but video processing won't work "
            "until FFmpeg is installed.\n\n"
            "Do you want to continue anyway?",
            icon="warning",
        )
        root.destroy()

        if not result:
            sys.exit(0)

    # Start the application
    app = VideoForgeApp()
    app.run()

    global _lock_file
    if _lock_file:
        try:
            _lock_file.close()
            lock_path = Path(tempfile.gettempdir()) / "VideoForge.lock"
            if lock_path.exists():
                lock_path.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    main()
