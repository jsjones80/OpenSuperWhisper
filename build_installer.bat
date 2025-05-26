@echo off
echo Building OpenSuperWhisper for Windows...
echo.

REM Activate virtual environment if it exists
if exist "opensuperwhisper_env\Scripts\activate.bat" (
    echo Activating virtual environment...
    call opensuperwhisper_env\Scripts\activate.bat
)

REM Install PyInstaller if not already installed
echo Installing PyInstaller...
pip install pyinstaller

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Create icon if it doesn't exist (you should replace this with a real icon)
if not exist "opensuperwhisper.ico" (
    echo Creating placeholder icon...
    echo. > opensuperwhisper.ico
)

REM Build with PyInstaller
echo Building executable with PyInstaller...
pyinstaller opensuperwhisper.spec --clean

if %errorlevel% neq 0 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable is in: dist\OpenSuperWhisper\
echo.

REM Create Inno Setup script if it doesn't exist
if not exist "installer_setup.iss" (
    echo Creating Inno Setup script...
    call :create_inno_script
)

echo.
echo To create the installer:
echo 1. Install Inno Setup from https://jrsoftware.org/isdl.php
echo 2. Open installer_setup.iss in Inno Setup
echo 3. Click "Build" -^> "Compile"
echo.
pause
exit /b 0

:create_inno_script
(
echo ; Inno Setup Script for OpenSuperWhisper
echo.
echo #define MyAppName "OpenSuperWhisper"
echo #define MyAppVersion "1.0.0"
echo #define MyAppPublisher "OpenSuperWhisper"
echo #define MyAppURL "https://github.com/OpenSuperWhisper"
echo #define MyAppExeName "OpenSuperWhisper.exe"
echo.
echo [Setup]
echo AppId={{A8E5F3C2-9A7B-4D6E-8F1C-2B3A4D5E6F7A}
echo AppName={#MyAppName}
echo AppVersion={#MyAppVersion}
echo AppPublisher={#MyAppPublisher}
echo AppPublisherURL={#MyAppURL}
echo AppSupportURL={#MyAppURL}
echo AppUpdatesURL={#MyAppURL}
echo DefaultDirName={autopf}\{#MyAppName}
echo DefaultGroupName={#MyAppName}
echo AllowNoIcons=yes
echo LicenseFile=LICENSE
echo InfoBeforeFile=README.md
echo OutputDir=installer_output
echo OutputBaseFilename=OpenSuperWhisper_Setup_{#MyAppVersion}
echo SetupIconFile=opensuperwhisper.ico
echo Compression=lzma
echo SolidCompression=yes
echo WizardStyle=modern
echo.
echo [Languages]
echo Name: "english"; MessagesFile: "compiler:Default.isl"
echo.
echo [Tasks]
echo Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
echo Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
echo.
echo [Files]
echo Source: "dist\OpenSuperWhisper\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
echo.
echo [Icons]
echo Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
echo Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
echo Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
echo Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon
echo.
echo [Run]
echo Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
) > installer_setup.iss
exit /b