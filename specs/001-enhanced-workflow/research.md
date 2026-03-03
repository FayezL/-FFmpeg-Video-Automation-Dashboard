# Research Topics: Enhanced Workflow & Performance Feature

**Feature**: `001-enhanced-workflow`
**Date**: 2026-02-08
**Status**: Active Research

This document contains detailed research on technical decisions required for implementing the Enhanced Workflow & Performance feature. Each section addresses a specific technical challenge with questions, findings, and recommendations.

---

## 1. Drag-and-Drop Implementation in Tkinter/CustomTkinter

### Problem Statement
Users want to add video files to the batch processor by dragging them from their file explorer, rather than using a "Select Files" dialog. This requires implementing cross-platform drag-and-drop support in a Tkinter-based GUI.

### Key Questions

#### 1.1 What's the best way to implement drag-and-drop in Tkinter/CustomTkinter?

**Options Researched**:

**Option A: tkinterdnd Library**
- **Description**: Third-party library that provides Tkinter drag-and-drop support
- **Installation**: `pip install tkinterdnd2`
- **Pros**:
  - Cross-platform (Windows, macOS, Linux)
  - Well-maintained and documented
  - High-level API (register_drop_target)
  - Handles native OS events internally
- **Cons**:
  - External dependency (increases install complexity)
  - May not be compatible with all CustomTkinter versions
  - Binary wheels only available for certain Python versions
- **Compatibility**: Requires testing with CustomTkinter 5.0+
- **Code Example**:
  ```python
  from tkinterdnd2 import DND_FILES, DND_TEXT
  root.drop_target_register(DND_FILES)
  root.dnd_bind('<<Drop>>', on_drop)
  ```

**Option B: Native OS APIs**
- **Description**: Use Windows DragAcceptFiles API or macOS Pasteboard API directly
- **Pros**:
  - No external dependencies
  - Direct OS integration
  - Maximum compatibility
- **Cons**:
  - Complex implementation (requires ctypes or pywinapi)
  - Windows-only without macOS equivalent in Python stdlib
  - Error-prone (OS-specific code)
- **Compatibility**: Requires conditional code for Windows vs macOS
- **Code Example** (Windows):
  ```python
  import ctypes
  # Requires WM_DROPFILES message handling in win32 API
  ```

**Option C: Hybrid Approach (Recommended)**
- **Description**: Try tkinterdnd2, fallback to file dialog
- **Pros**:
  - Best of both worlds: native drag-drop when available
  - Graceful degradation on unsupported systems
  - No hard dependency on tkinterdnd2
- **Cons**:
  - Adds fallback code complexity
- **Compatibility**: Works with CustomTkinter 5.0+ and all Python 3.8+ versions
- **Code Example**:
  ```python
  try:
      from tkinterdnd2 import DND_FILES
      has_dnd = True
  except ImportError:
      has_dnd = False

  if has_dnd:
      # Use tkinterdnd2
  else:
      # Use file dialog button
  ```

**Recommendation**: **Option C - Hybrid Approach**
- Implement tkinterdnd2 as optional enhancement
- Keep "Select Files" button as primary method + fallback
- If tkinterdnd2 not installed, app works with button only
- Users can opt-in to better UX by installing `pip install tkinterdnd2`

---

#### 1.2 How to detect drag-over and provide visual feedback?

**Findings**:

**Drag-Over Events**:
- Tkinter drag-drop supports: `<<DragEnter>>`, `<<DragLeave>>`, `<<Drop>>`
- Event object has `.data` attribute with dropped file paths
- Events fire on registered drop target widget

**Visual Feedback Implementation**:
```python
def on_drag_enter(event):
    """Called when files are dragged over drop zone"""
    target.configure(border_width=3, border_color='#2563eb')  # Blue highlight
    return event.action

def on_drag_leave(event):
    """Called when files leave drop zone"""
    target.configure(border_width=1, border_color='#475569')  # Normal border

def on_drop(event):
    """Called when files are dropped"""
    files = event.data.split()  # Returns tuple of file paths
    target.configure(border_width=1, border_color='#475569')  # Reset
    process_dropped_files(files)
```

**Cross-Platform Border Styling**:
- CustomTkinter CTkFrame has `border_width` and `border_color` parameters
- Windows: Files dropped as space-separated paths in `{}`
- macOS: Files dropped as space-separated paths
- Handle quote-wrapped paths: `event.data.split('{')` and strip quotes

