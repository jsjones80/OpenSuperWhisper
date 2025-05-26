#!/usr/bin/env python3
"""
OpenSuperWhisper GUI - PyQt6 Version
Modern, dark-themed interface matching the original OpenSuperWhisper design
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import threading

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QScrollArea, QFrame, QPushButton, QLabel, QMessageBox,
    QFileDialog, QMenuBar, QMenu, QSizePolicy, QDialog, QSystemTrayIcon
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject, QRect
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QAction, QCursor, QPainter, QBrush, QPen

# Import existing services
from whisper.audio_recorder import AudioRecorder
from whisper.transcription_service import TranscriptionService
from whisper.database import RecordingDatabase, Recording, get_database
from whisper.config_manager import ConfigManager, get_config_manager
from whisper.hotkeys import GlobalHotkeyManager, get_hotkey_manager

# Import clipboard functionality
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    try:
        import win32clipboard
        CLIPBOARD_AVAILABLE = True
    except ImportError:
        CLIPBOARD_AVAILABLE = False


class RecordButton(QPushButton):
    """Custom record button with red dot or white square"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_recording = False
        self.setText("")  # No text

    def set_recording(self, recording):
        self.is_recording = recording
        self.update()

    def paintEvent(self, event):
        """Custom paint event to draw the button"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw the button background (handled by stylesheet)
            super().paintEvent(event)

            # Draw the icon
            center = self.rect().center()

            if self.is_recording:
                # Draw white square for stop
                painter.setBrush(QBrush(QColor("#ffffff")))
                painter.setPen(QPen(Qt.PenStyle.NoPen))
                square_size = 16
                square_rect = QRect(
                    center.x() - square_size // 2,
                    center.y() - square_size // 2,
                    square_size,
                    square_size
                )
                painter.drawRect(square_rect)
            else:
                # Draw red circle for record
                painter.setBrush(QBrush(QColor("#ef4444")))
                painter.setPen(QPen(Qt.PenStyle.NoPen))
                radius = 8
                painter.drawEllipse(center, radius, radius)

            painter.end()
        except Exception as e:
            print(f"Error in RecordButton paintEvent: {e}")
            super().paintEvent(event)


class TranscriptionWorker(QObject):
    """Worker thread for transcription to avoid blocking UI"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, transcription_service, audio_path, settings):
        super().__init__()
        self.transcription_service = transcription_service
        self.audio_path = audio_path
        self.settings = settings

    def run(self):
        try:
            # Use the direct synchronous method to avoid asyncio blocking
            text = self._transcribe_directly()
            self.finished.emit(text)
        except Exception as e:
            self.error.emit(str(e))

    def _transcribe_directly(self):
        """Direct transcription without asyncio to avoid blocking"""
        # Double-check model state before transcription
        if self.transcription_service.model is None:
            raise RuntimeError("Transcription model not loaded")

        if getattr(self.transcription_service, 'is_loading', False):
            raise RuntimeError("Model is currently loading, please wait")

        if getattr(self.transcription_service, 'is_transcribing', False):
            raise RuntimeError("Another transcription is already in progress")

        # Default settings
        default_settings = {
            'language': None,  # Auto-detect
            'task': 'transcribe',  # or 'translate'
            'temperature': 0.0,
            'best_of': 5,
            'beam_size': 5,
            'patience': 1.0,
            'length_penalty': 1.0,
            'suppress_tokens': "-1",
            'initial_prompt': None,
            'condition_on_previous_text': True,
            'fp16': True,
            'compression_ratio_threshold': 2.4,
            'logprob_threshold': -1.0,
            'no_speech_threshold': 0.6,
            'word_timestamps': False,
            'prepend_punctuations': "\"'([{-",
            'append_punctuations': "\"'.,:)]}",
            'clip_timestamps': "0"
        }

        if self.settings:
            default_settings.update(self.settings)

        # Ensure audio_path is a string, not a Path object
        audio_path_str = str(self.audio_path)

        try:
            # Call the internal sync method directly
            result = self.transcription_service._transcribe_sync(
                audio_path_str, default_settings
            )
            return result['text']
        except Exception as e:
            # Log the error for debugging
            print(f"Transcription error: {e}")
            raise


class TranscriptionItem(QFrame):
    """Custom widget for displaying transcription items with sleek design"""

    def __init__(self, recording_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.recording_data = recording_data
        self.setup_ui()

    def setup_ui(self):
        """Setup the transcription item UI with modern card design"""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            TranscriptionItem {
                background-color: #1a1a1a;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 14px;
                margin: 4px 8px;
            }
            TranscriptionItem:hover {
                background-color: #1f1f1f;
                border-color: rgba(255, 255, 255, 0.15);
            }
        """)

        # Set dynamic height with better spacing
        self.setMinimumHeight(90)
        self.setMaximumHeight(140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        # Create header with timestamp and actions
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Timestamp with premium styling
        timestamp_label = QLabel(self.recording_data.get('timestamp', 'Unknown'))
        timestamp_label.setStyleSheet("""
            color: #666666;
            font-size: 12px;
            font-weight: 500;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
            letter-spacing: 0.3px;
        """)
        header_layout.addWidget(timestamp_label)

        # Add copy button (subtle)
        copy_btn = QPushButton("Copy")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: none;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
            }
        """)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self.copy_transcription)
        header_layout.addWidget(copy_btn)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Transcription text with beautiful typography
        transcription = self.recording_data.get('transcription', 'No transcription')
        self.text_label = QLabel(transcription)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("""
            color: #e0e0e0;
            font-size: 15px;
            font-weight: 400;
            line-height: 1.5;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
            padding-top: 4px;
        """)

        # Limit text length for clean appearance
        if len(transcription) > 150:
            display_text = transcription[:150] + "..."
            self.text_label.setText(display_text)
            self.text_label.setToolTip(transcription)  # Show full text on hover

        layout.addWidget(self.text_label)
        layout.addStretch()  # Push content to top

    def copy_transcription(self):
        """Copy the full transcription text to clipboard"""
        try:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            full_text = self.recording_data.get('transcription', '')
            clipboard.setText(full_text)
            # Visual feedback
            sender = self.sender()
            if sender:
                sender.setText("Copied!")
                QTimer.singleShot(1500, lambda: sender.setText("Copy"))
        except Exception as e:
            print(f"Failed to copy: {e}")


