# Building OpenSuperWhisper Windows Installer

This guide explains how to build a Windows installer for OpenSuperWhisper.

## Prerequisites

1. **Python 3.8 or higher** (64-bit)
2. **Visual Studio Build Tools** (for compiling Python extensions)
   - Download from: https://visualstudio.microsoft.com/downloads/
   - Install "Desktop development with C++" workload
3. **Inno Setup 6.x** (for creating the installer)
   - Download from: https://jrsoftware.org/isdl.php

## Build Steps

### 1. Prepare the Environment

```batch
# Clone the repository (if not already done)
git clone https://github.com/yourusername/OpenSuperWhisper.git
cd OpenSuperWhisper

# Create virtual environment
python -m venv opensuperwhisper_env

# Activate virtual environment
opensuperwhisper_env\Scripts\activate

# Install build requirements
pip install -r requirements-build.txt
```

### 2. Create Application Icon

```batch
# Generate the application icon
python create_icon.py
```

If this fails, you'll need to create `opensuperwhisper.ico` manually using an icon editor.

### 3. Build the Executable

```batch
# Run the build script
build_installer.bat
```

This will:
- Clean previous builds
- Build the executable using PyInstaller
- Create the `dist\OpenSuperWhisper\` directory with all files

### 4. Create the Installer

1. Open **Inno Setup Compiler**
2. Open `installer_setup.iss`
3. Click **Build** → **Compile**
4. The installer will be created in `installer_output\`

## Manual Build Steps

If the automated build fails, you can build manually:

### Build with PyInstaller

```batch
# Clean previous builds
rmdir /s /q build dist

# Build the executable
pyinstaller opensuperwhisper.spec --clean

# Or build with a simple command
pyinstaller --onedir --windowed --name OpenSuperWhisper opensuperwhisper_gui_pyqt6.py
```

### Common Build Issues

1. **Missing modules**: Add them to `hiddenimports` in `opensuperwhisper.spec`
2. **DLL errors**: Ensure Visual C++ Redistributables are installed
3. **Large file size**: Exclude unnecessary packages in the spec file
4. **Antivirus warnings**: Sign the executable with a code signing certificate

## Testing the Installer

1. Run the installer on a clean Windows system
2. Test all features:
   - Recording audio
   - Transcription
   - Settings/preferences
   - Hotkeys
   - System tray
   - Auto-start

## Distribution

### Signing the Installer

For distribution without Windows SmartScreen warnings:

```batch
# Sign the executable (requires code signing certificate)
signtool sign /tr http://timestamp.sectigo.com /td sha256 /fd sha256 /a "dist\OpenSuperWhisper\OpenSuperWhisper.exe"

# Sign the installer
signtool sign /tr http://timestamp.sectigo.com /td sha256 /fd sha256 /a "installer_output\OpenSuperWhisper_Setup_1.0.0_x64.exe"
```

### Creating a Portable Version

For users who prefer not to install:

```batch
# Copy the dist folder
xcopy /E /I dist\OpenSuperWhisper OpenSuperWhisper_Portable

# Create a batch file to run it
echo @echo off > OpenSuperWhisper_Portable\OpenSuperWhisper_Portable.bat
echo cd /d "%~dp0" >> OpenSuperWhisper_Portable\OpenSuperWhisper_Portable.bat
echo start OpenSuperWhisper.exe >> OpenSuperWhisper_Portable\OpenSuperWhisper_Portable.bat

# Zip the folder
powershell Compress-Archive -Path OpenSuperWhisper_Portable -DestinationPath OpenSuperWhisper_Portable_1.0.0.zip
```

## Automating Builds

For CI/CD, create a GitHub Actions workflow:

```yaml
name: Build Windows Installer

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        architecture: 'x64'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-build.txt
    
    - name: Build executable
      run: |
        pyinstaller opensuperwhisper.spec --clean
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: OpenSuperWhisper-Windows
        path: dist/
```

## Version Management

Update version numbers in:
1. `version_info.txt`
2. `installer_setup.iss`
3. `opensuperwhisper_gui_pyqt6.py` (in the About dialog)
4. `setup.py` (if you have one)

## Final Checklist

- [ ] All features work in the built executable
- [ ] Installer creates proper shortcuts
- [ ] Uninstaller removes all files
- [ ] Application runs on clean Windows 10/11
- [ ] No antivirus false positives
- [ ] File associations work (if implemented)
- [ ] Auto-start works correctly
- [ ] All dependencies are included