"""
FFmpeg video processing logic
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Optional, Dict, Callable, List, Tuple
import threading

try:
    import ffmpeg
    HAS_FFMPEG_PYTHON = True
except ImportError:
    HAS_FFMPEG_PYTHON = False

from src.state import AppState, ProcessingFile, FileStatus, CutMode


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
                    (s for s in probe['streams'] if s['codec_type'] == 'video'),
                    None
                )
                return {
                    'duration': float(probe['format'].get('duration', 0)),
                    'width': video_stream.get('width') if video_stream else None,
                    'height': video_stream.get('height') if video_stream else None,
                }
            else:
                # Fallback to ffprobe command
                cmd = [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-show_entries', 'stream=width,height',
                    '-of', 'json',
                    file_path
                ]
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                data = json.loads(result.stdout)
                video_stream = next(
                    (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
                    None
                )
                return {
                    'duration': float(data['format'].get('duration', 0)),
                    'width': video_stream.get('width') if video_stream else None,
                    'height': video_stream.get('height') if video_stream else None,
                }
        except Exception as e:
            self.state.add_log(f"Error probing video: {str(e)}")
            raise

    def _build_ffmpeg_params(self, output_path: str) -> dict:
        """Build FFmpeg parameters from processing profile"""
        from src.state import PROCESSING_PROFILES

        profile = PROCESSING_PROFILES[self.state.processing_profile]

        params = {
            'vcodec': profile.video_codec,
            'preset': profile.video_preset,
            'pix_fmt': profile.pixel_format,
            'acodec': profile.audio_codec,
            'audio_bitrate': profile.audio_bitrate,
        }

        # Use CRF or bitrate (mutually exclusive)
        if profile.video_crf is not None:
            params['crf'] = profile.video_crf
        elif profile.video_bitrate is not None:
            params['video_bitrate'] = profile.video_bitrate

        # Add faststart for MP4 files
        if profile.use_faststart and output_path.lower().endswith('.mp4'):
            params['movflags'] = '+faststart'

        return params

    def _build_ffmpeg_cmd_params(self, output_path: str) -> list:
        """Build FFmpeg command-line parameters from processing profile"""
        from src.state import PROCESSING_PROFILES

        profile = PROCESSING_PROFILES[self.state.processing_profile]

        cmd = [
            '-c:v', profile.video_codec,
            '-preset', profile.video_preset,
            '-pix_fmt', profile.pixel_format,
            '-c:a', profile.audio_codec,
            '-b:a', profile.audio_bitrate,
        ]

        # Use CRF or bitrate (mutually exclusive)
        if profile.video_crf is not None:
            cmd.extend(['-crf', str(profile.video_crf)])
        elif profile.video_bitrate is not None:
            cmd.extend(['-b:v', profile.video_bitrate])

        # Add x264-specific options if specified
        if profile.x264_profile or profile.x264_level:
            x264_opts = []
            if profile.x264_profile:
                x264_opts.append(f"profile={profile.x264_profile}")
            if profile.x264_level:
                x264_opts.append(f"level={profile.x264_level}")
            if x264_opts:
                cmd.extend(['-x264-params', ':'.join(x264_opts)])

        return cmd

    def process_video(
        self,
        input_path: str,
        output_path: str,
        on_progress: Optional[Callable[[float], None]] = None,
        on_log: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Process a single video file
        
        Returns:
            (success, error_message) - error_message is set when success is False
        """
        # Pre-flight checks
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
            # Calculate trim parameters based on cut mode
            duration = None
            start_time = 0.0
            
            if self.state.cut_mode != CutMode.NONE:
                metadata = self.probe_video(input_path)
                total_duration = metadata['duration']
                
                if self.state.cut_mode == CutMode.CUT_LAST:
                    cut_seconds = self.state.cut_total_seconds
                    duration = max(0, total_duration - cut_seconds)
                    start_time = 0.0
                elif self.state.cut_mode == CutMode.CUT_FIRST:
                    start_time = self.state.cut_total_seconds
                    duration = max(0, total_duration - start_time)
                elif self.state.cut_mode == CutMode.CUT_RANGE:
                    start_time = self.state.cut_start_total_seconds
                    end_seconds = self.state.cut_end_total_seconds
                    if end_seconds is not None:
                        duration = max(0, end_seconds - start_time)
                    else:
                        duration = max(0, total_duration - start_time)
            else:
                duration = None
                start_time = 0.0
            
            # Build FFmpeg command
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
        on_log: Optional[Callable[[str], None]]
    ) -> Tuple[bool, Optional[str]]:
        """Process using ffmpeg-python library"""
        try:
            # Apply duration cut with optional start
            input_kwargs = {}
            if start_time > 0:
                input_kwargs['ss'] = start_time
            if duration is not None:
                input_kwargs['t'] = duration
            input_stream = ffmpeg.input(input_path, **input_kwargs) if input_kwargs else ffmpeg.input(input_path)
            
            # Apply delogo if enabled
            if self.state.apply_delogo:
                params = self.state.delogo_params
                input_stream = ffmpeg.filter(
                    input_stream,
                    'delogo',
                    x=params.x,
                    y=params.y,
                    w=params.w,
                    h=params.h
                )
            
            # Build output stream with profile parameters
            params = self._build_ffmpeg_params(output_path)
            output = ffmpeg.output(
                input_stream,
                output_path,
                **params
            )
            
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
        on_log: Optional[Callable[[str], None]]
    ) -> Tuple[bool, Optional[str]]:
        """Process using subprocess with progress tracking"""
        import re
        
        cmd = ['ffmpeg', '-i', input_path]
        
        # Apply trim: -ss (start) and -t (duration)
        if start_time > 0:
            cmd.extend(['-ss', str(start_time)])
        if duration is not None:
            cmd.extend(['-t', str(duration)])
        
        # Apply delogo if enabled
        if self.state.apply_delogo:
            params = self.state.delogo_params
            cmd.extend([
                '-vf', f'delogo=x={params.x}:y={params.y}:w={params.w}:h={params.h}'
            ])
        
        # Encoding settings from profile
        cmd.extend(self._build_ffmpeg_cmd_params(output_path))
        cmd.extend(['-y'])  # Overwrite output

        # Faststart for MP4 (from profile)
        from src.state import PROCESSING_PROFILES
        profile = PROCESSING_PROFILES[self.state.processing_profile]
        if profile.use_faststart and output_path.lower().endswith('.mp4'):
            cmd.extend(['-movflags', '+faststart'])

        cmd.append(output_path)
        
        if on_log:
            on_log(f"Command: {' '.join(cmd)}\n")
        
        # Get total duration for progress calculation
        total_duration = duration
        if total_duration is None:
            try:
                metadata = self.probe_video(input_path)
                total_duration = metadata['duration']
            except Exception:
                total_duration = None
        
        # Collect output for error reporting
        output_lines: List[str] = []
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
        except FileNotFoundError:
            return False, (
                "FFmpeg not found. Please install FFmpeg and add it to your system PATH.\n\n"
                "Download from: https://ffmpeg.org/download.html"
            )
        
        # Monitor progress and collect output
        def monitor_progress():
            nonlocal output_lines
            time_pattern = re.compile(r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})')
            for line in process.stdout:
                output_lines.append(line)
                if on_log:
                    on_log(line)
                if total_duration and on_progress:
                    match = time_pattern.search(line)
                    if match:
                        hours, minutes, seconds, centiseconds = map(int, match.groups())
                        current_time = hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0
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
        on_file_error: Optional[Callable[[str, str], None]] = None
    ) -> None:
        """Process a queue of files. on_file_error(name, error_msg) called when a file fails."""
        self.state.is_processing = True
        
        try:
            for i, file in enumerate(files):
                if not self.state.is_processing:
                    self.state.add_log("Processing stopped by user.\n")
                    break
                
                self.state.current_file_index = i
                file.status = FileStatus.PROCESSING
                file.progress = 0.0
                
                self.state.add_log(f"\n=== Processing {i+1}/{len(files)}: {file.name} ===\n")
                
                # Determine output path with format, prefix, suffix
                output_folder = self.state.output_folder or os.path.dirname(file.path)
                if self.state.create_output_subfolder:
                    output_folder = os.path.join(output_folder, "output")
                    os.makedirs(output_folder, exist_ok=True)
                
                base_name = os.path.splitext(file.name)[0]
                ext = f".{self.state.output_format}"
                output_name = f"{self.state.output_prefix}{base_name}{self.state.output_suffix}{ext}"
                output_path = os.path.join(output_folder, output_name)
                
                def on_progress(percent: float):
                    file.progress = percent
                
                def on_log(message: str):
                    self.state.add_log(message)
                
                success, error_msg = self.process_video(
                    file.path,
                    output_path,
                    on_progress=on_progress,
                    on_log=on_log
                )
                
                if success:
                    file.status = FileStatus.COMPLETED
                    file.progress = 100.0
                    self.state.add_log(f"✓ Completed: {file.name}\n")
                else:
                    file.status = FileStatus.ERROR
                    file.error = error_msg or "Processing failed"
                    self.state.add_log(f"✗ Error: {file.name}\n{file.error}\n")
                    if on_file_error:
                        on_file_error(file.name, file.error)
            
            self.state.add_log("\n=== All files processed ===\n")
        finally:
            self.state.is_processing = False


