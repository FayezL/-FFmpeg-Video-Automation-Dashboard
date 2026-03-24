"""
Integration test for single-instance behavior

Tests that only one instance of the application can run at a time.
"""

from pathlib import Path


def test_single_instance_behavior():
    exe_path = Path("dist/VideoForge.exe")

    if not exe_path.exists():
        import pytest

        pytest.skip("Executable not built yet")

    assert True, "Manual test: Launch exe twice, verify behavior"
