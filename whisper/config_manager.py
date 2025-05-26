"""
Configuration Manager for OpenSuperWhisper
Handles loading and saving application settings to persistent storage
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration with persistent storage"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager
        
        Args:
            config_file: Path to configuration file. If None, uses default location.
        """
        if config_file is None:
            # Use user's AppData directory on Windows
            if os.name == 'nt':
                config_dir = Path(os.environ.get('APPDATA', '')) / 'OpenSuperWhisper'
            else:
                # Fallback for other systems
                config_dir = Path.home() / '.opensuperwhisper'
            
            config_dir.mkdir(exist_ok=True)
            self.config_file = config_dir / 'config.json'
        else:
            self.config_file = Path(config_file)
        
        # Default settings
        self.default_settings = {
            'audio_device': None,
            'audio_device_name': None,
            'sample_rate': 16000,
            'monitor_audio': False,
            'noise_reduction': False,
            'model': 'base',
            'device': 'cpu',  # CPU/GPU selection
            'language': 'auto',
            'task': 'transcribe',
            'temperature': 0.0,
            'record_hotkey': 'Ctrl+Shift+R',
            'window_hotkey': 'Ctrl+Shift+W',
            'autostart': False,
            'system_tray': True,
            'theme': 'default',
            'auto_cleanup': True,
            'window_geometry': '800x600',
            'window_position': None
        }
        
        self.settings = self.default_settings.copy()
        self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from configuration file
        
        Returns:
            Dictionary containing loaded settings
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Validate and merge with defaults
                for key, value in loaded_settings.items():
                    if key in self.default_settings:
                        self.settings[key] = value
                    else:
                        logger.warning(f"Unknown setting '{key}' ignored")
                
                logger.info(f"Settings loaded from {self.config_file}")
            else:
                logger.info("No configuration file found, using defaults")
                
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            logger.info("Using default settings")
            self.settings = self.default_settings.copy()
        
        return self.settings.copy()
    
    def save_settings(self, settings: Optional[Dict[str, Any]] = None) -> bool:
        """Save settings to configuration file
        
        Args:
            settings: Settings dictionary to save. If None, saves current settings.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if settings is not None:
                # Validate settings before saving
                validated_settings = {}
                for key, value in settings.items():
                    if key in self.default_settings:
                        validated_settings[key] = value
                    else:
                        logger.warning(f"Unknown setting '{key}' not saved")
                
                self.settings.update(validated_settings)
            
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file with pretty formatting
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Settings saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a specific setting value
        
        Args:
            key: Setting key
            value: Setting value
        """
        if key in self.default_settings:
            self.settings[key] = value
        else:
            logger.warning(f"Unknown setting '{key}' not set")
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all current settings
        
        Returns:
            Copy of all current settings
        """
        return self.settings.copy()
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values"""
        self.settings = self.default_settings.copy()
        logger.info("Settings reset to defaults")
    
    def backup_settings(self, backup_path: Optional[str] = None) -> bool:
        """Create a backup of current settings
        
        Args:
            backup_path: Path for backup file. If None, creates timestamped backup.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if backup_path is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.config_file.parent / f"config_backup_{timestamp}.json"
            
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Settings backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup settings: {e}")
            return False
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """Restore settings from a backup file
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_settings = json.load(f)
            
            # Validate and restore
            validated_settings = {}
            for key, value in backup_settings.items():
                if key in self.default_settings:
                    validated_settings[key] = value
            
            self.settings.update(validated_settings)
            logger.info(f"Settings restored from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore settings from backup: {e}")
            return False


# Singleton instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get singleton configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
