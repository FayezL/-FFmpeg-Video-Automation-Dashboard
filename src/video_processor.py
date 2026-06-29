"""
FFmpeg video processing logic
"""

import subprocess
import json
import os
from typing import Optional, Dict, Callable, List, Tuple
import threading

try:
    import ffmpeg

    HAS_FFMPEG_PYTHON = True
except ImportError:
    HAS_FFMPEG_PYTHON = False

from src.state import AppState, ProcessingFile, FileStatus, CutUnit


def convert_cut_value_to_seconds(
    value: float,
    unit: CutUnit,
    video_duration: float,
    video_fps: float,
) -> float:
    """Convert a cut value in the given unit to seconds.

    Args:
        value: The cut value (seconds, percentage, or frame number).
        unit: The unit to interpret the value in.
        video_duration: Total video duration in seconds (for PERCENT).
        video_fps: Video frame rate (for FRAMES).

    Returns:
        Equivalent time in seconds (always >= 0).

    Raises:
        ValueError: If unit is FRAMES and fps is 0/unknown, or unknown unit.
    """
    if unit == CutUnit.TIME:
        return max(0.0, float(value))
    if unit == CutUnit.PERCENT:
        clamped = max(0.0, min(100.0, float(value)))
        return video_duration * (clamped / 100.0)
    if unit == CutUnit.FRAMES:
        if video_fps <= 0:
            raise ValueError(
                "Cannot use frame-based cut: video FPS is unknown or zero"
            )
        return float(value) / float(video_fps)
    raise ValueError(f"Unknown unit: {unit}")


def _parse_frame_rate(rate_string) -> float:
    """Parse an ffprobe frame-rate string like '30/1' or '24000/1001' into a float.

    Returns 0.0 if the input is None, empty, or cannot be parsed.
    """
    if not rate_string:
        return 0.0
    try:
        if "/" in rate_string:
            num, den = rate_string.split("/", 1)
            den_f = float(den)
            return float(num) / den_f if den_f != 0 else 0.0
        return float(rate_string)
    except (ValueError, TypeError):
        return 0.0


