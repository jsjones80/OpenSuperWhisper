@echo off
echo ========================================
echo OpenSuperWhisper Windows Build Script
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Create/activate virtual environment
if not exist "opensuperwhisper_env" (
    echo Creating virtual environment...
    python -m venv opensuperwhisper_env
)

echo Activating virtual environment...
call opensuperwhisper_env\Scripts\activate.bat

REM Install/update pip
echo Updating pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt
pip install pyinstaller pillow pywin32-ctypes pefile

REM Create icon if needed
if not exist "opensuperwhisper.ico" (
    echo Creating application icon...
    python create_icon.py
)

REM Create installer images if needed
if not exist "installer_banner.bmp" (
    echo Creating installer images...
    python create_installer_images.py
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "installer_output" mkdir installer_output

REM Build executable
echo.
echo Building executable...
pyinstaller --clean --noconfirm opensuperwhisper.spec

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: dist\OpenSuperWhisper\
echo.
echo Next steps:
echo 1. Test the executable: dist\OpenSuperWhisper\OpenSuperWhisper.exe
echo 2. Install Inno Setup from: https://jrsoftware.org/isdl.php
echo 3. Open installer_setup.iss in Inno Setup
echo 4. Click Build -^> Compile to create the installer
echo.
echo The installer will be created in: installer_output\
echo.
pause