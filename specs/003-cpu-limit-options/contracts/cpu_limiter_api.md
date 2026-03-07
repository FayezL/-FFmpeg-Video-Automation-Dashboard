# CPULimiter Module API Contract

**Module**: `src/cpu_limiter.py`
**Purpose**: Provide CPU throttling and monitoring for FFmpeg video processing
**Version**: 1.0.0

## Public API

### Class: CPULimiter

```python
class CPULimiter:
    """Manages CPU limiting and monitoring for video processing operations"""

    def __init__(self, config: CPULimitConfig):
        """
        Initialize CPU limiter with configuration.

        Args:
            config: CPU limit configuration from AppState

        Raises:
            ValueError: If config validation fails
        """

    def calculate_threads(self) -> int:
        """
        Calculate FFmpeg thread count based on CPU limit percentage.

        Returns:
            Thread count (1 to cpu_count())

        Example:
            >>> limiter = CPULimiter(CPULimitConfig(limit_percent=50))
            >>> threads = limiter.calculate_threads()  # Returns 4 on 8-core system
        """

    def apply_priority(self, process: subprocess.Popen) -> None:
        """
        Apply process priority based on configuration.

        Args:
            process: FFmpeg subprocess to adjust

        Raises:
            PermissionError: If insufficient privileges for priority change

        Platform-specific:
            - Windows: Uses SetPriorityClass
            - macOS/Linux: Uses nice values
        """

    def start_monitoring(
        self,
        process: subprocess.Popen,
        callback: Callable[[CPUMetrics], None]
    ) -> None:
        """
        Start monitoring CPU usage for a process.

        Args:
            process: FFmpeg subprocess to monitor
            callback: Function called with updated metrics every interval

        Callback signature:
            def on_metrics_update(metrics: CPUMetrics) -> None:
                # Update UI, log, etc.

        Thread-safety:
            Callback executed on background thread. Use after_idle/after
            for UI updates in CustomTkinter.
        """

    def stop_monitoring(self) -> None:
        """
        Stop CPU monitoring and clean up background thread.

        Blocks until monitoring thread exits (max 2 seconds).
        Safe to call multiple times.
        """

    def get_current_metrics(self) -> CPUMetrics:
        """
        Get most recent CPU metrics.

        Returns:
            Current metrics (all zeros if monitoring not active)
        """

    def update_config(self, config: CPULimitConfig) -> None:
        """
        Update configuration during active monitoring.

        Args:
            config: New configuration

        Effects:
            - Thread count recalculated on next FFmpeg command
            - Process priority updated immediately if different
            - Monitoring interval adjusted
        """
```

## Usage Examples

### Basic CPU Limiting

```python
from src.cpu_limiter import CPULimiter
from src.state import CPULimitConfig
import subprocess

# Create limiter
config = CPULimitConfig(enabled=True, limit_percent=50, priority_level="low")
limiter = CPULimiter(config)

# Build FFmpeg command with thread limit
threads = limiter.calculate_threads()
cmd = ["ffmpeg", "-i", "input.mp4", "-threads", str(threads), "output.mp4"]

# Start process and apply priority
process = subprocess.Popen(cmd, ...)
limiter.apply_priority(process)

# Monitor CPU usage
def on_cpu_update(metrics: CPUMetrics):
    print(f"CPU: {metrics.process_cpu_percent:.1f}% (target: {metrics.target_limit}%)")

limiter.start_monitoring(process, on_cpu_update)

# Wait for completion
process.wait()
limiter.stop_monitoring()
```

### Integration with VideoProcessor

```python
class VideoProcessor:
    def _process_with_subprocess(self, ...) -> tuple[bool, str]:
        # ... existing code ...

        # NEW: Apply CPU limiting if enabled
        if self.state.cpu_limit_config.enabled:
            limiter = CPULimiter(self.state.cpu_limit_config)
            threads = limiter.calculate_threads()
            cmd.extend(["-threads", str(threads)])

        process = subprocess.Popen(cmd, ...)

        # NEW: Apply priority and start monitoring
        if self.state.cpu_limit_config.enabled:
            limiter.apply_priority(process)

            def cpu_callback(metrics: CPUMetrics):
                self.state.current_cpu_metrics = metrics
                if on_log:
                    on_log(f"CPU: {metrics.process_cpu_percent:.1f}%")

            limiter.start_monitoring(process, cpu_callback)

        # ... existing progress monitoring ...

        process.wait()

        # NEW: Stop monitoring
        if self.state.cpu_limit_config.enabled:
            limiter.stop_monitoring()

        # ... existing return logic ...
```

## Error Handling

| Error | Condition | Handling Strategy |
|-------|-----------|-------------------|
| ValueError | Invalid config during init | Raise with clear message, don't create limiter |
| PermissionError | Can't set priority (Windows) | Log warning, continue without priority adjustment |
| ProcessLookupError | Process died during monitoring | Stop monitoring gracefully, no error |
| psutil.NoSuchProcess | Process doesn't exist | Stop monitoring gracefully, no error |

## Thread Safety

- `start_monitoring()` creates background thread
- Callback executed on monitoring thread
- `stop_monitoring()` blocks until thread exits
- `update_config()` uses locks for config access
- Safe to call from UI thread (CustomTkinter main thread)

## Performance Characteristics

| Operation | Time Complexity | Notes |
|-----------|----------------|-------|
| calculate_threads() | O(1) | Simple arithmetic |
| apply_priority() | O(1) | Single OS call |
| start_monitoring() | O(1) | Thread creation |
| stop_monitoring() | O(1) | Thread join with timeout |
| Monitoring callback | O(1) per interval | psutil.Process().cpu_percent() |

## Dependencies

```python
import multiprocessing
import subprocess
import threading
import time
from typing import Callable, Optional
import psutil  # NEW DEPENDENCY
from src.state import CPULimitConfig, CPUMetrics
```

## Testing Contract

```python
# tests/unit/test_cpu_limiter.py

def test_thread_calculation_20_percent():
    """Threads should be ~20% of total cores"""
    config = CPULimitConfig(limit_percent=20)
    limiter = CPULimiter(config)
    threads = limiter.calculate_threads()
    assert threads >= 1
    assert threads <= multiprocessing.cpu_count() * 0.2 + 1

def test_thread_calculation_95_percent():
    """Threads should be ~95% of total cores"""
    config = CPULimitConfig(limit_percent=95)
    limiter = CPULimiter(config)
    threads = limiter.calculate_threads()
    assert threads >= multiprocessing.cpu_count() * 0.9

def test_cpu_monitoring_reports_metrics():
    """Monitoring should report CPU metrics via callback"""
    config = CPULimitConfig(enabled=True, limit_percent=50)
    limiter = CPULimiter(config)

    metrics_received = []
    def callback(m: CPUMetrics):
        metrics_received.append(m)

    # Simulate FFmpeg process
    process = subprocess.Popen(["sleep", "2"])
    limiter.start_monitoring(process, callback)
    time.sleep(2.5)  # Allow at least 2 updates
    limiter.stop_monitoring()

    assert len(metrics_received) >= 2
    assert all(m.thread_count > 0 for m in metrics_received)

def test_priority_setting_windows():
    """Priority should be applied on Windows"""
    if sys.platform != "win32":
        pytest.skip("Windows-only test")

    config = CPULimitConfig(priority_level="low")
    limiter = CPULimiter(config)
    process = subprocess.Popen(["timeout", "5"])

    limiter.apply_priority(process)
    # Verify priority via psutil
    p = psutil.Process(process.pid)
    assert p.nice() == psutil.BELOW_NORMAL_PRIORITY_CLASS
```
