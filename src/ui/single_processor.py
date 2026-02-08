"""
Single File Processor UI Component
"""

import customtkinter as ctk
import tkinter.filedialog as filedialog
from tkinter import messagebox
import threading
import os

from src.state import AppState, CutMode
from src.video_processor import VideoProcessor


class SingleProcessorFrame(ctk.CTkScrollableFrame):
    """Single file processor view"""
    
    def __init__(self, parent, state: AppState, processor: VideoProcessor):
        super().__init__(parent, fg_color="#0f172a")
        self.state = state
        self.processor = processor
        self.selected_file = None
        
        self._create_ui()
        
        # Register for log updates
        self.state.register_log_callback(self._on_log_update)
    
    def _create_ui(self):
        """Create the UI components"""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        title = ctk.CTkLabel(
            header,
            text="Single File Processor",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            header,
            text="Process a single video file",
            font=ctk.CTkFont(size=14),
            text_color="#94a3b8"
        )
        subtitle.pack(anchor="w", pady=(5, 0))
        
        # Processing Options
        self._create_options_section()
        
        # File Selection
        self._create_file_section()
        
        # Progress Display
        self.progress_frame = None
        
        # Action Button
        self._create_action_button()
    
    def _create_options_section(self):
        """Create processing options section"""
        options_frame = ctk.CTkFrame(self, fg_color="#1e293b")
        options_frame.pack(fill="x", pady=(0, 20))
        
        title = ctk.CTkLabel(
            options_frame,
            text="Processing Options",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(anchor="w", padx=20, pady=(20, 15))
        
        options_content = ctk.CTkFrame(options_frame, fg_color="transparent")
        options_content.pack(fill="x", padx=20, pady=(0, 20))
        
        # Cut Last Option
        self.cut_checkbox = ctk.CTkCheckBox(
            options_content,
            text="Cut Last:",
            command=self._on_cut_toggle,
            font=ctk.CTkFont(size=14)
        )
        self.cut_checkbox.pack(anchor="w", pady=5)
        if self.state.cut_last_5_minutes:
            self.cut_checkbox.select()

        # Cut time inputs
        self.cut_time_frame = ctk.CTkFrame(options_content, fg_color="transparent")
        self.cut_time_frame.pack(anchor="w", padx=30, pady=(5, 5))

        ctk.CTkLabel(
            self.cut_time_frame,
            text="Minutes:",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        ).pack(side="left", padx=(0, 8))

        self.cut_minutes_entry = ctk.CTkEntry(
            self.cut_time_frame,
            width=70,
            height=28
        )
        self.cut_minutes_entry.pack(side="left", padx=(0, 8))
        self.cut_minutes_entry.insert(0, "5")

        ctk.CTkLabel(
            self.cut_time_frame,
            text="Seconds:",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        ).pack(side="left", padx=(0, 8))

        self.cut_seconds_entry = ctk.CTkEntry(
            self.cut_time_frame,
            width=70,
            height=28
        )
        self.cut_seconds_entry.pack(side="left")
        self.cut_seconds_entry.insert(0, "0")

        if not self.state.cut_last_5_minutes:
            self.cut_time_frame.pack_forget()

        # Processing Profile
        from src.state import PROCESSING_PROFILES

        ctk.CTkLabel(
            options_content,
            text="",
            height=5
        ).pack()  # Spacer

        profile_label = ctk.CTkLabel(
            options_content,
            text="Processing Profile:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        profile_label.pack(anchor="w", pady=(10, 5))

        profile_frame = ctk.CTkFrame(options_content, fg_color="transparent")
        profile_frame.pack(anchor="w", padx=30, pady=(0, 5))

        self.profile_var = ctk.StringVar(value=self.state.processing_profile)

        profile_menu = ctk.CTkOptionMenu(
            profile_frame,
            values=list(PROCESSING_PROFILES.keys()),
            variable=self.profile_var,
            command=self._on_profile_change,
            width=300,
            height=36
        )
        profile_menu.pack(side="left")

        # Profile description
        self.profile_desc_label = ctk.CTkLabel(
            options_content,
            text=PROCESSING_PROFILES[self.state.processing_profile].description,
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
            wraplength=450,
            anchor="w",
            justify="left"
        )
        self.profile_desc_label.pack(anchor="w", padx=30, pady=(0, 10))

        # Apply Delogo
        self.delogo_checkbox = ctk.CTkCheckBox(
            options_content,
            text="Apply Delogo Filter",
            command=self._on_delogo_toggle,
            font=ctk.CTkFont(size=14)
        )
        self.delogo_checkbox.pack(anchor="w", pady=5)
        if self.state.apply_delogo:
            self.delogo_checkbox.select()
        
        # Delogo Parameters
        self.delogo_params_frame = ctk.CTkFrame(options_content, fg_color="transparent")
        self.delogo_params_frame.pack(fill="x", padx=30, pady=(10, 0))
        
        params = self.state.delogo_params
        labels = ["X", "Y", "Width", "Height"]
        values = [params.x, params.y, params.w, params.h]
        
        self.delogo_inputs = []
        for i, (label, value) in enumerate(zip(labels, values)):
            frame = ctk.CTkFrame(self.delogo_params_frame, fg_color="transparent")
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            self.delogo_params_frame.grid_columnconfigure(i, weight=1)
            
            lbl = ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12))
            lbl.pack(anchor="w", padx=5)
            
            entry = ctk.CTkEntry(frame, width=80)
            entry.insert(0, str(value))
            entry.pack(fill="x", padx=5)
            entry.bind('<KeyRelease>', lambda e, idx=i: self._on_delogo_param_change(idx))
            self.delogo_inputs.append(entry)
        
        if not self.state.apply_delogo:
            self.delogo_params_frame.pack_forget()
    
    def _create_file_section(self):
        """Create file selection section"""
        file_frame = ctk.CTkFrame(self, fg_color="#1e293b")
        file_frame.pack(fill="x", pady=(0, 20))
        
        content = ctk.CTkFrame(file_frame, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=20)
        
        # Input File
        input_frame = ctk.CTkFrame(content, fg_color="transparent")
        input_frame.pack(fill="x", pady=(0, 15))
        
        input_label = ctk.CTkLabel(
            input_frame,
            text="Input File",
            font=ctk.CTkFont(size=14),
            text_color="#94a3b8"
        )
        input_label.pack(anchor="w", pady=(0, 5))
        
        self.input_file_btn = ctk.CTkButton(
            input_frame,
            text="Select Video File",
            command=self._select_file,
            height=40,
            anchor="w",
            fg_color="#0f172a",
            hover_color="#1e293b"
        )
        self.input_file_btn.pack(fill="x")
        
        # Output Folder
        output_frame = ctk.CTkFrame(content, fg_color="transparent")
        output_frame.pack(fill="x")
        
        output_label = ctk.CTkLabel(
            output_frame,
            text="Output Folder",
            font=ctk.CTkFont(size=14),
            text_color="#94a3b8"
        )
        output_label.pack(anchor="w", pady=(0, 5))
        
        self.output_folder_btn = ctk.CTkButton(
            output_frame,
            text="Select Output Folder",
            command=self._select_output_folder,
            height=40,
            anchor="w",
            fg_color="#0f172a",
            hover_color="#1e293b"
        )
        self.output_folder_btn.pack(fill="x")
    
    def _create_action_button(self):
        """Create action button"""
        self.process_btn = ctk.CTkButton(
            self,
            text="Process Video",
            command=self._process_file,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8"
        )
        self.process_btn.pack(fill="x", pady=(0, 20))
    
    def _select_file(self):
        """Select input video file"""
        file = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.mkv *.avi *.mov *.m4v"),
                ("All Files", "*.*")
            ]
        )
        
        if file:
            self.selected_file = file
            filename = os.path.basename(file)
            self.input_file_btn.configure(text=filename)
            self.state.add_log(f"Selected file: {file}")
    
    def _select_output_folder(self):
        """Select output folder"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.state.output_folder = folder
            self.output_folder_btn.configure(text=folder)
            self.state.add_log(f"Selected output folder: {folder}")
    
    def _on_cut_toggle(self):
        """Handle cut checkbox toggle"""
        checked = self.cut_checkbox.get() == 1
        self.state.cut_last_5_minutes = checked
        self.state.cut_mode = CutMode.CUT_LAST if checked else CutMode.NONE

        if checked:
            self.cut_time_frame.pack(anchor="w", padx=30, pady=(5, 5))
            try:
                self.state.cut_minutes = float(self.cut_minutes_entry.get() or "5")
            except ValueError:
                self.state.cut_minutes = 5.0
            try:
                self.state.cut_seconds = float(self.cut_seconds_entry.get() or "0")
            except ValueError:
                self.state.cut_seconds = 0.0
        else:
            self.cut_time_frame.pack_forget()
            self.state.cut_minutes = 0.0
            self.state.cut_seconds = 0.0
    
    def _on_delogo_toggle(self):
        """Handle delogo checkbox toggle"""
        self.state.apply_delogo = self.delogo_checkbox.get() == 1
        if self.state.apply_delogo:
            self.delogo_params_frame.pack(fill="x", padx=30, pady=(10, 0))
        else:
            self.delogo_params_frame.pack_forget()
    
    def _on_delogo_param_change(self, index: int):
        """Handle delogo parameter change"""
        try:
            value = int(self.delogo_inputs[index].get())
            params = self.state.delogo_params
            if index == 0:
                params.x = value
            elif index == 1:
                params.y = value
            elif index == 2:
                params.w = value
            elif index == 3:
                params.h = value
        except ValueError:
            pass

    def _on_profile_change(self, value: str):
        """Update processing profile and description"""
        from src.state import PROCESSING_PROFILES
        self.state.processing_profile = value
        self.profile_desc_label.configure(
            text=PROCESSING_PROFILES[value].description
        )

    def _validate_inputs(self) -> tuple[bool, str]:
        """Validate user inputs before processing"""
        if self.cut_checkbox.get() == 1:
            try:
                mins = float(self.cut_minutes_entry.get() or "0")
                secs = float(self.cut_seconds_entry.get() or "0")
                if mins < 0 or secs < 0:
                    return False, "Time values cannot be negative"
                if mins == 0 and secs == 0:
                    return False, "Cut time cannot be zero when cut is enabled"
            except ValueError:
                return False, "Minutes and seconds must be valid numbers"
        return True, ""

    def _process_file(self):
        """Process the selected file"""
        if not self.selected_file:
            self.state.add_log("Error: No file selected")
            return

        if not self.state.output_folder:
            self.state.add_log("Error: No output folder selected")
            return

        # Validate inputs
        valid, error_msg = self._validate_inputs()
        if not valid:
            from tkinter import messagebox
            messagebox.showerror("Invalid Input", error_msg)
            self.state.add_log(f"Validation error: {error_msg}")
            return
        
        # Show progress frame
        if self.progress_frame:
            self.progress_frame.destroy()
        
        self.progress_frame = ctk.CTkFrame(self, fg_color="#1e293b")
        self.progress_frame.pack(fill="x", pady=(0, 20))
        
        progress_content = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        progress_content.pack(fill="x", padx=20, pady=20)
        
        progress_label = ctk.CTkLabel(
            progress_content,
            text="Processing...",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        progress_label.pack(anchor="w", pady=(0, 10))
        
        self.progress_bar = ctk.CTkProgressBar(progress_content)
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
        
        self.progress_percent = ctk.CTkLabel(
            progress_content,
            text="0%",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        )
        self.progress_percent.pack(anchor="w", pady=(5, 0))
        
        # Disable button
        self.process_btn.configure(state="disabled")
        
        # Process in separate thread
        thread = threading.Thread(target=self._process_thread, daemon=True)
        thread.start()
    
    def _process_thread(self):
        """Process file in a separate thread"""
        output_folder = self.state.output_folder
        if self.state.create_output_subfolder:
            output_folder = os.path.join(output_folder, "output")
            os.makedirs(output_folder, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(self.selected_file))[0]
        ext = f".{self.state.output_format}"
        output_name = f"{self.state.output_prefix}{base_name}{self.state.output_suffix}{ext}"
        output_path = os.path.join(output_folder, output_name)
        
        def on_progress(percent: float):
            self.after(0, lambda: self._update_progress(percent))
        
        def on_log(message: str):
            self.state.add_log(message)
        
        try:
            success, error_msg = self.processor.process_video(
                self.selected_file,
                output_path,
                on_progress=on_progress,
                on_log=on_log
            )
            
            if success:
                self.after(0, lambda: self._on_complete(True, None))
            else:
                self.after(0, lambda: self._on_complete(False, error_msg))
        except Exception as e:
            self.state.add_log(f"Error: {str(e)}")
            self.after(0, lambda: self._on_complete(False, str(e)))
    
    def _update_progress(self, percent: float):
        """Update progress bar"""
        self.progress_bar.set(percent / 100.0)
        self.progress_percent.configure(text=f"{percent:.1f}%")
    
    def _on_complete(self, success: bool, error_msg: str = None):
        """Handle processing completion"""
        if success:
            self.progress_bar.set(1.0)
            self.progress_percent.configure(text="100%")
            self.state.add_log("✓ Processing completed successfully!")
        else:
            msg = error_msg or "Processing failed"
            self.state.add_log(f"✗ Processing failed: {msg}")
            messagebox.showerror("Processing Failed", msg)
        
        self.process_btn.configure(state="normal")
    
    def _on_log_update(self, message: str):
        """Handle log updates"""
        pass


