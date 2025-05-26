"""
Quick fix to manually set the working Scarlett Solo device index
"""

import sys
import os

# Add whisper module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from whisper.audio_recorder import AudioRecorder

def find_working_scarlett():
    """Find the working Scarlett Solo device index"""
    print("Finding working Scarlett Solo device...")
    
    recorder = AudioRecorder()
    devices = recorder.get_audio_devices()
    
    # Find all Scarlett devices
    scarlett_devices = [d for d in devices if 'Scarlett Solo' in d['name']]
    
    print(f"Found {len(scarlett_devices)} Scarlett Solo devices:")
    for device in scarlett_devices:
        print(f"  Index {device['index']}: {device['name']} ({device['channels']} ch)")
    
    # Test each one
    for device in scarlett_devices:
        print(f"\nTesting device {device['index']}...")
        try:
            success = recorder.start_recording(device['index'])
            if success:
                print(f"✅ SUCCESS! Device {device['index']} works!")
                import time
                time.sleep(1)
                path = recorder.stop_recording()
                if path:
                    print(f"Recording saved: {path}")
                    return device['index']
                else:
                    print("Failed to save recording")
            else:
                print(f"❌ Device {device['index']} failed to start")
        except Exception as e:
            print(f"❌ Device {device['index']} exception: {e}")
    
    return None

if __name__ == "__main__":
    working_index = find_working_scarlett()
    if working_index is not None:
        print(f"\n🎉 WORKING DEVICE INDEX: {working_index}")
        print(f"Use this index in your settings!")
    else:
        print("\n❌ No working Scarlett Solo device found")
    
    input("\nPress Enter to exit...")