class OpenSuperWhisperGUI(QMainWindow):
    """Main GUI class for OpenSuperWhisper using PyQt6"""

    def __init__(self):
        super().__init__()

        try:
            print("Initializing OpenSuperWhisperGUI...")

            # Initialize services
            self.settings_manager = get_config_manager()
            self.settings = self.settings_manager.get_all_settings()
            self.database = get_database()
            self.audio_recorder = AudioRecorder()
            self.transcription_service = TranscriptionService()
            self.hotkey_manager = get_hotkey_manager()

            # State variables
            self.is_recording = False
            self.recordings = []
            self.transcription_items = []
            self.needs_ui_refresh = False  # Flag to indicate UI needs refresh
            self.is_model_loading = False  # Flag to indicate model is loading
            self.model_ready = False  # Flag to indicate model is ready for transcription

            # Batch transcription variables
            self.transcription_queue = []
            self.current_transcription_index = 0

            # Thread management
            self.transcription_thread = None
            self.transcription_worker = None
            self.is_transcribing = False

            print("Services initialized, setting up UI...")

            # Setup UI
            self.setup_ui()
            self.setup_system_tray()
            self.setup_services()
            self.load_recordings()

            # Setup hotkeys
            self.setup_hotkeys()

            # Connect transcription service callbacks for better progress feedback
            self.setup_transcription_callbacks()

            print("GUI initialization complete")

        except Exception as e:
            print(f"Error in GUI initialization: {e}")
            import traceback
            traceback.print_exc()

    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("OpenSuperWhisper")
        self.setGeometry(100, 100, 500, 700)
        self.setMinimumSize(420, 500)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Set dark theme
        self.set_dark_theme()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 10, 16, 16)
        main_layout.setSpacing(12)

        # Create menu bar
        self.create_menu_bar()

        # Search section
        self.create_search_section(main_layout)

        # Transcriptions list
        self.create_transcriptions_list(main_layout)

        # Recording controls
        self.create_recording_controls(main_layout)

    def set_dark_theme(self):
        """Apply sleek modern theme matching original OpenSuperWhisper"""
        self.setStyleSheet("""
            /* Main window - premium dark background */
            QMainWindow {
                background-color: #0d0d0d;
                color: #ffffff;
            }

            /* Central widget */
            QWidget {
                background-color: #0d0d0d;
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'SF Pro Display', Roboto, sans-serif;
            }

            /* Menu bar - ultra minimal */
            QMenuBar {
                background-color: #0d0d0d;
                color: #e0e0e0;
                border: none;
                padding: 5px 10px;
                font-size: 13px;
                font-weight: 400;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 14px;
                border-radius: 6px;
                margin: 0px 3px;
            }
            QMenuBar::item:selected {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QMenuBar::item:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }

            /* Dropdown menus */
            QMenu {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
                color: #e0e0e0;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #333333;
                margin: 6px 10px;
            }

            /* Search bar - premium design */
            QLineEdit {
                background-color: #1a1a1a;
                border: 2px solid transparent;
                border-radius: 12px;
                padding: 12px 20px;
                font-size: 15px;
                color: #ffffff;
                font-weight: 400;
                selection-background-color: #0078d4;
            }
            QLineEdit:hover {
                background-color: #1f1f1f;
                border-color: rgba(255, 255, 255, 0.05);
            }
            QLineEdit:focus {
                border-color: #0078d4;
                background-color: #1f1f1f;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #666666;
            }

            /* Recording button - circular with red dot */
            QPushButton#recordButton {
                background-color: #2a2a2a;
                border: 2px solid #404040;
                border-radius: 25px;
                min-width: 50px;
                min-height: 50px;
                max-width: 50px;
                max-height: 50px;
            }
            QPushButton#recordButton:hover {
                background-color: #333333;
                border-color: #505050;
            }
            QPushButton#recordButton:pressed {
                background-color: #252525;
            }

            /* Stop button - circular with white square */
            QPushButton#stopButton {
                background-color: #2a2a2a;
                border: 2px solid #404040;
                border-radius: 25px;
                min-width: 50px;
                min-height: 50px;
                max-width: 50px;
                max-height: 50px;
            }
            QPushButton#stopButton:hover {
                background-color: #333333;
                border-color: #505050;
            }
            QPushButton#stopButton:pressed {
                background-color: #252525;
            }

            /* Clear button - subtle text button */
            QPushButton#clearButton {
                background-color: transparent;
                border: none;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 400;
                color: #666666;
                min-height: 24px;
            }
            QPushButton#clearButton:hover {
                color: #999999;
            }
            QPushButton#clearButton:pressed {
                color: #cccccc;
            }

            /* Scroll area - seamless integration */
            QScrollArea {
                border: none;
                background-color: transparent;
                border-radius: 12px;
            }

            /* Scrollbar - ultra thin and modern */
            QScrollBar:vertical {
                background-color: transparent;
                width: 6px;
                border-radius: 3px;
                margin: 4px 2px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 3px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QScrollBar::handle:vertical:pressed {
                background-color: rgba(255, 255, 255, 0.4);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }

            /* Status label - sophisticated typography */
            QLabel#statusLabel {
                color: #a0a0a0;
                font-size: 14px;
                font-weight: 500;
                letter-spacing: 0.3px;
            }

            /* Tooltip styling */
            QToolTip {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
        """)

    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        transcribe_action = QAction('Transcribe File...', self)
        transcribe_action.triggered.connect(self.transcribe_file)
        file_menu.addAction(transcribe_action)

        file_menu.addSeparator()

        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu('Edit')

        clear_all_action = QAction('Clear All Transcriptions', self)
        clear_all_action.triggered.connect(self.clear_all_transcriptions)
        edit_menu.addAction(clear_all_action)

        # Settings menu
        settings_menu = menubar.addMenu('Settings')

        preferences_action = QAction('Preferences...', self)
        preferences_action.triggered.connect(self.show_preferences)
        settings_menu.addAction(preferences_action)

        # Help menu
        help_menu = menubar.addMenu('Help')

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_search_section(self, layout):
        """Create the search section"""
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in transcriptions")
        self.search_input.textChanged.connect(self.filter_transcriptions)
        layout.addWidget(self.search_input)

    def create_transcriptions_list(self, layout):
        """Create the transcriptions list area with modern styling"""
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create content widget for scroll area
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 8, 0, 8)
        self.scroll_layout.setSpacing(8)  # Tight spacing like original

        # Add drag and drop hint when no transcriptions exist
        self.create_drag_drop_hint()

        self.scroll_layout.addStretch()  # Push items to top

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

    def create_drag_drop_hint(self):
        """Create a hint widget for drag and drop when no transcriptions exist"""
        self.drag_drop_hint = QLabel()
        self.drag_drop_hint.setText(
            "🎙️ Welcome to OpenSuperWhisper\n\n"
            "Drop audio files here to transcribe\n"
            "or press Ctrl+Shift+R to start recording\n\n"
            "Supported: WAV • MP3 • M4A • FLAC • OGG"
        )
        self.drag_drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_drop_hint.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 15px;
                font-weight: 400;
                line-height: 1.8;
                padding: 60px 40px;
                border: 2px dashed rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                background-color: rgba(255, 255, 255, 0.02);
                margin: 40px;
            }
        """)
        self.scroll_layout.addWidget(self.drag_drop_hint)

    def create_recording_controls(self, layout):
        """Create the recording controls section matching original design"""
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(20, 20, 20, 10)
        controls_layout.setSpacing(15)

        # Recording button - temporarily use simple button
        self.record_button = QPushButton("●")
        self.record_button.setObjectName("recordButton")
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setCursor(Qt.CursorShape.PointingHandCursor)
        controls_layout.addWidget(self.record_button)

        # Status and hotkey info layout
        status_layout = QVBoxLayout()
        status_layout.setSpacing(4)

        # Status label (aligned with button center)
        self.status_label = QLabel("Ready to record")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        status_layout.addWidget(self.status_label)

        # Hotkey hint
        self.hotkey_label = QLabel("Press Ctrl+Shift+R to start recording")
        self.hotkey_label.setStyleSheet("""
            color: #666666;
            font-size: 12px;
            font-weight: 400;
        """)
        status_layout.addWidget(self.hotkey_label)

        controls_layout.addLayout(status_layout)

        # Add stretch to push clear button to right
        controls_layout.addStretch()

        # Clear all button on the right
        self.clear_button = QPushButton("Clear All")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.clicked.connect(self.clear_all_transcriptions)
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        controls_layout.addWidget(self.clear_button)

        layout.addLayout(controls_layout)

    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(self, "System Tray",
                               "System tray is not available on this system.")
            return

        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)

        # Create a simple icon (you can replace with a proper icon file)
        icon = self.create_tray_icon()
        self.tray_icon.setIcon(icon)

        # Create tray menu
        tray_menu = QMenu()

        # Show/Hide action
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        hide_action = QAction("Hide Window", self)
        hide_action.triggered.connect(self.hide_window)
        tray_menu.addAction(hide_action)

        tray_menu.addSeparator()

        # Recording actions
        record_action = QAction("Toggle Recording", self)
        record_action.triggered.connect(self.toggle_recording)
        tray_menu.addAction(record_action)

        tray_menu.addSeparator()

        # Settings action
        settings_action = QAction("Preferences...", self)
        settings_action.triggered.connect(self.show_preferences)
        tray_menu.addAction(settings_action)

        tray_menu.addSeparator()

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(exit_action)

        # Set the menu
        self.tray_icon.setContextMenu(tray_menu)

        # Connect double-click to show/hide
        self.tray_icon.activated.connect(self.tray_icon_activated)

        # Set tooltip
        self.tray_icon.setToolTip("OpenSuperWhisper - Ready to record")

        # Show the tray icon
        self.tray_icon.show()

    def create_tray_icon(self):
        """Create a simple tray icon"""
        # Create a simple icon using QIcon
        # You can replace this with loading an actual icon file
        from PyQt6.QtGui import QPixmap, QPainter, QBrush

        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawEllipse(2, 2, 12, 12)
        painter.setBrush(QBrush(Qt.GlobalColor.red))
        painter.drawEllipse(4, 4, 8, 8)
        painter.end()

        return QIcon(pixmap)

    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_window_visibility()

    def show_window(self):
        """Show the main window"""
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_window(self):
        """Hide the main window"""
        self.hide()

    def setup_services(self):
        """Setup and configure services"""
        try:
            # Audio recorder and transcription service are already initialized in __init__
            print("Services initialized successfully")

            # Check initial model state
            self.check_model_readiness()

            # Setup a timer to periodically check model loading status
            self.model_check_timer = QTimer()
            self.model_check_timer.timeout.connect(self.check_model_readiness)
            self.model_check_timer.start(1000)  # Check every second

        except Exception as e:
            QMessageBox.critical(self, "Initialization Error",
                               f"Failed to initialize services: {e}")

    def check_model_readiness(self):
        """Check if the transcription model is ready"""
        try:
            # Check transcription service state more robustly
            is_loading = getattr(self.transcription_service, 'is_loading', False)
            is_transcribing = getattr(self.transcription_service, 'is_transcribing', False)
            model_available = getattr(self.transcription_service, 'model', None) is not None

            # Model is ready only if it's loaded, not loading, and not currently transcribing
            previous_ready_state = self.model_ready
            previous_loading_state = self.is_model_loading
            self.is_model_loading = is_loading
            self.model_ready = model_available and not is_loading and not is_transcribing

            # Log state changes for debugging
            if previous_ready_state != self.model_ready or previous_loading_state != self.is_model_loading:
                print(f"Model state changed:")
                print(f"  Ready: {previous_ready_state} -> {self.model_ready}")
                print(f"  Loading: {previous_loading_state} -> {self.is_model_loading}")
                print(f"  Model available: {model_available}")
                print(f"  Is transcribing: {is_transcribing}")

            # Update UI based on model state
            self.update_ui_for_model_state()

        except Exception as e:
            print(f"Error checking model readiness: {e}")
            # On error, assume model is not ready for safety
            self.model_ready = False
            self.is_model_loading = False

    def update_ui_for_model_state(self):
        """Update UI elements based on model loading state"""
        try:
            if self.is_model_loading:
                # Model is loading/downloading - disable transcription features
                # Check if this is initial load or model change
                current_status = self.status_label.text()
                if "Downloading" not in current_status:
                    self.status_label.setText("Loading model...")
                self.record_button.setEnabled(False)
                # Update tray tooltip
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.setToolTip("OpenSuperWhisper - Loading model...")
                # Disable file transcription menu item
                for action in self.menuBar().actions():
                    if action.text() == 'File':
                        file_menu = action.menu()
                        for file_action in file_menu.actions():
                            if 'Transcribe File' in file_action.text():
                                file_action.setEnabled(False)

            elif self.model_ready:
                # Model is ready - enable transcription features
                if not self.is_recording and not self.is_transcribing:
                    self.status_label.setText("Ready to record")
                    # Update tray tooltip
                    if hasattr(self, 'tray_icon'):
                        self.tray_icon.setToolTip("OpenSuperWhisper - Ready to record")
                # Enable recording button if not transcribing
                self.record_button.setEnabled(not self.is_transcribing)
                # Enable file transcription menu item
                for action in self.menuBar().actions():
                    if action.text() == 'File':
                        file_menu = action.menu()
                        for file_action in file_menu.actions():
                            if 'Transcribe File' in file_action.text():
                                file_action.setEnabled(True)
            else:
                # Model not available - show error state
                self.status_label.setText("Model not available")
                self.record_button.setEnabled(False)
                # Update tray tooltip
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.setToolTip("OpenSuperWhisper - Model not available")

        except Exception as e:
            print(f"Error updating UI for model state: {e}")

    def setup_hotkeys(self):
        """Setup global hotkeys"""
        try:
            # Register recording hotkey (Ctrl+Shift+R)
            record_hotkey = self.settings.get('record_hotkey', 'Ctrl+Shift+R')
            record_keys = [key.strip().lower() for key in record_hotkey.split('+')]
            self.hotkey_manager.register_hotkey(
                'toggle_recording',
                record_keys,
                self.toggle_recording,
                'Toggle recording on/off'
            )

            # Register window show/hide hotkey (Ctrl+Shift+W)
            window_hotkey = self.settings.get('window_hotkey', 'Ctrl+Shift+W')
            window_keys = [key.strip().lower() for key in window_hotkey.split('+')]
            self.hotkey_manager.register_hotkey(
                'show_window',
                window_keys,
                self.toggle_window_visibility,
                'Show/hide main window'
            )

            # Start listening for hotkeys
            self.hotkey_manager.start_listening()

            print(f"Hotkeys registered:")
            print(f"  Recording: {record_hotkey}")
            print(f"  Window: {window_hotkey}")

        except Exception as e:
            print(f"Failed to setup hotkeys: {e}")

    def setup_transcription_callbacks(self):
        """Setup callbacks for transcription service to provide better UI feedback"""
        try:
            # Connect model loading callbacks
            self.transcription_service.on_model_loading = self.on_model_loading_started
            self.transcription_service.on_model_loaded = self.on_model_loading_finished
            self.transcription_service.on_download_progress = self.on_download_progress

            print("Transcription service callbacks connected")
        except Exception as e:
            print(f"Failed to setup transcription callbacks: {e}")

    def on_model_loading_started(self, message):
        """Handle model loading started"""
        try:
            # Use QTimer to safely update UI on main thread
            QTimer.singleShot(0, lambda: self._update_model_loading_ui(message, True))
        except Exception as e:
            print(f"Error handling model loading started: {e}")

    def on_model_loading_finished(self):
        """Handle model loading finished"""
        try:
            # Use QTimer to safely update UI on main thread
            QTimer.singleShot(0, lambda: self._update_model_loading_ui("Model loaded successfully", False))
        except Exception as e:
            print(f"Error handling model loading finished: {e}")

    def on_download_progress(self, downloaded, total):
        """Handle download progress updates"""
        try:
            # Calculate progress
            percentage = int((downloaded / total) * 100) if total > 0 else 0
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            message = f"Downloading model... {percentage}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)"

            # Use QTimer to safely update UI on main thread
            QTimer.singleShot(0, lambda msg=message, pct=percentage: self._update_download_progress_ui(msg, pct))
        except Exception as e:
            print(f"Error handling download progress: {e}")

    def _update_download_progress_ui(self, message, percentage):
        """Update UI for download progress - runs on main thread"""
        try:
            self.status_label.setText(message)
            # Update tray tooltip
            if hasattr(self, 'tray_icon'):
                self.tray_icon.setToolTip(f"OpenSuperWhisper - {message}")
        except Exception as e:
            print(f"Error updating download progress UI: {e}")

    def _update_model_loading_ui(self, message, is_loading):
        """Update UI for model loading state - runs on main thread"""
        try:
            if is_loading:
                self.status_label.setText("Downloading/Loading model...")
                self.record_button.setEnabled(False)
                # Update tray tooltip
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.setToolTip("OpenSuperWhisper - Loading model...")
                print(f"Model loading UI updated: {message}")
            else:
                # Model loading finished - let the normal model readiness check handle the UI
                print(f"Model loading finished: {message}")
                # Force a model readiness check
                QTimer.singleShot(100, self.check_model_readiness)
        except Exception as e:
            print(f"Error updating model loading UI: {e}")

    def load_recordings(self):
        """Load recordings from database"""
        # Ensure this runs on the main thread
        if threading.current_thread() != threading.main_thread():
            # Schedule on main thread
            QTimer.singleShot(0, self.load_recordings)
            return

        try:
            recordings = self.database.get_all_recordings(limit=100)
            self.recordings = []

            for recording in recordings:
                self.recordings.append({
                    'id': recording.id,
                    'timestamp': recording.timestamp.strftime("%d %B %Y\n%H:%M"),
                    'transcription': recording.transcription,
                    'duration': recording.duration,
                    'language': recording.language
                })

            self.update_transcriptions_display()

        except Exception as e:
            print(f"Error loading recordings: {e}")
            self.recordings = []

    def update_transcriptions_display(self):
        """Update the transcriptions display"""
        try:
            # Clear existing items
            for item in self.transcription_items:
                item.setParent(None)
                item.deleteLater()  # Properly delete the widget
            self.transcription_items.clear()

            # Add filtered recordings
            search_text = self.search_input.text().lower()
            visible_recordings = []

            for recording in self.recordings:
                if not search_text or search_text in recording.get('transcription', '').lower():
                    visible_recordings.append(recording)
                    item = TranscriptionItem(recording, parent=self.scroll_content)
                    self.transcription_items.append(item)
                    # Insert at the beginning (before stretch)
                    self.scroll_layout.insertWidget(0, item)

            # Show/hide drag and drop hint based on whether there are visible recordings
            if hasattr(self, 'drag_drop_hint'):
                if visible_recordings:
                    self.drag_drop_hint.hide()
                else:
                    self.drag_drop_hint.show()

        except Exception as e:
            print(f"Error updating transcriptions display: {e}")

    def filter_transcriptions(self):
        """Filter transcriptions based on search text"""
        self.update_transcriptions_display()

    def toggle_recording(self):
        """Toggle recording on/off"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        """Start audio recording"""
        # Check if model is ready before allowing recording
        if not self.model_ready:
            if self.is_model_loading:
                QMessageBox.warning(self, "Model Loading",
                                  "Please wait for the model to finish loading before recording.")
            else:
                QMessageBox.warning(self, "Model Not Ready",
                                  "Transcription model is not available. Please check your settings.")
            return

        # Check if currently transcribing
        if self.is_transcribing:
            QMessageBox.warning(self, "Transcription in Progress",
                              "Please wait for the current transcription to complete before recording.")
            return

        try:
            print("Starting recording...")
            device_index = self.settings.get('audio_device')
            print(f"Using device index: {device_index}")

            # Update UI first
            self.is_recording = True
            self.update_recording_ui()

            if self.audio_recorder.start_recording(device_index):
                print("Recording started successfully")
                self.status_label.setText("Recording...")
            else:
                print("Failed to start recording")
                self.is_recording = False
                self.update_recording_ui()
                QMessageBox.warning(self, "Recording Error",
                                  "Failed to start recording. Check microphone settings.")

        except Exception as e:
            print(f"Recording exception: {e}")
            import traceback
            traceback.print_exc()
            self.is_recording = False
            self.update_recording_ui()
            QMessageBox.critical(self, "Recording Error", f"Exception: {e}")

    def stop_recording(self):
        """Stop audio recording"""
        try:
            print("Stopping recording...")
            recording_path = self.audio_recorder.stop_recording()
            self.is_recording = False
            self.update_recording_ui()

            if recording_path:
                print(f"Recording saved to: {recording_path}")
                self.start_transcription(recording_path)
            else:
                print("No recording to transcribe")
                self.status_label.setText("Ready to record")

        except Exception as e:
            print(f"Stop recording exception: {e}")
            import traceback
            traceback.print_exc()
            self.is_recording = False
            self.update_recording_ui()
            QMessageBox.critical(self, "Stop Recording Error", f"Exception: {e}")

    def update_recording_ui(self):
        """Update recording button and status with modern styling"""
        if self.is_recording:
            # Update button based on type
            if isinstance(self.record_button, RecordButton):
                self.record_button.set_recording(True)
                self.record_button.setObjectName("stopButton")
            else:
                self.record_button.setText("■")
                self.record_button.setObjectName("stopButton")

            # Show recording status with red dot like original
            self.status_label.setText("🔴 Recording")
            self.status_label.setStyleSheet("""
                color: #ef4444;
                font-size: 14px;
                font-weight: 500;
            """)
            # Hide hotkey hint when recording
            if hasattr(self, 'hotkey_label'):
                self.hotkey_label.hide()
            # Update tray tooltip
            if hasattr(self, 'tray_icon'):
                self.tray_icon.setToolTip("OpenSuperWhisper - Recording...")
            # Add pulsing animation effect
            self.start_recording_animation()
        else:
            # Update button based on type
            if isinstance(self.record_button, RecordButton):
                self.record_button.set_recording(False)
                self.record_button.setObjectName("recordButton")
            else:
                self.record_button.setText("●")
                self.record_button.setObjectName("recordButton")

            if self.model_ready:
                self.status_label.setText("Ready to record")
                self.status_label.setStyleSheet("""
                    color: #a0a0a0;
                    font-size: 14px;
                    font-weight: 500;
                    letter-spacing: 0.3px;
                """)
                # Show hotkey hint when not recording
                if hasattr(self, 'hotkey_label'):
                    self.hotkey_label.show()
                # Update tray tooltip
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.setToolTip("OpenSuperWhisper - Ready to record")
            # Stop animation
            self.stop_recording_animation()

        # Refresh stylesheet to apply new object name styling
        self.record_button.setStyleSheet("")
        self.record_button.style().unpolish(self.record_button)
        self.record_button.style().polish(self.record_button)

    def start_recording_animation(self):
        """Start pulsing animation for recording button"""
        if not hasattr(self, 'recording_timer'):
            self.recording_timer = QTimer()
            self.recording_timer.timeout.connect(self.pulse_recording_button)
            self.pulse_state = 0
        self.recording_timer.start(600)  # Pulse every 600ms

    def stop_recording_animation(self):
        """Stop pulsing animation"""
        if hasattr(self, 'recording_timer'):
            self.recording_timer.stop()

    def pulse_recording_button(self):
        """Create pulsing effect for recording button"""
        self.pulse_state = (self.pulse_state + 1) % 2
        if self.pulse_state == 0:
            self.record_button.setStyleSheet("")
        else:
            self.record_button.setStyleSheet("""
                QPushButton#stopButton {
                    background-color: #ff6b6b;
                    border-color: #ff6b6b;
                }
            """)

    def start_transcription(self, audio_path):
        """Start transcription in background thread"""
        # Check if already transcribing
        if self.is_transcribing:
            print("Transcription already in progress, ignoring new request")
            return

        # Final safety check before starting transcription
        if not self.model_ready:
            error_msg = "Cannot start transcription: model not ready"
            if self.is_model_loading:
                error_msg = "Cannot start transcription: model is still loading"
            print(error_msg)
            self.status_label.setText("Ready to record")
            QMessageBox.warning(self, "Transcription Error", error_msg)
            return

        # Clean up any existing thread first
        self.cleanup_transcription_thread()

        self.is_transcribing = True
        self.status_label.setText("Transcribing...")

        # Create worker thread
        self.transcription_thread = QThread()
        self.transcription_worker = TranscriptionWorker(
            self.transcription_service, audio_path, self.settings
        )
        self.transcription_worker.moveToThread(self.transcription_thread)

        # Connect signals
        self.transcription_thread.started.connect(self.transcription_worker.run)
        self.transcription_worker.finished.connect(self.on_transcription_finished)
        self.transcription_worker.error.connect(self.on_transcription_error)
        self.transcription_worker.finished.connect(self.cleanup_transcription_thread)
        self.transcription_worker.error.connect(self.cleanup_transcription_thread)
        self.transcription_thread.finished.connect(self.transcription_thread.deleteLater)

        # Start thread
        self.transcription_thread.start()

    def cleanup_transcription_thread(self):
        """Clean up transcription thread safely"""
        try:
            self.is_transcribing = False

            if self.transcription_thread and self.transcription_thread.isRunning():
                # Wait for thread to finish gracefully
                self.transcription_thread.quit()
                if not self.transcription_thread.wait(5000):  # Wait up to 5 seconds
                    print("Warning: Transcription thread did not finish gracefully")
                    self.transcription_thread.terminate()
                    self.transcription_thread.wait()

            # Clear references
            self.transcription_thread = None
            self.transcription_worker = None

        except Exception as e:
            print(f"Error cleaning up transcription thread: {e}")

    def on_transcription_finished(self, transcription_text):
        """Handle successful transcription"""
        try:
            # Copy transcription to clipboard
            self.copy_to_clipboard(transcription_text)

            # Save to database
            recording = Recording(
                transcription=transcription_text,
                timestamp=datetime.now(),
                duration=0.0,  # TODO: Calculate actual duration
                language=self.settings.get('language', 'auto')
            )
            self.database.add_recording(recording)

            # Use QTimer to safely update UI on main thread
            QTimer.singleShot(0, lambda: self._update_ui_after_transcription(transcription_text))

        except Exception as e:
            self.on_transcription_error(f"Failed to save transcription: {e}")

    def _update_ui_after_transcription(self, transcription_text):
        """Update UI after transcription completion - runs on main thread"""
        try:
            self.load_recordings()

            # Check if we're processing a batch of files
            if hasattr(self, 'transcription_queue') and self.transcription_queue:
                # Move to next file in batch
                self.current_transcription_index += 1
                self.transcribe_next_in_queue()
            else:
                # Single file or batch complete
                self.status_label.setText("Ready to record")

            self.show_transcription_notification(transcription_text)
        except Exception as e:
            print(f"Error updating UI after transcription: {e}")

    def on_transcription_error(self, error_message):
        """Handle transcription error"""
        # Use QTimer to safely show error on main thread
        QTimer.singleShot(0, lambda: self._show_transcription_error(error_message))

    def _show_transcription_error(self, error_message):
        """Show transcription error - runs on main thread"""
        try:
            QMessageBox.critical(self, "Transcription Error", error_message)
            self.status_label.setText("Ready to record")
        except Exception as e:
            print(f"Error showing transcription error: {e}")

    def clear_all_transcriptions(self):
        """Clear all transcriptions with confirmation"""
        reply = QMessageBox.question(
            self, "Clear All",
            "Are you sure you want to clear all transcriptions?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.database.delete_all_recordings()
                self.recordings.clear()
                self.update_transcriptions_display()
                QMessageBox.information(self, "Success", "All transcriptions cleared.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear transcriptions: {e}")

    def transcribe_file(self):
        """Transcribe an audio file"""
        # Check if model is ready before allowing file transcription
        if not self.model_ready:
            if self.is_model_loading:
                QMessageBox.warning(self, "Model Loading",
                                  "Please wait for the model to finish loading before transcribing files.")
            else:
                QMessageBox.warning(self, "Model Not Ready",
                                  "Transcription model is not available. Please check your settings.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "",
            "Audio Files (*.wav *.mp3 *.m4a *.flac *.ogg);;All Files (*)"
        )

        if file_path:
            self.start_transcription(file_path)

    def show_preferences(self):
        """Show preferences dialog"""
        try:
            from preferences_dialog import PreferencesDialog

            print(f"Current settings before dialog: {self.settings}")

            dialog = PreferencesDialog(self)

            # Connect with debug
            def debug_settings_changed(new_settings):
                print(f"Settings changed signal received with: {new_settings}")
                self.on_settings_changed(new_settings)

            dialog.settings_changed.connect(debug_settings_changed)

            result = dialog.exec()
            print(f"Dialog result: {result}, Accepted={QDialog.DialogCode.Accepted}")

            if result == QDialog.DialogCode.Accepted:
                print("Settings dialog accepted")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open preferences: {e}")

    def on_settings_changed(self, new_settings):
        """Handle settings changes"""
        try:
            print(f"Settings changed received: {new_settings}")

            # Store old settings for comparison
            old_settings = self.settings.copy()

            # Update internal settings
            self.settings = new_settings

            # Restart services if needed with old vs new comparison
            self.restart_services_if_needed(old_settings, new_settings)

        except Exception as e:
            print(f"Error applying settings: {e}")

    def restart_services_if_needed(self, old_settings, new_settings):
        """Restart services if critical settings changed"""
        try:
            # Check if model or device changed
            current_model = old_settings.get('model', 'base')
            current_device = old_settings.get('device', 'cpu')

            new_model = new_settings.get('model', 'base')
            new_device = new_settings.get('device', 'cpu')

            model_changed = current_model != new_model
            device_changed = current_device != new_device

            print(f"Settings comparison:")
            print(f"  Model: {current_model} -> {new_model} (changed: {model_changed})")
            print(f"  Device: {current_device} -> {new_device} (changed: {device_changed})")

            if model_changed or device_changed:
                # Set loading state immediately
                self.is_model_loading = True
                self.model_ready = False
                self.update_ui_for_model_state()
                print("Model/device change detected - disabling transcription until ready")

            if model_changed:
                print(f"Model changed from {current_model} to {new_model}")
                try:
                    self.transcription_service.change_model(new_model)
                except Exception as e:
                    print(f"Error changing model: {e}")
                    # Reset to safe state on error
                    self.is_model_loading = False
                    self.model_ready = False
                    self.update_ui_for_model_state()

            if device_changed:
                print(f"Device changed from {current_device} to {new_device}")
                try:
                    # Force device change
                    success = self.transcription_service.change_device(new_device)
                    if success:
                        print(f"Device successfully changed to {new_device}")
                        # Update our local settings to reflect the change
                        self.settings['device'] = new_device
                        # Save settings
                        self.settings_manager.save_settings(self.settings)
                    else:
                        print(f"Device change to {new_device} failed")
                except Exception as e:
                    print(f"Error changing device: {e}")
                    # Reset to safe state on error
                    self.is_model_loading = False
                    self.model_ready = False
                    self.update_ui_for_model_state()

        except Exception as e:
            print(f"Error restarting services: {e}")

    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to clipboard using available method"""
        if not CLIPBOARD_AVAILABLE:
            print("Clipboard functionality not available")
            return False

        try:
            # Try pyperclip first (simpler)
            try:
                import pyperclip
                pyperclip.copy(text)
                print(f"Copied to clipboard via pyperclip: {text[:50]}...")
                return True
            except ImportError:
                pass

            # Fallback to win32clipboard
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text)
                win32clipboard.CloseClipboard()
                print(f"Copied to clipboard via win32clipboard: {text[:50]}...")
                return True
            except ImportError:
                pass

            # Last resort: use PyQt6 clipboard
            try:
                from PyQt6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
                print(f"Copied to clipboard via PyQt6: {text[:50]}...")
                return True
            except Exception as e:
                print(f"Failed to copy via PyQt6: {e}")
                return False

        except Exception as e:
            print(f"Failed to copy to clipboard: {e}")
            return False

    def show_transcription_notification(self, text: str):
        """Show notification that transcription was completed and copied"""
        # Truncate text for notification
        display_text = text[:100] + "..." if len(text) > 100 else text

        # Show status message
        self.status_label.setText(f"Transcribed and copied to clipboard")

        # Show system tray notification
        if hasattr(self, 'tray_icon') and self.tray_icon.supportsMessages():
            self.tray_icon.showMessage(
                "Transcription Complete",
                f"Text copied to clipboard:\n{display_text}",
                QSystemTrayIcon.MessageIcon.Information,
                3000  # Show for 3 seconds
            )

        # Optional: Show a brief message box (can be disabled in preferences)
        # QMessageBox.information(self, "Transcription Complete",
        #                        f"Transcription copied to clipboard:\n\n{display_text}")

    def toggle_window_visibility(self):
        """Toggle window visibility (show/hide)"""
        try:
            if self.isVisible() and not self.isMinimized():
                # Hide window
                self.hide()
                print("Window hidden via hotkey")
            else:
                # Show and bring to front
                self.show()
                self.raise_()
                self.activateWindow()
                print("Window shown via hotkey")
        except Exception as e:
            print(f"Error toggling window visibility: {e}")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About OpenSuperWhisper",
            "OpenSuperWhisper - Windows\n\n"
            "A modern transcription application powered by OpenAI Whisper.\n\n"
            "Built with PyQt6 for a native Windows experience."
        )

    def closeEvent(self, event):
        """Handle application close"""
        # If system tray is available, minimize to tray instead of closing
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            # Check if this is a real close request or just minimize to tray
            if not getattr(self, '_really_close', False):
                QMessageBox.information(self, "OpenSuperWhisper",
                                      "Application was minimized to tray. "
                                      "To close completely, use 'Exit' from the tray menu.")
                self.hide()
                event.ignore()
                return

        try:
            # Stop recording if active
            if self.is_recording:
                self.stop_recording()

            # Stop any running transcription
            if self.is_transcribing:
                print("Stopping transcription before exit...")
                self.cleanup_transcription_thread()

            # Stop model check timer
            if hasattr(self, 'model_check_timer'):
                self.model_check_timer.stop()

            # Hide tray icon
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()

            # Cleanup hotkeys
            self.hotkey_manager.cleanup()

            # Cleanup audio recorder
            self.audio_recorder.cleanup()

        except Exception as e:
            print(f"Error during cleanup: {e}")

        event.accept()

    def quit_application(self):
        """Quit the application completely"""
        self._really_close = True
        self.close()
        QApplication.quit()

    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            # Check if any of the dragged files are audio files
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if self.is_audio_file(file_path):
                        event.acceptProposedAction()
                        self.setStyleSheet(self.styleSheet() + """
                            QMainWindow {
                                border: 2px dashed #0078d4;
                                background-color: #1a1a1a;
                            }
                        """)
                        return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        # Reset the styling
        self.set_dark_theme()
        event.accept()

    def dropEvent(self, event):
        """Handle drop event"""
        # Reset the styling
        self.set_dark_theme()

        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            audio_files = []

            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if self.is_audio_file(file_path):
                        audio_files.append(file_path)

            if audio_files:
                if len(audio_files) == 1:
                    # Single file - transcribe directly
                    self.transcribe_dropped_file(audio_files[0])
                else:
                    # Multiple files - ask user what to do
                    self.handle_multiple_files(audio_files)
                event.acceptProposedAction()
            else:
                QMessageBox.warning(self, "Invalid Files",
                                  "Please drop audio files only.\n\n"
                                  "Supported formats: WAV, MP3, M4A, FLAC, OGG")
        else:
            event.ignore()

    def is_audio_file(self, file_path):
        """Check if file is a supported audio format"""
        audio_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac', '.wma'}
        return Path(file_path).suffix.lower() in audio_extensions

    def transcribe_dropped_file(self, file_path):
        """Transcribe a single dropped file"""
        # Check if model is ready
        if not self.model_ready:
            if self.is_model_loading:
                QMessageBox.warning(self, "Model Loading",
                                  "Please wait for the model to finish loading before transcribing files.")
            else:
                QMessageBox.warning(self, "Model Not Ready",
                                  "Transcription model is not available. Please check your settings.")
            return

        print(f"Transcribing dropped file: {file_path}")
        self.start_transcription(file_path)

    def handle_multiple_files(self, file_paths):
        """Handle multiple dropped files"""
        from PyQt6.QtWidgets import QInputDialog

        # Ask user what to do with multiple files
        options = [
            f"Transcribe first file only ({Path(file_paths[0]).name})",
            f"Transcribe all {len(file_paths)} files sequentially"
        ]

        choice, ok = QInputDialog.getItem(
            self, "Multiple Files",
            f"You dropped {len(file_paths)} audio files. What would you like to do?",
            options, 0, False
        )

        if ok:
            if choice.startswith("Transcribe first"):
                self.transcribe_dropped_file(file_paths[0])
            else:
                self.transcribe_multiple_files(file_paths)

    def transcribe_multiple_files(self, file_paths):
        """Transcribe multiple files sequentially"""
        # Check if model is ready
        if not self.model_ready:
            if self.is_model_loading:
                QMessageBox.warning(self, "Model Loading",
                                  "Please wait for the model to finish loading before transcribing files.")
            else:
                QMessageBox.warning(self, "Model Not Ready",
                                  "Transcription model is not available. Please check your settings.")
            return

        # Store the file queue for sequential processing
        self.transcription_queue = file_paths.copy()
        self.current_transcription_index = 0

        # Start with the first file
        if self.transcription_queue:
            print(f"Starting batch transcription of {len(self.transcription_queue)} files")
            self.transcribe_next_in_queue()

    def transcribe_next_in_queue(self):
        """Transcribe the next file in the queue"""
        if self.current_transcription_index < len(self.transcription_queue):
            current_file = self.transcription_queue[self.current_transcription_index]
            print(f"Transcribing file {self.current_transcription_index + 1}/{len(self.transcription_queue)}: {Path(current_file).name}")

            # Update status to show progress
            self.status_label.setText(f"Transcribing {self.current_transcription_index + 1}/{len(self.transcription_queue)}...")

            # Start transcription
            self.start_transcription(current_file)
        else:
            # All files processed
            print("Batch transcription completed")
            self.transcription_queue = []
            self.current_transcription_index = 0
            self.status_label.setText("Ready to record")

            # Show completion notification
            if hasattr(self, 'tray_icon') and self.tray_icon.supportsMessages():
                self.tray_icon.showMessage(
                    "Batch Transcription Complete",
                    "All files have been transcribed successfully!",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )


def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    print("Uncaught exception:", exc_type, exc_value)
    import traceback
    traceback.print_exception(exc_type, exc_value, exc_traceback)


def main():
    """Main application entry point"""
    try:
        print("Starting OpenSuperWhisper PyQt6...")

        # Set global exception handler
        sys.excepthook = handle_exception

        app = QApplication(sys.argv)

        # Set application properties
        app.setApplicationName("OpenSuperWhisper")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("OpenSuperWhisper")

        print("QApplication created successfully")

        # Create and show main window
        window = OpenSuperWhisperGUI()
        window.show()

        print("GUI started successfully")

        # Run application
        sys.exit(app.exec())

    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()

        # Try to show error dialog if possible
        try:
            if 'app' in locals():
                QMessageBox.critical(None, "Startup Error", f"Failed to start OpenSuperWhisper:\n\n{e}")
        except:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
