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
spec_dir = os.path.dirname(os.path.abspath(__name__))
project_root = os.path.dirname(os.path.dirname(spec_dir))

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

a = Analysis(
    ['../../main.py'],  # Entry point (relative to this spec file)
    pathex=[],
    binaries=binaries,
    datas=[
        # UI assets (if any exist)
        ('../packaging/assets', 'assets'),
    ],
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
    ],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI application
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
    version=os.path.join(spec_dir, 'version_info.txt'),
)
