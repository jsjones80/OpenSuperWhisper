"""
Test script to check if all imports work correctly
"""

import sys
import os

print("Testing imports...")

try:
    print("1. Testing basic imports...")
    import tkinter as tk
    print("✓ tkinter")
    
    import numpy as np
    print("✓ numpy")
    
    import torch
    print("✓ torch")
    
    print("2. Testing whisper imports...")
    import whisper
    print("✓ whisper")
    
    print("3. Testing custom modules...")
    from whisper.audio_recorder import AudioRecorder
    print("✓ audio_recorder")
    
    from whisper.transcription_service import get_transcription_service
    print("✓ transcription_service")
    
    from whisper.database import get_database, Recording
    print("✓ database")
    
    from whisper.hotkeys import get_hotkey_manager
    print("✓ hotkeys")
    
    print("4. Testing audio libraries...")
    try:
        import sounddevice as sd
        print("✓ sounddevice")
    except ImportError as e:
        print(f"✗ sounddevice: {e}")
    
    try:
        import pyaudio
        print("✓ pyaudio")
    except ImportError as e:
        print(f"✗ pyaudio: {e}")
    
    print("5. Testing Windows libraries...")
    try:
        import pynput
        print("✓ pynput")
    except ImportError as e:
        print(f"✗ pynput: {e}")
    
    try:
        import win32api
        print("✓ win32api")
    except ImportError as e:
        print(f"✗ win32api: {e}")
    
    print("\n✅ All core imports successful!")
    
    print("6. Testing basic functionality...")
    
    # Test audio recorder
    recorder = AudioRecorder()
    devices = recorder.get_audio_devices()
    print(f"✓ Found {len(devices)} audio devices")
    
    # Test transcription service
    service = get_transcription_service()
    models = service.get_available_models()
    print(f"✓ Available models: {', '.join(models)}")
    
    # Test database
    db = get_database()
    stats = db.get_statistics()
    print(f"✓ Database initialized, {stats.get('total_recordings', 0)} recordings")
    
    # Test hotkeys
    hotkey_manager = get_hotkey_manager()
    available = hotkey_manager.is_available()
    print(f"✓ Global hotkeys {'available' if available else 'not available'}")
    
    print("\n🎉 All tests passed! The application should work correctly.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
