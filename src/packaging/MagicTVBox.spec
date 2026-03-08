# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MagicTVBox

This file configures how PyInstaller bundles the application into
a standalone Windows executable.

To build: pyinstaller src/packaging/MagicTVBox.spec
"""

import os
import sys

block_cipher = None

# Get the directory where this spec file is located
# SPECPATH is automatically set by PyInstaller when running the spec file
try:
    spec_dir = SPECPATH
except NameError:
    # Fallback: derive from the spec file location
    spec_dir = os.path.dirname(os.path.abspath(sys.argv[0] if sys.argv[0] else '.'))

project_root = os.path.dirname(os.path.dirname(spec_dir))

# Debug output
print(f"[DEBUG] spec_dir: {spec_dir}")
print(f"[DEBUG] project_root: {project_root}")

# Determine FFmpeg path
ffmpeg_path = None
ffmpeg_locations = [
    'C:/ffmpeg/bin/ffmpeg.exe',  # Standard Windows location
    os.path.join(project_root, 'ffmpeg.exe'),  # Project root
    os.path.join(spec_dir, 'ffmpeg.exe'),  # Packaging directory
]

for location in ffmpeg_locations:
    if os.path.exists(location):
        ffmpeg_path = location
        break

# Prepare binaries list
binaries = []
if ffmpeg_path:
    binaries.append((ffmpeg_path, '.'))
    print(f"[INFO] FFmpeg found at: {ffmpeg_path}")
else:
    print("[WARNING] FFmpeg not found. Executable will require FFmpeg in PATH or same directory.")

# Prepare icon path
icon_path = os.path.join(spec_dir, 'icon.ico')
if not os.path.exists(icon_path):
    icon_path = None
    print("[INFO] No custom icon found, using default Windows icon")

# Prepare data files
datas = []
assets_path = os.path.join(spec_dir, 'assets')
if os.path.exists(assets_path):
    datas.append((assets_path, 'assets'))
    print(f"[INFO] Assets directory found: {assets_path}")
else:
    print("[INFO] No assets directory found (optional)")

# Build the Analysis
a = Analysis(
    [os.path.join(project_root, 'main.py')],  # Entry point (absolute path)
    pathex=[project_root],  # Add project root to path
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        # CustomTkinter and tkinter
        'customtkinter',
        'PIL._tkinter_finder',
        
        # Required for existing features
        'tkinterdnd2',
        
        # OpenCV and NumPy (Phase 4: AI Logo Detection)
        'cv2',
        'numpy.core._multiarray_umath',
        'numpy.core._methods',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unused packages to reduce size
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
        'tkinter.test',
        'unittest',
        'test',
        'tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Build the EXE with proper version file path
version_file = os.path.join(spec_dir, 'version_info.txt')
if not os.path.exists(version_file):
    print(f"[WARNING] Version file not found: {version_file}")
    version_file = None
else:
    print(f"[INFO] Version file found: {version_file}")

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MagicTVBox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Enable UPX compression for smaller size
    upx_exclude=[
        'vcruntime140.dll',
        'python38.dll',
        'python39.dll',
        'python310.dll',
        'python311.dll',
        'python312.dll',
        'python313.dll',
        'python314.dll',
    ],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI application
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
    version=version_file,
)
