# Quickstart Guide: Standalone Executable & Logo Detection

**Feature**: Standalone Executable & AI Logo Detection
**Date**: 2026-02-08
**Audience**: Developers and end users

---

## For Developers: Building the Executable

### Prerequisites

**Required**:
- Python 3.8+ installed
- All project dependencies: `pip install -r requirements.txt`
- PyInstaller 5.x: `pip install pyinstaller==5.13.0`
- FFmpeg 4.0+ installed and in PATH
- Windows 10+ (64-bit)

**Optional**:
- UPX for compression: Download from https://upx.github.io/

### Build Process

#### Step 1: Install Build Dependencies

```bash
# Install PyInstaller and build tools
pip install pyinstaller==5.13.0
pip install pywin32

# Verify installation
pyinstaller --version
```

#### Step 2: Prepare Build Environment

```bash
# Clean previous builds
rm -rf build/ dist/

# Create packaging directory if not exists
mkdir -p src/packaging/assets
```

#### Step 3: Configure PyInstaller Spec File

The spec file is located at `src/packaging/MagicTVBox.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../main.py'],  # Entry point
    pathex=['src'],
    binaries=[
        ('C:/ffmpeg/bin/ffmpeg.exe', '.'),  # Bundle FFmpeg
    ],
    datas=[
        ('src/packaging/assets', 'assets'),  # UI resources
    ],
    hiddenimports=[
        'customtkinter',
        'PIL._tkinter_finder',
        'cv2',
        'numpy.core._multiarray_umath',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'tkinter.test',
        'unittest',
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
    upx=True,  # Enable UPX compression
    upx_exclude=['vcruntime140.dll', 'python38.dll'],
    runtime_tmpdir=None,
    console=False,  # No console window
    icon='src/packaging/icon.ico',
    version_file='src/packaging/version_info.txt',
)
```

#### Step 4: Run Build Script

**Option A: Automated Build** (Recommended)
```bash
# Run build script
python src/packaging/build_exe.py

# Output: build/MagicTVBox.exe (~200MB)
```

**Option B: Manual Build**
```bash
# Change to project root
cd c:/Users/Administrator/Documents/GitHub/-FFmpeg-Video-Automation-Dashboard

# Run PyInstaller
pyinstaller --clean --noconfirm src/packaging/MagicTVBox.spec

# Output in: dist/MagicTVBox.exe
```

#### Step 5: Test the Executable

```bash
# Test on build machine (with Python)
./dist/MagicTVBox.exe

# Test on clean machine (without Python)
# Copy dist/MagicTVBox.exe to a VM without Python and test
```

### Build Troubleshooting

**Problem**: "ImportError: DLL load failed while importing cv2"
**Solution**: Add opencv dependencies to hiddenimports:
```python
hiddenimports=['cv2', 'numpy.core._multiarray_umath']
```

**Problem**: Executable size > 500MB
**Solution**:
1. Enable UPX compression: `upx=True`
2. Exclude unused packages: Add to `excludes=[]`
3. Use opencv-python-headless instead of opencv-python

**Problem**: "FFmpeg not found" error when running
**Solution**: Verify FFmpeg is bundled in spec file:
```python
binaries=[('C:/path/to/ffmpeg.exe', '.')]
```

**Problem**: Application crashes on startup
**Solution**:
1. Run with console: `console=True` to see error messages
2. Check for missing hidden imports
3. Verify all data files are included in `datas=[]`

### Build Optimization

**Size Reduction**:
```bash
# Before optimization: ~290MB
# After UPX compression: ~200MB
# After excluding unused deps: ~180MB
```

