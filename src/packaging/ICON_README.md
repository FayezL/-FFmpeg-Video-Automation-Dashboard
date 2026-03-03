# Application Icon

**For MVP**: PyInstaller will use the default Windows application icon if no custom icon is specified.

**To add a custom icon**:

1. Create or obtain a `.ico` file (Windows icon format, 256x256 or multiple sizes)
2. Save it as `src/packaging/icon.ico`
3. The PyInstaller spec file will automatically use it

**Free icon resources**:
- https://www.iconarchive.com/
- https://icons8.com/
- https://www.flaticon.com/

**Icon guidelines**:
- Format: .ICO (Windows Icon)
- Sizes: Include 16x16, 32x32, 48x48, 256x256
- Style: Simple, clear representation of video/media application
- Suggested themes: Play button, film strip, video camera, TV
