# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Get the project root directory
project_root = Path(SPECPATH)

a = Analysis(
    ['opensuperwhisper_gui_pyqt6.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include whisper assets
        ('whisper/assets/*', 'whisper/assets'),
        # Include any other data files
        ('*.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'whisper',
        'whisper.audio',
        'whisper.audio_recorder',
        'whisper.transcription_service',
        'whisper.database',
        'whisper.config_manager',
        'whisper.hotkeys',
        'whisper.settings_dialog',
        'whisper.windows_utils',
        'preferences_dialog',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'sounddevice',
        'pyaudio',
        'numpy',
        'torch',
        'tqdm',
        'numba',
        'tiktoken',
        'regex',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        'scipy',
        'scipy.signal',
        'win32api',
        'win32con',
        'win32gui',
        'win32process',
        'pywintypes',
        'pyperclip',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'notebook',
        'ipython',
        'jupyter',
        'test',
        'tests',
        'recordings',
        'recordings.db',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OpenSuperWhisper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='opensuperwhisper.ico',  # We'll create this icon file
    version='version_info.txt',  # We'll create this version file
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OpenSuperWhisper',
)