**Optimization Checklist**:
- ✅ UPX compression enabled
- ✅ Unused packages excluded (matplotlib, scipy, pandas)
- ✅ opencv-python-headless used (not opencv-python)
- ✅ Debug symbols stripped: `strip=False` (Windows doesn't benefit from strip)
- ✅ One-file mode (single .exe instead of directory)

---

## For End Users: Using the Application

### Installation

**Requirements**:
- Windows 10 or Windows 11 (64-bit)
- 4GB RAM minimum, 8GB recommended
- 500MB free disk space
- No Python required!

**Installation Steps**:

1. **Download** the application:
   - Download `MagicTVBox.exe` from the releases page
   - Or receive from a colleague

2. **First Run**:
   - Double-click `MagicTVBox.exe`
   - Windows SmartScreen may show a warning (click "More info" → "Run anyway")
   - Application will open in 3-5 seconds

3. **FFmpeg Setup** (if not bundled):
   - If you see "FFmpeg not found", download FFmpeg from: https://ffmpeg.org/download.html
   - Extract and add to PATH, or place `ffmpeg.exe` in the same folder as `MagicTVBox.exe`

### Basic Usage

#### 1. Processing Videos (Existing Functionality)

1. Launch MagicTVBox.exe
2. Click "Select Files" or drag-and-drop videos
3. Choose output folder
4. Configure processing options:
   - Cut mode (Cut Last, Cut First, Cut Range)
   - Time parameters (hours, minutes, seconds)
   - Delogo (manual coordinates)
   - Output format (MP4, MKV)
5. Click "Start Processing"

#### 2. Using Logo Detection (New Feature)

**Automatic Logo Detection**:

1. Load your video files
2. Navigate to the **Delogo** section
3. Click **"Detect Logos"** button
4. Wait for detection (typically 1-3 minutes for a 1-hour video)
5. Review detected regions:
   - Each region shows a preview with bounding box
   - Confidence percentage displayed (e.g., 87%)
   - Region coordinates (X, Y, Width, Height)

**Accepting Detected Logos**:

1. Click on a detected region to preview
2. If correct:
   - Click **"Accept"** or press Enter
   - Coordinates auto-populate delogo parameters
3. If incorrect:
   - Click **"Reject"** or press Delete
   - Detection is discarded
4. If partially correct:
   - Click **"Adjust"** to manually fine-tune coordinates
   - Use arrow keys or enter exact values

**Processing with Detected Logos**:

1. After accepting a logo region, delogo is automatically enabled
2. X, Y, W, H parameters are pre-filled
3. Proceed with normal video processing
4. FFmpeg delogo filter will remove the logo

### Logo Detection Tips

**For Best Results**:

1. **Use High-Quality Source Videos**
   - 1080p or higher recommended
   - Avoid heavily compressed videos
   - Clear, visible logos work best

2. **Adjust Sensitivity**
   - Default: 75% (balanced)
   - Higher = more detections (may include false positives)
   - Lower = fewer detections (may miss subtle logos)

3. **Logo Position Matters**
   - Corner logos (top-right, bottom-right) are easiest to detect
   - Centered or moving logos are harder
   - Static logos work best

4. **Handle False Positives**
   - Not all detections are logos (text, graphics, etc.)
   - Always review before accepting
   - Reject non-logo detections to improve future accuracy

### Saving Detection Profiles

**Why Use Profiles?**
If you process videos from the same source (e.g., CNN, HBO, BBC), you can save detection settings and logo patterns for faster processing in the future.

**Create a Profile**:

1. After successful detection, click **"Save Profile"**
2. Enter a descriptive name: "CNN Watermark"
3. Optionally add description and tags
4. Click **Save**

**Use a Saved Profile**:

1. In the Delogo section, click **"Load Profile"** dropdown
2. Select your saved profile (e.g., "CNN Watermark")
3. Click **"Detect Logos"**
4. Detection will use saved settings and patterns
5. Known logos will be detected faster and more accurately

**Profile Location**:
- Profiles are saved to: `C:/Users/[YourName]/AppData/Roaming/MagicTVBox/profiles/`
- You can share profiles with others by copying the JSON files

---

## Common Workflows

### Workflow 1: Quick Logo Removal

**Scenario**: You have a single video with a watermark you want to remove.

**Steps**:
1. Double-click `MagicTVBox.exe`
2. Drag video into the app
3. Select output folder
4. Click **"Detect Logos"** in Delogo section
5. Wait 1-2 minutes for detection
6. Review and accept the correct logo region
7. Click **"Start Processing"**
8. Done! Output video has logo removed

**Time**: ~5 minutes total (2 min detection + 3 min processing for 1-hour video)

---

### Workflow 2: Batch Processing with Same Logo

**Scenario**: You have 10 videos from the same TV channel with the same corner logo.

**Steps**:
1. Process first video:
   - Detect logos
   - Accept correct region
   - Save profile: "CNN Logo"
2. For videos 2-10:
   - Drag all videos into app
   - Load profile: "CNN Logo"
   - Click "Detect Logos" (faster with saved pattern)
   - Verify detections
   - Start batch processing

**Time Saved**: ~70% (detection uses saved pattern, no manual coordinate entry)

---

### Workflow 3: Manual Refinement

**Scenario**: Detection found the logo but bounding box is slightly off.

**Steps**:
1. After detection, click on the region
2. Click **"Adjust"**
3. Fine-tune coordinates:
   - X: Move left/right
   - Y: Move up/down
   - W: Adjust width
   - H: Adjust height
4. Preview shows real-time updates
5. Click **"Accept"** when satisfied
6. Process video

**Tip**: Use arrow keys for 1-pixel adjustments, or type exact values.

---

## Advanced Features

### Adjusting Sensitivity

**When to Adjust**:
- Too many false positives → Lower sensitivity (e.g., 60%)
- Missing subtle logos → Raise sensitivity (e.g., 85%)

**How to Adjust**:
1. In Delogo section, find **"Sensitivity"** slider
2. Drag to desired level (0-100%)
3. Click **"Detect Logos"** again
4. Compare results

**Sensitivity Guide**:
- **50-60%**: Very conservative, only high-confidence logos
- **70-80%**: Balanced (default 75%)
- **85-95%**: Aggressive, detects subtle logos but may have false positives

### Canceling Detection

**If detection takes too long**:
1. Click **"Cancel"** button
2. Detection stops immediately
3. Partial results are discarded
4. Try with lower sensitivity or fewer frames

### Profile Management

**View All Profiles**:
1. Click **"Manage Profiles"** in Delogo section
2. See list of all saved profiles
3. View statistics: accuracy, videos processed, etc.

**Edit Profile**:
1. Load profile
2. Adjust settings
3. Click **"Update Profile"**
4. Changes are saved

**Delete Profile**:
1. In "Manage Profiles", select profile
2. Click **"Delete"**
3. Confirm deletion
4. Profile is permanently removed

---

## Troubleshooting

### Application Issues

**Problem**: "Application failed to start"
**Solution**:
- Ensure you're running Windows 10+ (64-bit)
- Check if antivirus is blocking the application
- Run as Administrator (right-click → "Run as administrator")

**Problem**: "FFmpeg not found"
**Solution**:
- Download FFmpeg from https://ffmpeg.org
- Extract and place `ffmpeg.exe` in same folder as `MagicTVBox.exe`
- Or install FFmpeg and add to system PATH

**Problem**: Application is slow to start
**Solution**:
- First launch is slower (3-5 seconds is normal)
- Subsequent launches should be faster
- Check if antivirus is scanning the executable

### Detection Issues

**Problem**: "No logos detected" but logos are visible
**Solution**:
1. Increase sensitivity (try 85%)
2. Check if logos are in corners (easiest to detect)
3. Verify video quality (1080p+ recommended)
4. Try manual coordinate entry as fallback

**Problem**: Too many false positives
**Solution**:
1. Lower sensitivity (try 65%)
2. Reject false positives (improves future accuracy)
3. Use position zones to limit detection areas

**Problem**: Detection takes more than 5 minutes
**Solution**:
1. Cancel detection
2. Check video file size (4K videos take longer)
3. Try increasing frame sampling (e.g., every 60th frame instead of 30th)
4. Consider using manual coordinates for very long videos

**Problem**: Detected region is slightly off
**Solution**:
1. Use "Adjust" feature to fine-tune
2. Adjust X, Y, W, H values by 5-10 pixels
3. Preview updates in real-time
4. Accept when bounding box correctly covers logo

### Processing Issues

**Problem**: Processed video has visible logo remnants
**Solution**:
1. Bounding box may be too small
2. Re-detect or manually adjust to cover entire logo
3. Add 10-20 pixel margin around logo
4. Process again

**Problem**: Processed video has blurred area larger than logo
**Solution**:
1. Bounding box may be too large
2. Re-detect or manually adjust to exact logo size
3. Process again

---

## Keyboard Shortcuts

**During Detection Review**:
- `Enter` - Accept current region
- `Delete` - Reject current region
- `↑ ↓ ← →` - Adjust region by 1 pixel (when in Adjust mode)
- `Shift + ↑ ↓ ← →` - Adjust region by 10 pixels
- `Tab` - Next detected region
- `Shift + Tab` - Previous detected region
- `Esc` - Cancel detection / Close preview

**General**:
- `Ctrl + O` - Select files
- `Ctrl + S` - Save profile
- `Ctrl + Q` - Quit application
- `F1` - Help
- `F5` - Refresh file list

---

## Performance Notes

**Expected Performance**:

| Video Length | Resolution | Detection Time | Processing Time |
|--------------|------------|----------------|-----------------|
| 10 minutes | 1080p | 30-45 seconds | 1-2 minutes |
| 1 hour | 1080p | 2-3 minutes | 5-10 minutes |
| 2 hours | 1080p | 4-6 minutes | 10-20 minutes |
| 1 hour | 4K | 5-8 minutes | 30-60 minutes |

**Optimization Tips**:
- Close other applications during processing
- Use SSD for input/output folders (faster than HDD)
- Don't resize or move windows during detection (can slow UI)

---

## Sharing Profiles

**Export Profile**:
1. Navigate to: `C:/Users/[YourName]/AppData/Roaming/MagicTVBox/profiles/`
2. Copy the `.json` file (e.g., `cnn_watermark.json`)
3. Share via email, cloud drive, or USB

**Import Profile**:
1. Receive `.json` file from someone
2. Copy to: `C:/Users/[YourName]/AppData/Roaming/MagicTVBox/profiles/`
3. Restart MagicTVBox
4. Profile appears in "Load Profile" dropdown

**Profile Compatibility**:
- Profiles are cross-compatible between users
- Profile version must match application version
- Future versions will auto-migrate old profiles

---

## Getting Help

**In-App Help**:
- Press `F1` or click Help → Documentation
- Tooltip hover for control explanations

**Online Resources**:
- Project GitHub: [Link to repository]
- Issue Tracker: [Link to issues]
- Community Forum: [Link to discussions]

**Reporting Issues**:
1. Take screenshot of error message
2. Note steps to reproduce
3. Include video details (resolution, duration, format)
4. Open issue on GitHub or contact support

---

## What's Next?

**Current Features** (Phase 1 & 2):
- ✅ Standalone executable (no Python required)
- ✅ Automatic logo detection with AI
- ✅ Detection profiles (save/load)
- ✅ Manual adjustment of detected regions
- ✅ Integration with existing delogo feature

**Coming Soon** (Phase 3 - Future Enhancement):
- Learning from user corrections (improved accuracy over time)
- Batch detection across multiple videos
- Cloud profile sharing repository
- Support for animated/moving logos
- Mobile app version

---

**Enjoy automatic logo detection! 🎉**

For questions, suggestions, or issues, please visit our GitHub repository or contact support.
