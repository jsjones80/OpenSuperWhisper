"""
Setup script for OpenSuperWhisper Windows
"""

import os
import sys
import subprocess
from pathlib import Path
from setuptools import setup, find_packages

# Read version from whisper package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'whisper'))
from version import __version__

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Core requirements
requirements = [
    # Core Whisper dependencies
    "numba",
    "numpy",
    "torch",
    "tqdm",
    "more-itertools",
    "tiktoken",
    "triton>=2.0.0;platform_machine=='x86_64' and sys_platform=='linux' or sys_platform=='linux2'",
    
    # Audio processing
    "sounddevice>=0.4.6",
    "pyaudio>=0.2.11",
    
    # GUI and system integration
    "pynput>=1.7.6",
    "plyer>=2.1.0",
]

# Windows-specific requirements
windows_requirements = [
    "pywin32>=306;sys_platform=='win32'",
    "torch-directml>=0.2.0.dev230426;sys_platform=='win32'",
]

# Development requirements
dev_requirements = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
]

# Add Windows requirements if on Windows
if sys.platform == "win32":
    requirements.extend(windows_requirements)

setup(
    name="opensuperwhisper-windows",
    version=__version__,
    description="Real-time speech transcription for Windows using OpenAI Whisper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="OpenSuperWhisper Team",
    author_email="",
    url="https://github.com/opensuperwhisper/windows",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "windows": windows_requirements,
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="speech recognition, transcription, whisper, ai, windows",
    entry_points={
        "console_scripts": [
            "opensuperwhisper=opensuperwhisper_gui:main",
            "osw=opensuperwhisper_gui:main",
        ],
    },
    package_data={
        "whisper": [
            "assets/*",
            "normalizers/*.json",
        ],
    },
    zip_safe=False,
)


def install_system_dependencies():
    """Install system dependencies that can't be handled by pip"""
    print("Checking system dependencies...")
    
    # Check for FFmpeg (required for audio processing)
    try:
        subprocess.run(["ffmpeg", "-version"], 
                      capture_output=True, check=True)
        print("✓ FFmpeg found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ FFmpeg not found. Please install FFmpeg:")
        print("  Download from: https://ffmpeg.org/download.html")
        print("  Or use chocolatey: choco install ffmpeg")
        print("  Or use winget: winget install FFmpeg")
    
    # Check for Visual C++ Redistributable (required for some audio libraries)
    if sys.platform == "win32":
        print("Note: Some audio libraries may require Visual C++ Redistributable")
        print("Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe")


def post_install_setup():
    """Perform post-installation setup"""
    print("\nPost-installation setup...")
    
    # Create necessary directories
    directories = [
        "recordings",
        "models",
        "logs",
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    # Download default model
    print("\nDownloading default Whisper model...")
    try:
        import whisper
        model = whisper.load_model("base")
        print("✓ Default model downloaded successfully")
    except Exception as e:
        print(f"⚠ Failed to download default model: {e}")
        print("You can download it later from the application")
    
    print("\nSetup complete! You can now run:")
    print("  opensuperwhisper")
    print("  or")
    print("  python opensuperwhisper_gui.py")


if __name__ == "__main__":
    # Check if this is being run as a script (not during pip install)
    if len(sys.argv) > 1 and sys.argv[1] in ["install", "develop"]:
        # Run normal setup
        pass
    else:
        # Run post-install setup
        install_system_dependencies()
        post_install_setup()
