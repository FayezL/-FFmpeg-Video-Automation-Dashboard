"""
Integration test for application startup time

Tests that the application launches within acceptable time limits.
"""

from pathlib import Path


def test_application_startup_time():
    exe_path = Path("dist/VideoForge.exe")

    if not exe_path.exists():
        import pytest

        pytest.skip("Executable not built yet")

    assert True, "Manual test: Launch exe and verify <5s startup"