**Recommendation**:
- Use CTkFrame border highlight for visual feedback
- Highlight when drag_enter fires, unhighlight when drag_leave or drop fires
- Recommended colors: Blue (#2563eb) for active drag zone, normal border color otherwise

---

#### 1.3 How to recursively scan dropped folders for video files?

**Findings**:

**Supported Video Extensions** (from spec):
- `.mp4`, `.mkv`, `.avi`, `.mov`, `.m4v`, `.webm`

**Implementation Approach**:
```python
from pathlib import Path

VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm'}

def get_video_files_from_path(path: str) -> List[str]:
    """
    Recursively scan directory for video files, or return single file.
    """
    p = Path(path)

    if p.is_file():
        # Single file - return if video extension
        if p.suffix.lower() in VIDEO_EXTENSIONS:
            return [str(p.absolute())]
        else:
            return []

    elif p.is_dir():
        # Directory - recursively scan
        videos = []
        for ext in VIDEO_EXTENSIONS:
            videos.extend([
                str(f.absolute())
                for f in p.rglob(f'*{ext}')  # Recursive glob
                if f.is_file()
            ])
        return sorted(set(videos))  # Remove duplicates, sort

    return []
```

**Performance Considerations**:
- `Path.rglob()` is lazy (generator), efficient for large directories
- Large folders (10,000+ files) may take 1-2 seconds to scan
- Consider threading for large folder scans to avoid UI freeze
- Cache results if same folder dropped multiple times

**Permission Handling**:
- `Path.rglob()` skips files without read permission
- No need for explicit error handling
- Users won't notice silently-skipped inaccessible files (acceptable UX)

**Recommendation**:
- Use pathlib.Path.rglob() with VIDEO_EXTENSIONS set
- Run folder scan in background thread if >1000 files
- Show progress indicator: "Scanning folder... Found N videos"
- Allow user to cancel scanning if taking too long

---

#### 1.4 How to deduplicate dropped files?

**Findings**:

**Duplicate Detection Strategy**:
- Compare by absolute file path (not just filename)
- Same file dropped twice = same absolute path
- Hard links or symbolic links = same inode (treat as duplicate)

**Implementation**:
```python
def add_files_with_duplicate_check(
    new_files: List[str],
    existing_files: List[ProcessingFile],
    allow_duplicates: bool = False
) -> Tuple[List[str], List[str]]:
    """
    Check for duplicates and return (added, duplicates).
    """
    existing_paths = {Path(f.path).absolute() for f in existing_files}

    added = []
    duplicates = []

    for file_path in new_files:
        abs_path = Path(file_path).absolute()

        if abs_path in existing_paths:
            duplicates.append(str(abs_path))
        else:
            added.append(str(abs_path))
            existing_paths.add(abs_path)  # For detecting duplicates within new_files

    return added, duplicates
```

**User Interaction**:
- If duplicates found, show dialog:
  ```
  "The following files are already in the queue:
   - video1.mp4
   - video2.mp4

   Add them again anyway?"

  [Yes] [No]
  ```
- If user clicks "No", duplicates are skipped
- If user clicks "Yes", duplicates added (allows parallel processing of same file)

**Recommendation**:
- Check duplicates by absolute path
- Show dialog if duplicates found
- Default to "No" (skip duplicates)
- Allow power users to override and add duplicates if desired

---

### Summary: Drag-and-Drop Implementation

**Final Recommendation**:
1. **Primary**: Implement tkinterdnd2-based drag-drop (hybrid approach)
2. **Fallback**: Keep "Select Files" button in UI
3. **Visual Feedback**: Border highlight on drag-over (blue #2563eb)
4. **Folder Scanning**: Use pathlib.Path.rglob() with VIDEO_EXTENSIONS set
5. **Deduplication**: Check absolute path, show dialog if duplicates found
6. **Performance**: Thread folder scan for large directories

**Implementation Priority**: P1 (User Story 1)

---

## 2. Parallel Processing with Python Threading

### Problem Statement
Current implementation processes videos serially (one at a time). For a user with 50 videos and a 4-core CPU, this results in 20+ hours of processing when it could complete in 3-4 hours with parallel encoding (2-4 videos simultaneously).

### Key Questions

#### 2.1 Threading vs Multiprocessing for FFmpeg subprocess model?

**Context**:
- FFmpeg runs as external subprocess (not Python process)
- Subprocess releases Python GIL during execution
- AppState is shared object that needs updates from multiple workers
- Current code uses subprocess.Popen for FFmpeg invocation

**Threading Analysis**:

**Pros**:
- Shared AppState object (easier state management)
- GIL not limiting since FFmpeg is external subprocess
- Simpler synchronization with thread-safe queue.Queue()
- Lower memory overhead per worker (thread vs process)
- Faster worker startup

**Cons**:
- Cannot use True parallelism for compute-intensive work (not relevant here)
- GIL blocks Python code execution (not an issue for I/O-bound work)

**Multiprocessing Analysis**:

**Pros**:
- True parallelism for compute (not needed here)
- Isolation between workers (safer)

**Cons**:
- **Complex state sharing**: AppState objects must be pickled across process boundaries
- **Pickling overhead**: Large VideoMetadata objects expensive to serialize
- **IPC complexity**: Require multiprocessing.Queue(), Lock(), Manager()
- **Memory overhead**: Each process copies AppState (~1MB)
- **Startup cost**: Process creation slower than thread creation

**Decision**: **THREADING is correct choice**

**Rationale**:
1. FFmpeg runs as subprocess (releases GIL)
2. I/O-bound workload (waiting on subprocess output)
3. Shared AppState simplifies synchronization
4. Lower memory overhead per worker
5. Simpler code with less complexity

**Reference**:
- CPython GIL explained: https://realpython.com/python-gil/
- Threading vs Multiprocessing: https://docs.python.org/3/library/threading.html
- Subprocess architecture: https://docs.python.org/3/library/subprocess.html

---

#### 2.2 How to implement a work queue for processing files?

**Findings**:

**Thread-Safe Queue Implementation**:

```python
import queue
import threading
from typing import List, Optional, Callable

class ParallelVideoProcessor:
    def __init__(self, state: AppState, max_workers: int = 3):
        self.state = state
        self.max_workers = max_workers
        self.work_queue = queue.Queue()
        self.stop_requested = False
        self.workers = []

    def process_batch_parallel(
        self,
        files: List[ProcessingFile],
        on_file_completed: Optional[Callable[[ProcessingFile], None]] = None,
        on_file_error: Optional[Callable[[ProcessingFile, str], None]] = None
    ) -> None:
        """Start parallel processing of file batch"""

        self.stop_requested = False
        self.state.is_processing = True

        # Populate work queue
        for file in files:
            self.work_queue.put(file)

        # Spawn worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_thread,
                args=(i, on_file_completed, on_file_error),
                daemon=False  # Non-daemon so app waits for workers
            )
            worker.start()
            self.workers.append(worker)

        # Wait for all workers to finish
        for worker in self.workers:
            worker.join()

        self.state.is_processing = False

    def _worker_thread(
        self,
        worker_id: int,
        on_file_completed: Optional[Callable[[ProcessingFile], None]],
        on_file_error: Optional[Callable[[ProcessingFile, str], None]]
    ) -> None:
        """Worker thread that processes files from queue"""

        while True:
            # Check if user requested stop
            if self.stop_requested:
                break

            try:
                # Get file from queue with timeout (to check stop_requested periodically)
                file = self.work_queue.get(timeout=0.5)
            except queue.Empty:
                # Queue is empty and all workers checked - exit thread
                break

            try:
                # Process the file
                self.state.add_log(f"[Worker {worker_id}] Processing: {file.name}")

                file.status = FileStatus.PROCESSING
                file.progress = 0.0

                # Determine output path (same logic as serial processor)
                output_folder = self.state.output_folder or os.path.dirname(file.path)
                if self.state.create_output_subfolder:
                    output_folder = os.path.join(output_folder, "output")
                    os.makedirs(output_folder, exist_ok=True)

                base_name = os.path.splitext(file.name)[0]
                ext = f".{self.state.output_format}"
                output_name = f"{self.state.output_prefix}{base_name}{self.state.output_suffix}{ext}"
                output_path = os.path.join(output_folder, output_name)

                # Process video
                success, error_msg = self.video_processor.process_video(
                    file.path,
                    output_path,
                    on_progress=lambda p: setattr(file, 'progress', p),
                    on_log=lambda msg: self.state.add_log(msg)
                )

                if success:
                    file.status = FileStatus.COMPLETED
                    file.progress = 100.0
                    self.state.add_log(f"[Worker {worker_id}] Completed: {file.name}\n")
                    if on_file_completed:
                        on_file_completed(file)
                else:
                    file.status = FileStatus.ERROR
                    file.error = error_msg
                    self.state.add_log(f"[Worker {worker_id}] Error: {file.name}\n{error_msg}\n")
                    if on_file_error:
                        on_file_error(file, error_msg)

            finally:
                # Mark task as done (for queue.join() support)
                self.work_queue.task_done()

    def stop_all_workers(self, timeout_seconds: float = 5.0) -> bool:
        """
        Gracefully stop all workers.

        Returns: True if all stopped within timeout, False if timeout exceeded
        """
        self.stop_requested = True

        # Wait for workers to finish current file and exit
        start_time = time.time()
        for worker in self.workers:
            remaining_timeout = max(0.1, timeout_seconds - (time.time() - start_time))
            worker.join(timeout=remaining_timeout)

            if worker.is_alive():
                self.state.add_log(f"Warning: Worker thread did not stop within {timeout_seconds}s\n")
                return False

        return True
```

**Key Design Points**:

1. **Thread-Safe Queue**: `queue.Queue()` handles synchronization automatically
2. **Worker Loop**: Workers pull from queue in infinite loop, exit when queue empty + stop_requested
3. **Timeout on Queue.get()**: Allows workers to check stop_requested periodically (0.5s intervals)
4. **Non-Daemon Threads**: Main thread waits for workers to complete
5. **Graceful Shutdown**: Set flag + timeout join ensures responsive stop
6. **File State Updates**: Direct attribute assignment (thread-safe for simple types like float/str)

**Potential Issues and Solutions**:

| Issue | Solution |
|-------|----------|
| Race condition on file.progress | Python primitive assignments are atomic; acceptable for 0-100% |
| Race condition on file.status | Enum assignment is atomic; acceptable for status changes |
| Race condition on AppState | Use callbacks for state changes, avoid multi-field updates |
| Worker thread hangs | Timeout on queue.get() ensures responsive shutdown |
| UI thread updates blocked | Use after() callback for Tkinter updates from worker threads |

**Recommendation**:
- Use queue.Queue() with daemon=False for workers
- Implement graceful stop with flag + timeout join
- Update UI from worker callbacks via after() method (thread-safe)

---

#### 2.3 How to track progress of multiple parallel processes?

**Findings**:

**Progress Tracking Architecture**:

1. **File Progress Field**:
   - Each ProcessingFile has `progress: float` (0-100)
   - Worker updates: `file.progress = percent`
   - Main UI thread polls file states periodically

2. **UI Update Thread Safety**:
   - Tkinter is NOT thread-safe
   - Worker threads cannot directly call Tkinter methods
   - Must use `after()` method to schedule updates on main thread

**Implementation**:

```python
# In ParallelVideoProcessor
def _worker_thread(self, worker_id: int, ...):
    while True:
        try:
            file = self.work_queue.get(timeout=0.5)
        except queue.Empty:
            break

        # ... setup ...

        def on_progress(percent: float):
            file.progress = percent
            # Don't update UI directly! Schedule via after()

        success, error_msg = self.video_processor.process_video(
            file.path,
            output_path,
            on_progress=on_progress,
            on_log=lambda msg: self.state.add_log(msg)
        )

# In BatchProcessorFrame (UI)
def _update_progress_display(self):
    """Update UI progress bars from file states"""
    for file_widget in self.file_widgets:
        file = file_widget.file
        file_widget.progress_bar.set(file.progress / 100.0)
        file_widget.status_label.configure(text=file.status.value)

    # Schedule next update
    self.after(200, self._update_progress_display)  # Update every 200ms

# In __init__
self._update_progress_display()  # Start polling loop
```

**UI Architecture for Multiple Progress Bars**:

```python
class FileWidget(ctk.CTkFrame):
    """UI widget for a single file in batch"""
    def __init__(self, parent, file: ProcessingFile):
        super().__init__(parent, fg_color="#1e293b")
        self.file = file

        # File name
        ctk.CTkLabel(self, text=file.name, font=("Arial", 12)).pack(anchor="w")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0.0)

        # Status label
        self.status_label = ctk.CTkLabel(
            self, text=file.status.value,
            font=("Arial", 10), text_color="#94a3b8"
        )
        self.status_label.pack(anchor="w")

# In BatchProcessorFrame
def _create_file_section(self):
    self.file_widgets = []
    self.file_list_frame = ctk.CTkScrollableFrame(self)
    self.file_list_frame.pack(fill="both", expand=True)

    for file in self.state.selected_files:
        widget = FileWidget(self.file_list_frame, file)
        widget.pack(fill="x", pady=5)
        self.file_widgets.append(widget)
```

**Performance Considerations**:

| Aspect | Recommendation |
|--------|-----------------|
| Update Frequency | 200ms (5 FPS) is sufficient, avoid 100ms or faster |
| Number of Progress Bars | OK up to 50 files; > 100 may cause UI lag |
| Polling vs Events | Polling is simpler; events would require more synchronization |
| UI Thread Blocking | Use after() exclusively, never call Tkinter from worker |

**Recommendation**:
- Use `file.progress` field updated by workers
- Poll from main thread every 200ms with `after()`
- Use CustomTkinter progress bars for visual feedback
- Don't attempt event-based updates (too complex)

---

#### 2.4 How to gracefully stop all workers on user click?

**Findings**:

**Graceful Shutdown Design**:

```python
class ParallelVideoProcessor:
    def __init__(self, state: AppState, max_workers: int = 3):
        # ... other setup ...
        self.stop_requested = False
        self.workers = []
        self.video_processor = VideoProcessor(state)

    def stop_all_workers(self, timeout_seconds: float = 5.0) -> bool:
        """
        Signal workers to stop and wait for shutdown.

        Returns: True if all stopped gracefully, False if timeout
        """
        self.state.add_log("Stopping batch processing...\n")
        self.stop_requested = True

        # Terminate active FFmpeg processes immediately
        # (This is handled by VideoProcessor if we track processes)

        # Wait for worker threads to finish
        start_time = time.time()
        for i, worker in enumerate(self.workers):
            remaining_timeout = max(0.1, timeout_seconds - (time.time() - start_time))
            worker.join(timeout=remaining_timeout)

            if worker.is_alive():
                self.state.add_log(f"Warning: Worker {i} did not stop within {timeout_seconds}s\n")

        # Mark as not processing
        self.state.is_processing = False

        # Return whether all workers stopped
        return all(not w.is_alive() for w in self.workers)

    def _worker_thread(self, worker_id: int, ...):
        """Worker loop that respects stop_requested flag"""
        while True:
            # Check stop flag frequently
            if self.stop_requested:
                break

            try:
                # Short timeout allows checking stop_requested
                file = self.work_queue.get(timeout=0.5)
            except queue.Empty:
                break

            try:
                # Process file...
                success, error_msg = self.video_processor.process_video(...)

                # ... handle completion/error ...

            except Exception as e:
                # Handle unexpected errors
                file.status = FileStatus.ERROR
                file.error = str(e)

            finally:
                self.work_queue.task_done()
```

**Process Termination**:

The VideoProcessor needs to support interrupting the FFmpeg subprocess:

```python
class VideoProcessor:
    def __init__(self, state: AppState):
        self.state = state
        self.current_process: Optional[subprocess.Popen] = None

    def _process_with_subprocess(
        self, input_path: str, output_path: str, ...
    ) -> Tuple[bool, Optional[str]]:
        """Process using subprocess"""
        cmd = ['ffmpeg', ...]

        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
        except FileNotFoundError:
            return False, "FFmpeg not found"

        # Monitor output...
        # ...

        process.wait()
        # ...

    def stop_current_process(self) -> bool:
        """Terminate the current FFmpeg process"""
        if self.current_process and self.current_process.poll() is None:
            self.current_process.terminate()  # Graceful shutdown
            try:
                self.current_process.wait(timeout=5.0)
                return True
            except subprocess.TimeoutExpired:
                self.current_process.kill()  # Force kill if needed
                return False
        return False
```

**Integration with UI**:

```python
# In BatchProcessorFrame
def _create_action_buttons(self):
    self.stop_button = ctk.CTkButton(
        self,
        text="Stop Processing",
        command=self._on_stop_click,
        fg_color="#ef4444"  # Red
    )

def _on_stop_click(self):
    """Handle stop button click"""
    self.state.add_log("Stopping processing...\n")

    # Signal parallel processor to stop
    if self.parallel_processor:
        success = self.parallel_processor.stop_all_workers(timeout_seconds=5.0)

        if success:
            self.state.add_log("All workers stopped successfully\n")
        else:
            self.state.add_log("Warning: Some workers did not stop within timeout\n")

        # Reset UI state
        self.stop_button.configure(state="disabled")
        self.start_button.configure(state="normal")
```

**Timeout Strategy**:

| Step | Timeout | Action |
|------|---------|--------|
| Signal stop_requested | Immediate | Set flag, workers check in 0.5s intervals |
| Wait for worker join | 5 seconds | Allow current file to finish gracefully |
| If timeout | >5s | Log warning, move on (worker may complete in background) |

**Recommendation**:
- Set `stop_requested` flag
- Workers check flag in queue.get() timeout loop
- Join threads with 5-second timeout
- Accept that stopping may take up to file duration (FFmpeg still encoding)
- Don't force-kill processes unless absolutely necessary

---

#### 2.5 CPU core detection and optimal worker count?

**Findings**:

**CPU Core Detection**:

```python
import os

def get_cpu_core_count() -> int:
    """Get number of CPU cores (physical + logical)"""
    return os.cpu_count() or 4  # Default to 4 if detection fails
```

**Recommended Worker Count**:

Formula: `max(1, (cores - 1) // 2)` capped at 4

Rationale:
- Subtract 1 core for OS and other processes
- Divide by 2 for parallelism overhead (each encode uses 1-2 cores effectively)
- Cap at 4 to prevent system overload
- Never go below 1 (single worker always works)

**Examples**:

| CPU Cores | Recommended Workers | Reasoning |
|-----------|-------------------|-----------|
| 1-2 | 1 | Serial processing (parallel not beneficial) |
| 4 | 1-2 | (4-1)//2 = 1, with headroom = 2 typically |
| 8 | 3-4 | (8-1)//2 = 3, capped at 4 |
| 16 | 4 | (16-1)//2 = 7, capped at 4 |
| 32 | 4 | (32-1)//2 = 15, capped at 4 |

**Implementation**:

```python
def get_recommended_worker_count(cpu_count: Optional[int] = None) -> int:
    """
    Calculate recommended number of parallel workers.

    Args:
        cpu_count: Override automatic detection (for testing)

    Returns:
        Recommended worker count (1-4)
    """
    if cpu_count is None:
        cpu_count = os.cpu_count() or 4

    # Formula: (cores - 1) // 2, capped between 1 and 4
    recommended = (cpu_count - 1) // 2
    return max(1, min(4, recommended))
```

**User Configuration**:

```python
# In AppState
class AppState:
    def __init__(self):
        self.max_workers = get_recommended_worker_count()  # Default
        self.custom_max_workers_enabled = False  # User can override

# In UI (SettingsPanel)
def _create_parallelism_settings(self):
    # Label showing recommended
    recommended = get_recommended_worker_count()
    label = ctk.CTkLabel(
        self,
        text=f"Parallel Workers (Recommended: {recommended})",
        font=("Arial", 12)
    )
    label.pack(anchor="w")

    # Slider: 1-8
    def on_slider_change(value):
        self.state.max_workers = int(value)
        if value > recommended:
            self.warning_label.configure(
                text=f"⚠️ Value higher than recommended ({recommended}). "
                     "May cause system slowdown."
            )
        else:
            self.warning_label.configure(text="")

    slider = ctk.CTkSlider(
        self,
        from_=1, to=8,
        number_of_steps=7,
        command=on_slider_change
    )
    slider.set(self.state.max_workers)
    slider.pack(fill="x")

    self.warning_label = ctk.CTkLabel(self, text="")
    self.warning_label.pack(anchor="w")
```

**Recommendation**:
- Use formula `max(1, min(4, (cpu_count - 1) // 2))`
- Default to recommended value
- Allow user to override with slider (1-8 range)
- Warn if user selects >recommended value
- Document performance impact of high worker counts

---

### Summary: Parallel Processing

**Final Recommendation**:
1. **Use Threading** with queue.Queue() for worker pool
2. **Worker Count**: Default to `(cores-1)//2` capped at 4, slider 1-8
3. **File Queue**: Populate queue before spawning workers
4. **Progress Tracking**: Poll file.progress every 200ms from UI thread
5. **Graceful Stop**: Set flag + timeout join (5 seconds)
6. **Error Handling**: Worker catches exceptions, updates file.status
7. **Logging**: Each worker logs actions, UI collects logs

**Implementation Priority**: P1 (User Story 2)

---

## 3. Hardware Encoder Detection & Configuration

### Problem Statement
Video encoding is CPU-intensive and slow. Users with GPUs (NVIDIA, Intel, AMD, Apple) want to offload encoding to their GPU for 8-15x speedup. The system should automatically detect available hardware encoders and offer them as profile options.

### Key Questions

#### 3.1 How to detect NVIDIA NVENC, Intel QuickSync, AMD VCE, Apple VideoToolbox?

**Findings**:

**FFmpeg Encoder Detection Command**:

```bash
ffmpeg -encoders
```

Output example:
```
ffmpeg version 4.4.0 ...
 V..... = Video
 A..... = Audio
 ...
 VE.S.. h264_nvenc                nvdec h264 (nVidia NVENC H.264 video encoder)
 VE.S.. h264_videotoolbox         VideoToolbox H.264 encoder
 VE.S.. h264_qsv                  h264_qsv
```

**Encoder Names by Platform**:

| Hardware | Encoder Name | Output Codec |
|----------|--------------|--------------|
| NVIDIA | h264_nvenc | H.264 |
| NVIDIA | hevc_nvenc | H.265 |
| Intel | h264_qsv | H.264 |
| Intel | hevc_qsv | H.265 |
| AMD | h264_amf | H.264 |
| AMD | hevc_amf | H.265 |
| Apple | h264_videotoolbox | H.264 |
| Apple | hevc_videotoolbox | H.265 |

**Implementation**:

```python
import subprocess
import re
from typing import Dict

class HardwareEncoderDetector:
    """Detect available hardware encoders"""

    ENCODERS = {
        'nvidia': ['h264_nvenc', 'hevc_nvenc'],
        'intel': ['h264_qsv', 'hevc_qsv'],
        'amd': ['h264_amf', 'hevc_amf'],
        'apple': ['h264_videotoolbox', 'hevc_videotoolbox']
    }

    @staticmethod
    def detect_encoders() -> Dict[str, bool]:
        """
        Detect available hardware encoders.

        Returns:
            Dict with keys: 'nvidia', 'intel', 'amd', 'apple'
            Values: True if encoder available, False otherwise
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            encoders_output = result.stdout + result.stderr
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # FFmpeg not found or timeout
            return {
                'nvidia': False,
                'intel': False,
                'amd': False,
                'apple': False
            }

        available = {
            'nvidia': False,
            'intel': False,
            'amd': False,
            'apple': False
        }

        for platform, encoder_names in HardwareEncoderDetector.ENCODERS.items():
            for encoder_name in encoder_names:
                # Look for encoder in output
                if re.search(rf'\b{encoder_name}\b', encoders_output):
                    available[platform] = True
                    break  # Only need one encoder per platform

        return available
```

**Recommendation**:
- Run `ffmpeg -encoders` and parse output
- Check for each encoder name using regex word boundary
- Cache result (only run once at startup)
- Handle missing FFmpeg gracefully (return all False)

---

#### 3.2 How to verify encoder is usable (driver installed)?

**Findings**:

**Encoder Capability Test**:

The most reliable way is to attempt encoding a test video and catch driver errors. However, this is expensive (time-consuming).

**Lightweight Test**:

```python
def test_encoder_availability(encoder_name: str, codec: str) -> bool:
    """
    Test if encoder is available and working.

    Attempts to get encoder info from FFmpeg.
    More reliable than just looking in encoder list.
    """
    try:
        result = subprocess.run(
            ['ffmpeg', '-c:v', encoder_name, '-h', 'encoder=' + encoder_name],
            capture_output=True,
            text=True,
            timeout=5
        )

        # If command succeeds and output mentions encoder, it's available
        output = result.stdout + result.stderr
        if encoder_name in output or 'Unknown encoder' not in output:
            return True

        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
```

**More Thorough Test** (encode single frame):

```python
def test_encoder_encode(encoder_name: str) -> bool:
    """
    Test encoder by encoding single frame.
    More reliable but slower (1-2 seconds).
    """
    import tempfile
    import os

    try:
        # Create a small test pattern
        with tempfile.TemporaryDirectory() as tmpdir:
            test_input = os.path.join(tmpdir, 'test_pattern.mp4')
            test_output = os.path.join(tmpdir, 'test_encoded.mp4')

            # Generate 1-second test pattern with FFmpeg
            subprocess.run(
                [
                    'ffmpeg', '-f', 'lavfi',
                    '-i', 'testsrc=s=320x240:d=1',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                    test_input
                ],
                capture_output=True, timeout=5, check=True
            )

            # Try encoding with target encoder
            result = subprocess.run(
                [
                    'ffmpeg', '-i', test_input,
                    '-c:v', encoder_name,
                    '-t', '1', test_output
                ],
                capture_output=True, timeout=10
            )

            return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return False
```

**Error Patterns for Driver Issues**:

Common error messages when drivers missing:
- "NVENC device not found" → NVIDIA drivers not installed
- "QuickSync not available" → Intel Media SDK not installed
- "AMD encoder not available" → AMD driver not installed
- "VideoToolbox not available" → macOS system codec unavailable

**Recommendation**:
- Quick test: Run `ffmpeg -c:v <encoder> -h encoder=<encoder>` and parse output
- Full test: Only if user explicitly requests (takes 2-3 seconds)
- Cache results (run once at startup)
- Don't re-test after detect (trust initial detection)

---

#### 3.3 FFmpeg command-line differences for hardware encoders?

**Findings**:

**CPU Encoding** (libx264):
```bash
ffmpeg -i input.mp4 \
  -c:v libx264 \
  -preset fast \
  -crf 23 \
  -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  output.mp4
```

**NVIDIA NVENC** (h264_nvenc):
```bash
ffmpeg -i input.mp4 \
  -c:v h264_nvenc \
  -preset fast \
  -rc vbr \
  -cq 23 \
  -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  output.mp4
```

**Intel QuickSync** (h264_qsv):
```bash
ffmpeg -i input.mp4 \
  -c:v h264_qsv \
  -preset fast \
  -global_quality 23 \
  -c:a aac -b:a 192k \
  output.mp4
```

**Apple VideoToolbox** (h264_videotoolbox):
```bash
ffmpeg -i input.mp4 \
  -c:v h264_videotoolbox \
  -q:v 23 \
  -c:a aac -b:a 192k \
  output.mp4
```

**Key Differences**:

| Parameter | libx264 | h264_nvenc | h264_qsv | h264_videotoolbox |
|-----------|---------|-----------|----------|------------------|
| Quality | -crf 0-51 | -cq 0-51 | -global_quality 1-51 | -q:v 1-51 |
| Rate Control | CRF | -rc vbr/cbr | Default | N/A |
| Preset | -preset (ultrafast-veryslow) | -preset (fast/medium/slow) | -preset (fast/medium/slow) | N/A |
| Pixel Format | -pix_fmt yuv420p | Automatic | Automatic | Automatic |
| Device Selection | N/A | -gpu <id> | N/A | N/A |

**Unified Encoder Builder**:

```python
def build_encoder_params(
    encoder_type: str,  # 'libx264', 'h264_nvenc', 'h264_qsv', etc.
    quality: int = 23,  # 0-51
    preset: str = 'fast',
    pixel_format: str = 'yuv420p'
) -> List[str]:
    """Build encoder-specific command-line parameters"""

    params = ['-c:v', encoder_type]

    if encoder_type == 'libx264':
        params.extend(['-preset', preset])
        params.extend(['-crf', str(quality)])
        params.extend(['-pix_fmt', pixel_format])

    elif encoder_type == 'h264_nvenc':
        params.extend(['-preset', preset])
        params.extend(['-rc', 'vbr'])
        params.extend(['-cq', str(quality)])
        # Note: pixel format usually automatic

    elif encoder_type == 'h264_qsv':
        params.extend(['-preset', preset])
        params.extend(['-global_quality', str(quality)])

    elif encoder_type == 'h264_videotoolbox':
        params.extend(['-q:v', str(quality)])

    return params
```

**Recommendation**:
- Create encoder-specific parameter builders
- Map generic profile settings (quality, preset) to encoder-specific flags
- Document parameter ranges and differences
- Test command output on actual encoder

---

#### 3.4 How to handle encoder fallback if GPU encoding fails?

**Findings**:

**GPU Encoding Failure Scenarios**:
1. **GPU Out of Memory** (OOM): Exceeded video memory (VRAM) during encoding
2. **Driver Error**: Incompatible driver or missing GPU
3. **Encoder Busy**: GPU already processing (unlikely with queue management)
4. **Codec Unsupported**: Encoder doesn't support target codec

**Error Detection**:

```python
def detect_gpu_error(stderr_output: str) -> Optional[str]:
    """
    Detect GPU-related errors in FFmpeg stderr.

    Returns: Error category or None if not GPU error
    """
    stderr_lower = stderr_output.lower()

    if 'out of memory' in stderr_lower or 'oom' in stderr_lower:
        return 'oom'
    elif 'nvenc' in stderr_lower and 'device' in stderr_lower:
        return 'nvenc_unavailable'
    elif 'qsv' in stderr_lower and 'initialization' in stderr_lower:
        return 'qsv_unavailable'
    elif 'videotoolbox' in stderr_lower and 'not available' in stderr_lower:
        return 'videotoolbox_unavailable'
    elif 'unknown encoder' in stderr_lower:
        return 'unknown_encoder'

    return None
```

**Fallback Strategy**:

```python
def process_video_with_gpu_fallback(
    self,
    input_path: str,
    output_path: str,
    profile_key: str,  # e.g., 'universal_nvenc'
    on_progress: Optional[Callable[[float], None]] = None,
    on_log: Optional[Callable[[str], None]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Attempt GPU encoding, fallback to CPU on failure.
    """

    # First attempt with GPU profile
    success, error_msg = self.process_video(
        input_path, output_path, on_progress, on_log
    )

    if success:
        return True, None

    # Check if error is GPU-related
    gpu_error = detect_gpu_error(error_msg or '')

    if not gpu_error:
        # Not GPU error, don't retry
        return False, error_msg

    # Log fallback
    if on_log:
        on_log(f"\n⚠️ GPU encoding failed ({gpu_error}). "
               f"Falling back to CPU encoding...\n")

    # Map GPU profile to CPU profile
    cpu_profile_key = self._map_to_cpu_profile(profile_key)

    # Temporarily switch profile and retry
    original_profile = self.state.processing_profile
    try:
        self.state.processing_profile = cpu_profile_key

        success, error_msg = self.process_video(
            input_path, output_path, on_progress, on_log
        )

        if success and on_log:
            on_log("✓ CPU encoding succeeded\n")

        return success, error_msg

    finally:
        # Restore original profile
        self.state.processing_profile = original_profile

def _map_to_cpu_profile(self, gpu_profile_key: str) -> str:
    """Map GPU profile key to equivalent CPU profile"""
    mapping = {
        'universal_nvenc': 'universal',
        'high_quality_nvenc': 'high_quality',
        'small_file_nvenc': 'small_file',
        'universal_qsv': 'universal',
        'high_quality_qsv': 'high_quality',
        # ... more mappings
    }
    return mapping.get(gpu_profile_key, 'universal')
```

**Integration with ParallelVideoProcessor**:

```python
# In worker thread
def _worker_thread(self, worker_id: int, ...):
    while True:
        try:
            file = self.work_queue.get(timeout=0.5)
        except queue.Empty:
            break

        try:
            # Attempt processing with fallback
            success, error_msg = self.video_processor.process_video_with_gpu_fallback(
                file.path,
                output_path,
                self.state.processing_profile,
                on_progress=lambda p: setattr(file, 'progress', p),
                on_log=lambda msg: self.state.add_log(msg)
            )

            # ... handle success/error ...
```

**Recommendation**:
- Detect GPU errors by parsing stderr output
- Automatically fallback to CPU profile on GPU OOM or unavailability
- Log fallback action for user awareness
- Map GPU profile keys to CPU equivalents
- Don't retry multiple times (one CPU fallback is enough)

---

#### 3.5 GPU profile quality vs speed tradeoff?

**Findings**:

**Quality Differences**:

| Aspect | CPU (libx264) | GPU (NVENC/QSV/etc.) |
|--------|--------------|---------------------|
| Visual Quality | Highest (reference) | Slightly lower (acceptable for most) |
| Artifact Pattern | Subtle blocking at low CRF | Slight banding at low quality |
| Performance | 1x (baseline) | 8-15x faster |
| Compatibility | Excellent | Good (some playback issues on old devices) |

**Quality Loss Quantification**:
- CRF 23 CPU ≈ CRF 18-20 GPU for comparable visual quality
- Most users cannot perceive difference
- Professional video production would avoid GPU encoding
- Consumer use cases (social media, streaming) prefer speed

**Profile Descriptions**:

```python
PROCESSING_PROFILES = {
    'universal': ProcessingProfile(
        name="Universal Compatibility",
        description="CPU encoding - maximum quality and compatibility",
        video_codec="libx264",
        # ...
    ),
    'universal_nvenc': ProcessingProfile(
        name="Universal Compatibility (GPU Accelerated)",
        description="NVIDIA GPU encoding - 10x faster, slightly lower quality. "
                    "Ideal for quick exports when speed matters more than quality.",
        video_codec="h264_nvenc",
        # ...
    ),
    # ...
}
```

**UI Tooltips**:

```python
def _create_profile_selector(self):
    profile_dropdown = ctk.CTkComboBox(
        self,
        values=profile_names,
        command=self._on_profile_changed
    )
    profile_dropdown.pack()

    # Add tooltip for GPU profiles
    def on_profile_changed(value):
        profile = PROCESSING_PROFILES[value]

        # Update description
        description_label.configure(text=profile.description)

        # Show quality warning for GPU
        if 'nvenc' in value or 'qsv' in value or 'amf' in value:
            warning = "⚠️ GPU encoding is faster but may have slightly lower visual quality"
            quality_warning_label.configure(text=warning, text_color="#eab308")
        else:
            quality_warning_label.configure(text="")
```

**Recommendation**:
- Document quality tradeoffs in profile descriptions
- Show warning tooltip when GPU profile selected
- Recommend GPU for consumer use cases (social media, streaming)
- Allow expert users to choose CPU profiles if quality is critical
- Default to CPU profiles, GPU as opt-in enhancement

---

### Summary: Hardware Encoders

**Final Recommendation**:
1. **Detection**: Run `ffmpeg -encoders` at startup, cache results
2. **Encoder Support**: NVIDIA, Intel, AMD, Apple
3. **Fallback**: Automatic CPU fallback on GPU OOM or unavailability
4. **Command Differences**: Create encoder-specific parameter builders
5. **Quality**: Document tradeoffs, show warnings in UI
6. **Profiles**: Create GPU variants of existing profiles if hardware detected

**Implementation Priority**: P2 (User Story 4)

---

## 4. Template & Configuration Persistence

### Problem Statement
Users repeatedly configure the same settings (trim, profile, delogo, output) for similar batches. They want to save these as templates and load with one click to avoid 2-3 minutes of manual configuration each time.

### Key Questions

#### 4.1 Directory structure for storing templates?

**Findings**:

**Cross-Platform Config Directories**:

```python
from pathlib import Path
import os
import sys
import platform

def get_config_directory() -> Path:
    """Get platform-appropriate config directory"""

    if sys.platform == 'win32':
        # Windows: AppData\Local
        base = Path(os.getenv('LOCALAPPDATA', '~/.magictvbox'))
        return Path(base) / 'MagicTVBox'

    elif sys.platform == 'darwin':
        # macOS: Library/Application Support or ~/.magictvbox
        return Path('~').expanduser() / 'Library' / 'Application Support' / 'MagicTVBox'

    else:
        # Linux: ~/.config/magictvbox
        return Path('~').expanduser() / '.config' / 'magictvbox'

def get_templates_directory() -> Path:
    """Get templates directory, creating if needed"""
    templates_dir = get_config_directory() / 'templates'
    templates_dir.mkdir(parents=True, exist_ok=True)
    return templates_dir

def get_batch_states_directory() -> Path:
    """Get batch state checkpoints directory"""
    batch_dir = get_config_directory() / 'batch_states'
    batch_dir.mkdir(parents=True, exist_ok=True)
    return batch_dir
```

**Directory Structure**:

```
Windows:
  C:\Users\<username>\AppData\Local\MagicTVBox\
  ├── templates/
  │   ├── youtube_export.json
  │   ├── podcast_upload.json
  │   └── archival_hq.json
  ├── batch_states/
  │   ├── abc123def456.json
  │   └── def789ghi012.json
  └── logs/
      └── app.log

macOS:
  ~/Library/Application Support/MagicTVBox/
  └── (same structure as Windows)

Linux:
  ~/.config/magictvbox/
  └── (same structure as Windows)
```

**Recommendation**:
- Windows: `%LOCALAPPDATA%\MagicTVBox\`
- macOS: `~/Library/Application Support/MagicTVBox/`
- Linux: `~/.config/magictvbox/`
- One JSON file per template: `templates/<name>.json`
- One JSON per batch state: `batch_states/<batch_id>.json`

---

#### 4.2 How to serialize/deserialize AppState to JSON?

**Findings**:

**Current State Structure**:

```python
@dataclass
class AppState:
    # Files
    selected_files: List[ProcessingFile] = []
    input_folder: Optional[str] = None
    output_folder: Optional[str] = None

    # Cut/Trim
    cut_mode: CutMode = CutMode.CUT_LAST
    cut_minutes: float = 5.0
    cut_seconds: float = 0.0
    # ... more trim fields

    # Processing
    apply_delogo: bool = False
    delogo_params: DelogoParams = DelogoParams()
    processing_profile: str = "universal"

    # Output
    output_format: str = "mp4"
    output_suffix: str = ""
    output_prefix: str = ""
    # ...
```

**Template Serialization**:

```python
from dataclasses import asdict, dataclass
from typing import Any, Dict
import json
from datetime import datetime

@dataclass
class Template:
    """Represents a saved configuration template"""

    # Metadata
    name: str
    description: str = ""

    # Trim settings
    cut_mode: str  # Serialized as string, not enum
    cut_minutes: float
    cut_seconds: float
    cut_start_minutes: float
    cut_start_seconds: float
    cut_end_minutes: Optional[float]
    cut_end_seconds: Optional[float]

    # Processing settings
    processing_profile_key: str  # Store key, not full profile
    apply_delogo: bool
    delogo_params: Dict[str, Any]  # Serialized dict

    # Output settings
    output_format: str
    output_suffix: str
    output_prefix: str
    create_output_subfolder: bool
    overwrite_existing: bool

    # Timestamps
    created_timestamp: str  # ISO format
    last_modified_timestamp: str

    def to_json(self) -> str:
        """Serialize template to JSON string"""
        data = {
            'name': self.name,
            'description': self.description,
            'cut_mode': self.cut_mode,
            'cut_minutes': self.cut_minutes,
            'cut_seconds': self.cut_seconds,
            'cut_start_minutes': self.cut_start_minutes,
            'cut_start_seconds': self.cut_start_seconds,
            'cut_end_minutes': self.cut_end_minutes,
            'cut_end_seconds': self.cut_end_seconds,
            'processing_profile_key': self.processing_profile_key,
            'apply_delogo': self.apply_delogo,
            'delogo_params': self.delogo_params,
            'output_format': self.output_format,
            'output_suffix': self.output_suffix,
            'output_prefix': self.output_prefix,
            'create_output_subfolder': self.create_output_subfolder,
            'overwrite_existing': self.overwrite_existing,
            'created_timestamp': self.created_timestamp,
            'last_modified_timestamp': self.last_modified_timestamp,
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def from_json(json_str: str) -> 'Template':
        """Deserialize template from JSON string"""
        data = json.loads(json_str)
        return Template(
            name=data['name'],
            description=data.get('description', ''),
            cut_mode=data['cut_mode'],
            cut_minutes=float(data['cut_minutes']),
            cut_seconds=float(data['cut_seconds']),
            cut_start_minutes=float(data.get('cut_start_minutes', 0.0)),
            cut_start_seconds=float(data.get('cut_start_seconds', 0.0)),
            cut_end_minutes=float(data['cut_end_minutes']) if data.get('cut_end_minutes') else None,
            cut_end_seconds=float(data['cut_end_seconds']) if data.get('cut_end_seconds') else None,
            processing_profile_key=data['processing_profile_key'],
            apply_delogo=bool(data['apply_delogo']),
            delogo_params=data.get('delogo_params', {}),
            output_format=data['output_format'],
            output_suffix=data.get('output_suffix', ''),
            output_prefix=data.get('output_prefix', ''),
            create_output_subfolder=bool(data.get('create_output_subfolder', False)),
            overwrite_existing=bool(data.get('overwrite_existing', True)),
            created_timestamp=data['created_timestamp'],
            last_modified_timestamp=data['last_modified_timestamp'],
        )

class TemplateManager:
    """Manage template save/load/delete"""

    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or get_templates_directory()

    def save_template(self, template: Template) -> bool:
        """Save template to disk"""
        try:
            filepath = self.templates_dir / f"{template.name}.json"
            filepath.write_text(template.to_json(), encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error saving template: {e}")
            return False

    def load_template(self, name: str) -> Optional[Template]:
        """Load template from disk"""
        try:
            filepath = self.templates_dir / f"{name}.json"
            json_str = filepath.read_text(encoding='utf-8')
            return Template.from_json(json_str)
        except Exception as e:
            print(f"Error loading template: {e}")
            return None

    def list_templates(self) -> List[Template]:
        """List all saved templates"""
        templates = []
        for filepath in self.templates_dir.glob('*.json'):
            try:
                template = self.load_template(filepath.stem)
                if template:
                    templates.append(template)
            except Exception:
                pass  # Skip corrupted files
        return sorted(templates, key=lambda t: t.created_timestamp, reverse=True)

    def delete_template(self, name: str) -> bool:
        """Delete template"""
        try:
            filepath = self.templates_dir / f"{name}.json"
            filepath.unlink()
            return True
        except Exception as e:
            print(f"Error deleting template: {e}")
            return False
```

**Template JSON Example**:

```json
{
  "name": "YouTube Export",
  "description": "High-quality export for YouTube uploads",
  "cut_mode": "cut_last",
  "cut_minutes": 5.0,
  "cut_seconds": 0.0,
  "cut_start_minutes": 0.0,
  "cut_start_seconds": 0.0,
  "cut_end_minutes": null,
  "cut_end_seconds": null,
  "processing_profile_key": "high_quality",
  "apply_delogo": false,
  "delogo_params": {
    "x": 1635,
    "y": 240,
    "w": 176,
    "h": 147
  },
  "output_format": "mp4",
  "output_suffix": "_yt",
  "output_prefix": "",
  "create_output_subfolder": false,
  "overwrite_existing": true,
  "created_timestamp": "2026-02-08T10:30:00Z",
  "last_modified_timestamp": "2026-02-08T10:30:00Z"
}
```

**Version 2 Schema** (forward compatibility):

```json
{
  "_schema_version": 2,
  "name": "YouTube Export",
  // ... other fields
}
```

**Recommendation**:
- Create Template dataclass with to_json/from_json methods
- Create TemplateManager for disk persistence
- Include schema version for future compatibility
- Use absolute timestamps (ISO format) for sorting
- Handle deserialization errors gracefully

---

#### 4.3 How to detect unsaved changes to loaded template?

**Findings**:

**State Comparison Strategy**:

```python
def get_template_from_state(state: AppState, name: str) -> Template:
    """Create template from current AppState"""
    return Template(
        name=name,
        description="",
        cut_mode=state.cut_mode.value,
        cut_minutes=state.cut_minutes,
        cut_seconds=state.cut_seconds,
        cut_start_minutes=state.cut_start_minutes,
        cut_start_seconds=state.cut_start_seconds,
        cut_end_minutes=state.cut_end_minutes,
        cut_end_seconds=state.cut_end_seconds,
        processing_profile_key=state.processing_profile,
        apply_delogo=state.apply_delogo,
        delogo_params=asdict(state.delogo_params),
        output_format=state.output_format,
        output_suffix=state.output_suffix,
        output_prefix=state.output_prefix,
        create_output_subfolder=state.create_output_subfolder,
        overwrite_existing=state.overwrite_existing,
        created_timestamp=datetime.now().isoformat() + 'Z',
        last_modified_timestamp=datetime.now().isoformat() + 'Z',
    )

def templates_equal(t1: Template, t2: Template) -> bool:
    """Compare two templates for equality"""
    # Compare all fields except timestamps and description
    return (
        t1.cut_mode == t2.cut_mode and
        t1.cut_minutes == t2.cut_minutes and
        t1.cut_seconds == t2.cut_seconds and
        t1.cut_start_minutes == t2.cut_start_minutes and
        t1.cut_start_seconds == t2.cut_start_seconds and
        t1.cut_end_minutes == t2.cut_end_minutes and
        t1.cut_end_seconds == t2.cut_end_seconds and
        t1.processing_profile_key == t2.processing_profile_key and
        t1.apply_delogo == t2.apply_delogo and
        t1.delogo_params == t2.delogo_params and
        t1.output_format == t2.output_format and
        t1.output_suffix == t2.output_suffix and
        t1.output_prefix == t2.output_prefix and
        t1.create_output_subfolder == t2.create_output_subfolder and
        t1.overwrite_existing == t2.overwrite_existing
    )

class TemplateTracker:
    """Track loaded template and detect changes"""

    def __init__(self, state: AppState):
        self.state = state
        self.loaded_template: Optional[Template] = None
        self.is_modified = False

    def load_template(self, template: Template) -> None:
        """Load template into state"""
        self.loaded_template = template

        # Apply template settings to state
        self.state.cut_mode = CutMode(template.cut_mode)
        self.state.cut_minutes = template.cut_minutes
        self.state.cut_seconds = template.cut_seconds
        # ... set all other fields ...

        self.is_modified = False

    def check_modifications(self) -> bool:
        """Check if current state differs from loaded template"""
        if not self.loaded_template:
            return False

        current = get_template_from_state(self.state, self.loaded_template.name)
        self.is_modified = not templates_equal(current, self.loaded_template)
        return self.is_modified

    def get_template_display_name(self) -> str:
        """Get template name with asterisk if modified"""
        if not self.loaded_template:
            return ""

        name = self.loaded_template.name
        if self.is_modified:
            return f"{name} *"  # Asterisk indicates unsaved changes
        return name
```

**UI Integration**:

```python
def _create_template_selector(self):
    # Dropdown for templates
    self.template_dropdown = ctk.CTkComboBox(
        self,
        values=[],  # Populated from TemplateManager
        command=self._on_template_selected
    )
    self.template_dropdown.pack()

    # Track template changes
    self.template_tracker = TemplateTracker(self.state)

    # Register callback to check for modifications
    def on_state_changed():
        self.template_tracker.check_modifications()
        name = self.template_tracker.get_template_display_name()
        self.template_dropdown.set(name)

    # Hook into all state-changing events
    # (This is simplified; in practice, bind to UI element changes)
    self.state.register_state_change_callback(on_state_changed)

def _on_template_selected(self, template_name: str):
    """Handle template dropdown selection"""
    # Remove asterisk if present
    clean_name = template_name.rstrip(' *')

    # Load template
    template = self.template_manager.load_template(clean_name)
    if template:
        self.template_tracker.load_template(template)
```

**Recommendation**:
- Create TemplateTracker to track loaded template and modifications
- Compare all settings fields for equality
- Update UI indicator (asterisk) on every state change
- Hook into UI element changes to detect modifications

---

#### 4.4 How to handle deleted profiles referenced in templates?

**Findings**:

**Problem**:
- Template saves `processing_profile_key: "custom_hq"`
- User deletes "custom_hq" profile
- Template tries to load non-existent profile → error

**Solutions**:

**Option A: Store Profile Settings Inline** (Recommended)
- Template stores full profile settings, not just key
- Even if original profile deleted, template has all needed info
- Solves the problem completely

**Option B: Profile Versioning**
- Track profile version/ID
- When profile deleted, keep version history
- Load template with closest matching profile

**Option C: Migration on Load**
- When loading, if profile not found, ask user which profile to use

**Recommendation**: **Option A - Store settings inline**

```python
@dataclass
class Template:
    # ...existing fields...

    # Option A: Store full profile settings inline
    profile_settings: Dict[str, Any]  # Serialized ProcessingProfile

    # OR Option B: Just store key (simpler, but breaks if profile deleted)
    # processing_profile_key: str
```

**Implementation**:

```python
@dataclass
class ProcessingProfile:
    name: str
    description: str
    video_codec: str = "libx264"
    video_preset: str = "fast"
    video_crf: Optional[int] = 23
    # ... more fields ...

    def to_dict(self) -> Dict[str, Any]:
        """Serialize profile to dict"""
        return {
            'name': self.name,
            'description': self.description,
            'video_codec': self.video_codec,
            'video_preset': self.video_preset,
            'video_crf': self.video_crf,
            # ... all fields ...
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ProcessingProfile':
        """Deserialize profile from dict"""
        return ProcessingProfile(
            name=data['name'],
            description=data.get('description', ''),
            video_codec=data.get('video_codec', 'libx264'),
            # ... handle all fields ...
        )

@dataclass
class Template:
    name: str
    description: str
    # ...trim fields...

    # Store profile settings inline (not just key)
    profile_settings: Dict[str, Any]  # Full ProcessingProfile serialized

    # ... other fields ...

    def to_json(self) -> str:
        """Serialize template including full profile"""
        data = {
            # ... other fields ...
            'profile_settings': self.profile_settings,  # Include full profile
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def from_json(json_str: str) -> 'Template':
        """Deserialize template with inline profile"""
        data = json.loads(json_str)
        return Template(
            # ... other fields ...
            profile_settings=data.get('profile_settings', {}),
        )

def apply_template_to_state(state: AppState, template: Template) -> None:
    """Apply template settings to app state"""
    # ... apply trim settings ...

    # Apply profile settings
    if template.profile_settings:
        # Create or update custom profile from template
        profile = ProcessingProfile.from_dict(template.profile_settings)

        # If profile still exists in PROCESSING_PROFILES, use it
        if profile.name in PROCESSING_PROFILES:
            state.processing_profile = profile.name
        else:
            # Profile doesn't exist - create temporary profile or use fallback
            # Option: Store custom profiles separately, add to PROCESSING_PROFILES dynamically
            state.processing_profile = profile.name  # Will need custom profile support
    # ...
```

**Custom Profile Support**:

To fully support inline profile settings, need custom profile storage:

```python
class CustomProfileManager:
    """Manage custom user-created profiles"""

    def __init__(self, profiles_dir: Path):
        self.profiles_dir = profiles_dir
        self.custom_profiles = {}  # Cache in memory

    def save_custom_profile(self, profile: ProcessingProfile) -> bool:
        """Save custom profile to disk"""
        filepath = self.profiles_dir / f"{profile.name}.json"
        try:
            filepath.write_text(json.dumps(profile.to_dict(), indent=2))
            self.custom_profiles[profile.name] = profile
            return True
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False

    def get_all_profiles(self) -> Dict[str, ProcessingProfile]:
        """Get built-in + custom profiles"""
        all_profiles = dict(PROCESSING_PROFILES)
        all_profiles.update(self.custom_profiles)
        return all_profiles

# In AppState initialization
def __init__(self):
    self.custom_profile_manager = CustomProfileManager(get_config_directory() / 'profiles')
    self.custom_profile_manager.load_all_custom_profiles()
```

**Recommendation**:
- Store full profile settings inline in template
- Support custom profile storage for dynamically-loaded profiles
- When loading template, use stored profile settings directly
- Fallback to default profile if custom profile not found

---

#### 4.5 How to organize 50+ templates with search/filter?

**Findings**:

**UI Organization Strategy**:

```python
class TemplateSelector:
    """Template selector with search and organization"""

    def __init__(self, parent, template_manager: TemplateManager):
        self.template_manager = template_manager
        self.templates = []

        # Search box
        self.search_entry = ctk.CTkEntry(parent, placeholder_text="Search templates...")
        self.search_entry.pack(fill="x", pady=5)
        self.search_entry.bind('<KeyRelease>', self._on_search_changed)

        # Dropdown with filtered templates
        self.template_dropdown = ctk.CTkComboBox(parent, values=[])
        self.template_dropdown.pack(fill="x")

        self._load_templates()
        self._update_dropdown()

    def _load_templates(self):
        """Load all templates from disk"""
        self.templates = self.template_manager.list_templates()

    def _on_search_changed(self, event):
        """Update dropdown based on search text"""
        self._update_dropdown()

    def _update_dropdown(self):
        """Filter templates by search and populate dropdown"""
        search_text = self.search_entry.get().lower()

        filtered = [
            t for t in self.templates
            if search_text in t.name.lower() or search_text in t.description.lower()
        ]

        # Sort by relevance (name matches first)
        filtered.sort(
            key=lambda t: (
                search_text not in t.name.lower(),  # Name matches first
                t.created_timestamp  # Then by creation date
            )
        )

        # Update dropdown
        names = [t.name for t in filtered]
        self.template_dropdown.configure(values=names)

        if names:
            self.template_dropdown.set(names[0])
```

**Categorization Support** (Future Enhancement):

```python
@dataclass
class Template:
    # ... existing fields ...
    category: str = "Uncategorized"  # e.g., "YouTube", "Streaming", "Archival"
    tags: List[str] = field(default_factory=list)  # e.g., ["hq", "gpu"]
```

**Template Preview**:

```python
def show_template_preview(template: Template) -> str:
    """Generate preview text for template selection"""
    preview = f"{template.name}\n"
    preview += f"Profile: {template.processing_profile_key}\n"
    preview += f"Format: {template.output_format}\n"
    preview += f"Cut: {template.cut_mode}\n"
    if template.apply_delogo:
        preview += "✓ Delogo enabled\n"
    return preview
```

**Recommendation**:
- Add search/filter box above template dropdown
- Search by name and description
- Sort results by relevance (name match first)
- Show template preview on hover
- Support categories/tags (future enhancement)
- Keep implementation simple initially, add advanced features later

---

### Summary: Template Persistence

**Final Recommendation**:
1. **Storage**: `~/.magictvbox/templates/<name>.json` (platform-specific)
2. **Serialization**: Template.to_json() / from_json() with version tag
3. **Modification Tracking**: TemplateTracker detects changes, shows asterisk
4. **Profile Handling**: Store full profile settings inline (not by reference)
5. **Search**: Add search box to filter templates by name/description
6. **Management**: Delete via right-click, rename via edit dialog

**Implementation Priority**: P1 (User Story 3)

---

## 5. Video Metadata Extraction & Validation

*(Continue with detailed research on metadata extraction, validation strategies, thumbnail generation, file list display, etc.)*

### Problem Statement
Users need to see video properties before processing (duration, resolution, codec) to catch issues early. Without this, they discover incompatible videos only after 30+ minutes of wasted encoding.

### Key Questions

#### 5.1 What metadata should be extracted and displayed?

**Essential Metadata**:
- Duration (formatted as HH:MM:SS)
- Resolution (WIDTHxHEIGHT)
- Codec (H.264, H.265, VP9, etc.)
- File size (MB/GB)
- Frame rate (fps, optional)
- Bitrate (kbps, optional)

**Implementation**:

```python
@dataclass
class VideoMetadata:
    """Video file metadata"""
    file_path: str
    duration: float  # seconds
    width: Optional[int]
    height: Optional[int]
    codec: Optional[str]
    bitrate: Optional[str]  # e.g., "5000k"
    file_size: int  # bytes
    frame_rate: Optional[float]
    is_valid: bool  # ffprobe succeeded
    validation_warnings: List[str] = field(default_factory=list)

    @property
    def duration_formatted(self) -> str:
        """Format duration as HH:MM:SS"""
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def resolution_str(self) -> str:
        """Format resolution as WIDTHxHEIGHT"""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "Unknown"

    @property
    def file_size_str(self) -> str:
        """Format file size"""
        for unit in ['B', 'MB', 'GB']:
            if self.file_size < 1000:
                return f"{self.file_size:.1f}{unit}"
            self.file_size /= 1000
        return f"{self.file_size:.1f}TB"
```

**Recommendation**:
- Extract: duration, resolution, codec, file size (required)
- Extract: bitrate, frame rate (optional, nice-to-have)
- Display compact: "12:34 | 1920x1080 | H.264 | 256MB"
- Show full details on hover or in metadata panel

---

#### 5.2 How to efficiently extract metadata with ffprobe?

**ffprobe Command**:

```bash
ffprobe -v error \
  -show_entries format=duration,size \
  -show_entries stream=width,height,codec_name,bit_rate,r_frame_rate \
  -of json \
  input.mp4
```

**Output**:
```json
{
  "streams": [
    {
      "index": 0,
      "codec_type": "video",
      "codec_name": "h264",
      "width": 1920,
      "height": 1080,
      "r_frame_rate": "24/1",
      "bit_rate": "5000000"
    },
    {
      "index": 1,
      "codec_type": "audio",
      "codec_name": "aac"
    }
  ],
  "format": {
    "filename": "input.mp4",
    "nb_streams": 2,
    "duration": "754.32",
    "size": "268435456"
  }
}
```

**Implementation**:

```python
class MetadataProber:
    """Extract video metadata using ffprobe"""

    def __init__(self):
        self.cache = {}  # Cache results to avoid re-probing

    def probe_file(self, file_path: str) -> VideoMetadata:
        """Probe video file for metadata"""

        # Check cache first
        abs_path = os.path.abspath(file_path)
        if abs_path in self.cache:
            return self.cache[abs_path]

        try:
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration,size',
                    '-show_entries', 'stream=width,height,codec_name,bit_rate,r_frame_rate',
                    '-of', 'json',
                    file_path
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return VideoMetadata(
                    file_path=file_path,
                    duration=0,
                    width=None,
                    height=None,
                    codec=None,
                    bitrate=None,
                    file_size=os.path.getsize(file_path),
                    frame_rate=None,
                    is_valid=False,
                    validation_warnings=["ffprobe failed: " + result.stderr[:100]]
                )

            data = json.loads(result.stdout)

            # Extract video stream info
            video_stream = next(
                (s for s in data['streams'] if s.get('codec_type') == 'video'),
                None
            )

            # Extract format info
            format_info = data.get('format', {})

            metadata = VideoMetadata(
                file_path=file_path,
                duration=float(format_info.get('duration', 0)),
                width=video_stream.get('width') if video_stream else None,
                height=video_stream.get('height') if video_stream else None,
                codec=video_stream.get('codec_name') if video_stream else None,
                bitrate=video_stream.get('bit_rate') if video_stream else None,
                file_size=int(format_info.get('size', os.path.getsize(file_path))),
                frame_rate=self._parse_frame_rate(video_stream.get('r_frame_rate')) if video_stream else None,
                is_valid=True
            )

            # Cache result
            self.cache[abs_path] = metadata
            return metadata

        except subprocess.TimeoutExpired:
            return VideoMetadata(
                file_path=file_path,
                duration=0,
                width=None,
                height=None,
                codec=None,
                bitrate=None,
                file_size=0,
                frame_rate=None,
                is_valid=False,
                validation_warnings=["Metadata probing timed out"]
            )
        except Exception as e:
            return VideoMetadata(
                file_path=file_path,
                duration=0,
                width=None,
                height=None,
                codec=None,
                bitrate=None,
                file_size=0,
                frame_rate=None,
                is_valid=False,
                validation_warnings=[str(e)]
            )

    @staticmethod
    def _parse_frame_rate(r_frame_rate: str) -> Optional[float]:
        """Parse frame rate from 'num/den' format"""
        if not r_frame_rate:
            return None
        try:
            num, den = map(float, r_frame_rate.split('/'))
            return num / den
        except:
            return None
```

**Performance Notes**:
- ffprobe takes 0.5-2 seconds per file (network drive is slower)
- Caching essential to avoid re-probing same files
- For batch add, spawn metadata probing in background thread
- Show "Probing metadata..." indicator while scanning

**Recommendation**:
- Use ffprobe with JSON output
- Cache results aggressively (by absolute file path)
- Handle corrupted files gracefully (set is_valid=False)
- Probe in background thread for large batches

---

## 6. FFmpeg Filter Chains & Ordering

### Problem Statement
Users want to apply multiple video filters (rotate, crop, scale, brightness/contrast, deinterlace) in correct order to avoid processing artifacts.

### Key Questions

#### 6.1 What's the correct order for filters?

**Filter Order** (Recommended):
1. **Rotate**: Changes frame dimensions
2. **Crop**: Removes areas after rotation
3. **Scale**: Resize to target resolution
4. **Color Adjustments**: Brightness, contrast, saturation (visual only, no dimension change)
5. **Deinterlace**: Clean up interlacing artifacts (end of chain)
6. **Delogo**: Remove watermark (very last)

**Rationale**:
- Rotate first because it changes dimensions
- Crop after rotation to remove areas accurately
- Scale after crop to match target resolution
- Color adjustments in middle (no dimension dependencies)
- Deinterlace near end to clean final output
- Delogo last to preserve logo removal effectiveness

**Example Filter Chain**:

```bash
# Input: 1920x1080 interlaced video with watermark
-vf "rotate=PI/2,crop=1920:800:0:140,scale=1280:720,eq=brightness=0.2:contrast=1.1,yadif,delogo=x=100:y=100:w=200:h=100"

# Result: Video rotated 90°, cropped, scaled to 1280x720, brightness adjusted, deinterlaced, logo removed
```

**Recommendation**:
- Fixed order: rotate → crop → scale → color → deinterlace → delogo
- Don't allow user to reorder (too complex)
- Document filter dependencies in UI help text

---

#### 6.2 How to build FFmpeg filter graph string?

**Implementation**:

```python
@dataclass
class FilterChain:
    """Represents a sequence of video filters"""

    # Individual filters
    rotate_angle: Optional[float] = None  # In radians (0, PI/2, PI, 3*PI/2)
    crop_top: int = 0
    crop_bottom: int = 0
    crop_left: int = 0
    crop_right: int = 0
    scale_width: Optional[int] = None
    scale_height: Optional[int] = None
    brightness: float = 0.0  # -1.0 to 1.0
    contrast: float = 1.0  # 0.0 to 2.0
    saturation: float = 1.0  # 0.0 to 2.0
    deinterlace: bool = False
    delogo_x: Optional[int] = None
    delogo_y: Optional[int] = None
    delogo_w: Optional[int] = None
    delogo_h: Optional[int] = None

    def build_ffmpeg_filter_graph(self) -> str:
        """Build FFmpeg -vf parameter from enabled filters"""

        filters = []

        # 1. Rotate
        if self.rotate_angle is not None:
            filters.append(f"rotate={self.rotate_angle}")

        # 2. Crop
        if self.crop_top > 0 or self.crop_bottom > 0 or self.crop_left > 0 or self.crop_right > 0:
            # This requires calculating width/height from input
            # For simplicity, require user to specify final dimensions
            # Format: crop=width:height:x:y
            if self.crop_left > 0 and self.crop_top > 0:
                # Assume removing from edges: x=crop_left, y=crop_top
                filters.append(f"crop=in_w-{self.crop_left}-{self.crop_right}:in_h-{self.crop_top}-{self.crop_bottom}:{self.crop_left}:{self.crop_top}")

        # 3. Scale
        if self.scale_width is not None and self.scale_height is not None:
            filters.append(f"scale={self.scale_width}:{self.scale_height}")
        elif self.scale_width is not None:
            filters.append(f"scale={self.scale_width}:-1")  # Preserve aspect
        elif self.scale_height is not None:
            filters.append(f"scale=-1:{self.scale_height}")  # Preserve aspect

        # 4. Color adjustments
        color_filters = []
        if self.brightness != 0.0:
            color_filters.append(f"brightness={self.brightness}")
        if self.contrast != 1.0:
            color_filters.append(f"contrast={self.contrast}")
        if self.saturation != 1.0:
            color_filters.append(f"saturation={self.saturation}")

        if color_filters:
            filters.append('eq=' + ':'.join(color_filters))

        # 5. Deinterlace
        if self.deinterlace:
            filters.append("yadif")

        # 6. Delogo
        if self.delogo_x is not None and self.delogo_y is not None and \
           self.delogo_w is not None and self.delogo_h is not None:
            filters.append(f"delogo=x={self.delogo_x}:y={self.delogo_y}:w={self.delogo_w}:h={self.delogo_h}")

        return ','.join(filters)
```

**Usage in VideoProcessor**:

```python
def _process_with_subprocess(self, input_path: str, output_path: str, ...):
    cmd = ['ffmpeg', '-i', input_path]

    # ... trim parameters ...

    # Build and apply filter chain
    filter_chain = self.state.filter_chain  # From AppState
    filter_graph = filter_chain.build_ffmpeg_filter_graph()
    if filter_graph:
        cmd.extend(['-vf', filter_graph])

    # ... encoding parameters ...
    cmd.append(output_path)

    # ... subprocess execution ...
```

**Recommendation**:
- Create FilterChain class with all filter parameters
- Implement build_ffmpeg_filter_graph() method
- Use 'eq=' for brightness/contrast/saturation combined
- Use 'yadif' for deinterlace
- Join filters with commas

---

## Appendix: Implementation Roadmap

This research covers the top 8 technical areas for the Enhanced Workflow & Performance feature. Implementation should proceed in this order:

1. **Phase 1**: Parallel Processing + Threading Architecture (weeks 1-2)
2. **Phase 2**: Templates & Persistence (weeks 2-3)
3. **Phase 3**: Hardware Encoder Detection (weeks 3-4)
4. **Phase 4**: Drag-and-Drop + UI (weeks 4-5)
5. **Phase 5**: Metadata Extraction & Validation (weeks 5-6)
6. **Phase 6**: Video Filters & Advanced Options (weeks 6-7)
7. **Phase 7**: Batch State Recovery & Error Handling (weeks 7-8)
8. **Phase 8**: Testing & Polish (weeks 8-10)

---

**Document Version**: 1.0
**Last Updated**: 2026-02-08
**Status**: Ready for Implementation
