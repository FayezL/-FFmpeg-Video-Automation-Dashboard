#!/usr/bin/env python3
"""
Automated build script for VideoForge executable

This script builds the standalone Windows executable using PyInstaller.

Usage:
    python src/packaging/build_exe.py

Or from project root:
    cd src/packaging && python build_exe.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def main():
    print("=" * 60)
    print("VideoForge Executable Build Script")
    print("=" * 60)
    print()

    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    print(f"Project root: {project_root}")
    print(f"Build script: {script_dir}")
    print()

    os.chdir(project_root)
    print(f"Working directory: {os.getcwd()}")
    print()

    try:
        import PyInstaller

        print(f"[OK] PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("[ERROR] PyInstaller not found!")
        print("  Install with: pip install -r requirements.txt")
        return 1

    ffmpeg_path = Path("C:/ffmpeg/bin/ffmpeg.exe")
    if ffmpeg_path.exists():
        print(f"[OK] FFmpeg found at: {ffmpeg_path}")
    else:
        print(f"[WARNING] FFmpeg not found at {ffmpeg_path}")
        print("  The executable will still build but may not work without FFmpeg")

    print()
    print("-" * 60)
    print("Starting PyInstaller build...")
    print("-" * 60)
    print()

    if Path("build").exists():
        print("Cleaning previous build directory...")
        shutil.rmtree("build")

    if Path("dist").exists():
        print("Cleaning previous dist directory...")
        shutil.rmtree("dist")

    print()

    spec_file = script_dir / "VideoForge.spec"

    if not spec_file.exists():
        print(f"[ERROR] Spec file not found: {spec_file}")
        return 1

    print(f"Building with spec file: {spec_file}")
    print()

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--clean",
                "--noconfirm",
                str(spec_file),
            ],
            capture_output=False,
            text=True,
        )

        if result.returncode != 0:
            print()
            print("[ERROR] Build failed!")
            return result.returncode

    except Exception as e:
        print(f"[ERROR] Build error: {e}")
        return 1

    print()
    print("=" * 60)
    print("Build Complete!")
    print("=" * 60)
    print()

    exe_path = Path("dist/VideoForge.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"[OK] Executable created: {exe_path}")
        print(f"  Size: {size_mb:.1f} MB")

        if size_mb > 500:
            print(f"  [WARNING] Warning: Size exceeds 500MB target")
        else:
            print(f"  [OK] Size is within target (<500MB)")

        print()
        print("Next steps:")
        print("  1. Test the executable: dist\\VideoForge.exe")
        print("  2. Test on a machine without Python installed")
        print("  3. Verify all features work correctly")
    else:
        print("[ERROR] Executable not found in dist/")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
