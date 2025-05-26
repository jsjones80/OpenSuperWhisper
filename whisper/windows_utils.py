"""
Windows-specific utilities for OpenSuperWhisper
"""

import os
import sys
import winreg
from pathlib import Path


def get_autostart_registry_key():
    """Get the Windows registry key for autostart programs"""
    return winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_ALL_ACCESS
    )


def enable_autostart(app_name="OpenSuperWhisper", app_path=None):
    """Enable autostart on Windows startup"""
    try:
        if app_path is None:
            # Use the current executable or script
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                app_path = sys.executable
            else:
                # Running as script - create a batch file to launch it
                app_path = create_startup_batch()
        
        with get_autostart_registry_key() as key:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, str(app_path))
        
        print(f"Autostart enabled for {app_name}")
        return True
        
    except Exception as e:
        print(f"Failed to enable autostart: {e}")
        return False


def disable_autostart(app_name="OpenSuperWhisper"):
    """Disable autostart on Windows startup"""
    try:
        with get_autostart_registry_key() as key:
            winreg.DeleteValue(key, app_name)
        
        print(f"Autostart disabled for {app_name}")
        return True
        
    except FileNotFoundError:
        # Already disabled
        return True
    except Exception as e:
        print(f"Failed to disable autostart: {e}")
        return False


def is_autostart_enabled(app_name="OpenSuperWhisper"):
    """Check if autostart is enabled"""
    try:
        with get_autostart_registry_key() as key:
            value, _ = winreg.QueryValueEx(key, app_name)
            return bool(value)
    except FileNotFoundError:
        return False
    except Exception:
        return False


def create_startup_batch():
    """Create a batch file for starting the Python application"""
    # Get the path to the main script
    script_dir = Path(__file__).parent.parent
    main_script = script_dir / "opensuperwhisper_gui_pyqt6.py"
    
    # Create startup directory if it doesn't exist
    startup_dir = Path.home() / ".opensuperwhisper"
    startup_dir.mkdir(exist_ok=True)
    
    # Create batch file
    batch_file = startup_dir / "start_opensuperwhisper.bat"
    
    # Get Python executable path
    python_exe = sys.executable
    
    batch_content = f"""@echo off
cd /d "{script_dir}"
start "" "{python_exe}" "{main_script}"
exit
"""
    
    batch_file.write_text(batch_content)
    return str(batch_file)


def set_autostart(enabled: bool, app_name="OpenSuperWhisper"):
    """Set autostart status"""
    if enabled:
        return enable_autostart(app_name)
    else:
        return disable_autostart(app_name)