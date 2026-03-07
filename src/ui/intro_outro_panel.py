"""
Intro/Outro Detection UI Panel
"""

import customtkinter as ctk
import threading
from typing import Optional

from src.state import AppState, DetectedSegment, DetectionResult


def _fmt_time(seconds: float) -> str:
    """Format seconds as MM:SS"""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class IntroOutroPanel(ctk.CTkFrame):
    """Panel showing intro/outro detection results with review controls."""

    def __init__(self, parent, state: AppState, video_path: str = ""):
        super().__init__(parent, fg_color="#1e293b", corner_radius=10)
        self.state = state
        self.video_path = video_path
        self._result: Optional[DetectionResult] = None
        self._create_ui()

    def _create_ui(self):
        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 8))

        ctk.CTkLabel(
            header,
            text="Intro / Outro Detection",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#ffffff",
        ).pack(side="left")

        self.scan_btn = ctk.CTkButton(
            header,
            text="Scan",
            width=80,
            height=30,
            fg_color="#0ea5e9",
            hover_color="#38bdf8",
            font=ctk.CTkFont(size=13),
            command=self._run_scan,
        )
        self.scan_btn.pack(side="right")

        # Progress bar (hidden by default)
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, height=6, fg_color="#334155", progress_color="#0ea5e9"
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=16)

        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Scanning...",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
        )
        self.progress_label.pack(anchor="w", padx=16, pady=(2, 0))

        # Results area
        self.results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.results_frame.pack(fill="x", padx=16, pady=(0, 12))

        self.no_result_label = ctk.CTkLabel(
            self.results_frame,
            text="No scan results yet",
            font=ctk.CTkFont(size=12),
            text_color="#64748b",
        )
        self.no_result_label.pack(anchor="w")

    # ------------------------------------------------------------------ #
    #  Scanning                                                           #
    # ------------------------------------------------------------------ #

    def set_video(self, path: str):
        self.video_path = path
        self._clear_results()

    def _run_scan(self):
        if not self.video_path:
            return
        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.progress_frame.pack(fill="x", pady=(0, 4))
        self.progress_bar.set(0)
        self.progress_label.configure(text="Scanning...")
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        from src.intro_outro_detector import IntroOutroDetector

        detector = IntroOutroDetector()

        def on_progress(p: float):
            self.after(0, lambda: self._update_progress(p))

        result = detector.analyze_video(self.video_path, progress_callback=on_progress)
        self.after(0, lambda: self._on_scan_complete(result))

    def _update_progress(self, p: float):
        self.progress_bar.set(p)
        pct = int(p * 100)
        self.progress_label.configure(text=f"Scanning... {pct}%")

    def _on_scan_complete(self, result: DetectionResult):
        self._result = result
        self.scan_btn.configure(state="normal", text="Scan")
        self.progress_frame.pack_forget()
        self._display_results(result)
        self.state.add_log(
            f"Intro/outro scan complete for {result.file_path} "
            f"({result.analysis_duration:.1f}s)"
        )

    # ------------------------------------------------------------------ #
    #  Results display                                                    #
    # ------------------------------------------------------------------ #

    def _clear_results(self):
        for w in self.results_frame.winfo_children():
            w.destroy()
        self.no_result_label = ctk.CTkLabel(
            self.results_frame,
            text="No scan results yet",
            font=ctk.CTkFont(size=12),
            text_color="#64748b",
        )
        self.no_result_label.pack(anchor="w")
        self._result = None

    def _display_results(self, result: DetectionResult):
        for w in self.results_frame.winfo_children():
            w.destroy()

        if result.error:
            ctk.CTkLabel(
                self.results_frame,
                text=f"Error: {result.error}",
                font=ctk.CTkFont(size=12),
                text_color="#ef4444",
            ).pack(anchor="w")
            return

        if not result.has_detections:
            ctk.CTkLabel(
                self.results_frame,
                text="No intro or outro detected",
                font=ctk.CTkFont(size=12),
                text_color="#94a3b8",
            ).pack(anchor="w")
            return

        if result.intro:
            self._add_segment_row(result.intro)
        if result.outro:
            self._add_segment_row(result.outro)

    def _add_segment_row(self, seg: DetectedSegment):
        row = ctk.CTkFrame(self.results_frame, fg_color="#334155", corner_radius=8)
        row.pack(fill="x", pady=(4, 0))

        # Type label
        type_text = "INTRO" if seg.segment_type == "intro" else "OUTRO"
        ctk.CTkLabel(
            row,
            text=type_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38bdf8",
            width=55,
        ).pack(side="left", padx=(10, 6), pady=8)

        # Time range
        ctk.CTkLabel(
            row,
            text=f"{_fmt_time(seg.start_time)} - {_fmt_time(seg.end_time)}",
            font=ctk.CTkFont(size=12),
            text_color="#e2e8f0",
        ).pack(side="left", padx=(0, 10), pady=8)

        # Confidence badge
        conf_pct = int(seg.confidence * 100)
        if seg.confidence >= 0.75:
            conf_color = "#22c55e"
        elif seg.confidence >= 0.5:
            conf_color = "#f59e0b"
        else:
            conf_color = "#ef4444"

        ctk.CTkLabel(
            row,
            text=f"{conf_pct}%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=conf_color,
        ).pack(side="left", padx=(0, 10), pady=8)

        # Confirm / Reject buttons
        ctk.CTkButton(
            row,
            text="Skip",
            width=50,
            height=26,
            fg_color="#22c55e",
            hover_color="#16a34a",
            font=ctk.CTkFont(size=11),
            command=lambda s=seg: self._confirm_segment(s),
        ).pack(side="right", padx=(0, 10), pady=8)

        ctk.CTkButton(
            row,
            text="Keep",
            width=50,
            height=26,
            fg_color="#64748b",
            hover_color="#475569",
            font=ctk.CTkFont(size=11),
            command=lambda s=seg: self._reject_segment(s),
        ).pack(side="right", padx=(0, 4), pady=8)

    # ------------------------------------------------------------------ #
    #  User review actions                                                #
    # ------------------------------------------------------------------ #

    def _confirm_segment(self, seg: DetectedSegment):
        """Mark segment for skipping during processing."""
        seg.method = "user_confirmed"
        seg.confidence = 1.0
        self.state.add_log(
            f"{seg.segment_type.title()} confirmed for skipping: "
            f"{_fmt_time(seg.start_time)}-{_fmt_time(seg.end_time)}"
        )
        self._display_results(self._result)

    def _reject_segment(self, seg: DetectedSegment):
        """User says keep this segment (don't skip)."""
        if self._result:
            if seg.segment_type == "intro":
                self._result.intro = None
            else:
                self._result.outro = None
            self.state.add_log(f"{seg.segment_type.title()} marked to keep")
            self._display_results(self._result)

    # ------------------------------------------------------------------ #
    #  Public API                                                         #
    # ------------------------------------------------------------------ #

    def get_result(self) -> Optional[DetectionResult]:
        return self._result

    def get_skip_params(self) -> dict:
        """Return FFmpeg trim params to skip confirmed intro/outro.

        Returns dict with optional keys:
          ss: start time in seconds (skip intro)
          t:  duration in seconds (skip outro)
        """
        if not self._result:
            return {}
        params = {}
        if self._result.intro and self._result.intro.method == "user_confirmed":
            params["ss"] = self._result.intro.end_time
        if self._result.outro and self._result.outro.method == "user_confirmed":
            end = self._result.outro.start_time
            start = params.get("ss", 0.0)
            params["t"] = end - start
        return params
