@echo off
REM OpenSuperWhisper Windows Installation Script
REM This script sets up the environment and installs all dependencies

echo ========================================
echo OpenSuperWhisper Windows Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

REM Create virtual environment
echo Creating virtual environment...
python -m venv opensuperwhisper_env
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call opensuperwhisper_env\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install PyTorch with CUDA support (if available)
echo Installing PyTorch...
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

REM Install requirements
echo Installing requirements...
python -m pip install -r requirements.txt

REM Install the package in development mode
echo Installing OpenSuperWhisper...
python -m pip install -e .

REM Create desktop shortcut
echo Creating desktop shortcut...
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_PATH=%DESKTOP%\OpenSuperWhisper.lnk
set TARGET_PATH=%CD%\opensuperwhisper_env\Scripts\python.exe
set ARGUMENTS=%CD%\opensuperwhisper_gui.py
set WORKING_DIR=%CD%

powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%TARGET_PATH%'; $Shortcut.Arguments = '%ARGUMENTS%'; $Shortcut.WorkingDirectory = '%WORKING_DIR%'; $Shortcut.Save()"

REM Create start script
echo Creating start script...
echo @echo off > start_opensuperwhisper.bat
echo cd /d "%CD%" >> start_opensuperwhisper.bat
echo call opensuperwhisper_env\Scripts\activate.bat >> start_opensuperwhisper.bat
echo python opensuperwhisper_gui.py >> start_opensuperwhisper.bat
echo pause >> start_opensuperwhisper.bat

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo You can now run OpenSuperWhisper by:
echo 1. Double-clicking the desktop shortcut
echo 2. Running start_opensuperwhisper.bat
echo 3. Or manually: opensuperwhisper_env\Scripts\activate.bat then python opensuperwhisper_gui.py
echo.
echo Note: The first run may take longer as it downloads the AI model.
echo.
pause
