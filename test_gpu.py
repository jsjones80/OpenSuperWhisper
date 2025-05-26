"""
Test script to check GPU availability and compatibility
"""

import sys
import os

# Add whisper module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_gpu_availability():
    """Test GPU availability for different backends"""
    print("GPU Availability Test")
    print("=" * 50)
    
    # Test PyTorch CUDA
    print("\n1. Testing PyTorch CUDA:")
    try:
        import torch
        print(f"   PyTorch version: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA version: {torch.version.cuda}")
            print(f"   GPU count: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
                print(f"   GPU {i} memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB")
        else:
            print("   ❌ CUDA not available")
    except ImportError:
        print("   ❌ PyTorch not installed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test DirectML
    print("\n2. Testing DirectML:")
    try:
        import torch_directml
        print(f"   torch-directml available: True")
        print(f"   DirectML device count: {torch_directml.device_count()}")
        for i in range(torch_directml.device_count()):
            device = torch_directml.device(i)
            print(f"   DirectML device {i}: {device}")
    except ImportError:
        print("   ❌ torch-directml not installed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test system GPU info
    print("\n3. System GPU Information:")
    try:
        import subprocess
        result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header
                line = line.strip()
                if line:
                    print(f"   GPU: {line}")
        else:
            print("   ❌ Could not get GPU info")
    except Exception as e:
        print(f"   ❌ Error getting system GPU info: {e}")
    
    # Test Whisper with different devices
    print("\n4. Testing Whisper Model Loading:")
    try:
        from whisper.transcription_service import TranscriptionService
        
        # Test CPU
        print("   Testing CPU...")
        service_cpu = TranscriptionService(device='cpu')
        print("   ✅ CPU model loading works")
        
        # Test CUDA if available
        if torch.cuda.is_available():
            print("   Testing CUDA...")
            try:
                service_cuda = TranscriptionService(device='cuda')
                print("   ✅ CUDA model loading works")
            except Exception as e:
                print(f"   ❌ CUDA model loading failed: {e}")
        
        # Test DirectML if available
        try:
            import torch_directml
            print("   Testing DirectML...")
            service_directml = TranscriptionService(device='directml')
            print("   ✅ DirectML model loading works")
        except ImportError:
            print("   ⚠️ DirectML not available (torch-directml not installed)")
        except Exception as e:
            print(f"   ❌ DirectML model loading failed: {e}")
            
    except Exception as e:
        print(f"   ❌ Error testing Whisper: {e}")
    
    # Recommendations
    print("\n5. Recommendations:")
    
    if not torch.cuda.is_available():
        print("   🔧 To enable CUDA:")
        print("      - Install NVIDIA GPU drivers")
        print("      - Install CUDA toolkit")
        print("      - Reinstall PyTorch with CUDA support:")
        print("        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
    
    try:
        import torch_directml
    except ImportError:
        print("   🔧 To enable DirectML:")
        print("      - Install torch-directml:")
        print("        pip install torch-directml")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_gpu_availability()
    input("\nPress Enter to exit...")
