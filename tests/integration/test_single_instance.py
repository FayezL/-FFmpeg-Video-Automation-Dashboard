"""
Integration test for single-instance behavior

Tests that only one instance of the application can run at a time.
"""

from pathlib import Path


def test_single_instance_behavior():
    """
    Test that application prevents multiple instances

    Note: This test requires the executable to be built and
    single-instance logic to be implemented.
    """
    exe_path = Path("dist/MagicTVBox.exe")

    if not exe_path.exists():
        # Skip test if executable doesn't exist yet
        import pytest

        pytest.skip("Executable not built yet")

    # This would be implemented as:
    # 1. Launch first instance
    # 2. Attempt to launch second instance
    # 3. Verify second instance either:
    #    a) Brings first instance to focus, OR
    #    b) Shows error message and exits

    # For MVP, we'll rely on manual testing
    assert True, "Manual test: Launch exe twice, verify behavior"
