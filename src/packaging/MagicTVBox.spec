# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MagicTVBox

This file configures how PyInstaller bundles the application into
a standalone Windows executable.

To build: pyinstaller src/packaging/MagicTVBox.spec
"""

import os

block_cipher = None

a = Analysis(
    ['../../main.py'],  # Entry point (relative to this spec file: src/packaging/../../main.py)
    pathex=[],
    binaries=[
        # Bundle FFmpeg executable
        ('C:/ffmpeg/bin/ffmpeg.exe', '.'),
    ],
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
    icon='icon.ico' if os.path.exists('src/packaging/icon.ico') else None,
    version='version_info.txt',
)
