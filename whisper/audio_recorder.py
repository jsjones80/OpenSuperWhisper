"""
Windows Audio Recording Module for OpenSuperWhisper
Handles real-time microphone recording with Windows-specific optimizations
"""

import os
import sys
import time
import threading
import tempfile
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List
import numpy as np

try:
    import sounddevice as sd
    import pyaudio
    AUDIO_BACKEND = "sounddevice"
except ImportError:
    try:
        import pyaudio
        AUDIO_BACKEND = "pyaudio"
    except ImportError:
        AUDIO_BACKEND = None

if sys.platform == "win32":
    try:
        import winsound
        WINSOUND_AVAILABLE = True
    except ImportError:
        WINSOUND_AVAILABLE = False
else:
    WINSOUND_AVAILABLE = False


class AudioRecorder:
    """Windows-optimized audio recorder for real-time microphone capture"""

    # Audio settings optimized for Whisper
    SAMPLE_RATE = 16000
    CHANNELS = 1
    CHUNK_SIZE = 1024
    FORMAT = pyaudio.paInt16 if 'pyaudio' in sys.modules else None

    def __init__(self):
        self.is_recording = False
        self.is_playing = False
        self.current_recording_path: Optional[Path] = None
        self.current_playing_path: Optional[Path] = None

        # Audio stream objects
        self._audio_stream = None
        self._audio_interface = None
        self._recording_thread = None
        self._audio_data = []

        # Working audio configuration (may differ from target config)
        self._working_channels = self.CHANNELS
        self._working_rate = self.SAMPLE_RATE

        # Callbacks
        self.on_recording_start: Optional[Callable] = None
        self.on_recording_stop: Optional[Callable] = None
        self.on_audio_chunk: Optional[Callable[[np.ndarray], None]] = None

        # Initialize audio backend
        self._init_audio_backend()

        # Create recordings directory
        from .database import get_recordings_directory
        self.recordings_dir = get_recordings_directory()

        # Temporary directory for active recordings
        self.temp_dir = Path(tempfile.gettempdir()) / "opensuperwhisper"
        self.temp_dir.mkdir(exist_ok=True)

    def _init_audio_backend(self):
        """Initialize the audio backend (sounddevice or pyaudio)"""
        if AUDIO_BACKEND == "sounddevice":
            self._init_sounddevice()
        elif AUDIO_BACKEND == "pyaudio":
            self._init_pyaudio()
        else:
            raise RuntimeError("No audio backend available. Please install sounddevice or pyaudio.")

    def _init_sounddevice(self):
        """Initialize sounddevice backend"""
        try:
            # Set default device and sample rate
            sd.default.samplerate = self.SAMPLE_RATE
            sd.default.channels = self.CHANNELS

            # Test if we can query devices
            devices = sd.query_devices()
            if not devices:
                raise RuntimeError("No audio devices found")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize sounddevice: {e}")

    def _init_pyaudio(self):
        """Initialize pyaudio backend"""
        try:
            # Clean up any existing interface first
            if hasattr(self, '_audio_interface') and self._audio_interface:
                try:
                    self._audio_interface.terminate()
                except:
                    pass
                self._audio_interface = None

            self._audio_interface = pyaudio.PyAudio()

            # Test if we can get device info
            device_count = self._audio_interface.get_device_count()
            if device_count == 0:
                raise RuntimeError("No audio devices found")

        except Exception as e:
            if self._audio_interface:
                self._audio_interface.terminate()
                self._audio_interface = None
            raise RuntimeError(f"Failed to initialize pyaudio: {e}")

    def get_audio_devices(self) -> List[dict]:
        """Get list of available audio input devices"""
        devices = []

        if AUDIO_BACKEND == "sounddevice":
            try:
                device_list = sd.query_devices()
                for i, device in enumerate(device_list):
                    if device['max_input_channels'] > 0:
                        devices.append({
                            'index': i,
                            'name': device['name'],
                            'channels': device['max_input_channels'],
                            'sample_rate': device['default_samplerate']
                        })
            except Exception as e:
                print(f"Error querying sounddevice devices: {e}")

        elif AUDIO_BACKEND == "pyaudio" and self._audio_interface:
            try:
                for i in range(self._audio_interface.get_device_count()):
                    device_info = self._audio_interface.get_device_info_by_index(i)
                    if device_info['maxInputChannels'] > 0:
                        devices.append({
                            'index': i,
                            'name': device_info['name'],
                            'channels': device_info['maxInputChannels'],
                            'sample_rate': device_info['defaultSampleRate']
                        })
            except Exception as e:
                print(f"Error querying pyaudio devices: {e}")

        return devices

    def start_recording(self, device_index: Optional[int] = None) -> bool:
        """Start recording audio from microphone"""
        if self.is_recording:
            print("Already recording")
            return False

        try:
            # Generate temporary file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_recording_path = self.temp_dir / f"recording_{timestamp}.wav"

            # Clear audio data buffer
            self._audio_data = []

            # Validate device index
            if device_index is not None:
                devices = self.get_audio_devices()
                valid_indices = [d['index'] for d in devices]
                if device_index not in valid_indices:
                    print(f"Invalid device index {device_index}. Available: {valid_indices}")
                    device_index = None  # Fall back to default

            print(f"Starting recording with device index: {device_index}")

            # Start recording based on backend with fallback
            recording_started = False

            if AUDIO_BACKEND == "sounddevice":
                try:
                    self._start_sounddevice_recording(device_index)
                    recording_started = True
                except Exception as e:
                    print(f"SoundDevice failed: {e}")

            elif AUDIO_BACKEND == "pyaudio":
                try:
                    self._start_pyaudio_recording(device_index)
                    recording_started = True
                except Exception as e:
                    print(f"PyAudio failed: {e}")
                    # Try SoundDevice as fallback if available
                    if 'sounddevice' in sys.modules:
                        try:
                            print("Trying SoundDevice as fallback...")
                            self._start_sounddevice_recording(device_index)
                            recording_started = True
                        except Exception as e2:
                            print(f"SoundDevice fallback also failed: {e2}")

            if not recording_started:
                raise RuntimeError("All audio backends failed to start recording")

            self.is_recording = True

            # Play notification sound
            self._play_notification_sound()

            # Call callback
            if self.on_recording_start:
                self.on_recording_start()

            print(f"Started recording to: {self.current_recording_path}")
            return True

        except Exception as e:
            print(f"Failed to start recording: {e}")
            import traceback
            traceback.print_exc()
            self.is_recording = False
            return False

    def _start_sounddevice_recording(self, device_index: Optional[int]):
        """Start recording with sounddevice backend"""
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio callback status: {status}")

            # Convert to int16 and store
            audio_chunk = (indata[:, 0] * 32767).astype(np.int16)
            self._audio_data.extend(audio_chunk)

            # Call chunk callback if available
            if self.on_audio_chunk:
                self.on_audio_chunk(audio_chunk)

        self._audio_stream = sd.InputStream(
            device=device_index,
            channels=self.CHANNELS,
            samplerate=self.SAMPLE_RATE,
            callback=audio_callback,
            blocksize=self.CHUNK_SIZE
        )
        self._audio_stream.start()

    def _start_pyaudio_recording(self, device_index: Optional[int]):
        """Start recording with pyaudio backend"""
        def recording_thread():
            stream = None
            try:
                # Test device before opening stream
                if device_index is not None:
                    try:
                        device_info = self._audio_interface.get_device_info_by_index(device_index)
                        print(f"Using device: {device_info['name']}")
                        if device_info['maxInputChannels'] == 0:
                            raise ValueError(f"Device {device_index} has no input channels")
                    except Exception as e:
                        print(f"Device {device_index} not available: {e}")
                        device_index = None  # Fall back to default

                # Try different configurations for better compatibility
                stream_configs = [
                    # Original config
                    {
                        'format': self.FORMAT,
                        'channels': self.CHANNELS,
                        'rate': self.SAMPLE_RATE,
                        'input': True,
                        'input_device_index': device_index,
                        'frames_per_buffer': self.CHUNK_SIZE
                    },
                    # Try with device's native sample rate
                    {
                        'format': self.FORMAT,
                        'channels': self.CHANNELS,
                        'rate': int(device_info.get('defaultSampleRate', self.SAMPLE_RATE)),
                        'input': True,
                        'input_device_index': device_index,
                        'frames_per_buffer': self.CHUNK_SIZE
                    },
                    # Try with mono if device supports it
                    {
                        'format': self.FORMAT,
                        'channels': 1,
                        'rate': self.SAMPLE_RATE,
                        'input': True,
                        'input_device_index': device_index,
                        'frames_per_buffer': self.CHUNK_SIZE
                    },
                    # Try with device's native sample rate and mono
                    {
                        'format': self.FORMAT,
                        'channels': 1,
                        'rate': int(device_info.get('defaultSampleRate', self.SAMPLE_RATE)),
                        'input': True,
                        'input_device_index': device_index,
                        'frames_per_buffer': self.CHUNK_SIZE
                    }
                ]

                stream = None
                last_error = None

                for i, config in enumerate(stream_configs):
                    try:
                        print(f"Trying config {i+1}: {config['channels']} ch, {config['rate']} Hz")
                        stream = self._audio_interface.open(**config)
                        print(f"Success with config {i+1}")
                        # Store the working config for audio processing
                        self._working_channels = config['channels']
                        self._working_rate = config['rate']
                        break
                    except Exception as e:
                        last_error = e
                        print(f"Config {i+1} failed: {e}")
                        continue

                if stream is None:
                    raise Exception(f"All configurations failed. Last error: {last_error}")

                self._audio_stream = stream
                print(f"Audio stream opened successfully with device {device_index}")

                while self.is_recording:
                    try:
                        data = stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                        audio_chunk = np.frombuffer(data, dtype=np.int16)

                        # Handle channel conversion (stereo to mono)
                        if self._working_channels == 2 and self.CHANNELS == 1:
                            # Convert stereo to mono by averaging channels
                            audio_chunk = audio_chunk.reshape(-1, 2).mean(axis=1).astype(np.int16)

                        # Handle sample rate conversion if needed
                        if self._working_rate != self.SAMPLE_RATE:
                            # Simple resampling (for production, use librosa.resample)
                            ratio = self.SAMPLE_RATE / self._working_rate
                            new_length = int(len(audio_chunk) * ratio)
                            if new_length > 0:
                                indices = np.linspace(0, len(audio_chunk) - 1, new_length)
                                audio_chunk = np.interp(indices, np.arange(len(audio_chunk)), audio_chunk).astype(np.int16)

                        self._audio_data.extend(audio_chunk)

                        # Call chunk callback if available
                        if self.on_audio_chunk:
                            self.on_audio_chunk(audio_chunk)

                    except Exception as e:
                        print(f"Error reading audio data: {e}")
                        break

            except Exception as e:
                print(f"Recording thread error: {e}")
                import traceback
                traceback.print_exc()
                self.is_recording = False
            finally:
                if stream:
                    try:
                        stream.stop_stream()
                        stream.close()
                    except:
                        pass
                # Clear stream reference
                self._audio_stream = None

                # Force garbage collection
                import gc
                gc.collect()

        self._recording_thread = threading.Thread(target=recording_thread, daemon=True)
        self._recording_thread.start()

    def stop_recording(self) -> Optional[Path]:
        """Stop recording and save audio file"""
        if not self.is_recording:
            print("Not currently recording")
            return None

        try:
            self.is_recording = False

            # Stop audio stream
            if AUDIO_BACKEND == "sounddevice" and self._audio_stream:
                self._audio_stream.stop()
                self._audio_stream.close()
                self._audio_stream = None
            elif AUDIO_BACKEND == "pyaudio":
                # Wait for recording thread to finish
                if self._recording_thread and self._recording_thread.is_alive():
                    self._recording_thread.join(timeout=2.0)
                self._recording_thread = None

            # Check if we have audio data
            if not self._audio_data:
                print("No audio data recorded")
                return None

            # Check minimum duration (0.5 seconds)
            duration = len(self._audio_data) / self.SAMPLE_RATE
            if duration < 0.5:
                print(f"Recording too short: {duration:.2f}s")
                return None

            # Save audio data to WAV file
            self._save_audio_data()

            # Call callback
            if self.on_recording_stop:
                self.on_recording_stop()

            recording_path = self.current_recording_path
            self.current_recording_path = None

            print(f"Recording saved: {recording_path}")
            return recording_path

        except Exception as e:
            print(f"Failed to stop recording: {e}")
            return None

    def cancel_recording(self):
        """Cancel current recording without saving"""
        if not self.is_recording:
            return

        self.is_recording = False

        # Stop audio stream
        if AUDIO_BACKEND == "sounddevice" and self._audio_stream:
            self._audio_stream.stop()
            self._audio_stream.close()
            self._audio_stream = None
        elif AUDIO_BACKEND == "pyaudio":
            if self._recording_thread and self._recording_thread.is_alive():
                self._recording_thread.join(timeout=2.0)
            self._recording_thread = None

        # Clean up temporary file
        if self.current_recording_path and self.current_recording_path.exists():
            try:
                self.current_recording_path.unlink()
            except Exception as e:
                print(f"Failed to delete temporary file: {e}")

        self.current_recording_path = None
        self._audio_data = []

        print("Recording cancelled")

    def _save_audio_data(self):
        """Save recorded audio data to WAV file"""
        if not self._audio_data or not self.current_recording_path:
            return

        try:
            # Convert to numpy array
            audio_array = np.array(self._audio_data, dtype=np.int16)

            # Save as WAV file
            with wave.open(str(self.current_recording_path), 'wb') as wav_file:
                wav_file.setnchannels(self.CHANNELS)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.SAMPLE_RATE)
                wav_file.writeframes(audio_array.tobytes())

        except Exception as e:
            print(f"Failed to save audio data: {e}")
            raise

    def _play_notification_sound(self):
        """Play notification sound when recording starts"""
        if not WINSOUND_AVAILABLE:
            return

        try:
            # Play system sound
            winsound.MessageBeep(winsound.MB_OK)
        except Exception as e:
            print(f"Failed to play notification sound: {e}")

    def play_recording(self, file_path: Path) -> bool:
        """Play back a recorded audio file"""
        if self.is_playing:
            self.stop_playback()

        try:
            if AUDIO_BACKEND == "sounddevice":
                return self._play_with_sounddevice(file_path)
            elif AUDIO_BACKEND == "pyaudio":
                return self._play_with_pyaudio(file_path)
            return False

        except Exception as e:
            print(f"Failed to play recording: {e}")
            return False

    def _play_with_sounddevice(self, file_path: Path) -> bool:
        """Play audio file using sounddevice"""
        try:
            # Read WAV file
            with wave.open(str(file_path), 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                audio_data = np.frombuffer(frames, dtype=np.int16)

                # Convert to float32 for sounddevice
                audio_data = audio_data.astype(np.float32) / 32768.0

                # Play audio
                sd.play(audio_data, samplerate=self.SAMPLE_RATE)
                self.is_playing = True
                self.current_playing_path = file_path

                return True

        except Exception as e:
            print(f"Sounddevice playback error: {e}")
            return False

    def _play_with_pyaudio(self, file_path: Path) -> bool:
        """Play audio file using pyaudio"""
        try:
            def playback_thread():
                try:
                    with wave.open(str(file_path), 'rb') as wav_file:
                        stream = self._audio_interface.open(
                            format=self._audio_interface.get_format_from_width(wav_file.getsampwidth()),
                            channels=wav_file.getnchannels(),
                            rate=wav_file.getframerate(),
                            output=True
                        )

                        # Read and play audio in chunks
                        chunk_size = 1024
                        data = wav_file.readframes(chunk_size)

                        while data and self.is_playing:
                            stream.write(data)
                            data = wav_file.readframes(chunk_size)

                        stream.stop_stream()
                        stream.close()

                except Exception as e:
                    print(f"Playback thread error: {e}")
                finally:
                    self.is_playing = False
                    self.current_playing_path = None

            self.is_playing = True
            self.current_playing_path = file_path

            playback_thread = threading.Thread(target=playback_thread, daemon=True)
            playback_thread.start()

            return True

        except Exception as e:
            print(f"PyAudio playback error: {e}")
            return False

    def stop_playback(self):
        """Stop audio playback"""
        if not self.is_playing:
            return

        try:
            if AUDIO_BACKEND == "sounddevice":
                sd.stop()

            self.is_playing = False
            self.current_playing_path = None

        except Exception as e:
            print(f"Failed to stop playback: {e}")

    def move_recording(self, temp_path: Path, final_path: Path) -> bool:
        """Move recording from temporary location to final location"""
        try:
            # Ensure target directory exists
            final_path.parent.mkdir(parents=True, exist_ok=True)

            # Remove existing file if it exists
            if final_path.exists():
                final_path.unlink()

            # Move file
            temp_path.rename(final_path)
            return True

        except Exception as e:
            print(f"Failed to move recording: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        # Stop any active recording or playback
        if self.is_recording:
            self.cancel_recording()
        if self.is_playing:
            self.stop_playback()

        # Clean up audio interface
        if AUDIO_BACKEND == "pyaudio" and self._audio_interface:
            self._audio_interface.terminate()
            self._audio_interface = None

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()
