"""
Test script specifically for Scarlett Solo USB compatibility
"""

import sys
import os

# Add whisper module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from whisper.audio_recorder import AudioRecorder

def test_scarlett_solo():
    """Test Scarlett Solo USB specifically"""
    print("Testing Scarlett Solo USB Compatibility")
    print("=" * 50)
    
    try:
        recorder = AudioRecorder()
        devices = recorder.get_audio_devices()
        
        # Find Scarlett Solo devices
        scarlett_devices = [d for d in devices if 'Scarlett Solo' in d['name']]
        
        if not scarlett_devices:
            print("❌ No Scarlett Solo USB devices found!")
            return False
        
        print(f"✅ Found {len(scarlett_devices)} Scarlett Solo device(s):")
        for device in scarlett_devices:
            print(f"  Index: {device['index']}")
            print(f"  Name: {device['name']}")
            print(f"  Channels: {device['channels']}")
            print(f"  Sample Rate: {device['sample_rate']}")
            print()
        
        # Test each Scarlett device
        for device in scarlett_devices:
            print(f"Testing device {device['index']}: {device['name']}")
            
            try:
                success = recorder.start_recording(device['index'])
                if success:
                    print(f"✅ Recording started successfully with device {device['index']}!")
                    import time
                    time.sleep(2)  # Record for 2 seconds
                    path = recorder.stop_recording()
                    if path:
                        print(f"✅ Recording saved to: {path}")
                        print(f"✅ File size: {path.stat().st_size} bytes")
                        return True
                    else:
                        print("❌ Failed to save recording")
                else:
                    print(f"❌ Failed to start recording with device {device['index']}")
                    
            except Exception as e:
                print(f"❌ Exception with device {device['index']}: {e}")
                import traceback
                traceback.print_exc()
        
        return False
        
    except Exception as e:
        print(f"❌ Error testing Scarlett Solo: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_scarlett_solo()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
