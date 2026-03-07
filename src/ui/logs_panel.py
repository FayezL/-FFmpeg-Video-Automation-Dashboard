"""
Logs Panel UI Component
"""

import customtkinter as ctk
import tkinter as tk

from src.state import AppState


class LogsPanel(ctk.CTkScrollableFrame):
    """Logs panel view"""
    
    def __init__(self, parent, state: AppState):
        super().__init__(parent, fg_color="#0f172a")
        self.state = state
        
        self._create_ui()
        
        # Register for log updates
        self.state.register_log_callback(self._on_log_update)
        
        # Display existing logs
        self._refresh_logs()
    
    def _create_ui(self):
        """Create the UI components"""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)
        
        title = ctk.CTkLabel(
            title_frame,
            text="Logs",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#ffffff"
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            title_frame,
            text="FFmpeg processing output and messages",
            font=ctk.CTkFont(size=14),
            text_color="#94a3b8"
        )
        subtitle.pack(anchor="w", pady=(5, 0))
        
        # Clear button
        clear_btn = ctk.CTkButton(
            header,
            text="Clear Logs",
            command=self._clear_logs,
            width=120,
            fg_color="#B91C1C",
            hover_color="#B91C1C"
        )
        clear_btn.pack(side="right")
        
        # Logs display
        self.logs_frame = ctk.CTkFrame(self, fg_color="#0f172a")
        self.logs_frame.pack(fill="both", expand=True)
        
        # Text widget for logs (using tkinter Text for better performance)
        self.logs_text = tk.Text(
            self.logs_frame,
            bg="#1e293b",
            fg="#e2e8f0",
            font=("Consolas", 11),
            wrap=tk.WORD,
            insertbackground="#e2e8f0",
            selectbackground="#0369a1"
        )
        self.logs_text.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(
            self.logs_frame,
            command=self.logs_text.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.logs_text.configure(yscrollcommand=scrollbar.set)
    
    def _refresh_logs(self):
        """Refresh the logs display"""
        self.logs_text.delete("1.0", tk.END)
        for log in self.state.logs:
            self.logs_text.insert(tk.END, log)
        self.logs_text.see(tk.END)
    
    def _clear_logs(self):
        """Clear all logs"""
        self.state.clear_logs()
        self.logs_text.delete("1.0", tk.END)
    
    def _on_log_update(self, message: str):
        """Handle new log message (thread-safe: schedule on main thread)"""
        def _do_insert():
            try:
                self.logs_text.insert(tk.END, message)
                self.logs_text.see(tk.END)
            except tk.TclError:
                pass  # Widget may be destroyed
        self.after(0, _do_insert)


