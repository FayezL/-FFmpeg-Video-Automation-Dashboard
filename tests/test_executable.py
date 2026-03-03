"""
Tests for executable build output

These tests verify that the PyInstaller build produces a valid executable.
"""

import os
import subprocess
from pathlib import Path


def test_executable_exists():
    """Test that the executable file is created"""
    # This test will be run after build
    # For now, it's a placeholder that will fail until we build
    exe_path = Path("dist/MagicTVBox.exe")

    # This will fail initially (TDD approach)
    assert exe_path.exists(), "Executable not found. Run build script first."
    assert exe_path.stat().st_size > 0, "Executable is empty"


def test_executable_size_under_limit():
    """Test that executable size is under 500MB"""
    exe_path = Path("dist/MagicTVBox.exe")

    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        assert (
            size_mb < 500
        ), f"Executable size {size_mb:.1f}MB exceeds 500MB limit"


def test_build_script_exists():
    """Test that the build script is present"""
    build_script = Path("src/packaging/build_exe.py")
    assert build_script.exists(), "Build script not found"


def test_spec_file_exists():
    """Test that the PyInstaller spec file is present"""
    spec_file = Path("src/packaging/MagicTVBox.spec")
    assert spec_file.exists(), "PyInstaller spec file not found"
