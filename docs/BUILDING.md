# Building VideoForge Standalone Executable

This guide explains how to build a standalone Windows executable for VideoForge.

## Prerequisites

**Required**:
- Python 3.8 or higher
- All dependencies installed: `pip install -r requirements.txt`
- PyInstaller 5.13.0 (included in requirements.txt)
- Windows 10 or Windows 11 (64-bit)

**Optional**:
- UPX compression tool (for smaller executable size)
- Custom application icon (`.ico` file)

## Quick Start

The simplest way to build the executable:

```bash
python src/packaging/build_exe.py
```

This automated script will:
1. Clean previous builds
2. Run PyInstaller with the correct configuration
3. Create the executable in `dist/VideoForge.exe`
4. Report the final executable size

## Manual Build

If you prefer to run PyInstaller directly:

```bash
pyinstaller --clean --noconfirm src/packaging/VideoForge.spec
```

## Build Output

After a successful build:

- **Executable**: `dist/VideoForge.exe`
- **Build files**: `build/` (can be deleted)
- **Expected size**: 180-220 MB (with UPX compression)

## FFmpeg Integration

The executable bundles FFmpeg from `C:\ffmpeg\bin\ffmpeg.exe`.

**If FFmpeg is not at this location**:
1. Edit `src/packaging/VideoForge.spec`
2. Update the `binaries` path:
   ```python
   binaries=[
       ('C:/your/ffmpeg/path/ffmpeg.exe', '.'),
   ],
   ```
3. Rebuild

**Alternative**: Users can install FFmpeg separately and add it to PATH.

## Testing the Executable

### Basic Test (on your machine)
```bash
dist\VideoForge.exe
```

The application should:
- Launch within 5 seconds
- Show the main window with all UI elements
- Allow you to select and process videos

### Full Test (on clean machine)

**Important**: Test on a computer **without Python installed** to verify true standalone behavior.

1. Copy `dist\VideoForge.exe` to the test machine
2. Double-click to launch
3. Verify all features work:
   - File selection (drag-and-drop or browse)
   - Video processing (trim, delogo, format conversion)
   - Settings and preferences
   - Logs display

## Troubleshooting

### Build Fails

**"ModuleNotFoundError" during build**:
- Install missing dependencies: `pip install -r requirements.txt`

**"PyInstaller not found"**:
- Install PyInstaller: `pip install pyinstaller==5.13.0`

**FFmpeg not bundled**:
- Verify FFmpeg path in `VideoForge.spec`
- Or remove FFmpeg from spec and let users install it separately

### Executable Issues

**Application won't start**:
- Check if antivirus is blocking it
- Try running as Administrator
- Check `build/VideoForge/warn-VideoForge.txt` for warnings

**"FFmpeg not found" error**:
- FFmpeg was not bundled correctly
- Either fix the build or install FFmpeg on the target machine

**Executable too large (>500MB)**:
- Enable UPX compression in the spec file (already enabled)
- Check excludes list - ensure unused packages are excluded
- Remove unnecessary assets from `src/packaging/assets/`

## Size Optimization

Current configuration achieves ~200MB with these optimizations:

1. **UPX Compression** (enabled):
   ```python
   upx=True,
   ```

2. **Exclude Unused Packages** (already configured):
   ```python
   excludes=[
       'matplotlib', 'scipy', 'pandas',
       'IPython', 'jupyter', 'cv2', 'numpy'
   ]
   ```

3. **One-File Mode** (already configured):
   All files bundled into single .exe

**For even smaller size**:
- Don't bundle FFmpeg (let users install separately)
- Use one-folder mode instead of one-file (faster but less convenient)

## Distribution

### Simple Distribution
Just share the `VideoForge.exe` file. Users can:
1. Download it
2. Double-click to run
3. No installation needed!

### Professional Distribution
Create an installer using:
- Inno Setup (https://jrsoftware.org/isinfo.php)
- NSIS (https://nsis.sourceforge.io/)
- WiX Toolset (https://wixtoolset.org/)

Benefits of installer:
- Start menu shortcuts
- Desktop icon
- Proper uninstaller
- File associations
- More professional appearance

## Continuous Integration

To automate builds:

```yaml
# Example GitHub Actions workflow
- name: Build Executable
  run: |
    pip install -r requirements.txt
    python src/packaging/build_exe.py

- name: Upload Artifact
  uses: actions/upload-artifact@v2
  with:
    name: VideoForge-Windows
    path: dist/VideoForge.exe
```

## Version Updates

When releasing new versions:

1. Update version in `src/packaging/version_info.txt`:
   ```python
   filevers=(1, 1, 0, 0),  # Change version numbers
   prodvers=(1, 1, 0, 0),
   ```

2. Update version strings:
   ```python
   StringStruct(u'FileVersion', u'1.1.0.0'),
   StringStruct(u'ProductVersion', u'1.1.0.0')
   ```

3. Rebuild: `python src/packaging/build_exe.py`

## Custom Icon

To add a custom application icon:

1. Create or obtain a `.ico` file (256x256 recommended)
2. Save as `src/packaging/icon.ico`
3. The spec file will automatically use it
4. Rebuild

**Icon resources**:
- IconArchive: https://www.iconarchive.com/
- Icons8: https://icons8.com/
- Flaticon: https://www.flaticon.com/

## Notes

- **Build time**: Approximately 2-5 minutes on modern hardware
- **Disk space**: Build requires ~500MB temporary space
- **Python version**: Build machine Python version will be bundled
- **Dependencies**: All Python packages from requirements.txt are included
- **Cross-platform**: This build is Windows-only (macOS/Linux require separate builds)

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all prerequisites are met
3. Try a clean build (delete `build/` and `dist/` directories first)
4. Check the PyInstaller warnings in `build/VideoForge/warn-VideoForge.txt`

---

**Happy building!** 🚀
