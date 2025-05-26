#!/usr/bin/env python3
"""
Preferences Dialog for OpenSuperWhisper PyQt6 GUI
Provides settings for microphone, model, GPU, and other options
"""

import sys
from typing import Dict, Any, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget, QWidget,
    QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit,
    QPushButton, QLabel, QGroupBox, QSlider, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# Import existing services
from whisper.audio_recorder import AudioRecorder
from whisper.transcription_service import TranscriptionService
from whisper.config_manager import get_config_manager


class PreferencesDialog(QDialog):
    """Modern preferences dialog for OpenSuperWhisper"""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_manager = get_config_manager()
        self.current_settings = self.settings_manager.get_all_settings()

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Setup the preferences dialog UI"""
        self.setWindowTitle("Preferences - OpenSuperWhisper")
        self.setModal(True)
        self.resize(500, 600)

        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #555555;
            }
            QTabBar::tab:hover {
                background-color: #4a4a4a;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
                background-color: #404040;
                border: 1px solid #666666;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover {
                border-color: #888888;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                width: 0;
                height: 0;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #666666;
                border-radius: 3px;
                background-color: #404040;
            }
            QCheckBox::indicator:checked {
                background-color: #44ff44;
                border-color: #44ff44;
            }
            QPushButton {
                background-color: #555555;
                border: 1px solid #777777;
                border-radius: 4px;
                padding: 8px 16px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QPushButton:pressed {
                background-color: #444444;
            }
            QPushButton#primaryButton {
                background-color: #44ff44;
                color: #000000;
            }
            QPushButton#primaryButton:hover {
                background-color: #55ff55;
            }
            QSlider::groove:horizontal {
                border: 1px solid #666666;
                height: 6px;
                background: #404040;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #44ff44;
                border: 1px solid #44ff44;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #55ff55;
            }
        """)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.create_audio_tab()
        self.create_transcription_tab()
        self.create_interface_tab()
        self.create_hotkeys_tab()

        # Buttons
        self.create_buttons(layout)

    def create_audio_tab(self):
        """Create audio settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # Microphone settings
        mic_group = QGroupBox("Microphone Settings")
        mic_layout = QFormLayout(mic_group)

        # Microphone device selection
        self.mic_combo = QComboBox()
        self.refresh_microphones()
        mic_layout.addRow("Microphone Device:", self.mic_combo)

        # Sample rate
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["16000", "22050", "44100", "48000"])
        mic_layout.addRow("Sample Rate:", self.sample_rate_combo)

        # Audio monitoring
        self.monitor_audio_check = QCheckBox("Enable audio monitoring")
        mic_layout.addRow(self.monitor_audio_check)

        # Noise reduction
        self.noise_reduction_check = QCheckBox("Enable noise reduction")
        mic_layout.addRow(self.noise_reduction_check)

        layout.addWidget(mic_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "Audio")

    def create_transcription_tab(self):
        """Create transcription settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # Model settings
        model_group = QGroupBox("Model Settings")
        model_layout = QFormLayout(model_group)

        # Model selection
        self.model_combo = QComboBox()
        self.load_available_models()
        model_layout.addRow("Whisper Model:", self.model_combo)

        # Device selection
        self.device_combo = QComboBox()
        self.device_combo.addItems(["cpu", "cuda"])
        model_layout.addRow("Processing Device:", self.device_combo)

        # Language
        self.language_combo = QComboBox()
        self.language_combo.addItems(["auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"])
        model_layout.addRow("Language:", self.language_combo)

        # Task
        self.task_combo = QComboBox()
        self.task_combo.addItems(["transcribe", "translate"])
        model_layout.addRow("Task:", self.task_combo)

        layout.addWidget(model_group)

        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)

        # Temperature
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 1.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setDecimals(1)
        advanced_layout.addRow("Temperature:", self.temperature_spin)

        layout.addWidget(advanced_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "Transcription")

    def create_interface_tab(self):
        """Create interface settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)

        # Auto-start
        self.autostart_check = QCheckBox("Start with Windows")
        general_layout.addRow(self.autostart_check)

        # System tray
        self.system_tray_check = QCheckBox("Minimize to system tray")
        general_layout.addRow(self.system_tray_check)

        # Auto cleanup
        self.auto_cleanup_check = QCheckBox("Auto-cleanup old recordings")
        general_layout.addRow(self.auto_cleanup_check)

        layout.addWidget(general_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "Interface")

    def create_hotkeys_tab(self):
        """Create hotkeys settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # Hotkey settings
        hotkey_group = QGroupBox("Hotkey Settings")
        hotkey_layout = QFormLayout(hotkey_group)

        # Recording hotkey
        self.record_hotkey_edit = QLineEdit()
        hotkey_layout.addRow("Recording Hotkey:", self.record_hotkey_edit)

        # Window hotkey
        self.window_hotkey_edit = QLineEdit()
        hotkey_layout.addRow("Show Window Hotkey:", self.window_hotkey_edit)

        layout.addWidget(hotkey_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "Hotkeys")

    def create_buttons(self, layout):
        """Create dialog buttons"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Reset button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_button)

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.setObjectName("primaryButton")
        ok_button.clicked.connect(self.accept_settings)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)

    def refresh_microphones(self):
        """Refresh the list of available microphones"""
        try:
            audio_recorder = AudioRecorder()
            devices = audio_recorder.get_audio_devices()

            self.mic_combo.clear()
            self.mic_combo.addItem("Default", None)

            for device in devices:
                self.mic_combo.addItem(
                    f"{device['name']} ({device['channels']} ch)",
                    device['index']
                )

        except Exception as e:
            print(f"Failed to refresh microphones: {e}")
            self.mic_combo.clear()
            self.mic_combo.addItem("Default", None)

    def load_available_models(self):
        """Load available Whisper models dynamically"""
        try:
            from whisper import available_models
            models = available_models()

            # Filter and sort models for better UX
            # Prioritize the most commonly used models
            priority_models = ['tiny', 'base', 'small', 'medium', 'large-v3', 'large-v3-turbo', 'turbo']

            # Add priority models first (if they exist)
            model_list = []
            for model in priority_models:
                if model in models:
                    model_list.append(model)

            # Add any remaining models
            for model in sorted(models):
                if model not in model_list:
                    model_list.append(model)

            self.model_combo.clear()
            self.model_combo.addItems(model_list)

            print(f"Loaded {len(model_list)} Whisper models: {', '.join(model_list)}")

        except Exception as e:
            print(f"Failed to load available models: {e}")
            # Fallback to basic models
            self.model_combo.clear()
            self.model_combo.addItems(["tiny", "base", "small", "medium", "large-v3", "turbo"])

    def load_settings(self):
        """Load current settings into the dialog"""
        try:
            # Audio settings
            device_name = self.current_settings.get('audio_device_name', '')
            for i in range(self.mic_combo.count()):
                if device_name in self.mic_combo.itemText(i):
                    self.mic_combo.setCurrentIndex(i)
                    break

            sample_rate = str(self.current_settings.get('sample_rate', 16000))
            index = self.sample_rate_combo.findText(sample_rate)
            if index >= 0:
                self.sample_rate_combo.setCurrentIndex(index)

            self.monitor_audio_check.setChecked(self.current_settings.get('monitor_audio', False))
            self.noise_reduction_check.setChecked(self.current_settings.get('noise_reduction', False))

            # Transcription settings
            model = self.current_settings.get('model', 'base')
            index = self.model_combo.findText(model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)

            device = self.current_settings.get('device', 'cpu')
            index = self.device_combo.findText(device)
            if index >= 0:
                self.device_combo.setCurrentIndex(index)

            language = self.current_settings.get('language', 'auto')
            index = self.language_combo.findText(language)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)

            task = self.current_settings.get('task', 'transcribe')
            index = self.task_combo.findText(task)
            if index >= 0:
                self.task_combo.setCurrentIndex(index)

            self.temperature_spin.setValue(self.current_settings.get('temperature', 0.0))

            # Interface settings
            self.autostart_check.setChecked(self.current_settings.get('autostart', False))
            self.system_tray_check.setChecked(self.current_settings.get('system_tray', True))
            self.auto_cleanup_check.setChecked(self.current_settings.get('auto_cleanup', True))

            # Hotkey settings
            self.record_hotkey_edit.setText(self.current_settings.get('record_hotkey', 'Ctrl+Shift+R'))
            self.window_hotkey_edit.setText(self.current_settings.get('window_hotkey', 'Ctrl+Shift+W'))

        except Exception as e:
            print(f"Failed to load settings: {e}")

    def get_settings(self) -> Dict[str, Any]:
        """Get settings from the dialog"""
        settings = {}

        try:
            # Audio settings
            mic_data = self.mic_combo.currentData()
            if mic_data is not None:
                settings['audio_device'] = mic_data
                settings['audio_device_name'] = self.mic_combo.currentText()
            else:
                settings['audio_device'] = None
                settings['audio_device_name'] = None

            settings['sample_rate'] = int(self.sample_rate_combo.currentText())
            settings['monitor_audio'] = self.monitor_audio_check.isChecked()
            settings['noise_reduction'] = self.noise_reduction_check.isChecked()

            # Transcription settings
            settings['model'] = self.model_combo.currentText()
            settings['device'] = self.device_combo.currentText()
            settings['language'] = self.language_combo.currentText()
            settings['task'] = self.task_combo.currentText()
            settings['temperature'] = self.temperature_spin.value()

            # Interface settings
            settings['autostart'] = self.autostart_check.isChecked()
            settings['system_tray'] = self.system_tray_check.isChecked()
            settings['auto_cleanup'] = self.auto_cleanup_check.isChecked()

            # Hotkey settings
            settings['record_hotkey'] = self.record_hotkey_edit.text()
            settings['window_hotkey'] = self.window_hotkey_edit.text()

        except Exception as e:
            print(f"Failed to get settings: {e}")

        return settings

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.reset_to_defaults()
            self.current_settings = self.settings_manager.get_all_settings()
            self.load_settings()

    def accept_settings(self):
        """Accept and save settings"""
        try:
            new_settings = self.get_settings()
            
            # Handle autostart setting
            if sys.platform == "win32":
                try:
                    from whisper.windows_utils import set_autostart, is_autostart_enabled
                    current_autostart = is_autostart_enabled()
                    new_autostart = new_settings.get('autostart', False)
                    
                    if current_autostart != new_autostart:
                        if set_autostart(new_autostart):
                            print(f"Autostart {'enabled' if new_autostart else 'disabled'}")
                        else:
                            QMessageBox.warning(self, "Autostart", 
                                              f"Failed to {'enable' if new_autostart else 'disable'} autostart")
                except Exception as e:
                    print(f"Failed to handle autostart setting: {e}")

            # Save settings
            if self.settings_manager.save_settings(new_settings):
                self.settings_changed.emit(new_settings)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to save settings.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")


def main():
    """Test the preferences dialog"""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = PreferencesDialog()
    dialog.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
