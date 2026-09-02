# termux-tts

[![License](https://img.shields.io/badge/License-Apache_2.0-004499.svg?style=flat-square)](https://github.com/uno-km/uno-km)
[![PyPI](https://img.shields.io/pypi/v/termux-tts.svg?style=flat-square)](https://pypi.org/project/termux-tts/)
[![NPM](https://img.shields.io/npm/v/termux-tts.svg?style=flat-square)](https://www.npmjs.com/package/termux-tts)

> **High-Performance Multi-Backend Speech Synthesis Framework for Android Termux & Edge Linux**  
> Supports Zero-Dependency Parametric DSP Formant Vocoder, Deep Learning ONNX Neural Runtime, and Android Native System Voice Bridge.

---

## 📌 3-Tier Architecture Overview

```mermaid
flowchart TD
    Gateway[TTSEngine Gateway] -->|engine='dsp' (Default, 0MB)| DSP[ParametricDSPEngine (Rosenberg Glottal + Biquad Formant)]
    Gateway -->|engine='onnx' (Deep Learning)| ONNX[ONNXNeuralEngine (VITS / Piper / FastSpeech ONNX Session)]
    Gateway -->|engine='native' (Speaker Output)| Native[NativeAndroidEngine (Samsung / Google Voice Bridge)]
```

1. **Option A-DSP (Parametric Formant Vocoder - `engine='dsp'`)**:
   - 0MB Download overhead, Zero external C++ dependencies (pure standard library & numpy).
   - High-speed Direct Form II Transposed Biquad resonators (RTF < 0.08x).
2. **Option A-Neural (ONNX Neural Engine - `engine='onnx'`)**:
   - Executes deep learning `.onnx` acoustic models (VITS / Piper / FastSpeech).
   - Requires `onnxruntime` and a valid model file.
3. **Option B (Android System Native Voice - `engine='native'`)**:
   - Zero-download direct speaker output via Android `termux-tts-speak` IPC bridge.

---

## 🚀 Installation & Quickstart

### Python Toolchain (pip)
```bash
pip install termux-tts
```

```python
import termux_tts as tts

# 1. Zero-dependency DSP Mode (Default)
with tts.load(engine="dsp", language="ko") as engine:
    res = engine.synthesize("안녕하세요, 텀묵스 음성 합성입니다.", output="dsp_out.wav")
    print(f"Synthesized in {res.elapsed_ms:.1f}ms (RTF: {res.rtf:.4f}x)")

# 2. Deep Learning ONNX Mode
with tts.load(engine="onnx", model="vits_ko.onnx", language="ko") as engine:
    res = engine.synthesize("신경망 고품질 음성 합성입니다.", output="onnx_out.wav")

# 3. Android System Speaker Speak Mode
with tts.load(engine="native", language="ko") as engine:
    engine.speak("스피커로 즉시 발화합니다.")
```

### Node.js Toolchain (npm)
```bash
npm install termux-tts
```

```javascript
const tts = require('termux-tts');

async function main() {
    const engine = tts.load({ language: 'ko', engine: 'dsp' });
    const res = await engine.synthesize("노드 JS 초고속 음성 합성", { output: "output.wav" });
    console.log(`[SUCCESS] Duration: ${res.durationSec}s in ${res.elapsedMs}ms`);
}
main();
```

### Command-Line Interface (CLI)
```bash
# DSP Formant Synthesis (Default)
termux-tts synth -e dsp -t "안녕하세요 100원입니다" -o test.wav

# Deep Learning ONNX Synthesis
termux-tts synth -e onnx -m vits_model.onnx -t "신경망 음성" -o onnx.wav

# Android Speaker Speak
termux-tts speak -t "안녕하세요 반갑습니다"

# Hardware Diagnostics
termux-tts doctor
```

---

## 📖 Official Documentation & Benchmarks
- [Official Architecture & API Reference](https://uno-km.vercel.app/lib/tts/)
- [Ecosystem Metrics & Registry Stats](https://uno-km.vercel.app/foundation/metrics)
- [AMEVA Open-Source Foundation Portal](https://uno-km.vercel.app/foundation/index.html)

---

## 📄 License
Licensed under the Apache-2.0 License. Copyright (c) 2026 Eunho Kim ([@uno-km](https://github.com/uno-km)).

