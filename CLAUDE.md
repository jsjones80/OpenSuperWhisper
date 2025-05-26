# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenSuperWhisper is a Windows-native real-time speech transcription application built on OpenAI's Whisper ASR model. It provides GUI-based audio recording and transcription with global hotkey support.

## Common Development Commands

### Installation
```bash
# Create and activate virtual environment
python -m venv opensuperwhisper_env
opensuperwhisper_env\Scripts\activate

# Install in development mode
pip install -r requirements.txt
pip install -e .
```

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_transcribe.py

# Run with verbose output
pytest -v tests/

# Test installation integrity
python test_installation.py
```

### Running the Application
```bash
# Main GUI application (Tkinter)
python opensuperwhisper_gui.py

# Alternative PyQt6 GUI
python opensuperwhisper_gui_pyqt6.py
```

## High-Level Architecture

### Core Services Architecture
The application uses a service-oriented architecture with these key components:

1. **AudioRecorder** (`whisper/audio_recorder.py`): 
   - Manages Windows audio capture using sounddevice/pyaudio
   - Records at 16kHz sample rate to WAV files
   - Handles device enumeration and selection

2. **TranscriptionService** (`whisper/transcription_service.py`):
   - Manages Whisper model loading and caching
   - Handles async transcription with progress callbacks
   - Supports GPU (CUDA/DirectML) and CPU inference

3. **Database** (`whisper/database.py`):
   - SQLite-based storage for recordings and transcriptions
   - Implements full-text search capabilities
   - Handles automatic cleanup based on retention policies

4. **HotkeyManager** (`whisper/hotkeys.py`):
   - Windows global hotkey registration using pynput
   - System-wide recording control without focus

### GUI Event Flow
1. User triggers recording via GUI button or global hotkey
2. AudioRecorder captures audio to temporary WAV file
3. On stop, TranscriptionService processes the audio asynchronously
4. Results are stored in SQLite database
5. GUI updates with transcription result and recording history

### Model Loading Strategy
- Models are loaded on-demand and cached in memory
- Default model: "turbo" (fastest, good accuracy)
- Supports all Whisper model sizes: tiny, base, small, medium, large, turbo
- GPU acceleration automatically detected and used when available

## Key Implementation Details

### Audio Recording
- Uses sounddevice library with fallback to pyaudio
- Records mono audio at 16kHz (Whisper's expected format)
- Stores recordings in `recordings/` directory with timestamp filenames

### Database Schema
```sql
recordings (
    id INTEGER PRIMARY KEY,
    filename TEXT,
    transcription TEXT,
    timestamp DATETIME,
    duration REAL,
    language TEXT,
    model_name TEXT
)
```

### Configuration
- Settings stored in `~/.opensuperwhisper/config.json`
- Configurable: model selection, GPU usage, hotkeys, retention policy
- GUI preferences dialog for user configuration

### Testing Approach
- Unit tests use pytest framework
- Test audio files in `tests/` directory
- Mock audio devices for CI compatibility
- Installation verification scripts for deployment