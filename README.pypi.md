# Termux-TTS (Python)

[![PyPI](https://img.shields.io/pypi/v/termux-tts.svg?style=flat-square&color=0369a1)](https://pypi.org/project/termux-tts/)
[![Python](https://img.shields.io/pypi/pyversions/termux-tts.svg?style=flat-square)](https://pypi.org/project/termux-tts/)
[![License](https://img.shields.io/badge/License-Apache_2.0-004499.svg?style=flat-square)](https://github.com/uno-km/termux-tts)

> **High-Performance Multi-Backend Speech Synthesis Framework for Android Termux & Edge Linux**  
> Supports Zero-Dependency Parametric DSP Formant Vocoder, Deep Learning ONNX Neural Runtime, and Android Native System Voice Bridge.

## Installation

```bash
pip install termux-tts
```

## Quickstart

```python
import termux_tts as tts

# 1. Zero-Dependency DSP Formant Mode (Default)
with tts.load(engine="dsp", language="ko") as engine:
    res = engine.synthesize("안녕하세요, 텀묵스 음성 합성입니다.", output="dsp.wav")
    print(f"Synthesized in {res.elapsed_ms:.1f}ms (RTF: {res.rtf:.4f}x)")

# 2. Deep Learning ONNX Mode
with tts.load(engine="onnx", model="vits_ko.onnx", language="ko") as engine:
    res = engine.synthesize("신경망 고품질 음성 합성입니다.", output="onnx.wav")

# 3. Android System Native Speak Mode
with tts.load(engine="native", language="ko") as engine:
    engine.speak("스피커로 즉시 발화합니다.")
```

## Features
- **Zero-Dependency DSP Engine**: Instant CPU execution with 0MB download overhead (Rosenberg Glottal Pulse + 5-Band Biquad Filters).
- **Authentic ONNX Neural Runtime**: Deep learning acoustic model execution for VITS, Piper, and FastSpeech ONNX models.
- **Android Native Bridge**: Direct speaker speech playback via Termux IPC.
- **Cross-Platform CLI & Node.js Binding**: First-class support for Python, npm, and shell scripts.

## Documentation
- [Official Documentation & API Reference](https://uno-km.vercel.app/lib/tts/)
- [GitHub Repository](https://github.com/uno-km/termux-tts)

## License
Apache-2.0 License. Copyright (c) 2026 Eunho Kim (@uno-km).

