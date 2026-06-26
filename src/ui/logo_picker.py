"""
Visual logo position picker dialog.

Opens a Toplevel window showing a frame from the video, lets the user
click-drag a rectangle over the logo area, and returns the coordinates.
"""

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
from tkinter import messagebox
from typing import Callable, Optional, Tuple

from src.logo_position_utils import (
    extract_preview_frame,
    scale_frame_for_display,
)


class LogoPickerDialog(ctk.CTkToplevel):
    """A modal dialog that shows a video frame and lets the user draw a
    rectangle over the logo by clicking and dragging.

    When the user clicks "Apply", the callback ``on_apply(x, y, w, h)`` is
    called with the coordinates in the ORIGINAL video resolution (not the
    scaled-down display resolution).
    """

    def __init__(
        self,
        parent,
        video_path: str,
        on_apply: Callable[[int, int, int, int], None],
        initial_rect: Optional[Tuple[int, int, int, int]] = None,
    ):
        super().__init__(parent)
        self.title("Select Logo Area")
        self.transient(parent)
        self.grab_set()

        self._on_apply = on_apply
        self._scale = 1.0
        self._rect_id = None
        self._start_x = 0
        self._start_y = 0
        self._photo = None  # keep reference to prevent GC

        self._load_frame(video_path)
        if self._photo is None:
            messagebox.showerror(
                "Error", "Could not open video or extract a frame.", parent=self
            )
            self.after(100, self.destroy)
            return

        self._build_ui(initial_rect)

        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - self.winfo_width()) // 2
        y = (sh - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    # ─── Setup ──────────────────────────────────────────────────────────

    def _load_frame(self, video_path: str) -> None:
        """Extract a frame from the video and convert it for display."""
        frame = extract_preview_frame(video_path, position_frac=0.1)
        if frame is None:
            return

        scaled, scale = scale_frame_for_display(frame, max_width=900, max_height=600)
        self._scale = scale

        # BGR → RGB → PIL → ImageTk
        rgb = cv2.cvtColor(scaled, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        self._photo = ImageTk.PhotoImage(pil_img)
        self._display_w = pil_img.width
        self._display_h = pil_img.height

    def _build_ui(self, initial_rect) -> None:
        """Build the dialog UI."""
        # ── Instructions ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(
            header,
            text="Click and drag over the logo to select it",
            font=ctk.CTkFont(size=13),
        ).pack()

        self._coord_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#60a5fa",
        )
        self._coord_label.pack(pady=(2, 0))

        # ── Canvas with the frame ──
        self._canvas = ctk.CTkCanvas(
            self,
            width=self._display_w,
            height=self._display_h,
            highlightthickness=0,
            bg="#0f172a",
        )
        self._canvas.pack(padx=16, pady=8)
        self._canvas.create_image(0, 0, anchor="nw", image=self._photo)

        # Bind mouse events
        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)

        # Draw initial rectangle if provided
        if initial_rect:
            self._draw_initial_rect(initial_rect)

        # ── Buttons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))

        self._apply_btn = ctk.CTkButton(
            btn_frame,
            text="Apply",
            command=self._on_apply_clicked,
            width=100,
            fg_color="#10B981",
            hover_color="#059669",
            state="disabled",
        )
        self._apply_btn.pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            width=100,
            fg_color="#475569",
            hover_color="#334155",
        ).pack(side="right")

    def _draw_initial_rect(self, rect) -> None:
        """Draw an existing rectangle on the canvas."""
        x, y, w, h = rect
        sx = x * self._scale
        sy = y * self._scale
        sw = w * self._scale
        sh = h * self._scale
        self._rect_id = self._canvas.create_rectangle(
            sx, sy, sx + sw, sy + sh,
            outline="#ef4444", width=2,
        )
        self._current_rect = (x, y, w, h)
        self._coord_label.configure(text=f"X={x}  Y={y}  W={w}  H={h}")
        self._apply_btn.configure(state="normal")

    # ─── Mouse handlers ─────────────────────────────────────────────────

    def _on_press(self, event) -> None:
        self._start_x = event.x
        self._start_y = event.y
        if self._rect_id:
            self._canvas.delete(self._rect_id)
        self._rect_id = self._canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="#ef4444", width=2,
        )

    def _on_drag(self, event) -> None:
        if not self._rect_id:
            return
        # Clamp within canvas bounds
        x = max(0, min(event.x, self._display_w))
        y = max(0, min(event.y, self._display_h))
        self._canvas.coords(self._rect_id, self._start_x, self._start_y, x, y)

        # Update coordinate label (convert to original resolution)
        ox, oy, ow, oh = self._calc_original_rect(
            self._start_x, self._start_y, x, y
        )
        self._coord_label.configure(text=f"X={ox}  Y={oy}  W={ow}  H={oh}")

    def _on_release(self, event) -> None:
        if not self._rect_id:
            return
        x = max(0, min(event.x, self._display_w))
        y = max(0, min(event.y, self._display_h))

        ox, oy, ow, oh = self._calc_original_rect(self._start_x, self._start_y, x, y)
        if ow < 2 or oh < 2:
            # Too small — treat as a click, not a drag
            self._canvas.delete(self._rect_id)
            self._rect_id = None
            return

        self._current_rect = (ox, oy, ow, oh)
        self._coord_label.configure(text=f"X={ox}  Y={oy}  W={ow}  H={oh}")
        self._apply_btn.configure(state="normal")

    # ─── Helpers ────────────────────────────────────────────────────────

    def _calc_original_rect(self, sx, sy, ex, ey) -> Tuple[int, int, int, int]:
        """Convert canvas pixel coords → original video resolution coords."""
        x = int(min(sx, ex) / self._scale)
        y = int(min(sy, ey) / self._scale)
        w = int(abs(ex - sx) / self._scale)
        h = int(abs(ey - sy) / self._scale)
        return x, y, w, h

    def _on_apply_clicked(self) -> None:
        if hasattr(self, "_current_rect"):
            self._on_apply(*self._current_rect)
        self.destroy()
