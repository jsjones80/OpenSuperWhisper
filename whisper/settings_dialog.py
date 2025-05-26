"""
Settings Dialog for OpenSuperWhisper Windows
Allows configuration of microphone, models, and other settings
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, List
import threading

from .audio_recorder import AudioRecorder
from .transcription_service import get_transcription_service


class SettingsDialog:
    """Settings configuration dialog"""

    def __init__(self, parent, current_settings: Dict[str, Any] = None):
        self.parent = parent
        self.result = None
        self.current_settings = current_settings or {}

        # Services
        self.audio_recorder = AudioRecorder()
        self.transcription_service = get_transcription_service()

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("OpenSuperWhisper Settings")
        self.dialog.geometry("500x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self._center_dialog()

        # Create UI
        self._create_ui()

        # Load current settings
        self._load_current_settings()

        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _center_dialog(self):
        """Center the dialog on the parent window"""
        self.dialog.update_idletasks()

        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Calculate center position
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()

        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f"+{x}+{y}")

    def _create_ui(self):
        """Create the settings UI"""
        # Main container with padding
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        main_frame.rowconfigure(0, weight=1)

        # Create tabs
        self._create_audio_tab()
        self._create_transcription_tab()
        self._create_general_tab()

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        buttons_frame.columnconfigure(0, weight=1)

        # Buttons
        button_container = ttk.Frame(buttons_frame)
        button_container.grid(row=0, column=0)

        ttk.Button(
            button_container,
            text="OK",
            command=self._on_ok,
            width=10
        ).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(
            button_container,
            text="Cancel",
            command=self._on_cancel,
            width=10
        ).grid(row=0, column=1, padx=(10, 0))

        ttk.Button(
            button_container,
            text="Apply",
            command=self._on_apply,
            width=10
        ).grid(row=0, column=2, padx=(10, 0))

    def _create_audio_tab(self):
        """Create audio settings tab"""
        audio_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(audio_frame, text="Audio")

        # Microphone selection
        mic_label = ttk.Label(audio_frame, text="Microphone Device:")
        mic_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.mic_var = tk.StringVar()
        self.mic_combo = ttk.Combobox(
            audio_frame,
            textvariable=self.mic_var,
            state="readonly",
            width=50
        )
        self.mic_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        audio_frame.columnconfigure(0, weight=1)

        # Refresh devices button
        refresh_btn = ttk.Button(
            audio_frame,
            text="Refresh Devices",
            command=self._refresh_audio_devices
        )
        refresh_btn.grid(row=2, column=0, sticky=tk.W, pady=(0, 20))

        # Audio quality settings
        quality_label = ttk.Label(audio_frame, text="Audio Quality:")
        quality_label.grid(row=3, column=0, sticky=tk.W, pady=(0, 5))

        quality_frame = ttk.Frame(audio_frame)
        quality_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(quality_frame, text="Sample Rate:").grid(row=0, column=0, sticky=tk.W)
        self.sample_rate_var = tk.StringVar(value="16000")
        sample_rate_combo = ttk.Combobox(
            quality_frame,
            textvariable=self.sample_rate_var,
            values=["8000", "16000", "22050", "44100", "48000"],
            state="readonly",
            width=10
        )
        sample_rate_combo.grid(row=0, column=1, padx=(10, 0))

        ttk.Label(quality_frame, text="Hz").grid(row=0, column=2, padx=(5, 0))

        # Audio monitoring
        self.monitor_var = tk.BooleanVar(value=False)
        monitor_check = ttk.Checkbutton(
            audio_frame,
            text="Enable audio level monitoring",
            variable=self.monitor_var
        )
        monitor_check.grid(row=5, column=0, sticky=tk.W, pady=(0, 10))

        # Noise reduction
        self.noise_reduction_var = tk.BooleanVar(value=True)
        noise_check = ttk.Checkbutton(
            audio_frame,
            text="Enable noise reduction",
            variable=self.noise_reduction_var
        )
        noise_check.grid(row=6, column=0, sticky=tk.W)

        # Load audio devices
        self._refresh_audio_devices()

    def _create_transcription_tab(self):
        """Create transcription settings tab"""
        trans_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(trans_frame, text="Transcription")

        # Model selection
        model_label = ttk.Label(trans_frame, text="Whisper Model:")
        model_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            trans_frame,
            textvariable=self.model_var,
            state="readonly",
            width=30
        )
        self.model_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        trans_frame.columnconfigure(0, weight=1)

        # Model info
        self.model_info_label = ttk.Label(
            trans_frame,
            text="Select a model to see details",
            foreground="gray"
        )
        self.model_info_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 10))

        # Device selection (CPU/GPU)
        device_label = ttk.Label(trans_frame, text="Processing Device:")
        device_label.grid(row=3, column=0, sticky=tk.W, pady=(0, 5))

        self.device_var = tk.StringVar(value="cpu")
        device_frame = ttk.Frame(trans_frame)
        device_frame.grid(row=4, column=0, sticky=tk.W, pady=(0, 10))

        ttk.Radiobutton(
            device_frame,
            text="CPU (Compatible)",
            variable=self.device_var,
            value="cpu"
        ).grid(row=0, column=0, padx=(0, 20))

        ttk.Radiobutton(
            device_frame,
            text="GPU - CUDA (NVIDIA)",
            variable=self.device_var,
            value="cuda"
        ).grid(row=0, column=1, padx=(0, 20))

        ttk.Radiobutton(
            device_frame,
            text="GPU - DirectML (AMD/Intel)",
            variable=self.device_var,
            value="directml"
        ).grid(row=0, column=2)

        # Device info
        self.device_info_label = ttk.Label(
            trans_frame,
            text="CPU is recommended for compatibility",
            foreground="gray"
        )
        self.device_info_label.grid(row=5, column=0, sticky=tk.W, pady=(0, 20))

        # Bind device selection change
        self.device_var.trace('w', self._on_device_changed)

        # Language settings
        lang_label = ttk.Label(trans_frame, text="Language:")
        lang_label.grid(row=6, column=0, sticky=tk.W, pady=(0, 5))

        self.language_var = tk.StringVar(value="auto")
        lang_combo = ttk.Combobox(
            trans_frame,
            textvariable=self.language_var,
            values=["auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
            width=30
        )
        lang_combo.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Task selection
        task_label = ttk.Label(trans_frame, text="Task:")
        task_label.grid(row=8, column=0, sticky=tk.W, pady=(0, 5))

        self.task_var = tk.StringVar(value="transcribe")
        task_frame = ttk.Frame(trans_frame)
        task_frame.grid(row=9, column=0, sticky=tk.W, pady=(0, 20))

        ttk.Radiobutton(
            task_frame,
            text="Transcribe",
            variable=self.task_var,
            value="transcribe"
        ).grid(row=0, column=0, padx=(0, 20))

        ttk.Radiobutton(
            task_frame,
            text="Translate to English",
            variable=self.task_var,
            value="translate"
        ).grid(row=0, column=1)

        # Advanced settings
        advanced_label = ttk.Label(trans_frame, text="Advanced Settings:")
        advanced_label.grid(row=10, column=0, sticky=tk.W, pady=(0, 5))

        advanced_frame = ttk.Frame(trans_frame)
        advanced_frame.grid(row=11, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(advanced_frame, text="Temperature:").grid(row=0, column=0, sticky=tk.W)
        self.temperature_var = tk.DoubleVar(value=0.0)
        temp_scale = ttk.Scale(
            advanced_frame,
            from_=0.0,
            to=1.0,
            variable=self.temperature_var,
            orient=tk.HORIZONTAL,
            length=200
        )
        temp_scale.grid(row=0, column=1, padx=(10, 10))
        self.temp_value_label = ttk.Label(advanced_frame, text="0.0")
        self.temp_value_label.grid(row=0, column=2)

        # Update temperature label
        def update_temp_label(*args):
            self.temp_value_label.config(text=f"{self.temperature_var.get():.1f}")
        self.temperature_var.trace('w', update_temp_label)

        # Load available models
        self._load_available_models()

        # Bind model selection change
        self.model_combo.bind('<<ComboboxSelected>>', self._on_model_changed)

    def _create_general_tab(self):
        """Create general settings tab"""
        general_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(general_frame, text="General")

        # Hotkeys section
        hotkey_label = ttk.Label(general_frame, text="Global Hotkeys:")
        hotkey_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        hotkey_frame = ttk.Frame(general_frame)
        hotkey_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        general_frame.columnconfigure(0, weight=1)

        ttk.Label(hotkey_frame, text="Toggle Recording:").grid(row=0, column=0, sticky=tk.W)
        self.record_hotkey_var = tk.StringVar(value="Ctrl+Shift+R")
        ttk.Entry(hotkey_frame, textvariable=self.record_hotkey_var, width=20).grid(row=0, column=1, padx=(10, 0))

        ttk.Label(hotkey_frame, text="Show/Hide Window:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.window_hotkey_var = tk.StringVar(value="Ctrl+Shift+W")
        ttk.Entry(hotkey_frame, textvariable=self.window_hotkey_var, width=20).grid(row=1, column=1, padx=(10, 0), pady=(10, 0))

        # Auto-start
        self.autostart_var = tk.BooleanVar(value=False)
        autostart_check = ttk.Checkbutton(
            general_frame,
            text="Start with Windows",
            variable=self.autostart_var
        )
        autostart_check.grid(row=2, column=0, sticky=tk.W, pady=(0, 10))

        # System tray
        self.system_tray_var = tk.BooleanVar(value=True)
        tray_check = ttk.Checkbutton(
            general_frame,
            text="Minimize to system tray",
            variable=self.system_tray_var
        )
        tray_check.grid(row=3, column=0, sticky=tk.W, pady=(0, 10))

        # Theme selection
        theme_label = ttk.Label(general_frame, text="Theme:")
        theme_label.grid(row=4, column=0, sticky=tk.W, pady=(0, 5))

        self.theme_var = tk.StringVar(value="default")
        theme_combo = ttk.Combobox(
            general_frame,
            textvariable=self.theme_var,
            values=["default", "dark", "light"],
            state="readonly",
            width=20
        )
        theme_combo.grid(row=5, column=0, sticky=tk.W, pady=(0, 20))

        # Storage settings
        storage_label = ttk.Label(general_frame, text="Storage:")
        storage_label.grid(row=6, column=0, sticky=tk.W, pady=(0, 10))

        self.auto_cleanup_var = tk.BooleanVar(value=True)
        cleanup_check = ttk.Checkbutton(
            general_frame,
            text="Auto-cleanup recordings older than 30 days",
            variable=self.auto_cleanup_var
        )
        cleanup_check.grid(row=7, column=0, sticky=tk.W)

    def _refresh_audio_devices(self):
        """Refresh the list of audio devices"""
        try:
            devices = self.audio_recorder.get_audio_devices()
            device_names = []
            self.device_map = {}
            self.tested_devices = {}  # Track which devices actually work

            # Add default option
            device_names.append("Default System Device")
            self.device_map["Default System Device"] = None

            # Group devices by name to find working ones
            device_groups = {}
            for device in devices:
                base_name = device['name']
                if base_name not in device_groups:
                    device_groups[base_name] = []
                device_groups[base_name].append(device)

            # For each device group, test and find working index
            for base_name, device_list in device_groups.items():
                if len(device_list) == 1:
                    # Single device, add normally
                    device = device_list[0]
                    name = f"{device['name']} ({device['channels']} ch)"
                    device_names.append(name)
                    self.device_map[name] = device['index']
                    print(f"Device: {name} -> Index: {device['index']}")
                else:
                    # Multiple devices with same name, test to find working one
                    working_device = self._find_working_device(device_list)
                    if working_device:
                        name = f"{working_device['name']} ({working_device['channels']} ch) [Tested]"
                        device_names.append(name)
                        self.device_map[name] = working_device['index']
                        print(f"Working Device: {name} -> Index: {working_device['index']}")
                    else:
                        # Add all variants if none work
                        for i, device in enumerate(device_list):
                            name = f"{device['name']} ({device['channels']} ch) [#{i+1}]"
                            device_names.append(name)
                            self.device_map[name] = device['index']
                            print(f"Untested Device: {name} -> Index: {device['index']}")

            self.mic_combo['values'] = device_names

            if device_names:
                self.mic_combo.set(device_names[0])  # Select default by default
            else:
                self.mic_combo.set("No audio devices found")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load audio devices: {e}")
            print(f"Device refresh error: {e}")
            import traceback
            traceback.print_exc()

    def _find_working_device(self, device_list):
        """Test devices to find one that actually works"""
        print(f"Testing {len(device_list)} devices with same name...")

        for device in device_list:
            try:
                print(f"Testing device index {device['index']}...")

                # Quick test - try to open the device
                if hasattr(self.audio_recorder, '_audio_interface') and self.audio_recorder._audio_interface:
                    try:
                        # Test with PyAudio
                        test_stream = self.audio_recorder._audio_interface.open(
                            format=self.audio_recorder.FORMAT,
                            channels=device['channels'],
                            rate=int(device['sample_rate']),
                            input=True,
                            input_device_index=device['index'],
                            frames_per_buffer=1024
                        )
                        test_stream.close()
                        print(f"✅ Device {device['index']} works!")
                        return device
                    except Exception as e:
                        print(f"❌ Device {device['index']} failed: {e}")
                        continue

            except Exception as e:
                print(f"Error testing device {device['index']}: {e}")
                continue

        print("No working device found in group")
        return None

    def _load_available_models(self):
        """Load available Whisper models"""
        try:
            models = self.transcription_service.get_available_models()
            self.model_combo['values'] = models

            if models:
                # Set current model or default to 'base'
                current_model = self.transcription_service.model_name
                if current_model in models:
                    self.model_combo.set(current_model)
                else:
                    self.model_combo.set('base')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load models: {e}")

    def _on_model_changed(self, event=None):
        """Handle model selection change"""
        model = self.model_var.get()

        # Model size information
        model_info = {
            'tiny': 'Tiny (39 MB) - Fastest, least accurate',
            'base': 'Base (74 MB) - Good balance of speed and accuracy',
            'small': 'Small (244 MB) - Better accuracy, slower',
            'medium': 'Medium (769 MB) - High accuracy, much slower',
            'large': 'Large (1550 MB) - Highest accuracy, very slow',
            'turbo': 'Turbo (809 MB) - Fast and accurate (if available)'
        }

        info = model_info.get(model, 'Unknown model')
        self.model_info_label.config(text=info)

    def _on_device_changed(self, *args):
        """Handle device selection change"""
        device = self.device_var.get()

        # Device information
        device_info = {
            'cpu': 'CPU processing - Compatible with all systems, slower',
            'cuda': 'NVIDIA GPU - Much faster, requires CUDA-compatible GPU',
            'directml': 'AMD/Intel GPU - Faster than CPU, broader GPU support'
        }

        info = device_info.get(device, 'Unknown device')
        self.device_info_label.config(text=info)

        # Check GPU availability
        if device == 'cuda':
            try:
                import torch
                if not torch.cuda.is_available():
                    self.device_info_label.config(
                        text="⚠️ CUDA not available - Install NVIDIA drivers and CUDA toolkit",
                        foreground="orange"
                    )
                else:
                    gpu_name = torch.cuda.get_device_name(0)
                    self.device_info_label.config(
                        text=f"✅ CUDA available - {gpu_name}",
                        foreground="green"
                    )
            except ImportError:
                self.device_info_label.config(
                    text="⚠️ PyTorch not available for CUDA detection",
                    foreground="orange"
                )
        elif device == 'directml':
            self.device_info_label.config(
                text="DirectML - Should work with most modern GPUs",
                foreground="blue"
            )
        else:
            self.device_info_label.config(
                text=info,
                foreground="gray"
            )

    def _load_current_settings(self):
        """Load current settings into the dialog"""
        if not self.current_settings:
            return

        try:
            # Audio settings
            if 'audio_device_name' in self.current_settings:
                device_name = self.current_settings['audio_device_name']
                if device_name and device_name in self.device_map:
                    self.mic_var.set(device_name)
                elif 'audio_device' in self.current_settings and self.current_settings['audio_device'] is None:
                    self.mic_var.set("Default System Device")

            if 'sample_rate' in self.current_settings:
                self.sample_rate_var.set(str(self.current_settings['sample_rate']))

            if 'monitor_audio' in self.current_settings:
                self.monitor_var.set(self.current_settings['monitor_audio'])

            if 'noise_reduction' in self.current_settings:
                self.noise_reduction_var.set(self.current_settings['noise_reduction'])

            # Transcription settings
            if 'model' in self.current_settings:
                model = self.current_settings['model']
                if model in self.model_combo['values']:
                    self.model_var.set(model)

            if 'device' in self.current_settings:
                self.device_var.set(self.current_settings['device'])

            if 'language' in self.current_settings:
                self.language_var.set(self.current_settings['language'])

            if 'task' in self.current_settings:
                self.task_var.set(self.current_settings['task'])

            if 'temperature' in self.current_settings:
                self.temperature_var.set(self.current_settings['temperature'])

            # General settings
            if 'record_hotkey' in self.current_settings:
                self.record_hotkey_var.set(self.current_settings['record_hotkey'])

            if 'window_hotkey' in self.current_settings:
                self.window_hotkey_var.set(self.current_settings['window_hotkey'])

            if 'autostart' in self.current_settings:
                self.autostart_var.set(self.current_settings['autostart'])

            if 'system_tray' in self.current_settings:
                self.system_tray_var.set(self.current_settings['system_tray'])

            if 'theme' in self.current_settings:
                self.theme_var.set(self.current_settings['theme'])

            if 'auto_cleanup' in self.current_settings:
                self.auto_cleanup_var.set(self.current_settings['auto_cleanup'])

            print("Current settings loaded into dialog")

        except Exception as e:
            print(f"Error loading current settings: {e}")
            # Continue with defaults if loading fails

    def _on_ok(self):
        """Handle OK button click"""
        if self._apply_settings():
            self.result = self._get_settings()
            self.dialog.destroy()

    def _on_cancel(self):
        """Handle Cancel button click"""
        self.result = None
        self.dialog.destroy()

    def _on_apply(self):
        """Handle Apply button click"""
        self._apply_settings()

    def _apply_settings(self) -> bool:
        """Apply the current settings"""
        try:
            settings = self._get_settings()

            # Apply model change
            if settings['model'] != self.transcription_service.model_name:
                self.transcription_service.change_model(settings['model'])

            # Apply other settings would go here

            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings: {e}")
            return False

    def _get_settings(self) -> Dict[str, Any]:
        """Get current settings from the dialog"""
        selected_device = self.mic_var.get()
        device_index = self.device_map.get(selected_device, None)

        return {
            'audio_device': device_index,
            'audio_device_name': selected_device,
            'sample_rate': int(self.sample_rate_var.get()),
            'monitor_audio': self.monitor_var.get(),
            'noise_reduction': self.noise_reduction_var.get(),
            'model': self.model_var.get(),
            'device': self.device_var.get(),  # CPU/GPU selection
            'language': self.language_var.get(),
            'task': self.task_var.get(),
            'temperature': self.temperature_var.get(),
            'record_hotkey': self.record_hotkey_var.get(),
            'window_hotkey': self.window_hotkey_var.get(),
            'autostart': self.autostart_var.get(),
            'system_tray': self.system_tray_var.get(),
            'theme': self.theme_var.get(),
            'auto_cleanup': self.auto_cleanup_var.get()
        }

    def show(self) -> Optional[Dict[str, Any]]:
        """Show the dialog and return the result"""
        self.dialog.wait_window()
        return self.result


def show_settings_dialog(parent, current_settings: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Show the settings dialog and return the selected settings"""
    dialog = SettingsDialog(parent, current_settings)
    return dialog.show()
