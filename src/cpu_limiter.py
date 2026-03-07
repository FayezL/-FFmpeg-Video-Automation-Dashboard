"""
CPU Limiting and Monitoring for FFmpeg Video Processing

Provides thread-count calculation, process priority control,
and real-time CPU usage monitoring via psutil.
"""

import multiprocessing
import subprocess
import sys
import threading
import time
from typing import Callable, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from src.state import CPULimitConfig, CPUMetrics


class CPULimiter:
    """Controls CPU usage for FFmpeg subprocesses.

    Usage:
        limiter = CPULimiter(config)
        threads = limiter.calculate_threads()
        # ... build ffmpeg cmd with -threads {threads} ...
        limiter.apply_priority(process)
        limiter.start_monitoring(process, callback)
        process.wait()
        limiter.stop_monitoring()
    """

    def __init__(self, config: CPULimitConfig):
        valid, msg = config.validate()
        if not valid:
            raise ValueError(msg)
        self._config = config
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._latest_metrics = CPUMetrics()
        self._lock = threading.Lock()

    @property
    def config(self) -> CPULimitConfig:
        return self._config

    def calculate_threads(self) -> int:
        """Map CPU limit percentage to FFmpeg thread count.

        Returns a conservative thread count (1..cpu_count) so FFmpeg
        stays near the user's target. Not perfectly linear — video
        encoding doesn't scale linearly with threads — but a good
        first approximation.
        """
        total_cores = multiprocessing.cpu_count()
        threads = max(1, int(total_cores * (self._config.limit_percent / 100.0)))
        return min(threads, total_cores)

    def apply_priority(self, process: subprocess.Popen) -> None:
        """Set OS-level scheduling priority on the FFmpeg process."""
        if not PSUTIL_AVAILABLE:
            return

        try:
            p = psutil.Process(process.pid)
            if sys.platform == "win32":
                priority_map = {
                    "low": psutil.IDLE_PRIORITY_CLASS,
                    "normal": psutil.NORMAL_PRIORITY_CLASS,
                    "high": psutil.HIGH_PRIORITY_CLASS,
                }
            else:
                # Unix nice values: higher = lower priority
                priority_map = {
                    "low": 15,
                    "normal": 0,
                    "high": -5,
                }
            nice_val = priority_map.get(self._config.priority_level)
            if nice_val is not None:
                p.nice(nice_val)
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
            pass  # Best-effort; don't crash if we can't set priority

    def start_monitoring(
        self,
        process: subprocess.Popen,
        callback: Optional[Callable[[CPUMetrics], None]] = None,
    ) -> None:
        """Start a background thread that samples CPU usage.

        The callback fires every `config.monitor_interval` seconds
        with a fresh CPUMetrics snapshot. Thread-safe but the
        callback runs on the monitor thread — use `widget.after()`
        to forward updates to the UI thread.
        """
        if not PSUTIL_AVAILABLE:
            return
        self._stop_event.clear()

        def _monitor():
            try:
                p = psutil.Process(process.pid)
                # Prime the counter (first call always returns 0.0)
                p.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return

            while not self._stop_event.is_set():
                try:
                    proc_pct = p.cpu_percent(interval=self._config.monitor_interval)
                    sys_pct = psutil.cpu_percent(interval=None)
                    threads = p.num_threads()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break

                metrics = CPUMetrics(
                    process_cpu_percent=round(proc_pct, 1),
                    system_cpu_percent=round(sys_pct, 1),
                    thread_count=threads,
                    target_limit=self._config.limit_percent,
                    timestamp=time.time(),
                )

                with self._lock:
                    self._latest_metrics = metrics

                if callback:
                    callback(metrics)

        self._monitor_thread = threading.Thread(target=_monitor, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Signal the monitor thread to stop and wait for it."""
        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        self._monitor_thread = None

    def get_current_metrics(self) -> CPUMetrics:
        """Return the most recent metrics snapshot (thread-safe)."""
        with self._lock:
            return self._latest_metrics

    def update_config(self, config: CPULimitConfig) -> None:
        """Hot-swap the configuration (takes effect on next interval)."""
        valid, msg = config.validate()
        if not valid:
            raise ValueError(msg)
        with self._lock:
            self._config = config
