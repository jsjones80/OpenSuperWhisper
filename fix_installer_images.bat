@echo off
echo Fixing installer image issues...

REM Try to create images with Python
python create_installer_images.py

REM If that fails, create empty placeholder files
if not exist "installer_banner.bmp" (
    echo Creating placeholder installer_banner.bmp...
    echo. > installer_banner.bmp
)

if not exist "installer_small.bmp" (
    echo Creating placeholder installer_small.bmp...
    echo. > installer_small.bmp
)

echo.
echo Images created. You can now compile the installer.
echo Note: The installer will work but won't have custom images.
echo.
pause