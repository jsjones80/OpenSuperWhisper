"""
Test script to check available audio devices
"""

import sys
import os

# Add whisper module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from whisper.audio_recorder import AudioRecorder

def test_audio_devices():
    """Test and display available audio devices"""
    print("Testing Audio Devices")
    print("=" * 50)
    
    try:
        recorder = AudioRecorder()
        devices = recorder.get_audio_devices()
        
        if not devices:
            print("❌ No audio input devices found!")
            return False
        
        print(f"✅ Found {len(devices)} audio input device(s):")
        print()
        
        for i, device in enumerate(devices):
            print(f"Device {i + 1}:")
            print(f"  Index: {device['index']}")
            print(f"  Name: {device['name']}")
            print(f"  Channels: {device['channels']}")
            print(f"  Sample Rate: {device['sample_rate']}")
            print()
        
        # Test recording with default device
        print("Testing recording with default device...")
        success = recorder.start_recording()
        if success:
            print("✅ Recording started successfully!")
            import time
            time.sleep(1)  # Record for 1 second
            path = recorder.stop_recording()
            if path:
                print(f"✅ Recording saved to: {path}")
                print(f"✅ File size: {path.stat().st_size} bytes")
            else:
                print("❌ Failed to save recording")
        else:
            print("❌ Failed to start recording with default device")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing audio devices: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_audio_devices()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
