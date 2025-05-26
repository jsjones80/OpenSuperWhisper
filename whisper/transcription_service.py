"""
Enhanced Transcription Service for OpenSuperWhisper Windows
Extends the base Whisper functionality with real-time capabilities and Windows optimizations
"""

import asyncio
import threading
import time
from pathlib import Path
from typing import Optional, Callable, Dict, Any, Union
import torch
import numpy as np

from . import load_model, transcribe
from .audio import load_audio


class TranscriptionService:
    """Enhanced transcription service with real-time capabilities"""

    def __init__(self):
        self.model = None
        self.model_name = "base"
        
        # Try to get device from settings first
        try:
            from .config_manager import get_config_manager
            config = get_config_manager()
            settings = config.get_all_settings()
            saved_device = settings.get('device', None)
            if saved_device and saved_device in ['cpu', 'cuda']:
                self.device = saved_device
                print(f"Using saved device preference: {self.device}")
            else:
                self.device = self._detect_device()
                print(f"Using auto-detected device: {self.device}")
        except:
            self.device = self._detect_device()
            print(f"Using auto-detected device: {self.device}")
            
        self.is_loading = False
        self.is_transcribing = False
        self.progress = 0.0
        self.current_task = None
        self.transcription_lock = threading.Lock()  # Prevent concurrent transcriptions
        self.transcription_count = 0  # Track number of transcriptions

        # Callbacks
        self.on_progress: Optional[Callable[[float], None]] = None
        self.on_segment: Optional[Callable[[str], None]] = None
        self.on_complete: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

        # Load default model
        self._load_model_async()

    def _detect_device(self) -> str:
        """Detect the best available device for inference"""
        if torch.cuda.is_available():
            # Check available CUDA memory
            try:
                # Get GPU memory info
                gpu_memory = torch.cuda.get_device_properties(0).total_memory
                gpu_memory_gb = gpu_memory / (1024**3)
                print(f"GPU detected with {gpu_memory_gb:.1f}GB memory")
                
                # Use CUDA only if we have enough memory (at least 2GB for base model)
                if gpu_memory_gb >= 2.0:
                    return "cuda"
                else:
                    print("Insufficient GPU memory, falling back to CPU")
                    return "cpu"
            except:
                return "cuda"  # Default to CUDA if we can't check memory

        # For now, use CPU to avoid DirectML compatibility issues
        # DirectML support can be added later once compatibility is verified
        return "cpu"

    def _load_model_async(self):
        """Load model asynchronously"""
        def load_model_thread():
            try:
                self.is_loading = True
                print(f"Loading Whisper model '{self.model_name}' on device '{self.device}'...")

                self.model = load_model(
                    name=self.model_name,
                    device=self.device
                )

                print(f"Model loaded successfully on {self.device}")
                
                # Verify the model is actually on the correct device
                model_info = self.get_model_info()
                print(f"Model verification - Actual device: {model_info.get('device', 'unknown')}, Configured: {self.device}")

            except Exception as e:
                print(f"Failed to load model: {e}")
                if self.on_error:
                    self.on_error(e)
            finally:
                self.is_loading = False

        thread = threading.Thread(target=load_model_thread, daemon=True)
        thread.start()

    def change_model(self, model_name: str):
        """Change the Whisper model"""
        if self.is_transcribing:
            print("Cannot change model while transcribing")
            return False

        if model_name == self.model_name and self.model is not None:
            print(f"Model '{model_name}' already loaded")
            return True

        self.model_name = model_name
        self.model = None
        self._load_model_async()
        return True

    def change_device(self, device: str):
        """Change the processing device (cpu/cuda/directml)"""
        if self.is_transcribing:
            print("Cannot change device while transcribing")
            return False

        if device == self.device and self.model is not None:
            print(f"Device '{device}' already in use")
            return True

        print(f"Changing device from {self.device} to {device}")
        
        # Properly cleanup existing model
        if self.model is not None:
            print(f"Unloading model from {self.device}")
            # Move model to CPU first if it's on GPU
            if self.device.startswith('cuda'):
                try:
                    self.model = self.model.to('cpu')
                except:
                    pass
            
            # Delete the model
            del self.model
            self.model = None
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear GPU cache if we were using CUDA
            if self.device.startswith('cuda') and torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                print("GPU memory cleared")
        
        self.device = device
        self._load_model_async()
        return True

    def get_available_models(self) -> list:
        """Get list of available Whisper models"""
        from . import available_models
        return available_models()

    async def transcribe_audio_async(
        self,
        audio_path: Union[str, Path],
        settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """Transcribe audio file asynchronously"""

        if self.is_transcribing:
            raise RuntimeError("Already transcribing")

        if self.model is None:
            raise RuntimeError("Model not loaded")

        # Default settings
        default_settings = {
            'language': None,  # Auto-detect
            'task': 'transcribe',  # or 'translate'
            'temperature': 0.0,
            'best_of': 5,
            'beam_size': 5,
            'patience': 1.0,
            'length_penalty': 1.0,
            'suppress_tokens': "-1",
            'initial_prompt': None,
            'condition_on_previous_text': True,
            'fp16': True,
            'compression_ratio_threshold': 2.4,
            'logprob_threshold': -1.0,
            'no_speech_threshold': 0.6,
            'word_timestamps': False,
            'prepend_punctuations': "\"'([{-",
            'append_punctuations': "\"'.,:)]}",
            'clip_timestamps': "0"
        }

        if settings:
            default_settings.update(settings)

        try:
            self.is_transcribing = True
            self.progress = 0.0

            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                str(audio_path),
                default_settings
            )

            self.progress = 1.0

            if self.on_complete:
                self.on_complete(result['text'])

            return result['text']

        except Exception as e:
            if self.on_error:
                self.on_error(e)
            raise
        finally:
            self.is_transcribing = False

    def _transcribe_sync(self, audio_path: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous transcription with progress tracking"""
        
        # Use lock to prevent concurrent transcriptions
        with self.transcription_lock:
            self.transcription_count += 1
            print(f"Starting transcription #{self.transcription_count}")
            
            # Force cleanup every 3 transcriptions to prevent memory accumulation
            if self.transcription_count % 3 == 0:
                print("Performing periodic memory cleanup...")
                import gc
                gc.collect()
                if self.device.startswith('cuda') and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()

            # Filter settings to only include valid Whisper transcription parameters
            valid_whisper_params = {
                'language', 'task', 'temperature', 'best_of', 'beam_size', 'patience',
                'length_penalty', 'suppress_tokens', 'initial_prompt',
                'condition_on_previous_text', 'fp16', 'compression_ratio_threshold',
                'logprob_threshold', 'no_speech_threshold', 'word_timestamps',
                'prepend_punctuations', 'append_punctuations', 'clip_timestamps'
            }

            # Only include valid parameters
            filtered_settings = {
                key: value for key, value in settings.items()
                if key in valid_whisper_params
            }

            # Update progress manually
            if self.on_progress:
                self.on_progress(0.1)  # Starting

            try:
                # Log actual device being used
                actual_device = str(self.model.device) if hasattr(self.model, 'device') else 'unknown'
                print(f"Transcribing on device: {actual_device} (configured: {self.device})")
                
                # Perform transcription
                result = transcribe(
                    model=self.model,
                    audio=audio_path,
                    **filtered_settings
                )

                # Update progress to complete
                if self.on_progress:
                    self.on_progress(1.0)  # Complete

                return result
            finally:
                # More aggressive cleanup to prevent CUDA memory accumulation
                import gc
                
                # Clear any references
                if 'audio' in locals():
                    del audio
                if 'mel' in locals():
                    del mel
                    
                # Force garbage collection multiple times
                for _ in range(3):
                    gc.collect()
                
                # Clear GPU cache aggressively if using CUDA
                if self.device.startswith('cuda') and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()  # Wait for all CUDA operations to complete
                    
                    # Additional memory cleanup
                    if torch.cuda.is_available():
                        torch.cuda.reset_peak_memory_stats()
                        torch.cuda.empty_cache()

    def transcribe_audio_sync(
        self,
        audio_path: Union[str, Path],
        settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """Synchronous transcription (blocking)"""

        if self.is_transcribing:
            raise RuntimeError("Already transcribing")

        if self.model is None:
            raise RuntimeError("Model not loaded")

        # Use asyncio to run the async version
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.transcribe_audio_async(audio_path, settings)
        )

    def cancel_transcription(self):
        """Cancel current transcription"""
        if not self.is_transcribing:
            return

        # Set cancellation flag
        self.is_transcribing = False

        # Cancel current task if available
        if self.current_task:
            self.current_task.cancel()
            self.current_task = None

        self.progress = 0.0
        print("Transcription cancelled")

    def detect_language(self, audio_path: Union[str, Path]) -> Dict[str, float]:
        """Detect language of audio file"""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        try:
            # Load and preprocess audio
            audio = load_audio(str(audio_path))
            audio = torch.from_numpy(audio).to(self.model.device)

            # Detect language
            from .decoding import detect_language
            language_probs = detect_language(self.model, audio)

            return language_probs

        except Exception as e:
            print(f"Language detection failed: {e}")
            return {}

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        if self.model is None:
            return {
                'name': self.model_name,
                'loaded': False,
                'device': self.device,
                'loading': self.is_loading
            }

        # Get actual device the model is on
        actual_device = 'unknown'
        try:
            # Check encoder device (which should represent the whole model)
            if hasattr(self.model, 'encoder') and hasattr(self.model.encoder, 'conv1'):
                actual_device = str(next(self.model.encoder.conv1.parameters()).device)
            elif hasattr(self.model, 'device'):
                actual_device = str(self.model.device)
        except:
            pass

        return {
            'name': self.model_name,
            'loaded': True,
            'device': actual_device,
            'configured_device': self.device,
            'loading': self.is_loading,
            'is_multilingual': self.model.is_multilingual,
            'dimensions': {
                'n_mels': self.model.dims.n_mels,
                'n_audio_ctx': self.model.dims.n_audio_ctx,
                'n_vocab': self.model.dims.n_vocab,
                'n_text_ctx': self.model.dims.n_text_ctx
            }
        }

    def get_supported_languages(self) -> Dict[str, str]:
        """Get supported languages"""
        from .tokenizer import LANGUAGES
        return LANGUAGES

    def estimate_transcription_time(self, audio_path: Union[str, Path]) -> float:
        """Estimate transcription time based on audio duration and model"""
        try:
            import librosa
            duration = librosa.get_duration(filename=str(audio_path))
        except ImportError:
            # Fallback: estimate from file size (rough approximation)
            file_size = Path(audio_path).stat().st_size
            # Assume ~1MB per minute for typical audio
            duration = file_size / (1024 * 1024) * 60

        # Rough estimation based on model size and device
        model_multipliers = {
            'tiny': 0.1,
            'base': 0.2,
            'small': 0.4,
            'medium': 0.8,
            'large': 1.5,
            'turbo': 0.15
        }

        device_multipliers = {
            'cuda': 1.0,
            'cpu': 5.0
        }

        model_mult = model_multipliers.get(self.model_name, 1.0)
        device_mult = device_multipliers.get(self.device.split(':')[0], 3.0)

        estimated_time = duration * model_mult * device_mult
        return max(estimated_time, 1.0)  # Minimum 1 second

    def cleanup(self):
        """Clean up resources"""
        self.cancel_transcription()

        # Clear model from memory
        if self.model is not None:
            del self.model
            self.model = None

        # Clear GPU cache if using CUDA
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


# Singleton instance
_transcription_service = None

def get_transcription_service() -> TranscriptionService:
    """Get singleton transcription service instance"""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service
