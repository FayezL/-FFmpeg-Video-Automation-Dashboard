"""
Settings Panel UI Component — Tabbed interface for all application settings.
"""

import multiprocessing
import customtkinter as ctk

from src.state import AppState, PROCESSING_PROFILES


# -- Reusable helpers for dark-themed rows ----------------------------------

def _label(parent, text, **kw):
    return ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(size=13), text_color="#94a3b8", **kw
    )


def _heading(parent, text):
    return ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(size=15, weight="bold"), text_color="#e2e8f0"
    )


def _row(parent, pady=(0, 10)):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(fill="x", pady=pady)
    return f


class SettingsPanel(ctk.CTkScrollableFrame):
    """Settings panel with tabbed categories."""

    def __init__(self, parent, state: AppState):
        super().__init__(parent, fg_color="#0f172a")
        self.state = state
        self._create_ui()

    # ------------------------------------------------------------------ #
    #  Layout                                                             #
    # ------------------------------------------------------------------ #

    def _create_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            header, text="Settings",
            font=ctk.CTkFont(size=32, weight="bold"), text_color="#ffffff"
        ).pack(anchor="w")

        ctk.CTkLabel(
            header, text="Configure application settings",
            font=ctk.CTkFont(size=14), text_color="#94a3b8"
        ).pack(anchor="w", pady=(5, 0))

        # Tabview
        self.tabs = ctk.CTkTabview(
            self, fg_color="#1e293b", segmented_button_fg_color="#334155",
            segmented_button_selected_color="#0ea5e9",
            segmented_button_unselected_color="#334155",
            segmented_button_selected_hover_color="#0284c7",
            text_color="#e2e8f0"
        )
        self.tabs.pack(fill="both", expand=True, pady=(0, 16))

        for name in ("Performance", "Output", "Quality", "Advanced"):
            self.tabs.add(name)

        self._build_performance_tab()
        self._build_output_tab()
        self._build_quality_tab()
        self._build_advanced_tab()

        self.tabs.set("Performance")

        # About section (below tabs)
        self._build_about()

    # ================================================================== #
    #  Performance Tab                                                    #
    # ================================================================== #

    def _build_performance_tab(self):
        tab = self.tabs.tab("Performance")
        pad = ctk.CTkFrame(tab, fg_color="transparent")
        pad.pack(fill="both", expand=True, padx=16, pady=12)

        # --- CPU Limiting ---
        _heading(pad, "CPU Limiting").pack(anchor="w", pady=(0, 8))

        row = _row(pad)
        self.cpu_checkbox = ctk.CTkCheckBox(
            row, text="Enable CPU Limiting",
            font=ctk.CTkFont(size=13), text_color="#e2e8f0",
            fg_color="#0ea5e9", hover_color="#0284c7",
            command=self._on_cpu_toggle
        )
        self.cpu_checkbox.pack(side="left")
        if self.state.cpu_limit_config.enabled:
            self.cpu_checkbox.select()

        # Slider row
        self.cpu_slider_frame = _row(pad, pady=(0, 6))
        _label(self.cpu_slider_frame, "Limit:", width=45).pack(side="left")
        self.cpu_slider = ctk.CTkSlider(
            self.cpu_slider_frame, from_=20, to=95, number_of_steps=15,
            width=200, fg_color="#334155", progress_color="#0ea5e9",
            button_color="#38bdf8", button_hover_color="#7dd3fc"
        )
        self.cpu_slider.set(self.state.cpu_limit_config.limit_percent)
        self.cpu_slider.pack(side="left", padx=(0, 8))
        self.cpu_pct = ctk.CTkLabel(
            self.cpu_slider_frame,
            text=f"{self.state.cpu_limit_config.limit_percent}%",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#38bdf8", width=50
        )
        self.cpu_pct.pack(side="left")
        self.cpu_slider.configure(command=self._on_cpu_slider)

        # Priority row
        self._prio_row = _row(pad, pady=(0, 6))
        _label(self._prio_row, "Priority:", width=60).pack(side="left")
        self.prio_menu = ctk.CTkOptionMenu(
            self._prio_row, values=["low", "normal", "high"],
            command=self._on_priority_change,
            width=120, height=30, fg_color="#334155",
            button_color="#475569", button_hover_color="#64748b",
            text_color="#e2e8f0"
        )
        self.prio_menu.set(self.state.cpu_limit_config.priority_level)
        self.prio_menu.pack(side="left")

        cores = multiprocessing.cpu_count()
        _label(pad,
               f"{cores} CPU cores detected. Lower limit = more CPU for other apps.",
               text_color="#64748b",
               wraplength=460).pack(anchor="w", pady=(0, 16))

        if not self.state.cpu_limit_config.enabled:
            self.cpu_slider_frame.pack_forget()
            self._prio_row.pack_forget()

        # --- Parallel Processing ---
        _heading(pad, "Parallel Processing").pack(anchor="w", pady=(0, 8))

        row2 = _row(pad)
        _label(row2, "Max parallel jobs:", width=140).pack(side="left")
        self.workers_slider = ctk.CTkSlider(
            row2, from_=1, to=4, number_of_steps=3, width=180,
            fg_color="#334155", progress_color="#0ea5e9",
            button_color="#38bdf8", button_hover_color="#7dd3fc"
        )
        self.workers_slider.set(self.state.parallel_config.max_workers)
        self.workers_slider.pack(side="left", padx=(0, 8))
        self.workers_val = ctk.CTkLabel(
            row2, text=str(self.state.parallel_config.max_workers),
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#e2e8f0", width=30
        )
        self.workers_val.pack(side="left")
        self.workers_slider.configure(command=self._on_workers)

        _label(pad,
               "Recommended 2-3 for most systems. Higher values slow individual files.",
               text_color="#64748b",
               wraplength=460).pack(anchor="w")

    # ================================================================== #
    #  Output Tab                                                         #
    # ================================================================== #

    def _build_output_tab(self):
        tab = self.tabs.tab("Output")
        pad = ctk.CTkFrame(tab, fg_color="transparent")
        pad.pack(fill="both", expand=True, padx=16, pady=12)

        _heading(pad, "File Naming").pack(anchor="w", pady=(0, 8))

        # Prefix
        row = _row(pad)
        _label(row, "Prefix:", width=65).pack(side="left")
        self.prefix_entry = ctk.CTkEntry(
            row, width=200, height=32, fg_color="#334155",
            border_color="#475569", text_color="#e2e8f0",
            placeholder_text="e.g. converted_"
        )
        self.prefix_entry.insert(0, self.state.output_prefix)
        self.prefix_entry.pack(side="left")
        self.prefix_entry.bind("<KeyRelease>",
                               lambda e: setattr(self.state, "output_prefix", self.prefix_entry.get()))

        # Suffix
        row2 = _row(pad)
        _label(row2, "Suffix:", width=65).pack(side="left")
        self.suffix_entry = ctk.CTkEntry(
            row2, width=200, height=32, fg_color="#334155",
            border_color="#475569", text_color="#e2e8f0",
            placeholder_text="e.g. _processed"
        )
        self.suffix_entry.insert(0, self.state.output_suffix)
        self.suffix_entry.pack(side="left")
        self.suffix_entry.bind("<KeyRelease>",
                               lambda e: setattr(self.state, "output_suffix", self.suffix_entry.get()))

        _heading(pad, "Output Format").pack(anchor="w", pady=(12, 8))

        row3 = _row(pad)
        _label(row3, "Format:", width=65).pack(side="left")
        self.format_menu = ctk.CTkOptionMenu(
            row3, values=["mp4", "mkv"],
            command=lambda v: setattr(self.state, "output_format", v),
            width=100, height=30, fg_color="#334155",
            button_color="#475569", button_hover_color="#64748b",
            text_color="#e2e8f0"
        )
        self.format_menu.set(self.state.output_format)
        self.format_menu.pack(side="left")

        # Subfolder toggle
        row4 = _row(pad, pady=(8, 6))
        self.subfolder_cb = ctk.CTkCheckBox(
            row4, text="Create 'output' subfolder",
            font=ctk.CTkFont(size=13), text_color="#e2e8f0",
            fg_color="#0ea5e9", hover_color="#0284c7",
            command=lambda: setattr(
                self.state, "create_output_subfolder",
                self.subfolder_cb.get() == 1
            )
        )
        self.subfolder_cb.pack(side="left")
        if self.state.create_output_subfolder:
            self.subfolder_cb.select()

        # Overwrite toggle
        row5 = _row(pad, pady=(0, 6))
        self.overwrite_cb = ctk.CTkCheckBox(
            row5, text="Overwrite existing files",
            font=ctk.CTkFont(size=13), text_color="#e2e8f0",
            fg_color="#0ea5e9", hover_color="#0284c7",
            command=lambda: setattr(
                self.state, "overwrite_existing",
                self.overwrite_cb.get() == 1
            )
        )
        self.overwrite_cb.pack(side="left")
        if self.state.overwrite_existing:
            self.overwrite_cb.select()

    # ================================================================== #
    #  Quality Tab                                                        #
    # ================================================================== #

    def _build_quality_tab(self):
        tab = self.tabs.tab("Quality")
        pad = ctk.CTkFrame(tab, fg_color="transparent")
        pad.pack(fill="both", expand=True, padx=16, pady=12)

        _heading(pad, "Default Processing Profile").pack(anchor="w", pady=(0, 8))

        row = _row(pad)
        self.profile_menu = ctk.CTkOptionMenu(
            row, values=list(PROCESSING_PROFILES.keys()),
            command=self._on_profile_change,
            width=260, height=34, fg_color="#334155",
            button_color="#475569", button_hover_color="#64748b",
            text_color="#e2e8f0"
        )
        profile_key = self.state.processing_profile
        if profile_key not in PROCESSING_PROFILES:
            profile_key = "universal"
            self.state.processing_profile = profile_key
        self.profile_menu.set(profile_key)
        self.profile_menu.pack(side="left")

        profile = PROCESSING_PROFILES[profile_key]
        self.profile_desc = ctk.CTkLabel(
            pad, text=profile.description,
            font=ctk.CTkFont(size=12), text_color="#94a3b8",
            wraplength=460, anchor="w", justify="left"
        )
        self.profile_desc.pack(anchor="w", pady=(4, 12))

        # Profile detail card
        _heading(pad, "Current Profile Details").pack(anchor="w", pady=(0, 8))
        self.profile_detail = ctk.CTkLabel(
            pad, text=self._profile_info(profile),
            font=ctk.CTkFont(size=12, family="Consolas"), text_color="#94a3b8",
            justify="left", anchor="w"
        )
        self.profile_detail.pack(anchor="w")

    # ================================================================== #
    #  Advanced Tab                                                       #
    # ================================================================== #

    def _build_advanced_tab(self):
        tab = self.tabs.tab("Advanced")
        pad = ctk.CTkFrame(tab, fg_color="transparent")
        pad.pack(fill="both", expand=True, padx=16, pady=12)

        _heading(pad, "Custom FFmpeg Parameters").pack(anchor="w", pady=(0, 8))

        _label(pad,
               "Extra flags appended to every FFmpeg command (advanced users only).",
               text_color="#64748b",
               wraplength=460).pack(anchor="w", pady=(0, 6))

        self.custom_params_entry = ctk.CTkEntry(
            pad, width=460, height=34, fg_color="#334155",
            border_color="#475569", text_color="#e2e8f0",
            placeholder_text="-movflags +faststart"
        )
        self.custom_params_entry.pack(anchor="w", pady=(0, 16))

        _heading(pad, "Logging").pack(anchor="w", pady=(0, 8))

        row = _row(pad)
        _label(row, "Log level:", width=75).pack(side="left")
        self.log_menu = ctk.CTkOptionMenu(
            row, values=["error", "warning", "info", "debug"],
            width=120, height=30, fg_color="#334155",
            button_color="#475569", button_hover_color="#64748b",
            text_color="#e2e8f0"
        )
        self.log_menu.set("info")
        self.log_menu.pack(side="left")

        # Save settings button
        save_btn = ctk.CTkButton(
            pad, text="Save Settings",
            command=self._save_settings,
            height=40, width=160,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#0ea5e9", hover_color="#38bdf8"
        )
        save_btn.pack(anchor="w", pady=(24, 0))

        self.save_status = ctk.CTkLabel(
            pad, text="", font=ctk.CTkFont(size=12), text_color="#22c55e"
        )
        self.save_status.pack(anchor="w", pady=(4, 0))

    # ------------------------------------------------------------------ #
    #  About (below tabs)                                                 #
    # ------------------------------------------------------------------ #

    def _build_about(self):
        frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
        frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            frame, text="About",
            font=ctk.CTkFont(size=18, weight="bold"), text_color="#ffffff"
        ).pack(anchor="w", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            frame,
            text=(
                "MagicTVBox - FFmpeg Video Automation Dashboard  v2.1.0\n\n"
                "Batch processing | Custom trim | Processing profiles\n"
                "Delogo filter | CPU limiting | Universal compatibility\n\n"
                "Built with Python and CustomTkinter"
            ),
            font=ctk.CTkFont(size=12), text_color="#94a3b8",
            justify="left", anchor="w"
        ).pack(anchor="w", padx=20, pady=(0, 16))

    # ================================================================== #
    #  Callbacks                                                          #
    # ================================================================== #

    def _on_cpu_toggle(self):
        enabled = self.cpu_checkbox.get() == 1
        self.state.cpu_limit_config.enabled = enabled
        if enabled:
            self.cpu_slider_frame.pack(fill="x", pady=(0, 6),
                                       before=self._prio_row)
            self._prio_row.pack(fill="x", pady=(0, 6))
        else:
            self.cpu_slider_frame.pack_forget()
            self._prio_row.pack_forget()

    def _on_cpu_slider(self, value):
        pct = max(20, min(95, round(value / 5) * 5))
        self.state.cpu_limit_config.limit_percent = pct
        self.cpu_pct.configure(text=f"{pct}%")

    def _on_priority_change(self, value: str):
        self.state.cpu_limit_config.priority_level = value

    def _on_workers(self, value):
        w = int(value)
        self.state.parallel_config.max_workers = w
        self.workers_val.configure(text=str(w))

    def _on_profile_change(self, value: str):
        self.state.processing_profile = value
        profile = PROCESSING_PROFILES[value]
        self.profile_desc.configure(text=profile.description)
        self.profile_detail.configure(text=self._profile_info(profile))

    def _save_settings(self):
        mgr = self.state.settings_manager
        if mgr:
            mgr.migrate_from_state(self.state)
            self.save_status.configure(text="Settings saved", text_color="#22c55e")
        else:
            self.save_status.configure(text="Settings manager not available",
                                       text_color="#f59e0b")
        self.after(3000, lambda: self.save_status.configure(text=""))

    # ================================================================== #
    #  Helpers                                                            #
    # ================================================================== #

    @staticmethod
    def _profile_info(profile) -> str:
        lines = [
            f"Codec:   {profile.video_codec}",
            f"Preset:  {profile.video_preset}",
        ]
        if profile.video_crf is not None:
            lines.append(f"CRF:     {profile.video_crf}")
        if profile.video_bitrate:
            lines.append(f"Bitrate: {profile.video_bitrate}")
        lines.append(f"Pixel:   {profile.pixel_format}")
        if profile.x264_profile:
            lines.append(f"Profile: {profile.x264_profile}")
        if profile.x264_level:
            lines.append(f"Level:   {profile.x264_level}")
        lines += [
            f"Audio:   {profile.audio_codec} @ {profile.audio_bitrate}",
            f"Fast:    {'Yes' if profile.use_faststart else 'No'}",
        ]
        return "\n".join(lines)
