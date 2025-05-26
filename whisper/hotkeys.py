"""
Global Hotkey System for OpenSuperWhisper Windows
Handles system-wide keyboard shortcuts for recording control
"""

import sys
import threading
import time
from typing import Callable, Dict, Optional, List, Tuple
from dataclasses import dataclass

if sys.platform == "win32":
    try:
        from pynput import keyboard
        from pynput.keyboard import Key, KeyCode, Listener, GlobalHotKeys
        PYNPUT_AVAILABLE = True
    except ImportError:
        PYNPUT_AVAILABLE = False

    try:
        import win32con
        import win32gui
        import win32api
        WIN32_AVAILABLE = True
    except ImportError:
        WIN32_AVAILABLE = False
else:
    PYNPUT_AVAILABLE = False
    WIN32_AVAILABLE = False


@dataclass
class HotkeyConfig:
    """Configuration for a hotkey"""
    name: str
    keys: List[str]
    description: str
    callback: Optional[Callable] = None
    enabled: bool = True


class GlobalHotkeyManager:
    """Manages global hotkeys for the application"""

    def __init__(self):
        self.hotkeys: Dict[str, HotkeyConfig] = {}
        self.listener: Optional[GlobalHotKeys] = None
        self.is_running = False
        self.lock = threading.Lock()

        # Default hotkeys
        self._setup_default_hotkeys()

        # Check availability
        if not PYNPUT_AVAILABLE:
            print("Warning: pynput not available. Global hotkeys disabled.")
            return

    def _setup_default_hotkeys(self):
        """Setup default hotkey configurations"""
        self.hotkeys = {
            "toggle_recording": HotkeyConfig(
                name="toggle_recording",
                keys=["ctrl", "shift", "r"],
                description="Toggle recording on/off"
            ),
            "quick_transcribe": HotkeyConfig(
                name="quick_transcribe",
                keys=["ctrl", "shift", "t"],
                description="Quick transcribe clipboard audio"
            ),
            "show_window": HotkeyConfig(
                name="show_window",
                keys=["ctrl", "shift", "w"],
                description="Show/hide main window"
            )
        }

    def register_hotkey(
        self,
        name: str,
        keys: List[str],
        callback: Callable,
        description: str = ""
    ) -> bool:
        """Register a new hotkey"""
        if not PYNPUT_AVAILABLE:
            return False

        try:
            # Validate keys
            normalized_keys = self._normalize_keys(keys)
            if not normalized_keys:
                print(f"Invalid keys for hotkey '{name}': {keys}")
                return False

            # Create hotkey config
            hotkey_config = HotkeyConfig(
                name=name,
                keys=normalized_keys,
                description=description,
                callback=callback,
                enabled=True
            )

            with self.lock:
                self.hotkeys[name] = hotkey_config

            print(f"Registered hotkey '{name}': {' + '.join(normalized_keys)}")
            return True

        except Exception as e:
            print(f"Failed to register hotkey '{name}': {e}")
            return False

    def unregister_hotkey(self, name: str) -> bool:
        """Unregister a hotkey"""
        try:
            with self.lock:
                if name in self.hotkeys:
                    del self.hotkeys[name]
                    print(f"Unregistered hotkey '{name}'")
                    return True
                return False
        except Exception as e:
            print(f"Failed to unregister hotkey '{name}': {e}")
            return False

    def set_hotkey_callback(self, name: str, callback: Callable) -> bool:
        """Set callback for an existing hotkey"""
        try:
            with self.lock:
                if name in self.hotkeys:
                    self.hotkeys[name].callback = callback
                    return True
                return False
        except Exception as e:
            print(f"Failed to set callback for hotkey '{name}': {e}")
            return False

    def enable_hotkey(self, name: str) -> bool:
        """Enable a hotkey"""
        try:
            with self.lock:
                if name in self.hotkeys:
                    self.hotkeys[name].enabled = True
                    return True
                return False
        except Exception as e:
            print(f"Failed to enable hotkey '{name}': {e}")
            return False

    def disable_hotkey(self, name: str) -> bool:
        """Disable a hotkey"""
        try:
            with self.lock:
                if name in self.hotkeys:
                    self.hotkeys[name].enabled = False
                    return True
                return False
        except Exception as e:
            print(f"Failed to disable hotkey '{name}': {e}")
            return False

    def start_listening(self) -> bool:
        """Start listening for global hotkeys"""
        if not PYNPUT_AVAILABLE:
            print("Cannot start hotkey listening: pynput not available")
            return False

        if self.is_running:
            print("Hotkey listener already running")
            return True

        try:
            # Build hotkey mapping for GlobalHotKeys
            hotkey_mapping = {}

            with self.lock:
                for name, config in self.hotkeys.items():
                    if config.enabled and config.callback:
                        # Convert keys to pynput format
                        key_combination = self._keys_to_pynput_format(config.keys)
                        if key_combination:
                            hotkey_mapping[key_combination] = config.callback
                            print(f"Mapped hotkey: {key_combination} -> {name}")

            if not hotkey_mapping:
                print("No valid hotkeys to register")
                return False

            # Create GlobalHotKeys listener
            self.listener = GlobalHotKeys(hotkey_mapping)
            self.listener.start()
            self.is_running = True

            print("Global hotkey listener started")
            return True

        except Exception as e:
            print(f"Failed to start hotkey listener: {e}")
            return False

    def stop_listening(self):
        """Stop listening for global hotkeys"""
        if not self.is_running:
            return

        try:
            if self.listener:
                self.listener.stop()
                self.listener = None

            self.is_running = False
            self.pressed_keys.clear()

            print("Global hotkey listener stopped")

        except Exception as e:
            print(f"Failed to stop hotkey listener: {e}")

    def _normalize_keys(self, keys: List[str]) -> List[str]:
        """Normalize key names to standard format"""
        normalized = []

        key_mapping = {
            # Modifiers
            'ctrl': 'ctrl',
            'control': 'ctrl',
            'shift': 'shift',
            'alt': 'alt',
            'win': 'cmd',
            'cmd': 'cmd',
            'super': 'cmd',

            # Special keys
            'space': 'space',
            'enter': 'enter',
            'return': 'enter',
            'tab': 'tab',
            'escape': 'esc',
            'esc': 'esc',
            'backspace': 'backspace',
            'delete': 'delete',
            'del': 'delete',

            # Function keys
            'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4',
            'f5': 'f5', 'f6': 'f6', 'f7': 'f7', 'f8': 'f8',
            'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
        }

        for key in keys:
            key_lower = key.lower().strip()

            if key_lower in key_mapping:
                normalized.append(key_mapping[key_lower])
            elif len(key_lower) == 1 and key_lower.isalnum():
                # Single character key
                normalized.append(key_lower)
            else:
                print(f"Unknown key: {key}")
                return []

        return normalized

    def _keys_to_pynput_format(self, keys: List[str]) -> Optional[str]:
        """Convert our key format to pynput GlobalHotKeys format"""
        try:
            pynput_keys = []

            for key in keys:
                if key == 'ctrl':
                    pynput_keys.append('<ctrl>')
                elif key == 'shift':
                    pynput_keys.append('<shift>')
                elif key == 'alt':
                    pynput_keys.append('<alt>')
                elif key == 'cmd':
                    pynput_keys.append('<cmd>')
                elif key == 'space':
                    pynput_keys.append('<space>')
                elif key == 'enter':
                    pynput_keys.append('<enter>')
                elif key == 'tab':
                    pynput_keys.append('<tab>')
                elif key == 'esc':
                    pynput_keys.append('<esc>')
                elif key == 'backspace':
                    pynput_keys.append('<backspace>')
                elif key == 'delete':
                    pynput_keys.append('<delete>')
                elif len(key) == 1 and key.isalnum():
                    pynput_keys.append(key)
                else:
                    print(f"Unknown key for pynput format: {key}")
                    return None

            if pynput_keys:
                return '+'.join(pynput_keys)
            return None

        except Exception as e:
            print(f"Error converting keys to pynput format: {e}")
            return None

    def get_hotkey_info(self, name: str) -> Optional[Dict]:
        """Get information about a hotkey"""
        with self.lock:
            if name in self.hotkeys:
                config = self.hotkeys[name]
                return {
                    'name': config.name,
                    'keys': config.keys,
                    'description': config.description,
                    'enabled': config.enabled,
                    'has_callback': config.callback is not None
                }
        return None

    def get_all_hotkeys(self) -> Dict[str, Dict]:
        """Get information about all registered hotkeys"""
        result = {}
        with self.lock:
            for name, config in self.hotkeys.items():
                result[name] = {
                    'name': config.name,
                    'keys': config.keys,
                    'description': config.description,
                    'enabled': config.enabled,
                    'has_callback': config.callback is not None
                }
        return result

    def is_available(self) -> bool:
        """Check if global hotkeys are available on this system"""
        return PYNPUT_AVAILABLE

    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()


# Singleton instance
_hotkey_manager = None

def get_hotkey_manager() -> GlobalHotkeyManager:
    """Get singleton hotkey manager instance"""
    global _hotkey_manager
    if _hotkey_manager is None:
        _hotkey_manager = GlobalHotkeyManager()
    return _hotkey_manager
