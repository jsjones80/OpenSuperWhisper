"""
OpenSuperWhisper Windows GUI Application
Main application window with recording, transcription, and management features
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import sys
import os

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

# Add whisper module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from whisper.audio_recorder import AudioRecorder
from whisper.transcription_service import get_transcription_service
from whisper.database import get_database, Recording
from whisper.settings_dialog import show_settings_dialog
from whisper.config_manager import get_config_manager
from whisper.hotkeys import get_hotkey_manager


class OpenSuperWhisperGUI:
    """Main GUI application for OpenSuperWhisper Windows"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OpenSuperWhisper - Windows")

        # Configuration manager
        self.config_manager = get_config_manager()

        # Load settings and apply window geometry
        self.settings = self.config_manager.get_all_settings()

        # Apply window settings
        geometry = self.settings.get('window_geometry', '800x600')
        self.root.geometry(geometry)
        self.root.minsize(600, 400)

        # Apply window position if saved
        position = self.settings.get('window_position')
        if position:
            self.root.geometry(f"{geometry}+{position}")

        # Services
        self.audio_recorder = AudioRecorder()
        self.transcription_service = get_transcription_service()
        self.database = get_database()
        self.hotkey_manager = get_hotkey_manager()

        # State variables
        self.is_recording = tk.BooleanVar(value=False)
        self.is_transcribing = tk.BooleanVar(value=False)
        self.recording_duration = tk.StringVar(value="00:00")
        self.transcription_progress = tk.DoubleVar(value=0.0)
        self.current_recording_path: Optional[Path] = None

        # Setup callbacks
        self._setup_callbacks()

        # Create GUI
        self._create_gui()

        # Apply loaded settings to services
        self._apply_loaded_settings()

        # Setup global hotkeys
        self._setup_hotkeys()

        # Load initial recordings
        self._load_recordings()

        # Setup window close handler to save settings
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_callbacks(self):
        """Setup callbacks for audio recorder and transcription service"""
        self.audio_recorder.on_recording_start = self._on_recording_start
        self.audio_recorder.on_recording_stop = self._on_recording_stop

        self.transcription_service.on_progress = self._on_transcription_progress
        self.transcription_service.on_complete = self._on_transcription_complete
        self.transcription_service.on_error = self._on_transcription_error

    def _apply_loaded_settings(self):
        """Apply loaded settings to services"""
        try:
            # Apply model settings if different from current
            model = self.settings.get('model', 'base')
            if model != self.transcription_service.model_name:
                print(f"Applying saved model setting: {model}")
                self.transcription_service.change_model(model)

            # Apply device settings if different from current
            device = self.settings.get('device', 'cpu')
            if device != self.transcription_service.device:
                print(f"Applying saved device setting: {device}")
                self.transcription_service.change_device(device)

            print("Loaded settings applied to services")

        except Exception as e:
            print(f"Error applying loaded settings: {e}")
            # Continue with current settings if applying fails

    def _setup_hotkeys(self):
        """Setup global hotkeys"""
        try:
            if not self.hotkey_manager.is_available():
                print("Global hotkeys not available on this system")
                return

            # Register hotkey callbacks
            self.hotkey_manager.set_hotkey_callback("toggle_recording", self._hotkey_toggle_recording)
            self.hotkey_manager.set_hotkey_callback("show_window", self._hotkey_show_window)

            # Apply custom hotkeys from settings
            record_hotkey = self.settings.get('record_hotkey', 'Ctrl+Shift+R')
            window_hotkey = self.settings.get('window_hotkey', 'Ctrl+Shift+W')

            # Parse and register custom hotkeys
            self._register_custom_hotkey("toggle_recording", record_hotkey, self._hotkey_toggle_recording)
            self._register_custom_hotkey("show_window", window_hotkey, self._hotkey_show_window)

            # Start listening for hotkeys
            if self.hotkey_manager.start_listening():
                print("Global hotkeys enabled")
            else:
                print("Failed to start global hotkey listener")

        except Exception as e:
            print(f"Error setting up hotkeys: {e}")

    def _register_custom_hotkey(self, name: str, hotkey_string: str, callback):
        """Register a custom hotkey from string format"""
        try:
            # Parse hotkey string (e.g., "Ctrl+Shift+R")
            keys = []
            parts = hotkey_string.lower().replace(' ', '').split('+')

            for part in parts:
                if part in ['ctrl', 'control']:
                    keys.append('ctrl')
                elif part == 'shift':
                    keys.append('shift')
                elif part == 'alt':
                    keys.append('alt')
                elif part in ['win', 'windows', 'cmd']:
                    keys.append('cmd')
                elif len(part) == 1 and part.isalnum():
                    keys.append(part)
                else:
                    print(f"Unknown key in hotkey '{hotkey_string}': {part}")
                    return False

            if keys:
                return self.hotkey_manager.register_hotkey(
                    name, keys, callback, f"Custom hotkey: {hotkey_string}"
                )
            return False

        except Exception as e:
            print(f"Error registering custom hotkey '{hotkey_string}': {e}")
            return False

    def _hotkey_toggle_recording(self):
        """Hotkey callback for toggle recording"""
        try:
            # Use the main thread to execute GUI operations
            self.root.after(0, self._toggle_recording)
        except Exception as e:
            print(f"Error in toggle recording hotkey: {e}")

    def _hotkey_show_window(self):
        """Hotkey callback for show/hide window"""
        try:
            # Use the main thread to execute GUI operations
            self.root.after(0, self._toggle_window_visibility)
        except Exception as e:
            print(f"Error in show window hotkey: {e}")

    def _toggle_window_visibility(self):
        """Toggle window visibility (show/hide)"""
        try:
            if self.root.state() == 'withdrawn' or not self.root.winfo_viewable():
                # Show window
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                print("Window shown via hotkey")
            else:
                # Hide window
                self.root.withdraw()
                print("Window hidden via hotkey")
        except Exception as e:
            print(f"Error toggling window visibility: {e}")

    def _update_hotkeys(self):
        """Update hotkeys when settings change"""
        try:
            if not self.hotkey_manager.is_available():
                return

            # Get new hotkey settings
            record_hotkey = self.settings.get('record_hotkey', 'Ctrl+Shift+R')
            window_hotkey = self.settings.get('window_hotkey', 'Ctrl+Shift+W')

            # Re-register hotkeys with new key combinations
            self._register_custom_hotkey("toggle_recording", record_hotkey, self._hotkey_toggle_recording)
            self._register_custom_hotkey("show_window", window_hotkey, self._hotkey_show_window)

            print(f"Hotkeys updated: Record={record_hotkey}, Window={window_hotkey}")

        except Exception as e:
            print(f"Error updating hotkeys: {e}")

    def _create_gui(self):
        """Create the main GUI layout - mirroring original OpenSuperWhisper design"""
        # Configure dark theme
        self._configure_dark_theme()

        # Set window properties
        self.root.configure(bg='#2b2b2b')

        # Main container with dark background
        main_frame = tk.Frame(self.root, bg='#2b2b2b', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Search section at top
        self._create_search_section(main_frame)

        # Transcriptions list (main content)
        self._create_transcriptions_list(main_frame)

        # Recording controls at bottom
        self._create_recording_controls_bottom(main_frame)

        # Menu bar
        self._create_menu_bar()

    def _configure_dark_theme(self):
        """Configure dark theme styling"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure dark colors
        style.configure('Dark.TFrame', background='#2b2b2b')
        style.configure('Dark.TLabel', background='#2b2b2b', foreground='#ffffff')
        style.configure('Dark.TButton', background='#404040', foreground='#ffffff')
        style.configure('Dark.TEntry', background='#404040', foreground='#ffffff', fieldbackground='#404040')
        style.configure('Dark.Treeview', background='#353535', foreground='#ffffff', fieldbackground='#353535')
        style.configure('Dark.Treeview.Heading', background='#404040', foreground='#ffffff')

    def _create_search_section(self, parent):
        """Create search section at top"""
        search_frame = tk.Frame(parent, bg='#2b2b2b')
        search_frame.pack(fill=tk.X, pady=(0, 15))

        # Search entry with placeholder-like styling
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self._on_search_changed)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               bg='#3a3a3a', fg='#cccccc', insertbackground='#cccccc',
                               font=('Arial', 12), relief=tk.FLAT, bd=0)
        search_entry.pack(fill=tk.X, ipady=12, ipadx=15)

        # Add placeholder text behavior
        self._setup_search_placeholder(search_entry)

    def _setup_search_placeholder(self, entry):
        """Setup placeholder text for search entry"""
        placeholder_text = "Search in transcriptions"

        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, tk.END)
                entry.config(fg='#ffffff')

        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder_text)
                entry.config(fg='#888888')

        # Set initial placeholder
        entry.insert(0, placeholder_text)
        entry.config(fg='#888888')

        # Bind events
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)

    def _create_transcriptions_list(self, parent):
        """Create main transcriptions list"""
        # Frame for transcriptions
        list_frame = tk.Frame(parent, bg='#2b2b2b')
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Scrollable frame for transcription items
        canvas = tk.Canvas(list_frame, bg='#353535', highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg='#353535')

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Store canvas reference for updating
        self.transcriptions_canvas = canvas

    def _create_recording_controls_bottom(self, parent):
        """Create recording controls at bottom"""
        controls_frame = tk.Frame(parent, bg='#2b2b2b')
        controls_frame.pack(fill=tk.X)

        # Center the controls
        center_frame = tk.Frame(controls_frame, bg='#2b2b2b')
        center_frame.pack(expand=True)

        # Recording button (circular style)
        self.record_button = tk.Button(center_frame, text="●", font=('Arial', 24),
                                      bg='#44ff44', fg='#ffffff', relief=tk.FLAT,
                                      width=4, height=2, command=self._toggle_recording)
        self.record_button.pack(side=tk.LEFT, padx=10)

        # Status label
        self.status_label = tk.Label(center_frame, text="Ready to record",
                                    bg='#2b2b2b', fg='#ffffff', font=('Arial', 12))
        self.status_label.pack(side=tk.LEFT, padx=20)

        # Clear all button
        clear_button = tk.Button(center_frame, text="Clear All", font=('Arial', 10),
                                bg='#666666', fg='#ffffff', relief=tk.FLAT,
                                padx=20, pady=5, command=self._clear_all_transcriptions)
        clear_button.pack(side=tk.LEFT, padx=10)

    def _create_recording_controls(self, parent):
        """Create recording controls section"""
        controls_frame = ttk.LabelFrame(parent, text="Recording Controls", padding="10")
        controls_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Record button
        self.record_button = ttk.Button(
            controls_frame,
            text="Start Recording",
            command=self._toggle_recording,
            style="Accent.TButton"
        )
        self.record_button.grid(row=0, column=0, padx=(0, 10))

        # Recording duration
        duration_label = ttk.Label(controls_frame, text="Duration:")
        duration_label.grid(row=0, column=1, padx=(0, 5))

        duration_value = ttk.Label(
            controls_frame,
            textvariable=self.recording_duration,
            font=("Consolas", 12, "bold")
        )
        duration_value.grid(row=0, column=2, padx=(0, 20))

        # Transcribe file button
        transcribe_button = ttk.Button(
            controls_frame,
            text="Transcribe File...",
            command=self._transcribe_file
        )
        transcribe_button.grid(row=0, column=3)

    def _create_status_section(self, parent):
        """Create status section"""
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)

        # Model info
        model_label = ttk.Label(status_frame, text="Model:")
        model_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        self.model_info = ttk.Label(status_frame, text="Loading...")
        self.model_info.grid(row=0, column=1, sticky=tk.W)

        # Progress bar
        progress_label = ttk.Label(status_frame, text="Progress:")
        progress_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))

        self.progress_bar = ttk.Progressbar(
            status_frame,
            variable=self.transcription_progress,
            maximum=100
        )
        self.progress_bar.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(5, 0))

    def _create_recordings_section(self, parent):
        """Create recordings list section"""
        recordings_frame = ttk.LabelFrame(parent, text="Recordings", padding="10")
        recordings_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        recordings_frame.columnconfigure(0, weight=1)
        recordings_frame.rowconfigure(1, weight=1)

        # Search bar
        search_frame = ttk.Frame(recordings_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)

        search_label = ttk.Label(search_frame, text="Search:")
        search_label.grid(row=0, column=0, padx=(0, 10))

        # Note: search_var is already created in _create_search_section
        if not hasattr(self, 'search_var'):
            self.search_var = tk.StringVar()
            self.search_var.trace_add('write', self._on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

        clear_button = ttk.Button(search_frame, text="Clear", command=self._clear_search)
        clear_button.grid(row=0, column=2)

        # Recordings tree
        tree_frame = ttk.Frame(recordings_frame)
        tree_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Create treeview
        columns = ("timestamp", "duration", "language", "transcription")
        self.recordings_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)

        # Configure columns
        self.recordings_tree.heading("timestamp", text="Date/Time")
        self.recordings_tree.heading("duration", text="Duration")
        self.recordings_tree.heading("language", text="Language")
        self.recordings_tree.heading("transcription", text="Transcription")

        self.recordings_tree.column("timestamp", width=150, minwidth=100)
        self.recordings_tree.column("duration", width=80, minwidth=60)
        self.recordings_tree.column("language", width=80, minwidth=60)
        self.recordings_tree.column("transcription", width=400, minwidth=200)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.recordings_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.recordings_tree.xview)
        self.recordings_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid layout
        self.recordings_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Context menu
        self._create_context_menu()

        # Bind events
        self.recordings_tree.bind("<Double-1>", self._on_recording_double_click)
        self.recordings_tree.bind("<Button-3>", self._on_recording_right_click)
        self.recordings_tree.bind("<Delete>", self._on_delete_key)
        self.recordings_tree.bind("<KeyPress>", self._on_key_press)

    def _create_context_menu(self):
        """Create context menu for recordings"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Play", command=self._play_selected_recording)
        self.context_menu.add_command(label="Copy Text", command=self._copy_selected_text)
        self.context_menu.add_command(label="Export...", command=self._export_selected_recording)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete", command=self._delete_selected_recording)

    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Transcribe File...", command=self._transcribe_file)
        file_menu.add_separator()
        file_menu.add_command(label="Export All...", command=self._export_all_recordings)
        file_menu.add_command(label="Import...", command=self._import_recordings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Delete Selected Recording(s)", command=self._delete_selected_recording, accelerator="Delete")
        edit_menu.add_separator()
        edit_menu.add_command(label="Clear All Recordings", command=self._clear_all_recordings)

        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences...", command=self._show_preferences)
        settings_menu.add_command(label="Audio Devices...", command=self._show_audio_devices)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _setup_periodic_updates(self):
        """Setup periodic updates for UI"""
        self._update_model_info()
        self._update_recording_duration()

        # Schedule next update
        self.root.after(1000, self._setup_periodic_updates)

    def _update_model_info(self):
        """Update model information display"""
        model_info = self.transcription_service.get_model_info()
        if model_info['loaded']:
            text = f"{model_info['name']} ({model_info['device']})"
        elif model_info['loading']:
            text = f"Loading {model_info['name']}..."
        else:
            text = "No model loaded"

        self.model_info.config(text=text)

    def _update_recording_duration(self):
        """Update recording duration display"""
        if self.is_recording.get() and self.current_recording_path:
            # Calculate duration based on file size or elapsed time
            # This is a simplified version - you might want to track actual time
            duration = "Recording..."
        else:
            duration = "00:00"

        self.recording_duration.set(duration)

    def _start_recording(self):
        """Start audio recording"""
        device_index = self.settings.get('audio_device', None)
        device_name = self.settings.get('audio_device_name', 'Default')

        print(f"=== RECORDING DEBUG ===")
        print(f"Device name: {device_name}")
        print(f"Device index: {device_index}")
        print(f"Device index type: {type(device_index)}")
        print(f"All settings: {self.settings}")
        print(f"======================")

        try:
            if self.audio_recorder.start_recording(device_index):
                self.is_recording.set(True)
                self._update_recording_button()
                print("Recording started successfully")
            else:
                error_msg = f"Failed to start recording with device: {device_name}\n\n"
                error_msg += "Possible solutions:\n"
                error_msg += "• Check if microphone is connected and working\n"
                error_msg += "• Try selecting a different microphone in Settings\n"
                error_msg += "• Make sure no other application is using the microphone\n"
                error_msg += "• Run the application as Administrator"

                messagebox.showerror("Recording Error", error_msg)
        except Exception as e:
            print(f"Exception in _start_recording: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Recording Error", f"Exception: {e}")

    def _toggle_recording(self):
        """Toggle recording on/off"""
        if self.is_recording.get():
            self._stop_recording()
        else:
            self._start_recording()

    def _stop_recording(self):
        """Stop audio recording"""
        recording_path = self.audio_recorder.stop_recording()
        self.is_recording.set(False)
        self._update_recording_button()

        if recording_path:
            self.current_recording_path = recording_path
            self._start_transcription(recording_path)
        else:
            print("No recording to transcribe")

    def _update_recording_button(self):
        """Update recording button appearance based on state"""
        if hasattr(self, 'record_button') and hasattr(self, 'status_label'):
            if self.is_recording.get():
                self.record_button.config(text="■", bg='#ff4444')
                self.status_label.config(text="Recording...")
            else:
                self.record_button.config(text="●", bg='#44ff44')
                self.status_label.config(text="Ready to record")

    def _start_transcription(self, audio_path: Path):
        """Start transcription of recorded audio"""
        def transcribe_thread():
            try:
                self.is_transcribing.set(True)

                # Prepare transcription settings
                transcription_settings = {
                    'language': self.settings.get('language', 'auto') if self.settings.get('language') != 'auto' else None,
                    'task': self.settings.get('task', 'transcribe'),
                    'temperature': self.settings.get('temperature', 0.0)
                }

                # Run transcription
                text = self.transcription_service.transcribe_audio_sync(audio_path, transcription_settings)

                # Create recording object
                recording = Recording(
                    timestamp=datetime.now(),
                    filename=audio_path.name,
                    transcription=text,
                    duration=0.0,  # TODO: Calculate actual duration
                    language="auto",  # TODO: Detect language
                    model_used=self.transcription_service.model_name,
                    file_size=audio_path.stat().st_size if audio_path.exists() else 0
                )

                # Save to database
                self.database.add_recording(recording)

                # Move file to recordings directory
                from whisper.database import get_recordings_directory
                final_path = get_recordings_directory() / audio_path.name
                if self.audio_recorder.move_recording(audio_path, final_path):
                    recording.filename = final_path.name
                    self.database.update_recording(recording)

                # Update UI
                self.root.after(0, lambda: self._load_recordings())

            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Transcription Error", msg))
            finally:
                self.is_transcribing.set(False)
                self.transcription_progress.set(0)

                # Force garbage collection to prevent memory accumulation
                import gc
                gc.collect()

        thread = threading.Thread(target=transcribe_thread, daemon=True)
        thread.start()

    def _transcribe_file(self):
        """Transcribe an audio file selected by user"""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio Files", "*.wav *.mp3 *.m4a *.flac *.ogg"),
                ("All Files", "*.*")
            ]
        )

        if file_path:
            self._start_transcription(Path(file_path))

    def _load_recordings(self):
        """Load recordings from database and display in list"""
        try:
            # Load recordings from database
            recordings = self.database.get_all_recordings(limit=100)

            # Convert to list format for compatibility
            self.recordings = []
            for recording in recordings:
                self.recordings.append({
                    'id': recording.id,
                    'timestamp': recording.timestamp.strftime("%Y-%m-%d %H:%M"),
                    'transcription': recording.transcription,
                    'duration': recording.duration,
                    'language': recording.language
                })

            # Display transcriptions
            self._filter_transcriptions()

        except Exception as e:
            print(f"Error loading recordings: {e}")
            self.recordings = []

    # Callback methods
    def _on_recording_start(self):
        """Called when recording starts"""
        pass

    def _on_recording_stop(self):
        """Called when recording stops"""
        pass

    def _on_transcription_progress(self, progress: float):
        """Called when transcription progress updates"""
        self.transcription_progress.set(progress * 100)

    def _on_transcription_complete(self, text: str):
        """Called when transcription completes"""
        print(f"Transcription complete: {text[:50]}...")

        # Copy transcription to clipboard
        self._copy_to_clipboard(text)

        # Show notification
        self._show_transcription_notification(text)

    def _on_transcription_error(self, error: Exception):
        """Called when transcription error occurs"""
        messagebox.showerror("Transcription Error", str(error))

    # Event handlers
    def _on_search_changed(self, *args):
        """Called when search text changes"""
        self._filter_transcriptions()

    def _filter_transcriptions(self):
        """Filter transcriptions based on search text"""
        search_text = self.search_var.get().lower()

        # Clear current display
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Filter and display transcriptions
        for recording in self.recordings:
            if search_text in recording.get('transcription', '').lower():
                self._add_transcription_item(recording)

    def _add_transcription_item(self, recording):
        """Add a transcription item to the list"""
        # Create item frame with better styling
        item_frame = tk.Frame(self.scrollable_frame, bg='#3a3a3a', relief=tk.FLAT, bd=0)
        item_frame.pack(fill=tk.X, padx=8, pady=4)

        # Inner content frame with padding
        content_frame = tk.Frame(item_frame, bg='#3a3a3a')
        content_frame.pack(fill=tk.X, padx=15, pady=12)

        # Date/time label (smaller, more subtle)
        timestamp = recording.get('timestamp', 'Unknown')
        date_label = tk.Label(content_frame, text=timestamp,
                             bg='#3a3a3a', fg='#888888', font=('Arial', 9))
        date_label.pack(anchor=tk.W, pady=(0, 6))

        # Transcription text (larger, more prominent)
        transcription = recording.get('transcription', 'No transcription')
        text_label = tk.Label(content_frame, text=transcription,
                             bg='#3a3a3a', fg='#ffffff', font=('Arial', 12),
                             wraplength=700, justify=tk.LEFT, anchor='w')
        text_label.pack(anchor=tk.W, fill=tk.X)

        # Add hover effect
        self._add_hover_effect(item_frame, content_frame, date_label, text_label)

    def _clear_all_transcriptions(self):
        """Clear all transcriptions"""
        if messagebox.askyesno("Clear All", "Are you sure you want to clear all transcriptions?"):
            try:
                # Clear from database
                self.database.clear_all_recordings()
                # Clear local list
                self.recordings.clear()
                # Refresh display
                self._filter_transcriptions()
                messagebox.showinfo("Success", "All transcriptions cleared.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear transcriptions: {e}")

    def _clear_search(self):
        """Clear search text"""
        self.search_var.set("")

    def _on_recording_double_click(self, event):
        """Called when recording is double-clicked"""
        pass

    def _on_recording_right_click(self, event):
        """Called when recording is right-clicked"""
        # Select the item under the cursor
        item = self.recordings_tree.identify_row(event.y)
        if item:
            self.recordings_tree.selection_set(item)
            self.recordings_tree.focus(item)

        self.context_menu.post(event.x_root, event.y_root)

    def _on_delete_key(self, event):
        """Called when Delete key is pressed"""
        self._delete_selected_recording()

    def _on_key_press(self, event):
        """Called when any key is pressed in the recordings tree"""
        if event.keysym == 'Delete':
            self._delete_selected_recording()
        elif event.keysym == 'F2':
            # Future: Rename/edit functionality
            pass
        elif event.char.lower() == 'a' and event.state & 0x4:  # Ctrl+A
            # Select all recordings
            for item in self.recordings_tree.get_children():
                self.recordings_tree.selection_add(item)

    # Menu command methods (to be implemented)
    def _play_selected_recording(self):
        """Play selected recording"""
        pass

    def _copy_selected_text(self):
        """Copy selected recording text to clipboard"""
        # Get selected item
        selection = self.recordings_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a recording to copy.")
            return

        # Get recording ID from the selected item
        item = selection[0]
        tags = self.recordings_tree.item(item, 'tags')
        if not tags:
            messagebox.showerror("Error", "Could not identify the selected recording.")
            return

        recording_id = tags[0]

        # Get recording from database
        recording = self.database.get_recording(recording_id)
        if not recording:
            messagebox.showerror("Error", "Recording not found in database.")
            return

        # Copy transcription to clipboard
        if self._copy_to_clipboard(recording.transcription):
            messagebox.showinfo("Success", "Transcription copied to clipboard.")
        else:
            messagebox.showerror("Error", "Failed to copy to clipboard.")

    def _copy_to_clipboard(self, text: str) -> bool:
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

            # Last resort: use tkinter
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.root.update()  # Required for clipboard to work
                print(f"Copied to clipboard via tkinter: {text[:50]}...")
                return True
            except Exception as e:
                print(f"Failed to copy via tkinter: {e}")
                return False

        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            return False

    def _show_transcription_notification(self, text: str):
        """Show notification when transcription is complete"""
        try:
            # Create a simple notification window
            notification = tk.Toplevel(self.root)
            notification.title("Transcription Complete")
            notification.geometry("400x150")
            notification.resizable(False, False)

            # Center the notification
            notification.transient(self.root)
            notification.grab_set()

            # Add content
            frame = ttk.Frame(notification, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(frame, text="✅ Transcription Complete!",
                     font=("Arial", 12, "bold")).pack(pady=(0, 10))

            # Show preview of transcription
            preview = text[:100] + "..." if len(text) > 100 else text
            ttk.Label(frame, text=preview, wraplength=350).pack(pady=(0, 10))

            ttk.Label(frame, text="📋 Text copied to clipboard",
                     font=("Arial", 9)).pack(pady=(0, 10))

            # Close button
            ttk.Button(frame, text="OK",
                      command=notification.destroy).pack()

            # Auto-close after 5 seconds
            notification.after(5000, notification.destroy)

        except Exception as e:
            print(f"Error showing notification: {e}")
            # Fallback to simple message
            messagebox.showinfo("Transcription Complete",
                              f"Text copied to clipboard:\n{text[:100]}...")

    def _export_selected_recording(self):
        """Export selected recording"""
        pass

    def _delete_selected_recording(self):
        """Delete selected recording(s)"""
        # Get selected items
        selection = self.recordings_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select one or more recordings to delete.")
            return

        # Get recording IDs from selected items
        recording_ids = []
        recordings = []

        for item in selection:
            tags = self.recordings_tree.item(item, 'tags')
            if tags:
                recording_id = tags[0]
                recording = self.database.get_recording(recording_id)
                if recording:
                    recording_ids.append(recording_id)
                    recordings.append(recording)

        if not recordings:
            messagebox.showerror("Error", "Could not identify the selected recording(s).")
            return

        # Show confirmation dialog
        if len(recordings) == 1:
            # Single recording deletion
            recording = recordings[0]
            timestamp_str = recording.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            transcription_preview = recording.transcription[:50] + "..." if len(recording.transcription) > 50 else recording.transcription

            confirm_msg = f"Are you sure you want to delete this recording?\n\n"
            confirm_msg += f"Date: {timestamp_str}\n"
            confirm_msg += f"Duration: {recording.duration:.1f}s\n"
            confirm_msg += f"Text: {transcription_preview}\n\n"
            confirm_msg += "This action cannot be undone."

            title = "Confirm Deletion"
        else:
            # Multiple recordings deletion
            confirm_msg = f"Are you sure you want to delete {len(recordings)} recordings?\n\n"
            confirm_msg += "Selected recordings:\n"
            for i, recording in enumerate(recordings[:3]):  # Show first 3
                timestamp_str = recording.timestamp.strftime("%Y-%m-%d %H:%M")
                transcription_preview = recording.transcription[:30] + "..." if len(recording.transcription) > 30 else recording.transcription
                confirm_msg += f"• {timestamp_str}: {transcription_preview}\n"

            if len(recordings) > 3:
                confirm_msg += f"• ... and {len(recordings) - 3} more\n"

            confirm_msg += "\nThis action cannot be undone."
            title = f"Confirm Deletion of {len(recordings)} Recordings"

        if not messagebox.askyesno(title, confirm_msg, icon='warning'):
            return

        try:
            deleted_files = 0
            failed_files = 0
            deleted_db = 0
            failed_db = 0

            for recording in recordings:
                try:
                    # Delete the audio file if it exists
                    file_path = recording.file_path
                    if file_path.exists():
                        file_path.unlink()
                        deleted_files += 1
                        print(f"Deleted audio file: {file_path}")

                    # Delete from database
                    if self.database.delete_recording(recording.id):
                        deleted_db += 1
                        print(f"Deleted recording from database: {recording.id}")
                    else:
                        failed_db += 1
                        print(f"Failed to delete recording from database: {recording.id}")

                except Exception as e:
                    failed_files += 1
                    failed_db += 1
                    print(f"Error deleting recording {recording.id}: {e}")

            # Refresh the recordings list
            self._load_recordings()

            # Show result message
            if len(recordings) == 1:
                if deleted_db > 0:
                    messagebox.showinfo("Success", "Recording deleted successfully.")
                else:
                    messagebox.showerror("Error", "Failed to delete recording.")
            else:
                success_msg = f"Deletion completed:\n\n"
                success_msg += f"• Database: {deleted_db} deleted"
                if failed_db > 0:
                    success_msg += f", {failed_db} failed"
                success_msg += f"\n• Audio files: {deleted_files} deleted"
                if failed_files > 0:
                    success_msg += f", {failed_files} failed"

                if failed_db > 0 or failed_files > 0:
                    messagebox.showwarning("Partial Success", success_msg)
                else:
                    messagebox.showinfo("Success", success_msg)

        except Exception as e:
            print(f"Error deleting recordings: {e}")
            messagebox.showerror("Error", f"Failed to delete recordings: {e}")

    def _export_all_recordings(self):
        """Export all recordings"""
        pass

    def _import_recordings(self):
        """Import recordings"""
        pass

    def _clear_all_recordings(self):
        """Clear all recordings"""
        # Get count of recordings for confirmation
        stats = self.database.get_statistics()
        total_recordings = stats.get('total_recordings', 0)

        if total_recordings == 0:
            messagebox.showinfo("No Recordings", "There are no recordings to delete.")
            return

        # Show confirmation dialog
        confirm_msg = f"Are you sure you want to delete ALL {total_recordings} recordings?\n\n"
        confirm_msg += "This will permanently delete:\n"
        confirm_msg += f"• {total_recordings} recording(s) from the database\n"
        confirm_msg += f"• All associated audio files\n\n"
        confirm_msg += "This action cannot be undone!"

        if not messagebox.askyesno("Confirm Delete All", confirm_msg, icon='warning'):
            return

        # Double confirmation for safety
        if not messagebox.askyesno("Final Confirmation",
                                   "This is your final warning!\n\n"
                                   "ALL recordings will be permanently deleted.\n\n"
                                   "Are you absolutely sure?",
                                   icon='warning'):
            return

        try:
            # Get all recordings to delete their files
            all_recordings = self.database.get_all_recordings()
            deleted_files = 0
            failed_files = 0

            # Delete audio files
            for recording in all_recordings:
                try:
                    file_path = recording.file_path
                    if file_path.exists():
                        file_path.unlink()
                        deleted_files += 1
                        print(f"Deleted audio file: {file_path}")
                except Exception as e:
                    failed_files += 1
                    print(f"Failed to delete audio file {recording.filename}: {e}")

            # Delete all recordings from database
            if self.database.delete_all_recordings():
                print("All recordings deleted from database")

                # Refresh the recordings list
                self._load_recordings()

                # Show success message
                success_msg = f"Successfully deleted all recordings!\n\n"
                success_msg += f"• Database: {total_recordings} recording(s) deleted\n"
                success_msg += f"• Audio files: {deleted_files} deleted"
                if failed_files > 0:
                    success_msg += f", {failed_files} failed"

                messagebox.showinfo("Success", success_msg)
            else:
                messagebox.showerror("Error", "Failed to delete recordings from database.")

        except Exception as e:
            print(f"Error clearing all recordings: {e}")
            messagebox.showerror("Error", f"Failed to clear recordings: {e}")

    def _show_preferences(self):
        """Show preferences dialog"""
        result = show_settings_dialog(self.root, self.settings)
        if result:
            self._apply_settings(result)

    def _show_audio_devices(self):
        """Show audio devices dialog"""
        # Show just the audio tab of settings
        result = show_settings_dialog(self.root, self.settings)
        if result:
            self._apply_settings(result)

    def _apply_settings(self, new_settings: Dict[str, Any]):
        """Apply new settings to the application"""
        try:
            # Update internal settings
            self.settings.update(new_settings)

            # Apply model change
            if 'model' in new_settings:
                model = new_settings['model']
                if model != self.transcription_service.model_name:
                    self.transcription_service.change_model(model)
                    print(f"Changed model to: {model}")

            # Apply device change (CPU/GPU)
            if 'device' in new_settings:
                device = new_settings['device']
                if device != self.transcription_service.device:
                    self.transcription_service.change_device(device)
                    print(f"Changed processing device to: {device}")

            # Apply audio device change
            if 'audio_device' in new_settings:
                device_index = new_settings['audio_device']
                if device_index is not None:
                    # Store for use in recording
                    self.settings['audio_device'] = device_index
                    print(f"Selected audio device: {new_settings.get('audio_device_name', 'Unknown')}")

            # Update hotkeys if they changed
            if 'record_hotkey' in new_settings or 'window_hotkey' in new_settings:
                self._update_hotkeys()

            # Save settings to persistent storage
            if self.config_manager.save_settings(self.settings):
                print("Settings saved successfully")
            else:
                print("Warning: Failed to save settings to file")

            print("Settings applied successfully")

        except Exception as e:
            messagebox.showerror("Settings Error", f"Failed to apply settings: {e}")

    def _on_closing(self):
        """Handle application closing - save settings and cleanup"""
        try:
            # Save current window geometry and position
            geometry = self.root.geometry()
            if '+' in geometry:
                size_part, position_part = geometry.split('+', 1)
                self.settings['window_geometry'] = size_part
                self.settings['window_position'] = position_part
            else:
                self.settings['window_geometry'] = geometry

            # Save final settings
            self.config_manager.save_settings(self.settings)
            print("Settings saved on exit")

            # Cleanup hotkey manager
            if hasattr(self, 'hotkey_manager'):
                self.hotkey_manager.cleanup()
                print("Hotkey manager cleaned up")

        except Exception as e:
            print(f"Error saving settings on exit: {e}")
        finally:
            # Close the application
            self.root.destroy()

    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About OpenSuperWhisper",
            "OpenSuperWhisper for Windows\n\n"
            "A real-time speech transcription application\n"
            "based on OpenAI Whisper\n\n"
            "Version 1.0.0"
        )

    def run(self):
        """Run the application"""
        try:
            self.root.mainloop()
        finally:
            # Cleanup
            self.audio_recorder.cleanup()
            self.transcription_service.cleanup()


def main():
    """Main entry point"""
    app = OpenSuperWhisperGUI()
    app.run()


if __name__ == "__main__":
    main()
