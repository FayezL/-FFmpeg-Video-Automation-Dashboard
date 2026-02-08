"""
Batch Processor UI Component
"""

import customtkinter as ctk
import tkinter.filedialog as filedialog
from tkinter import messagebox
from typing import List
import threading
import os
import glob

from src.state import AppState, ProcessingFile, FileStatus, CutMode
from src.video_processor import VideoProcessor
from src.ui.drag_drop import DragDropHandler

# Video file extensions for scanning
VIDEO_EXTENSIONS = ('*.mp4', '*.mkv', '*.avi', '*.mov', '*.m4v', '*.webm')


class BatchProcessorFrame(ctk.CTkScrollableFrame):
    """Batch processor view with expanded options"""
    
    def __init__(self, parent, state: AppState, processor: VideoProcessor):
        super().__init__(parent, fg_color="#0f172a")
        self.state = state
        self.processor = processor
        self.drag_drop_handler = None  # Will be initialized after UI creation

        self._create_ui()
        self.state.register_log_callback(self._on_log_update)

        # Initialize drag-drop after UI is created
        self._init_drag_drop()
    
    def _create_ui(self):
        """Create the UI components"""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))
        
        title = ctk.CTkLabel(
            header,
            text="Batch Processor",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            header,
            text="Process multiple videos with customizable trim, delogo, and output options",
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8"
        )
        subtitle.pack(anchor="w", pady=(4, 0))
        
        # === INPUT SECTION ===
        self._create_input_section()
        
        # === TRIM/CUT SECTION ===
        self._create_trim_section()

        # === PROCESSING PROFILE SECTION ===
        self._create_profile_section()

        # === PROCESSING OPTIONS (Delogo) ===
        self._create_delogo_section()
        
        # === OUTPUT SECTION ===
        self._create_output_section()
        
        # === FILE LIST ===
        self._create_file_section()
        
        # === ACTION BUTTONS ===
        self.progress_frame = None
        self._create_action_buttons()
    
    def _create_input_section(self):
        """Input source section - files or folder"""
        input_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
        input_frame.pack(fill="x", pady=(0, 12))
        
        # Section header
        section_header = ctk.CTkFrame(input_frame, fg_color="transparent")
        section_header.pack(fill="x", padx=16, pady=(16, 12))
        
        ctk.CTkLabel(
            section_header,
            text="📁 Input Source",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")
        
        content = ctk.CTkFrame(input_frame, fg_color="transparent")
        content.pack(fill="x", padx=16, pady=(0, 16))
        
        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 8))
        
        ctk.CTkButton(
            btn_row,
            text="Select Files",
            command=self._select_files,
            width=130,
            height=36,
            fg_color="#334155",
            hover_color="#475569"
        ).pack(side="left", padx=(0, 8))
        
        ctk.CTkButton(
            btn_row,
            text="Select Folder",
            command=self._select_folder,
            width=130,
            height=36,
            fg_color="#334155",
            hover_color="#475569"
        ).pack(side="left", padx=(0, 8))
        
        # Pattern filter
        pattern_row = ctk.CTkFrame(content, fg_color="transparent")
        pattern_row.pack(fill="x", pady=(4, 0))
        
        ctk.CTkLabel(
            pattern_row,
            text="File pattern:",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
            width=80
        ).pack(side="left", padx=(0, 8))
        
        self.pattern_entry = ctk.CTkEntry(
            pattern_row,
            placeholder_text="e.g. *.mkv or S01E*.mp4 (leave empty for all)",
            width=320,
            height=32
        )
        self.pattern_entry.pack(side="left")
        self.pattern_entry.insert(0, "*")
    
    def _create_trim_section(self):
        """Trim/Cut options section"""
        trim_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
        trim_frame.pack(fill="x", pady=(0, 12))
        
        section_header = ctk.CTkFrame(trim_frame, fg_color="transparent")
        section_header.pack(fill="x", padx=16, pady=(16, 12))
        
        ctk.CTkLabel(
            section_header,
            text="✂️ Trim / Cut Options",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")
        
        content = ctk.CTkFrame(trim_frame, fg_color="transparent")
        content.pack(fill="x", padx=16, pady=(0, 16))
        
        # Mode selector
        mode_row = ctk.CTkFrame(content, fg_color="transparent")
        mode_row.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(
            mode_row,
            text="Mode:",
            font=ctk.CTkFont(size=13),
            width=100
        ).pack(side="left", padx=(0, 12))
        
        self.cut_mode_var = ctk.StringVar(value="cut_last")
        modes = [
            ("none", "No trim"),
            ("cut_last", "Cut last X min"),
            ("cut_first", "Cut first X min"),
            ("cut_range", "Cut range (start→end)"),
        ]
        mode_btns = ctk.CTkFrame(mode_row, fg_color="transparent")
        mode_btns.pack(side="left")
        for val, label in modes:
            rb = ctk.CTkRadioButton(
                mode_btns,
                text=label,
                variable=self.cut_mode_var,
                value=val,
                command=self._on_cut_mode_change,
                font=ctk.CTkFont(size=12)
            )
            rb.pack(side="left", padx=(0, 16))
        
        # Cut parameters row
        self.cut_params_row = ctk.CTkFrame(content, fg_color="transparent")
        self.cut_params_row.pack(fill="x", pady=(8, 0))
        
        # Cut last/first minutes
        self.cut_minutes_frame = ctk.CTkFrame(self.cut_params_row, fg_color="transparent")
        self.cut_minutes_frame.pack(side="left", padx=(100, 0))

        # Hours
        ctk.CTkLabel(
            self.cut_minutes_frame,
            text="Hours:",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        ).pack(side="left", padx=(0, 8))

        self.cut_hours_entry = ctk.CTkEntry(
            self.cut_minutes_frame,
            width=60,
            height=28
        )
        self.cut_hours_entry.pack(side="left", padx=(0, 8))
        self.cut_hours_entry.insert(0, "0")

        # Minutes
        ctk.CTkLabel(
            self.cut_minutes_frame,
            text="Minutes:",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        ).pack(side="left", padx=(0, 8))

        self.cut_minutes_entry = ctk.CTkEntry(
            self.cut_minutes_frame,
            width=60,
            height=28
        )
        self.cut_minutes_entry.pack(side="left", padx=(0, 8))
        self.cut_minutes_entry.insert(0, "5")

        # Seconds
        ctk.CTkLabel(
            self.cut_minutes_frame,
            text="Seconds:",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        ).pack(side="left", padx=(0, 8))

        self.cut_seconds_entry = ctk.CTkEntry(
            self.cut_minutes_frame,
            width=60,
            height=28
        )
        self.cut_seconds_entry.pack(side="left")
        self.cut_seconds_entry.insert(0, "0")
        
        # Cut range (start, end)
        self.cut_range_frame = ctk.CTkFrame(self.cut_params_row, fg_color="transparent")
        self.cut_range_frame.pack(side="left", padx=(100, 0))

        # Start time
        ctk.CTkLabel(self.cut_range_frame, text="Start:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(side="left", padx=(0, 6))

        self.cut_start_hours_entry = ctk.CTkEntry(self.cut_range_frame, width=45, height=28)
        self.cut_start_hours_entry.pack(side="left", padx=(0, 2))
        self.cut_start_hours_entry.insert(0, "0")
        ctk.CTkLabel(self.cut_range_frame, text="h", font=ctk.CTkFont(size=11), text_color="#64748b").pack(side="left", padx=(0, 6))

        self.cut_start_entry = ctk.CTkEntry(self.cut_range_frame, width=45, height=28)
        self.cut_start_entry.pack(side="left", padx=(0, 2))
        self.cut_start_entry.insert(0, "0")
        ctk.CTkLabel(self.cut_range_frame, text="m", font=ctk.CTkFont(size=11), text_color="#64748b").pack(side="left", padx=(0, 6))

        self.cut_start_sec_entry = ctk.CTkEntry(self.cut_range_frame, width=45, height=28)
        self.cut_start_sec_entry.pack(side="left", padx=(0, 2))
        self.cut_start_sec_entry.insert(0, "0")
        ctk.CTkLabel(self.cut_range_frame, text="s", font=ctk.CTkFont(size=11), text_color="#64748b").pack(side="left", padx=(0, 16))

        # End time
        ctk.CTkLabel(self.cut_range_frame, text="End:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(side="left", padx=(0, 6))

        self.cut_end_hours_entry = ctk.CTkEntry(self.cut_range_frame, width=45, height=28)
        self.cut_end_hours_entry.pack(side="left", padx=(0, 2))
        self.cut_end_hours_entry.insert(0, "")
        ctk.CTkLabel(self.cut_range_frame, text="h", font=ctk.CTkFont(size=11), text_color="#64748b").pack(side="left", padx=(0, 6))

        self.cut_end_entry = ctk.CTkEntry(self.cut_range_frame, width=45, height=28)
        self.cut_end_entry.pack(side="left", padx=(0, 2))
        self.cut_end_entry.insert(0, "")
        ctk.CTkLabel(self.cut_range_frame, text="m", font=ctk.CTkFont(size=11), text_color="#64748b").pack(side="left", padx=(0, 6))

        self.cut_end_sec_entry = ctk.CTkEntry(self.cut_range_frame, width=45, height=28)
        self.cut_end_sec_entry.pack(side="left", padx=(0, 2))
        self.cut_end_sec_entry.insert(0, "")
        ctk.CTkLabel(self.cut_range_frame, text="s", font=ctk.CTkFont(size=11), text_color="#64748b").pack(side="left")
        
        self._on_cut_mode_change()

    def _create_profile_section(self):
        """Processing profile/quality section"""
        from src.state import PROCESSING_PROFILES

        profile_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
        profile_frame.pack(fill="x", pady=(0, 12))

        section_header = ctk.CTkFrame(profile_frame, fg_color="transparent")
        section_header.pack(fill="x", padx=16, pady=(16, 12))

        ctk.CTkLabel(
            section_header,
            text="🎬 Processing Profile",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")

        content = ctk.CTkFrame(profile_frame, fg_color="transparent")
        content.pack(fill="x", padx=16, pady=(0, 16))

        # Profile selector row
        profile_row = ctk.CTkFrame(content, fg_color="transparent")
        profile_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            profile_row,
            text="Quality preset:",
            font=ctk.CTkFont(size=13),
            width=120,
            anchor="w"
        ).pack(side="left", padx=(0, 12))

        self.profile_var = ctk.StringVar(value=self.state.processing_profile)

        profile_menu = ctk.CTkOptionMenu(
            profile_row,
            values=list(PROCESSING_PROFILES.keys()),
            variable=self.profile_var,
            command=self._on_profile_change,
            width=250,
            height=36
        )
        profile_menu.pack(side="left")

        # Profile description
        self.profile_desc_label = ctk.CTkLabel(
            content,
            text=PROCESSING_PROFILES[self.state.processing_profile].description,
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
            wraplength=600,
            anchor="w",
            justify="left"
        )
        self.profile_desc_label.pack(anchor="w", pady=(8, 0), padx=(120, 0))

    def _create_delogo_section(self):
        """Delogo filter section"""
        delogo_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
        delogo_frame.pack(fill="x", pady=(0, 12))
        
        section_header = ctk.CTkFrame(delogo_frame, fg_color="transparent")
        section_header.pack(fill="x", padx=16, pady=(16, 12))
        
        self.delogo_checkbox = ctk.CTkCheckBox(
            section_header,
            text="🎭 Apply Delogo Filter",
            command=self._on_delogo_toggle,
            font=ctk.CTkFont(size=14)
        )
        self.delogo_checkbox.pack(anchor="w")
        if self.state.apply_delogo:
            self.delogo_checkbox.select()
        
        self.delogo_params_frame = ctk.CTkFrame(delogo_frame, fg_color="transparent")
        self.delogo_params_frame.pack(fill="x", padx=16, pady=(0, 16))
        
        params = self.state.delogo_params
        labels = ["X", "Y", "Width", "Height"]
        values = [params.x, params.y, params.w, params.h]
        
        self.delogo_inputs = []
        for i, (label, value) in enumerate(zip(labels, values)):
            f = ctk.CTkFrame(self.delogo_params_frame, fg_color="transparent")
            f.pack(side="left", padx=(0, 16))
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11), text_color="#94a3b8").pack(anchor="w")
            e = ctk.CTkEntry(f, width=70, height=28)
            e.insert(0, str(value))
            e.pack(anchor="w", pady=(2, 0))
            e.bind('<KeyRelease>', lambda ev, idx=i: self._on_delogo_param_change(idx))
            self.delogo_inputs.append(e)
        
        if not self.state.apply_delogo:
            self.delogo_params_frame.pack_forget()
    
    def _create_output_section(self):
        """Output options section"""
        output_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
        output_frame.pack(fill="x", pady=(0, 12))
        
        section_header = ctk.CTkFrame(output_frame, fg_color="transparent")
        section_header.pack(fill="x", padx=16, pady=(16, 12))
        
        ctk.CTkLabel(
            section_header,
            text="📤 Output Options",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")
        
        content = ctk.CTkFrame(output_frame, fg_color="transparent")
        content.pack(fill="x", padx=16, pady=(0, 16))
        
        # Output folder row
        folder_row = ctk.CTkFrame(content, fg_color="transparent")
        folder_row.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(
            folder_row,
            text="Output folder:",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
            width=100
        ).pack(side="left", padx=(0, 8))
        
        self.output_label = ctk.CTkLabel(
            folder_row,
            text=self.state.output_folder or "Not selected",
            font=ctk.CTkFont(size=12),
            text_color="#cbd5e1"
        )
        self.output_label.pack(side="left", fill="x", expand=True)
        
        ctk.CTkButton(
            folder_row,
            text="Browse",
            command=self._select_output_folder,
            width=90,
            height=32
        ).pack(side="right")
        
        # Output format & naming row
        opts_row = ctk.CTkFrame(content, fg_color="transparent")
        opts_row.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(opts_row, text="Format:", font=ctk.CTkFont(size=12), text_color="#94a3b8", width=100).pack(side="left", padx=(0, 8))
        self.format_var = ctk.StringVar(value=self.state.output_format)
        format_menu = ctk.CTkOptionMenu(
            opts_row,
            values=["mp4", "mkv"],
            variable=self.format_var,
            command=self._on_format_change,
            width=100,
            height=32
        )
        format_menu.pack(side="left", padx=(0, 24))
        
        ctk.CTkLabel(opts_row, text="Prefix:", font=ctk.CTkFont(size=12), text_color="#94a3b8", width=60).pack(side="left", padx=(0, 8))
        self.prefix_entry = ctk.CTkEntry(opts_row, width=100, height=28)
        self.prefix_entry.insert(0, self.state.output_prefix)
        self.prefix_entry.pack(side="left", padx=(0, 16))
        
        ctk.CTkLabel(opts_row, text="Suffix:", font=ctk.CTkFont(size=12), text_color="#94a3b8", width=60).pack(side="left", padx=(0, 8))
        self.suffix_entry = ctk.CTkEntry(opts_row, width=100, height=28)
        self.suffix_entry.insert(0, self.state.output_suffix)
        self.suffix_entry.pack(side="left")
        
        # Checkboxes row
        cb_row = ctk.CTkFrame(content, fg_color="transparent")
        cb_row.pack(fill="x", pady=(8, 0))
        
        self.subfolder_cb = ctk.CTkCheckBox(
            cb_row,
            text="Create 'output' subfolder",
            command=self._on_subfolder_toggle,
            font=ctk.CTkFont(size=12)
        )
        self.subfolder_cb.pack(side="left", padx=(100, 24))
        if self.state.create_output_subfolder:
            self.subfolder_cb.select()
        
        self.overwrite_cb = ctk.CTkCheckBox(
            cb_row,
            text="Overwrite existing files",
            command=self._on_overwrite_toggle,
            font=ctk.CTkFont(size=12)
        )
        self.overwrite_cb.pack(side="left")
        if self.state.overwrite_existing:
            self.overwrite_cb.select()
    
    def _create_file_section(self):
        """File list section"""
        file_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
        file_frame.pack(fill="both", expand=True, pady=(0, 12))
        
        header = ctk.CTkFrame(file_frame, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 12))
        
        ctk.CTkLabel(
            header,
            text="📋 Files to Process",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        self.file_count_label = ctk.CTkLabel(
            header,
            text="0 files",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        )
        self.file_count_label.pack(side="left", padx=(12, 0))
        
        clear_btn = ctk.CTkButton(
            header,
            text="Clear List",
            command=self._clear_files,
            width=100,
            height=32,
            fg_color="#dc2626",
            hover_color="#b91c1c"
        )
        clear_btn.pack(side="right")
        
        self.file_list_frame = ctk.CTkScrollableFrame(
            file_frame,
            fg_color="#0f172a",
            height=220,
            corner_radius=6
        )
        self.file_list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self._update_file_list()
    
    def _create_action_buttons(self):
        """Action buttons"""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 16))
        
        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="▶ Start Processing",
            command=self._start_processing,
            height=48,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8"
        )
        self.start_btn.pack(side="left", padx=(0, 12))
        
        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹ Stop",
            command=self._stop_processing,
            height=48,
            font=ctk.CTkFont(size=16),
            fg_color="#dc2626",
            hover_color="#b91c1c"
        )
        self.stop_btn.pack_forget()
    
    def _select_files(self):
        """Select video files"""
        files = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[
                ("Video Files", "*.mp4 *.mkv *.avi *.mov *.m4v *.webm"),
                ("All Files", "*.*")
            ]
        )
        if files:
            self._add_files_from_paths(list(files))
    
    def _select_folder(self):
        """Select folder and scan for videos"""
        folder = filedialog.askdirectory(title="Select Folder with Videos")
        if folder:
            self.state.input_folder = folder
            pattern = self.pattern_entry.get().strip() or "*"
            self._scan_folder_for_videos(folder, pattern)
    
    def _scan_folder_for_videos(self, folder: str, pattern: str):
        """Scan folder for video files matching pattern"""
        found = []
        if not pattern or pattern.strip() == "*":
            for ext in VIDEO_EXTENSIONS:
                found.extend(glob.glob(os.path.join(folder, ext)))
        else:
            p = pattern.strip()
            if not p.startswith("*"):
                p = "*" + p
            found.extend(glob.glob(os.path.join(folder, p)))
        found = list(dict.fromkeys(found))
        found.sort()
        if found:
            self._add_files_from_paths(found)
            self.state.add_log(f"Scanned folder: found {len(found)} video(s)")
        else:
            self.state.add_log(f"No videos found matching '{pattern}' in {folder}")
    
    def _add_files_from_paths(self, paths: List[str]):
        """Add files to the list from paths"""
        for path in paths:
            if not os.path.isfile(path):
                continue
            name = os.path.basename(path)
            if any(f.path == path for f in self.state.selected_files):
                continue
            self.state.selected_files.append(
                ProcessingFile(id=f"file-{len(self.state.selected_files)}", path=path, name=name)
            )
        self.state.add_log(f"Added {len(paths)} file(s)")
        self._update_file_list()
    
    def _clear_files(self):
        """Clear selected files"""
        self.state.selected_files.clear()
        self._update_file_list()
        self.state.clear_logs()
    
    def _select_output_folder(self):
        """Select output folder"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.state.output_folder = folder
            self.output_label.configure(text=folder)
            self.state.add_log(f"Output folder: {folder}")
    
    def _update_file_list(self):
        """Update file list display"""
        for w in self.file_list_frame.winfo_children():
            w.destroy()
        
        count = len(self.state.selected_files)
        self.file_count_label.configure(text=f"{count} file{'s' if count != 1 else ''}")
        
        if not self.state.selected_files:
            ctk.CTkLabel(
                self.file_list_frame,
                text="No files selected. Use 'Select Files' or 'Select Folder' to add videos.",
                font=ctk.CTkFont(size=13),
                text_color="#64748b"
            ).pack(pady=40)
            return
        
        for file in self.state.selected_files:
            self._create_file_item(file)
    
    def _create_file_item(self, file: ProcessingFile):
        """Create a file item widget"""
        colors = {
            FileStatus.PENDING: "#334155",
            FileStatus.PROCESSING: "#2563eb",
            FileStatus.COMPLETED: "#16a34a",
            FileStatus.ERROR: "#dc2626"
        }
        item = ctk.CTkFrame(
            self.file_list_frame,
            fg_color=colors.get(file.status, "#334155"),
            corner_radius=6
        )
        item.pack(fill="x", pady=4)
        
        row = ctk.CTkFrame(item, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=8)
        
        ctk.CTkLabel(
            row,
            text=file.name,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        ).pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            row,
            text=file.status.value.upper(),
            font=ctk.CTkFont(size=11),
            text_color="#e2e8f0"
        ).pack(side="right", padx=(8, 0))
        
        if file.status == FileStatus.PROCESSING:
            pb = ctk.CTkProgressBar(item)
            pb.pack(fill="x", padx=12, pady=(0, 8))
            pb.set(file.progress / 100.0)
        
        if file.error:
            err_display = file.error[:200] + "..." if len(file.error) > 200 else file.error
            ctk.CTkLabel(
                item,
                text=f"Error: {err_display}",
                font=ctk.CTkFont(size=11),
                text_color="#fca5a5",
                wraplength=500,
                anchor="w",
                justify="left"
            ).pack(anchor="w", padx=12, pady=(0, 8), fill="x")
    
    def _on_cut_mode_change(self):
        """Show/hide cut parameter fields based on mode"""
        mode = self.cut_mode_var.get()
        self.state.cut_mode = CutMode(mode)
        
        self.cut_minutes_frame.pack_forget()
        self.cut_range_frame.pack_forget()
        
        if mode == "cut_last" or mode == "cut_first":
            self.cut_minutes_frame.pack(side="left", padx=(100, 0))
        elif mode == "cut_range":
            self.cut_range_frame.pack(side="left", padx=(100, 0))
    
    def _on_delogo_toggle(self):
        """Toggle delogo section visibility"""
        self.state.apply_delogo = self.delogo_checkbox.get() == 1
        if self.state.apply_delogo:
            self.delogo_params_frame.pack(fill="x", padx=16, pady=(0, 16))
        else:
            self.delogo_params_frame.pack_forget()
    
    def _on_delogo_param_change(self, index: int):
        """Update delogo params"""
        try:
            v = int(self.delogo_inputs[index].get())
            p = self.state.delogo_params
            if index == 0: p.x = v
            elif index == 1: p.y = v
            elif index == 2: p.w = v
            elif index == 3: p.h = v
        except ValueError:
            pass
    
    def _on_format_change(self, value: str):
        """Update output format"""
        self.state.output_format = value
    
    def _on_subfolder_toggle(self):
        """Toggle create output subfolder"""
        self.state.create_output_subfolder = self.subfolder_cb.get() == 1
    
    def _on_overwrite_toggle(self):
        """Toggle overwrite existing"""
        self.state.overwrite_existing = self.overwrite_cb.get() == 1

    def _on_profile_change(self, value: str):
        """Update processing profile and description"""
        from src.state import PROCESSING_PROFILES
        self.state.processing_profile = value
        self.profile_desc_label.configure(
            text=PROCESSING_PROFILES[value].description
        )

    def _sync_state_from_ui(self):
        """Sync cut/trim and output options from UI to state"""
        self.state.cut_mode = CutMode(self.cut_mode_var.get())

        # For CUT_LAST and CUT_FIRST modes
        try:
            self.state.cut_hours = float(self.cut_hours_entry.get() or "0")
        except ValueError:
            self.state.cut_hours = 0.0
        try:
            self.state.cut_minutes = float(self.cut_minutes_entry.get() or "0")
        except ValueError:
            self.state.cut_minutes = 0.0
        try:
            self.state.cut_seconds = float(self.cut_seconds_entry.get() or "0")
        except ValueError:
            self.state.cut_seconds = 0.0

        # For CUT_RANGE mode - Start time
        try:
            self.state.cut_start_hours = float(self.cut_start_hours_entry.get() or "0")
        except ValueError:
            self.state.cut_start_hours = 0.0
        try:
            self.state.cut_start_minutes = float(self.cut_start_entry.get() or "0")
        except ValueError:
            self.state.cut_start_minutes = 0.0
        try:
            self.state.cut_start_seconds = float(self.cut_start_sec_entry.get() or "0")
        except ValueError:
            self.state.cut_start_seconds = 0.0

        # For CUT_RANGE mode - End time
        try:
            end_hours = self.cut_end_hours_entry.get().strip()
            self.state.cut_end_hours = float(end_hours) if end_hours else None
        except ValueError:
            self.state.cut_end_hours = None
        try:
            end = self.cut_end_entry.get().strip()
            self.state.cut_end_minutes = float(end) if end else None
        except ValueError:
            self.state.cut_end_minutes = None
        try:
            end_sec = self.cut_end_sec_entry.get().strip()
            self.state.cut_end_seconds = float(end_sec) if end_sec else None
        except ValueError:
            self.state.cut_end_seconds = None

        self.state.output_format = self.format_var.get()
        self.state.output_prefix = self.prefix_entry.get()
        self.state.output_suffix = self.suffix_entry.get()
    
    def _check_ffmpeg(self) -> bool:
        """Verify FFmpeg is available. Returns True if OK."""
        import subprocess
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5
            )
            return True
        except FileNotFoundError:
            messagebox.showerror(
                "FFmpeg Not Found",
                "FFmpeg is not installed or not in your PATH.\n\n"
                "Please install FFmpeg from https://ffmpeg.org/download.html\n"
                "and add it to your system PATH."
            )
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Could not run FFmpeg: {e}")
            return False
    
    def _validate_inputs(self) -> tuple[bool, str]:
        """Validate user inputs before processing"""
        # Validate time inputs are numeric
        try:
            hours = float(self.cut_hours_entry.get() or "0")
            mins = float(self.cut_minutes_entry.get() or "0")
            secs = float(self.cut_seconds_entry.get() or "0")
            if hours < 0 or mins < 0 or secs < 0:
                return False, "Time values cannot be negative"
        except ValueError:
            return False, "Hours, minutes and seconds must be valid numbers"

        # Validate range mode
        if self.state.cut_mode == CutMode.CUT_RANGE:
            try:
                start_hours = float(self.cut_start_hours_entry.get() or "0")
                start_mins = float(self.cut_start_entry.get() or "0")
                start_secs = float(self.cut_start_sec_entry.get() or "0")
                end_hours_str = self.cut_end_hours_entry.get().strip()
                end_mins_str = self.cut_end_entry.get().strip()
                end_secs_str = self.cut_end_sec_entry.get().strip()

                if start_hours < 0 or start_mins < 0 or start_secs < 0:
                    return False, "Start time cannot be negative"

                if end_hours_str or end_mins_str or end_secs_str:
                    end_hours = float(end_hours_str) if end_hours_str else 0
                    end_mins = float(end_mins_str) if end_mins_str else 0
                    end_secs = float(end_secs_str) if end_secs_str else 0

                    if end_hours < 0 or end_mins < 0 or end_secs < 0:
                        return False, "End time cannot be negative"

                    start_total = (start_hours * 3600) + (start_mins * 60) + start_secs
                    end_total = (end_hours * 3600) + (end_mins * 60) + end_secs

                    if end_total <= start_total:
                        return False, "End time must be after start time"
            except ValueError:
                return False, "Range times must be valid numbers"

        return True, ""

    def _start_processing(self):
        """Start batch processing"""
        if not self.state.selected_files:
            messagebox.showerror("Error", "No files selected.\n\nAdd files using 'Select Files' or 'Select Folder'.")
            self.state.add_log("Error: No files selected")
            return
        if not self.state.output_folder:
            messagebox.showerror("Error", "No output folder selected.\n\nClick 'Browse' next to Output folder to choose where to save processed videos.")
            self.state.add_log("Error: Select an output folder")
            return
        if not self._check_ffmpeg():
            return

        # Validate inputs
        valid, error_msg = self._validate_inputs()
        if not valid:
            messagebox.showerror("Invalid Input", error_msg)
            self.state.add_log(f"Validation error: {error_msg}")
            return

        self._sync_state_from_ui()
        
        thread = threading.Thread(target=self._process_thread, daemon=True)
        thread.start()
        
        self.start_btn.pack_forget()
        self.stop_btn.pack(side="left", padx=(0, 12))
    
    def _stop_processing(self):
        """Stop processing"""
        self.state.is_processing = False
        self.state.add_log("Processing stopped by user")
        self.stop_btn.pack_forget()
        self.start_btn.pack(side="left", padx=(0, 12))
    
    def _process_thread(self):
        """Process queue in background"""
        failed_errors = []
        try:
            self.processor.process_queue(
                self.state.selected_files,
                on_file_error=lambda name, err: failed_errors.append((name, err))
            )
        except Exception as e:
            self.state.add_log(f"Processing error: {str(e)}")
            failed_errors.append(("", str(e)))
        finally:
            self.after(0, lambda: self._on_processing_complete(failed_errors))
    
    def _on_processing_complete(self, failed_errors: list = None):
        """Handle completion"""
        self.stop_btn.pack_forget()
        self.start_btn.pack(side="left", padx=(0, 12))
        self._update_file_list()
        
        if failed_errors:
            name, err = failed_errors[0]
            summary = f"{err}" if not name else f"{name}:\n\n{err}"
            if len(failed_errors) > 1:
                summary += f"\n\n(... and {len(failed_errors) - 1} more - see Logs for details)"
            messagebox.showerror("Processing Failed", summary)
    
    def _on_log_update(self, message: str):
        pass

    def _init_drag_drop(self):
        """Initialize drag-drop handler for the file list frame"""
        try:
            self.drag_drop_handler = DragDropHandler(
                self.file_list_frame,
                self._on_files_dropped
            )
            self.drag_drop_handler.enable()
            self.state.add_log("Drag-drop enabled - drag video files onto the file list")
        except Exception as e:
            self.state.add_log(f"Warning: Could not enable drag-drop: {e}")
            # Drag-drop is optional, continue without it

    def _on_files_dropped(self, file_paths: List[str]):
        """
        Handle files dropped onto the file list.

        Args:
            file_paths: List of video file paths from drag-drop
        """
        if not file_paths:
            return

        # Check for duplicates
        existing_paths = {f.path for f in self.state.selected_files}
        new_files = [p for p in file_paths if p not in existing_paths]
        duplicate_count = len(file_paths) - len(new_files)

        if duplicate_count > 0:
            messagebox.showinfo(
                "Duplicate Files",
                f"Skipped {duplicate_count} duplicate file(s). "
                f"Added {len(new_files)} new file(s)."
            )

        # Add new files to state
        for path in new_files:
            file_obj = ProcessingFile(
                id=str(len(self.state.selected_files) + 1),
                path=path,
                name=os.path.basename(path)
            )
            self.state.selected_files.append(file_obj)

        # Update UI
        self._update_file_list()

        if new_files:
            self.state.add_log(f"Added {len(new_files)} file(s) via drag-drop")
