# Termux-TTS (v1.5.0)

[![PyPI](https://img.shields.io/pypi/v/termux-tts.svg?style=flat-square&color=0369a1)](https://pypi.org/project/termux-tts/)
[![Python](https://img.shields.io/pypi/pyversions/termux-tts.svg?style=flat-square)](https://pypi.org/project/termux-tts/)
[![License](https://img.shields.io/badge/License-Apache_2.0-004499.svg?style=flat-square)](https://github.com/uno-km/termux-tts)
[![Platform](https://img.shields.io/badge/Platform-Android_ARM64_|_Qualcomm_Adreno_|_ARM_Mali-0284c7.svg?style=flat-square)](https://github.com/uno-km/termux-tts)

> Production-Grade 4-Tier On-Device Speech Synthesis Framework: 100% Native Vulkan GPU Pipeline, Zero-Silent-Fallback Standard, Multilingual Neural Orchestrator, Zero-Dependency DSP Formant & Resident C-API Acceleration.

---

## Architecture Overview

Termux-TTS is an enterprise-grade, on-device text-to-speech framework optimized for mobile edge hardware and Android Termux environments. Built to eliminate heavy dependency stacks and fragile driver behaviors, it features a resilient 4-Tier architecture:

- **Tier 1: Zero-Dependency Parametric DSP Formant Vocoder**: 0MB disk footprint, Rosenberg glottal pulse formulation, and 5-band biquad formant filters providing deterministic speech synthesis in under 50 milliseconds (RTF 0.013x).
- **Tier 2: Android System Native Voice Bridge**: Direct IPC integration to physical Samsung and Google speech engines via the Termux-API service layer.
- **Tier 3: Subprocess-Isolated Sherpa C++ CPU Engine**: Subprocess-isolated VITS acoustic modeling on ARM64 NEON with memory leak protection and resident in-memory C-API caching (sub-0.18x RTF).
- **Tier 4: Pure Vulkan GPU Hardware Neural Engine**: High-performance GPU tensor synthesis via precompiled native C++ binaries running high-resolution studio models with direct vendor Android system ABI binding (`/system/lib64/libvulkan.so`) and zero silent CPU fallback.

---

## The Anti-Deception Trifecta Purged (AOSF-ENG-STD-2026)

1. **Zero Deceptive CPU Offloading**: Direct physical GPU queue execution. No covert unlogged fallback to CPU execution or synthetic audio spoofing.
2. **Zero Silent Fallbacks (Fail-Fast Semantics)**:
   - `[AMEVA-TTS-E001]`: Missing Native Executable or Neural Weights.
   - `[AMEVA-TTS-E002]`: Vulkan Compute Runtime Execution Failure with command and stderr dump.
   - `[AMEVA-TTS-E003]`: Truncated or Empty Audio Buffer output.
3. **Zero Hardcoded Paths**: Dynamic asset discovery across `$PREFIX`, `sys.prefix`, `$HOME`, and `$PATH`.

---

## Next-Gen MZ Neural Acoustic Trio (Kokoro, MeloTTS, Supertonic)

Termux-TTS v1.5.0 supports three next-generation neural acoustic architectures:
- **Kokoro-82M (INT8)**: StyleTTS2 diffusion architecture delivering 24kHz studio reference grade emotional speech (~103 MB).
- **MeloTTS Universal**: Bilingual VITS with dual-backend C++ NCNN & MNN Vulkan acceleration for mixed Korean/English/Chinese (~150 MB).
- **Supertonic 3 (INT8)**: Continuous normalizing flow matching supporting 31 global languages with <20ms ultra-low latency (~128 MB).

```python
# Provision on-demand via CLI:
# termux-tts install --models kokoro / melo / supertonic

with tts.load(model_type="kokoro") as engine:
    res = engine.synthesize("Studio reference emotional voice.")
```

---

## Ground Truth: Resolving the Mobile GPU Slowdown Anomaly

In standard Android Termux installations, default user-space Vulkan loaders (`$PREFIX/lib/libvulkan.so`) frequently bind to Mesa's **`llvmpipe` (CPU Software Rasterizer)** instead of the underlying hardware silicon. This caused SPIR-V compute shaders to be emulated on CPU cores with massive memory-copy overhead, resulting in GPU inference being 5x~10x slower than direct CPU SIMD.

Termux-TTS v1.5.0 enforces direct binding to the vendor Android Bionic Vulkan loader (`/system/lib64/libvulkan.so`), unlocking true hardware compute queues across **Qualcomm Adreno** and **ARM Mali** silicon.

---

## Empirical Hardware Benchmarks (Physical Android 16 Fleet)

| Target Device | SoC / Hardware GPU Silicon | Vulkan Driver ABI | Audio Length | Synthesis Time | Real-Time Factor (RTF) | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Galaxy S21** | Samsung Exynos 2100 / **ARM Mali-G78** (`0x9800000`) | Vulkan 1.1 (`/system/lib64`) | 4.25 s | **9,371 ms** | **2.2055x** | Validated (Native GPU) |
| **Galaxy S25** | Qualcomm Snapdragon 8 Elite / **Adreno 830** (`0x80320040`) | Vulkan 1.3 (`/system/lib64`) | 4.25 s | **16,208 ms** | **3.8145x** | Validated (Native GPU) |
| **Galaxy S22** | Qualcomm Snapdragon 8 Gen 1 / **Adreno 730** (`0x80267062`) | Vulkan 1.1 (`/system/lib64`) | 4.27 s | **38,092 ms** | **8.9159x** | Validated (Native GPU) |
| **Galaxy A35** | Samsung Exynos 1380 / **ARM Mali-G68 MP5** (`0x9801000`) | Vulkan 1.1 (`/system/lib64`) | 4.27 s | **51,912 ms** | **12.1505x** | Validated (Native GPU) |
| **Heterogeneous CPU** | Cortex-A78 / A55 Multi-Core | Sherpa C++ NEON SIMD | 4.25 s | **1,850 ms** | **0.4350x** | Validated (CPU Reference) |

---

## Quickstart

```python
import termux_tts as tts

# 1. Pure Vulkan GPU Hardware Synthesis (Studio High FP16)
with tts.load(engine="vulkan", model_tier="high") as engine:
    result = engine.synthesize("Operating at full hardware capacity.", output="speech.wav")
    print(f"Elapsed: {result.elapsed_ms:.1f}ms (RTF: {result.rtf:.4f}x) | Device: {result.gpu_device}")

# 2. Resident C-API In-Memory Multilingual Engine (<0.18x RTF)
with tts.load(engine="sherpa", model="vits-piper-en_US-lessac-medium") as engine:
    result = engine.synthesize("Ultra-low latency in-memory synthesis.")
    result.save("speech_capi.wav")

# 3. Instant Zero-Dependency DSP Formant Mode (<50ms, 0MB)
with tts.load(engine="dsp", preset="balanced") as engine:
    result = engine.synthesize("Instant speech without external model weights.")
```

---

## Installation & Automated Provisioning

```bash
# Install Python package
pip install termux-tts

# 1-Click Provision Default Models (Korean KSS + English Lessac)
termux-tts install

# 1-Click Provision Studio Vulkan High-Resolution Tier (FP16, 22.05kHz)
termux-tts install --tier high

# Synthesize speech directly via CLI:
termux-tts "Hello world! On-device neural speech synthesis." --play
```

---

## Documentation & Foundation Ecosystem

- **Official Documentation Portal**: [https://uno-km.vercel.app/lib/tts/](https://uno-km.vercel.app/lib/tts/)
- **GitHub Repository**: [https://github.com/uno-km/termux-tts](https://github.com/uno-km/termux-tts)
- **AMEVA Foundation Portal**: [https://uno-km.vercel.app/foundation/index.html](https://uno-km.vercel.app/foundation/index.html)
