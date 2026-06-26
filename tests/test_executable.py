"""
Tests for executable build output

These tests verify that the PyInstaller build produces a valid executable.
"""

from pathlib import Path


def test_executable_exists():
    exe_path = Path("dist/VideoForge.exe")

    assert exe_path.exists(), "Executable not found. Run build script first."
    assert exe_path.stat().st_size > 0, "Executable is empty"


def test_executable_size_under_limit():
    exe_path = Path("dist/VideoForge.exe")

    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        assert size_mb < 500, f"Executable size {size_mb:.1f}MB exceeds 500MB limit"


def test_build_script_exists():
    build_script = Path("src/packaging/build_exe.py")
    assert build_script.exists(), "Build script not found"


def test_spec_file_exists():
    spec_file = Path("src/packaging/VideoForge.spec")
    assert spec_file.exists(), "PyInstaller spec file not found"
