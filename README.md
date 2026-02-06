# MagicTVBox - FFmpeg Video Automation Dashboard

A modern Python desktop application for automating video processing tasks using FFmpeg. Convert your Bash scripts into a user-friendly dashboard for batch processing TV series, removing logos, and formatting videos for iOS/TV boxes.

## Features

- **Batch Processing**: Process multiple video files with the same settings
- **Single File Processing**: Process individual video files
- **Cut Last 5 Minutes**: Automatically calculate and cut the last 5 minutes from videos
- **Delogo Filter**: Remove logos with configurable position and size
- **Real-time Progress**: Track processing progress with visual feedback
- **Queue System**: Process files sequentially with status tracking
- **Logs Panel**: View FFmpeg output and processing logs
- **Dark Theme**: Modern, dashboard-style UI built with CustomTkinter

## Tech Stack

- **Python 3.8+**: Core programming language
- **CustomTkinter**: Modern, customizable Tkinter-based GUI framework
- **ffmpeg-python**: Python wrapper for FFmpeg (optional, falls back to subprocess)
- **Pillow**: Image processing library (required by CustomTkinter)

## Prerequisites

- Python 3.8 or higher
- FFmpeg installed and available in your system PATH

### Installing FFmpeg

**Windows:**
- Download from [FFmpeg website](https://ffmpeg.org/download.html)
- Extract and add to PATH, or use a package manager like Chocolatey: `choco install ffmpeg`

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
# Debian/Ubuntu
sudo apt install ffmpeg

# RHEL/CentOS
sudo yum install ffmpeg
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd -FFmpeg-Video-Automation-Dashboard
```

2. Create a virtual environment (recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

Or install using pip:
```bash
pip install customtkinter Pillow ffmpeg-python
```

## Running the Application

### Development Mode

Simply run the main Python file:

```bash
python main.py
```

Or if installed as a package:

```bash
magic-tv-box
```

## Usage

### Batch Processing

1. Navigate to **Batch Processor** in the sidebar
2. Configure processing options:
   - Enable/disable "Cut Last 5 Minutes"
   - Enable/disable "Apply Delogo Filter" (with X, Y, Width, Height parameters)
3. Click **Select Files** to choose video files to process
4. Click **Select Folder** to choose the output directory
5. Click **Start Processing** to begin

The application will process files sequentially, showing progress for each file in real-time.

### Single File Processing

1. Navigate to **Single File** in the sidebar
2. Configure processing options
3. Select a video file and output folder
4. Click **Process Video**

### Viewing Logs

Navigate to **Logs** in the sidebar to view FFmpeg output and processing messages in real-time. You can clear logs using the "Clear Logs" button.

### Settings

The Settings panel displays information about FFmpeg encoding settings and application information.

## Processing Options

### Cut Last 5 Minutes
Automatically calculates the video duration and cuts the last 5 minutes (300 seconds) from the video.

### Delogo Filter
Removes logos from videos. Default parameters:
- X: 1635
- Y: 240
- Width: 176
- Height: 147

You can adjust these values in the UI to match your video's logo position.

### Encoding Settings
The application uses the following FFmpeg settings (hardcoded for compatibility):
- Video Codec: H.264 (libx264)
- Preset: fast
- CRF: 23
- Pixel Format: YUV420P
- Audio Codec: AAC
- Audio Bitrate: 192k
- Faststart: Enabled (for web streaming)

These settings provide a good balance between quality and file size, ensuring compatibility with iOS devices and TV boxes.

## Project Structure

```
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup script
├── pyproject.toml         # Modern Python project configuration
├── src/
│   ├── __init__.py
│   ├── state.py           # Application state management
│   ├── video_processor.py # FFmpeg processing logic
│   └── ui/
│       ├── __init__.py
│       ├── batch_processor.py    # Batch processing UI
│       ├── single_processor.py  # Single file processing UI
│       ├── logs_panel.py         # Logs display UI
│       ├── settings_panel.py     # Settings UI
│       └── main_window.py        # Main window (placeholder)
```

## Building/Packaging

### Install as Package

```bash
pip install -e .
```

This installs the package in editable mode, allowing you to run `magic-tv-box` from anywhere.

### Create Distribution Package

```bash
python setup.py sdist bdist_wheel
```

This creates distribution packages in the `dist/` directory.

## Troubleshooting

### FFmpeg Not Found

If you get an error that FFmpeg is not found:
1. Ensure FFmpeg is installed
2. Verify it's in your system PATH by running `ffmpeg -version` in a terminal
3. On Windows, you may need to restart your terminal/IDE after adding FFmpeg to PATH

### Import Errors

If you encounter import errors:
1. Ensure you're using Python 3.8 or higher
2. Make sure all dependencies are installed: `pip install -r requirements.txt`
3. Verify you're in the correct virtual environment (if using one)

### GUI Not Displaying

If the GUI doesn't appear:
1. Check that CustomTkinter is properly installed
2. Ensure you're running the script, not importing it
3. Check for error messages in the terminal

## Development

### Code Style

The project follows Python PEP 8 style guidelines. Key principles:
- Use type hints where possible
- Keep functions focused and small
- Use meaningful variable and function names
- Add docstrings to classes and functions

### Adding Features

1. State management is handled in `src/state.py`
2. FFmpeg processing logic is in `src/video_processor.py`
3. UI components are in `src/ui/`
4. Main application logic is in `main.py`

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
