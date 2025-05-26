"""
Test script to verify OpenSuperWhisper installation
Run this script to check if all components are working correctly
"""

import sys
import os
import traceback
from pathlib import Path

def test_python_version():
    """Test Python version compatibility"""
    print("Testing Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def test_core_imports():
    """Test core library imports"""
    print("\nTesting core imports...")
    
    tests = [
        ("numpy", "NumPy"),
        ("torch", "PyTorch"),
        ("tqdm", "tqdm"),
        ("tiktoken", "tiktoken"),
    ]
    
    all_passed = True
    for module, name in tests:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError as e:
            print(f"✗ {name} - {e}")
            all_passed = False
    
    return all_passed

def test_audio_libraries():
    """Test audio processing libraries"""
    print("\nTesting audio libraries...")
    
    tests = [
        ("sounddevice", "SoundDevice"),
        ("pyaudio", "PyAudio"),
    ]
    
    passed = 0
    for module, name in tests:
        try:
            __import__(module)
            print(f"✓ {name}")
            passed += 1
        except ImportError as e:
            print(f"✗ {name} - {e}")
    
    if passed == 0:
        print("⚠ No audio libraries available - audio recording will not work")
        return False
    elif passed < len(tests):
        print(f"⚠ Only {passed}/{len(tests)} audio libraries available - some features may not work")
    
    return True

def test_windows_libraries():
    """Test Windows-specific libraries"""
    print("\nTesting Windows libraries...")
    
    if sys.platform != "win32":
        print("⚠ Not running on Windows - skipping Windows-specific tests")
        return True
    
    tests = [
        ("pynput", "PyInput (for global hotkeys)"),
        ("win32api", "PyWin32 (for Windows integration)"),
        ("plyer", "Plyer (for notifications)"),
    ]
    
    all_passed = True
    for module, name in tests:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError as e:
            print(f"✗ {name} - {e}")
            all_passed = False
    
    return all_passed

def test_whisper_module():
    """Test Whisper module"""
    print("\nTesting Whisper module...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        import whisper
        print("✓ Whisper module imported")
        
        # Test available models
        models = whisper.available_models()
        print(f"✓ Available models: {', '.join(models)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Whisper module - {e}")
        return False

def test_custom_modules():
    """Test custom OpenSuperWhisper modules"""
    print("\nTesting custom modules...")
    
    modules = [
        ("whisper.audio_recorder", "Audio Recorder"),
        ("whisper.transcription_service", "Transcription Service"),
        ("whisper.database", "Database"),
        ("whisper.hotkeys", "Global Hotkeys"),
    ]
    
    all_passed = True
    for module, name in modules:
        try:
            __import__(module)
            print(f"✓ {name}")
        except Exception as e:
            print(f"✗ {name} - {e}")
            all_passed = False
    
    return all_passed

def test_gpu_support():
    """Test GPU acceleration support"""
    print("\nTesting GPU support...")
    
    try:
        import torch
        
        # Test CUDA
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown"
            print(f"✓ CUDA available - {device_count} device(s), Primary: {device_name}")
            return True
        
        # Test DirectML (Windows)
        if sys.platform == "win32":
            try:
                import torch_directml
                if torch_directml.is_available():
                    print("✓ DirectML available")
                    return True
            except ImportError:
                pass
        
        print("⚠ No GPU acceleration available - will use CPU (slower)")
        return True
        
    except Exception as e:
        print(f"✗ GPU test failed - {e}")
        return False

def test_audio_devices():
    """Test audio device detection"""
    print("\nTesting audio devices...")
    
    try:
        # Try sounddevice first
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            print(f"✓ SoundDevice found {len(input_devices)} input device(s)")
            return True
        except:
            pass
        
        # Try pyaudio
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            device_count = pa.get_device_count()
            input_devices = []
            for i in range(device_count):
                device_info = pa.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    input_devices.append(device_info)
            pa.terminate()
            print(f"✓ PyAudio found {len(input_devices)} input device(s)")
            return True
        except:
            pass
        
        print("✗ No audio devices detected")
        return False
        
    except Exception as e:
        print(f"✗ Audio device test failed - {e}")
        return False

def test_gui():
    """Test GUI components"""
    print("\nTesting GUI...")
    
    try:
        import tkinter as tk
        
        # Test basic tkinter
        root = tk.Tk()
        root.withdraw()  # Hide window
        root.destroy()
        print("✓ Tkinter GUI available")
        
        # Test ttk
        from tkinter import ttk
        print("✓ TTK themes available")
        
        return True
        
    except Exception as e:
        print(f"✗ GUI test failed - {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\nTesting database...")
    
    try:
        import sqlite3
        
        # Test database creation
        test_db = Path("test_db.sqlite")
        conn = sqlite3.connect(test_db)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        conn.close()
        
        # Clean up
        test_db.unlink()
        
        print("✓ SQLite database functionality")
        return True
        
    except Exception as e:
        print(f"✗ Database test failed - {e}")
        return False

def main():
    """Run all tests"""
    print("OpenSuperWhisper Installation Test")
    print("=" * 50)
    
    tests = [
        test_python_version,
        test_core_imports,
        test_audio_libraries,
        test_windows_libraries,
        test_whisper_module,
        test_custom_modules,
        test_gpu_support,
        test_audio_devices,
        test_gui,
        test_database,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! OpenSuperWhisper should work correctly.")
        print("\nYou can now run: python opensuperwhisper_gui.py")
    elif passed >= total * 0.8:
        print("⚠ Most tests passed. Some features may not work optimally.")
        print("Check the failed tests above and install missing dependencies.")
    else:
        print("❌ Many tests failed. Please check your installation.")
        print("Run the installation script again or install missing dependencies manually.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
