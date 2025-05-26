# OpenSuperWhisper for Windows

A Windows-native real-time speech transcription application based on OpenAI Whisper, inspired by [OpenSuperWhisper for macOS](https://github.com/Starmel/OpenSuperWhisper).

## Features

🎙️ **Real-time Recording** - Record audio directly from your microphone with one click
⌨️ **Global Hotkeys** - Control recording from anywhere with customizable keyboard shortcuts
🌍 **Multi-language Support** - Automatic language detection and support for 99+ languages
🔄 **Translation** - Optional translation to English for better understanding
💾 **Local Storage** - All recordings and transcriptions stored locally with full-text search
🎛️ **Advanced Settings** - Customizable transcription parameters and model selection
🖥️ **Windows Integration** - Native Windows GUI with system tray support
⚡ **GPU Acceleration** - Supports both CUDA and DirectML for faster transcription

## Screenshots

*Coming soon - GUI screenshots will be added here*

## Quick Start

### Option 1: Automated Installation (Recommended)

1. Download or clone this repository
2. Run `install_windows.bat` as Administrator
3. Follow the on-screen instructions
4. Launch from desktop shortcut or start menu

### Option 2: Manual Installation

1. **Prerequisites**
   - Python 3.8 or later
   - Git (optional)
   - FFmpeg (for audio processing)

2. **Clone the repository**
   ```bash
   git clone https://github.com/your-repo/opensuperwhisper-windows.git
   cd opensuperwhisper-windows
   ```

3. **Create virtual environment**
   ```bash
   python -m venv opensuperwhisper_env
   opensuperwhisper_env\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

5. **Run the application**
   ```bash
   python opensuperwhisper_gui.py
   ```


## Usage

### Basic Recording

1. **Start the application** - Launch OpenSuperWhisper from desktop shortcut or start menu
2. **Click Record** - Press the red record button or use the global hotkey (Ctrl+Shift+R)
3. **Speak clearly** - Talk into your microphone
4. **Stop recording** - Click the button again or use the hotkey
5. **View transcription** - The text will appear automatically in the history

### Global Hotkeys

- **Ctrl+Shift+R** - Toggle recording on/off
- **Ctrl+Shift+T** - Quick transcribe (for files)
- **Ctrl+Shift+W** - Show/hide main window

*Hotkeys can be customized in Settings*

### File Transcription

1. Click **"Transcribe File..."** button
2. Select an audio file (WAV, MP3, M4A, FLAC, OGG)
3. Wait for processing
4. View results in the history

### Search and Management

- Use the search bar to find specific transcriptions
- Right-click recordings for options (play, copy, export, delete)
- Export individual recordings or all data
- Automatic cleanup of old recordings (configurable)

## Configuration

### Audio Settings

- **Input Device** - Select your preferred microphone
- **Sample Rate** - 16kHz (optimized for Whisper)
- **Audio Quality** - Automatic noise reduction and level adjustment

### Transcription Settings

- **Model** - Choose from tiny, base, small, medium, large, turbo
- **Language** - Auto-detect or specify language
- **Translation** - Enable translation to English
- **Advanced** - Temperature, beam search, and other parameters

### Performance

- **GPU Acceleration** - Automatically detects CUDA or DirectML
- **Model Caching** - Models are cached for faster subsequent loads
- **Background Processing** - Non-blocking transcription

## Troubleshooting

### Common Issues

**"No audio devices found"**
- Check microphone connections
- Ensure microphone permissions are granted
- Try running as Administrator

**"Model loading failed"**
- Check internet connection for first-time model download
- Ensure sufficient disk space (models are 100MB-3GB)
- Try a smaller model (tiny/base) first

**"Transcription is slow"**
- Use GPU acceleration if available
- Try a smaller model
- Close other resource-intensive applications

**"Global hotkeys not working"**
- Run as Administrator
- Check for conflicting applications
- Disable/customize conflicting hotkeys

### Performance Tips

- **Use GPU** - NVIDIA GPUs with CUDA or AMD GPUs with DirectML
- **Choose appropriate model** - Larger models are more accurate but slower
- **Close unnecessary apps** - Free up system resources
- **Use SSD storage** - Faster model loading and file operations

## System Requirements

### Minimum
- Windows 10 (64-bit)
- Python 3.8+
- 4GB RAM
- 2GB free disk space
- Microphone

### Recommended
- Windows 11 (64-bit)
- Python 3.10+
- 8GB+ RAM
- NVIDIA GPU with 4GB+ VRAM or AMD GPU with DirectML
- 5GB+ free disk space
- High-quality USB microphone

## Original Whisper Information

This application is built on top of OpenAI's Whisper model:

A Transformer sequence-to-sequence model is trained on various speech processing tasks, including multilingual speech recognition, speech translation, spoken language identification, and voice activity detection. These tasks are jointly represented as a sequence of tokens to be predicted by the decoder, allowing a single model to replace many stages of a traditional speech-processing pipeline. The multitask training format uses a set of special tokens that serve as task specifiers or classification targets.


## Setup

We used Python 3.9.9 and [PyTorch](https://pytorch.org/) 1.10.1 to train and test our models, but the codebase is expected to be compatible with Python 3.8-3.11 and recent PyTorch versions. The codebase also depends on a few Python packages, most notably [OpenAI's tiktoken](https://github.com/openai/tiktoken) for their fast tokenizer implementation. You can download and install (or update to) the latest release of Whisper with the following command:

    pip install -U openai-whisper

Alternatively, the following command will pull and install the latest commit from this repository, along with its Python dependencies:

    pip install git+https://github.com/openai/whisper.git

To update the package to the latest version of this repository, please run:

    pip install --upgrade --no-deps --force-reinstall git+https://github.com/openai/whisper.git

It also requires the command-line tool [`ffmpeg`](https://ffmpeg.org/) to be installed on your system, which is available from most package managers:

```bash
# on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

# on Arch Linux
sudo pacman -S ffmpeg

# on MacOS using Homebrew (https://brew.sh/)
brew install ffmpeg

# on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg

# on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg
```

You may need [`rust`](http://rust-lang.org) installed as well, in case [tiktoken](https://github.com/openai/tiktoken) does not provide a pre-built wheel for your platform. If you see installation errors during the `pip install` command above, please follow the [Getting started page](https://www.rust-lang.org/learn/get-started) to install Rust development environment. Additionally, you may need to configure the `PATH` environment variable, e.g. `export PATH="$HOME/.cargo/bin:$PATH"`. If the installation fails with `No module named 'setuptools_rust'`, you need to install `setuptools_rust`, e.g. by running:

```bash
pip install setuptools-rust
```


## Available models and languages

There are six model sizes, four with English-only versions, offering speed and accuracy tradeoffs.
Below are the names of the available models and their approximate memory requirements and inference speed relative to the large model.
The relative speeds below are measured by transcribing English speech on a A100, and the real-world speed may vary significantly depending on many factors including the language, the speaking speed, and the available hardware.

|  Size  | Parameters | English-only model | Multilingual model | Required VRAM | Relative speed |
|:------:|:----------:|:------------------:|:------------------:|:-------------:|:--------------:|
|  tiny  |    39 M    |     `tiny.en`      |       `tiny`       |     ~1 GB     |      ~10x      |
|  base  |    74 M    |     `base.en`      |       `base`       |     ~1 GB     |      ~7x       |
| small  |   244 M    |     `small.en`     |      `small`       |     ~2 GB     |      ~4x       |
| medium |   769 M    |    `medium.en`     |      `medium`      |     ~5 GB     |      ~2x       |
| large  |   1550 M   |        N/A         |      `large`       |    ~10 GB     |       1x       |
| turbo  |   809 M    |        N/A         |      `turbo`       |     ~6 GB     |      ~8x       |

The `.en` models for English-only applications tend to perform better, especially for the `tiny.en` and `base.en` models. We observed that the difference becomes less significant for the `small.en` and `medium.en` models.
Additionally, the `turbo` model is an optimized version of `large-v3` that offers faster transcription speed with a minimal degradation in accuracy.

Whisper's performance varies widely depending on the language. The figure below shows a performance breakdown of `large-v3` and `large-v2` models by language, using WERs (word error rates) or CER (character error rates, shown in *Italic*) evaluated on the Common Voice 15 and Fleurs datasets. Additional WER/CER metrics corresponding to the other models and datasets can be found in Appendix D.1, D.2, and D.4 of [the paper](https://arxiv.org/abs/2212.04356), as well as the BLEU (Bilingual Evaluation Understudy) scores for translation in Appendix D.3.

![WER breakdown by language](https://github.com/openai/whisper/assets/266841/f4619d66-1058-4005-8f67-a9d811b77c62)



## Command-line usage

The following command will transcribe speech in audio files, using the `turbo` model:

    whisper audio.flac audio.mp3 audio.wav --model turbo

The default setting (which selects the `turbo` model) works well for transcribing English. To transcribe an audio file containing non-English speech, you can specify the language using the `--language` option:

    whisper japanese.wav --language Japanese

Adding `--task translate` will translate the speech into English:

    whisper japanese.wav --language Japanese --task translate

Run the following to view all available options:

    whisper --help

See [tokenizer.py](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py) for the list of all available languages.


## Python usage

Transcription can also be performed within Python:

```python
import whisper

model = whisper.load_model("turbo")
result = model.transcribe("audio.mp3")
print(result["text"])
```

Internally, the `transcribe()` method reads the entire file and processes the audio with a sliding 30-second window, performing autoregressive sequence-to-sequence predictions on each window.

Below is an example usage of `whisper.detect_language()` and `whisper.decode()` which provide lower-level access to the model.

```python
import whisper

model = whisper.load_model("turbo")

# load audio and pad/trim it to fit 30 seconds
audio = whisper.load_audio("audio.mp3")
audio = whisper.pad_or_trim(audio)

# make log-Mel spectrogram and move to the same device as the model
mel = whisper.log_mel_spectrogram(audio, n_mels=model.dims.n_mels).to(model.device)

# detect the spoken language
_, probs = model.detect_language(mel)
print(f"Detected language: {max(probs, key=probs.get)}")

# decode the audio
options = whisper.DecodingOptions()
result = whisper.decode(model, mel, options)

# print the recognized text
print(result.text)
```

## More examples

Please use the [🙌 Show and tell](https://github.com/openai/whisper/discussions/categories/show-and-tell) category in Discussions for sharing more example usages of Whisper and third-party extensions such as web demos, integrations with other tools, ports for different platforms, etc.


## License

Whisper's code and model weights are released under the MIT License. See [LICENSE](https://github.com/openai/whisper/blob/main/LICENSE) for further details.