class VideoProcessor:
    """Handles FFmpeg video processing"""

    def __init__(self, state: AppState):
        self.state = state

    def probe_video(self, file_path: str) -> Dict:
        """Probe video file to get metadata"""
        try:
            if HAS_FFMPEG_PYTHON:
                probe = ffmpeg.probe(file_path)
                video_stream = next(
                    (s for s in probe["streams"] if s["codec_type"] == "video"), None
                )
                return {
                    "duration": float(probe["format"].get("duration", 0)),
                    "width": video_stream.get("width") if video_stream else None,
                    "height": video_stream.get("height") if video_stream else None,
                    "fps": _parse_frame_rate(
                        video_stream.get("r_frame_rate") if video_stream else None
                    ),
                }
            else:
                # Fallback to ffprobe command
                cmd = [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-show_entries",
                    "stream=codec_type,width,height,r_frame_rate",
                    "-of",
                    "json",
                    file_path,
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                data = json.loads(result.stdout)
                video_stream = next(
                    (
                        s
                        for s in data.get("streams", [])
                        if s.get("codec_type") == "video"
                    ),
                    None,
                )
                return {
                    "duration": float(data["format"].get("duration", 0)),
                    "width": video_stream.get("width") if video_stream else None,
                    "height": video_stream.get("height") if video_stream else None,
                    "fps": _parse_frame_rate(
                        video_stream.get("r_frame_rate") if video_stream else None
                    ),
                }
        except Exception as e:
            self.state.add_log(f"Error probing video: {str(e)}")
            raise

    def _build_ffmpeg_params(self, output_path: str) -> dict:
        """Build FFmpeg parameters from processing profile"""
        from src.state import PROCESSING_PROFILES

        profile = PROCESSING_PROFILES[self.state.processing_profile]

        params = {
            "vcodec": profile.video_codec,
            "preset": profile.video_preset,
            "pix_fmt": profile.pixel_format,
            "acodec": profile.audio_codec,
            "audio_bitrate": profile.audio_bitrate,
        }

        # Use CRF or bitrate (mutually exclusive)
        if profile.video_crf is not None:
            params["crf"] = profile.video_crf
        elif profile.video_bitrate is not None:
            params["video_bitrate"] = profile.video_bitrate

        # Add faststart for MP4 files
        if profile.use_faststart and output_path.lower().endswith(".mp4"):
            params["movflags"] = "+faststart"

        return params

    def _build_ffmpeg_cmd_params(self, output_path: str) -> list:
        """Build FFmpeg command-line parameters from processing profile"""
        from src.state import PROCESSING_PROFILES

        profile = PROCESSING_PROFILES[self.state.processing_profile]

        cmd = [
            "-c:v",
            profile.video_codec,
            "-preset",
            profile.video_preset,
            "-pix_fmt",
            profile.pixel_format,
            "-c:a",
            profile.audio_codec,
            "-b:a",
            profile.audio_bitrate,
        ]

        # Use CRF or bitrate (mutually exclusive)
        if profile.video_crf is not None:
            cmd.extend(["-crf", str(profile.video_crf)])
        elif profile.video_bitrate is not None:
            cmd.extend(["-b:v", profile.video_bitrate])

        # Add x264-specific options if specified
        if profile.x264_profile or profile.x264_level:
            x264_opts = []
            if profile.x264_profile:
                x264_opts.append(f"profile={profile.x264_profile}")
            if profile.x264_level:
                x264_opts.append(f"level={profile.x264_level}")
            if x264_opts:
                cmd.extend(["-x264-params", ":".join(x264_opts)])

        return cmd

    def _compute_cut_from_unit(
        self, total_duration: float, video_fps: float
    ) -> Tuple[float, float]:
        """Compute (start_time, end_time) in seconds from the current cut_unit setting.

        Mirrors the dual-checkbox model used by the TIME path:
        - cut_start_enabled + cut_start_percent/frame → remove from start
        - cut_end_enabled + cut_end_percent/frame → remove from end

        Returns:
            (start_time, end_time) in seconds.
        """
        unit = self.state.cut_unit
        cfg = self.state

        start_time = 0.0
        end_time = total_duration

        if cfg.cut_start_enabled:
            val = (
                cfg.cut_start_percent
                if unit == CutUnit.PERCENT
                else cfg.cut_start_frame
            )
            start_time = convert_cut_value_to_seconds(
                val, unit, total_duration, video_fps
            )

        if cfg.cut_end_enabled:
            val = (
                cfg.cut_end_percent
                if unit == CutUnit.PERCENT
                else cfg.cut_end_frame
            )
            if val is not None:
                amount = convert_cut_value_to_seconds(
                    val, unit, total_duration, video_fps
                )
                end_time = max(1.0, total_duration - amount)

        return start_time, end_time

    def process_video(
        self,
        input_path: str,
        output_path: str,
        on_progress: Optional[Callable[[float], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
        processing_file: Optional[ProcessingFile] = None,
    ) -> Tuple[bool, Optional[str]]:
        if not os.path.isfile(input_path):
            err = f"Input file not found: {input_path}"
            if on_log:
                on_log(err + "\n")
            return False, err

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                err = f"Cannot create output folder: {output_dir}\n{e}"
                if on_log:
                    on_log(err + "\n")
                return False, err

        try:
            metadata = self.probe_video(input_path)
            total_duration = metadata["duration"]
            video_fps = metadata.get("fps", 0.0)

            start_time = 0.0
            end_time = total_duration

            if processing_file and processing_file.use_custom_cut:
                if processing_file.custom_cut_start_seconds is not None:
                    start_time = processing_file.custom_cut_start_seconds
                if processing_file.custom_cut_end_seconds is not None:
                    end_time = processing_file.custom_cut_end_seconds
            elif self.state.cut_unit != CutUnit.TIME:
                start_time, end_time = self._compute_cut_from_unit(
                    total_duration, video_fps
                )
            elif self.state.cut_start_enabled or self.state.cut_end_enabled:
                if self.state.cut_start_enabled:
                    start_seconds = self.state.cut_start_total_seconds_trim
                    start_time = start_seconds
                if self.state.cut_end_enabled:
                    end_seconds = self.state.cut_end_total_seconds_trim
                    end_time = max(start_time + 1, total_duration - end_seconds)

            duration = end_time - start_time
            if duration <= 0:
                duration = 0

            if HAS_FFMPEG_PYTHON:
                return self._process_with_ffmpeg_python(
                    input_path, output_path, duration, start_time, on_progress, on_log
                )
            else:
                return self._process_with_subprocess(
                    input_path, output_path, duration, start_time, on_progress, on_log
                )
        except FileNotFoundError as e:
            err = f"FFmpeg not found. Please install FFmpeg and add it to your PATH.\n\nDetails: {e}"
            if on_log:
                on_log(err + "\n")
            return False, err
        except Exception as e:
            err = f"{type(e).__name__}: {str(e)}"
            if on_log:
                on_log(err + "\n")
            self.state.add_log(err)
            return False, err

    def _process_with_ffmpeg_python(
        self,
        input_path: str,
        output_path: str,
        duration: Optional[float],
        start_time: float,
        on_progress: Optional[Callable[[float], None]],
        on_log: Optional[Callable[[str], None]],
    ) -> Tuple[bool, Optional[str]]:
        """Process using ffmpeg-python library"""
        try:
            # Apply duration cut with optional start
            input_kwargs = {}
            if start_time > 0:
                input_kwargs["ss"] = start_time
            if duration is not None:
                input_kwargs["t"] = duration
            input_stream = (
                ffmpeg.input(input_path, **input_kwargs)
                if input_kwargs
                else ffmpeg.input(input_path)
            )

            # Apply delogo if enabled
            if self.state.apply_delogo:
                params = self.state.delogo_params
                input_stream = ffmpeg.filter(
                    input_stream,
                    "delogo",
                    x=params.x,
                    y=params.y,
                    w=params.w,
                    h=params.h,
                )

            # Build output stream with profile parameters
            params = self._build_ffmpeg_params(output_path)
            output = ffmpeg.output(input_stream, output_path, **params)

            if on_log:
                on_log(f"Command: {' '.join(ffmpeg.compile(output))}\n")

            # Run FFmpeg with progress tracking
            return self._process_with_subprocess(
                input_path, output_path, duration, start_time, on_progress, on_log
            )
        except Exception as e:
            err = f"{type(e).__name__}: {str(e)}"
            if on_log:
                on_log(f"Error: {err}\n")
            return False, err

    def _process_with_subprocess(
        self,
        input_path: str,
        output_path: str,
        duration: Optional[float],
        start_time: float,
        on_progress: Optional[Callable[[float], None]],
        on_log: Optional[Callable[[str], None]],
    ) -> Tuple[bool, Optional[str]]:
        """Process using subprocess with progress tracking"""
        import re

        cmd = ["ffmpeg", "-i", input_path]

        # Apply trim: -ss (start) and -t (duration)
        if start_time > 0:
            cmd.extend(["-ss", str(start_time)])
        if duration is not None:
            cmd.extend(["-t", str(duration)])

        # Apply delogo if enabled
        if self.state.apply_delogo:
            params = self.state.delogo_params
            cmd.extend(
                ["-vf", f"delogo=x={params.x}:y={params.y}:w={params.w}:h={params.h}"]
            )

        # Encoding settings from profile
        cmd.extend(self._build_ffmpeg_cmd_params(output_path))

        # Limit threads per FFmpeg process to prevent CPU saturation
        cmd.extend(["-threads", str(self.state.ffmpeg_threads)])

        cmd.extend(["-y"])  # Overwrite output

        # Faststart for MP4 (from profile)
        from src.state import PROCESSING_PROFILES

        profile = PROCESSING_PROFILES[self.state.processing_profile]
        if profile.use_faststart and output_path.lower().endswith(".mp4"):
            cmd.extend(["-movflags", "+faststart"])

        cmd.append(output_path)

        if on_log:
            on_log(f"Command: {' '.join(cmd)}\n")

        # Get total duration for progress calculation
        total_duration = duration
        if total_duration is None:
            try:
                metadata = self.probe_video(input_path)
                total_duration = metadata["duration"]
            except Exception:
                total_duration = None

        # Collect output for error reporting
        output_lines: List[str] = []

        try:
            creationflags = 0
            if os.name == "nt" and self.state.process_priority == "low":
                creationflags = subprocess.BELOW_NORMAL_PRIORITY_CLASS
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                creationflags=creationflags,
            )
        except FileNotFoundError:
            return False, (
                "FFmpeg not found. Please install FFmpeg and add it to your system PATH.\n\n"
                "Download from: https://ffmpeg.org/download.html"
            )

        # Monitor progress and collect output
        def monitor_progress():
            nonlocal output_lines
            time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")
            for line in process.stdout:
                output_lines.append(line)
                if on_log:
                    on_log(line)
                if total_duration and on_progress:
                    match = time_pattern.search(line)
                    if match:
                        hours, minutes, seconds, centiseconds = map(int, match.groups())
                        current_time = (
                            hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0
                        )
                        percent = min(100.0, (current_time / total_duration) * 100.0)
                        on_progress(percent)

        monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
        monitor_thread.start()

        process.wait()

        if process.returncode == 0:
            if on_progress:
                on_progress(100.0)
            if on_log:
                on_log("Processing completed successfully!\n")
            return True, None

        # Build detailed error message from FFmpeg output
        last_lines = output_lines[-15:] if len(output_lines) > 15 else output_lines
        ffmpeg_err = "".join(last_lines).strip() if last_lines else "(no output)"
        err_msg = (
            f"FFmpeg failed (exit code {process.returncode}).\n\n"
            f"Last output:\n{ffmpeg_err}"
        )
        if on_log:
            on_log(f"FFmpeg error: {err_msg}\n")
        return False, err_msg

    def process_queue(
        self,
        files: List[ProcessingFile],
        on_file_error: Optional[Callable[[str, str], None]] = None,
        output_folder_override: Optional[str] = None,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:
        """Process a queue of files using parallel processing.
        output_folder_override: use this folder for outputs (e.g. for Task 2).
        on_complete: called when the whole batch finishes (so UI can clear task running state).
        """
        from src.parallel_processor import ParallelProcessor

        if on_complete is None:
            self.state.is_processing = True
        max_workers = self.state.parallel_config.max_workers

        parallel = ParallelProcessor(
            self.state,
            self,
            max_workers=max_workers,
            output_folder_override=output_folder_override or None,
        )

        def on_file_start(file: ProcessingFile):
            file.status = FileStatus.PROCESSING
            file.progress = 0.0
            self.state.add_log(f"\n=== Processing: {file.name} ===\n")

        def on_file_complete(
            file: ProcessingFile, success: bool, error_msg: Optional[str]
        ):
            if success:
                file.status = FileStatus.COMPLETED
                file.progress = 1.0
                self.state.add_log(f"✓ Completed: {file.name}\n")
            else:
                file.status = FileStatus.ERROR
                file.error = error_msg
                self.state.add_log(f"✗ Failed: {file.name} - {error_msg}\n")
                if on_file_error:
                    on_file_error(file.name, error_msg or "Unknown error")

        def on_progress(file_id: str, percent: float):
            for f in files:
                if f.id == file_id:
                    f.progress = percent
                    break

        try:
            parallel.process_batch(
                files,
                on_file_start=on_file_start,
                on_file_complete=on_file_complete,
                on_progress=on_progress,
            )
            # Wait for all workers to finish
            for worker in parallel._workers:
                worker.join()
            self.state.add_log("\n=== All files processed ===\n")
        finally:
            if on_complete is None:
                self.state.is_processing = False
            if on_complete:
                on_complete()

    def _get_output_path(
        self,
        input_path: str,
        output_folder_override: Optional[str] = None,
        file_index: Optional[int] = None,
    ) -> str:
        """Get output path for a file.

        When the Rename Plan is enabled, the output filename becomes:
            {rename_base}{N:0<pad>d}{ext}
        where N = rename_start + file_index (0-based position in the batch).

        Works for any batch size — 1 file, 30 episodes, or 50+.
        Falls back to the original filename (+ prefix/suffix) when rename is off
        or the base name is empty.
        """
        base = (
            output_folder_override
            if output_folder_override is not None
            else self.state.output_folder
        )
        output_folder = base or os.path.dirname(input_path)
        if self.state.create_output_subfolder:
            output_folder = os.path.join(output_folder, "output")
            os.makedirs(output_folder, exist_ok=True)

        ext = f".{self.state.output_format}"

        # --- Rename Plan (sequential episode numbering) ---
        if self.state.rename_enabled and self.state.rename_base.strip():
            ep_number = self.state.rename_start + (file_index or 0)
            padded = str(ep_number).zfill(self.state.rename_pad)
            output_name = f"{self.state.rename_base.strip()}{padded}{ext}"
        else:
            # Original behaviour: keep input filename + optional prefix/suffix
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_name = (
                f"{self.state.output_prefix}{base_name}{self.state.output_suffix}{ext}"
            )

        return os.path.join(output_folder, output_name)
