"""
Benchmark: VideoForge parallel processing vs manual sequential FFmpeg.

Generates a batch of test videos, then times two approaches:
  1. Manual: ffmpeg command run sequentially, one file at a time
  2. VideoForge: ParallelProcessor with worker pool (parallel encoding)

Both do identical work: trim 1s from start, re-encode to H.264 slow.
"""

import subprocess
import time
from pathlib import Path

NUM_FILES = 8
CLIP_SECONDS = 12
TRIM_SECONDS = 1

WORKDIR = Path("/tmp/opencode/videoforge_bench")
INPUT_DIR = WORKDIR / "input"
OUT_MANUAL = WORKDIR / "output_manual"
OUT_PARALLEL = WORKDIR / "output_parallel"


def generate_test_videos():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    for i in range(NUM_FILES):
        out = INPUT_DIR / f"clip_{i:02d}.mp4"
        if out.exists():
            continue
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"testsrc=size=640x480:rate=25:duration={CLIP_SECONDS}",
                "-f", "lavfi",
                "-i", f"sine=frequency={200 + i * 50}:duration={CLIP_SECONDS}",
                "-c:v", "libx264", "-preset", "slow", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                str(out),
            ],
            check=True,
            capture_output=True,
        )
        print(f"  generated {out.name}")


def bench_manual():
    OUT_MANUAL.mkdir(parents=True, exist_ok=True)
    files = sorted(INPUT_DIR.glob("*.mp4"))

    start = time.time()
    for f in files:
        out = OUT_MANUAL / f.name
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", str(TRIM_SECONDS),
                "-i", str(f),
                "-t", str(CLIP_SECONDS - TRIM_SECONDS),
                "-c:v", "libx264", "-preset", "slow", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-threads", "2",
                str(out),
            ],
            check=True,
            capture_output=True,
        )
        print(f"  [manual] done: {f.name}")
    return time.time() - start


def bench_parallel(workers=4):
    OUT_PARALLEL.mkdir(parents=True, exist_ok=True)
    for f in OUT_PARALLEL.glob("*"):
        f.unlink()

    from src.state import AppState, ProcessingFile
    from src.parallel_processor import ParallelProcessor
    from src.video_processor import VideoProcessor

    state = AppState()
    state.ffmpeg_threads = 2
    state.cut_start_enabled = True
    state.cut_start_seconds = TRIM_SECONDS
    state.cut_end_enabled = False

    files = sorted(INPUT_DIR.glob("*.mp4"))
    file_list = [
        ProcessingFile(id=str(i), path=str(f), name=f.name)
        for i, f in enumerate(files)
    ]
    state.selected_files = file_list

    processor = VideoProcessor(state)
    pp = ParallelProcessor(
        state=state,
        video_processor=processor,
        max_workers=workers,
        output_folder_override=str(OUT_PARALLEL),
    )

    completed = []

    def on_complete(file, success, error_msg):
        completed.append((file.name, success))
        print(f"  [parallel {workers}w] done: {file.name}")

    start = time.time()
    pp.process_batch(
        file_list,
        on_file_complete=on_complete,
    )

    while pp.is_processing():
        time.sleep(0.2)

    elapsed = time.time() - start
    return elapsed


def main():
    print("=" * 65)
    print("  VideoForge Benchmark: Sequential vs Parallel Processing")
    print("=" * 65)
    print(f"  Files:     {NUM_FILES} clips x {CLIP_SECONDS}s each")
    print("  Encoder:   libx264 -preset slow -crf 23")
    print("  Threads:   2 per process (capped via -threads flag)")
    print(f"  CPU cores: {__import__('os').cpu_count()}")
    print()

    print("Step 1: Generating test videos...")
    generate_test_videos()
    print()

    print("Step 2: Manual sequential FFmpeg (1 file at a time)...")
    manual_time = bench_manual()
    print(f"  -> {manual_time:.1f}s\n")

    print("Step 3: VideoForge ParallelProcessor (4 workers)...")
    parallel4_time = bench_parallel(workers=4)
    print(f"  -> {parallel4_time:.1f}s\n")

    print("Step 4: VideoForge ParallelProcessor (8 workers)...")
    parallel8_time = bench_parallel(workers=8)
    print(f"  -> {parallel8_time:.1f}s\n")

    print("=" * 65)
    print("  RESULTS")
    print("=" * 65)
    print(f"  Manual (sequential):     {manual_time:6.1f}s  ({manual_time/NUM_FILES:.1f}s/file)")
    print(f"  VideoForge (4 workers):  {parallel4_time:6.1f}s  ({parallel4_time/NUM_FILES:.1f}s/file)")
    print(f"  VideoForge (8 workers):  {parallel8_time:6.1f}s  ({parallel8_time/NUM_FILES:.1f}s/file)")
    print()
    s4 = manual_time / parallel4_time
    s8 = manual_time / parallel8_time
    print(f"  Speedup (4 workers):     {s4:5.2f}x  ({(1 - parallel4_time/manual_time)*100:.0f}% faster)")
    print(f"  Speedup (8 workers):     {s8:5.2f}x  ({(1 - parallel8_time/manual_time)*100:.0f}% faster)")
    print("=" * 65)


if __name__ == "__main__":
    main()
