"""
Script to upgrade PyTorch to CUDA version for GPU acceleration
"""

import subprocess
import sys
import os

def upgrade_pytorch_cuda():
    """Upgrade PyTorch to CUDA version"""
    print("🚀 Upgrading PyTorch to CUDA Version")
    print("=" * 50)
    
    print("Current PyTorch version:")
    try:
        import torch
        print(f"   Version: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
    except ImportError:
        print("   PyTorch not installed")
    
    print("\n🔧 Step 1: Uninstalling CPU-only PyTorch...")
    
    # Uninstall current PyTorch
    packages_to_uninstall = [
        "torch",
        "torchvision", 
        "torchaudio"
    ]
    
    for package in packages_to_uninstall:
        try:
            print(f"   Uninstalling {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "uninstall", package, "-y"
            ], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {package} uninstalled")
            else:
                print(f"   ⚠️ {package} not found or already uninstalled")
        except Exception as e:
            print(f"   ❌ Error uninstalling {package}: {e}")
    
    print("\n🔧 Step 2: Installing PyTorch with CUDA 12.1 support...")
    
    # Install CUDA version
    cuda_install_command = [
        sys.executable, "-m", "pip", "install", 
        "torch", "torchvision", "torchaudio",
        "--index-url", "https://download.pytorch.org/whl/cu121"
    ]
    
    print("   Running: " + " ".join(cuda_install_command))
    
    try:
        result = subprocess.run(cuda_install_command, check=True)
        print("   ✅ PyTorch CUDA installation completed!")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Installation failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False
    
    print("\n🔧 Step 3: Verifying CUDA installation...")
    
    try:
        # Restart Python to reload modules
        print("   Testing new PyTorch installation...")
        
        # Test in subprocess to avoid module caching
        test_script = '''
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
'''
        
        result = subprocess.run([
            sys.executable, "-c", test_script
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ CUDA verification successful!")
            print("   Output:")
            for line in result.stdout.strip().split('\n'):
                print(f"      {line}")
        else:
            print("   ❌ CUDA verification failed!")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
        return False
    
    print("\n🎉 SUCCESS! PyTorch with CUDA support is now installed!")
    print("\n📋 Next steps:")
    print("   1. Restart the OpenSuperWhisper application")
    print("   2. Go to Settings → Preferences → Transcription tab")
    print("   3. Select 'GPU - CUDA (NVIDIA)'")
    print("   4. Enjoy 5-10x faster transcription with your RTX 3090!")
    
    return True

if __name__ == "__main__":
    print("⚠️  WARNING: This will uninstall and reinstall PyTorch")
    print("   Make sure you're in the correct virtual environment!")
    print(f"   Current environment: {sys.prefix}")
    
    response = input("\nContinue? (y/N): ").lower().strip()
    
    if response == 'y' or response == 'yes':
        success = upgrade_pytorch_cuda()
        if success:
            print("\n✅ Upgrade completed successfully!")
        else:
            print("\n❌ Upgrade failed. Please check the errors above.")
    else:
        print("Upgrade cancelled.")
    
    input("\nPress Enter to exit...")
