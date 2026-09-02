"""
Authentic ONNX Runtime Neural Inference Engine for termux-tts (Option A-Neural).
Executes deep learning VITS / Piper / FastSpeech ONNX neural acoustic models.
"""

import os
import time
import platform
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .exceptions import TTSModelLoadError, TTSInferenceError, VulkanInitializationError
from .tokenizer import PhoneticTokenizer
from .audio import AudioBuffer
from .vulkan_probe import VulkanDoctor
from .engine_dsp import apply_biquad_resonator, QUALITY_PRESETS, _detect_cpu_backend

@dataclass
class ONNXResult:
    text: str
    audio_buffer: AudioBuffer
    sample_rate: int
    duration_sec: float
    elapsed_ms: float
    rtf: float
    model_name: str
    preset: str
    backend: str
    device_model: str

    def save(self, filepath: str) -> str:
        return self.audio_buffer.save(filepath)

    @property
    def wav_bytes(self) -> bytes:
        return self.audio_buffer.to_wav_bytes()

class ONNXNeuralEngine:
    """Production-Grade ONNX Runtime Neural Speech Synthesis Engine."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        language: str = "ko",
        preset: str = "balanced",
        device: str = "auto",
        sample_rate: int = 22050
    ):
        self.language = language.lower()
        self.preset = preset.lower()
        self.requested_device = device.lower()
        self.sample_rate = sample_rate
        self.model_path = model_path
        self.tokenizer = PhoneticTokenizer(language=language)
        self._is_closed = False

        self.doctor = VulkanDoctor()
        self.diag_info = self.doctor.probe_all() if self.requested_device != "cpu" else {}

        # 1. Check onnxruntime availability
        try:
            import onnxruntime as ort
            self._ort = ort
        except ImportError as e:
            raise TTSModelLoadError(
                "Cannot initialize ONNXNeuralEngine: 'onnxruntime' is not installed in Python environment. "
                "Please run 'pip install onnxruntime' or use the zero-dependency DSP engine ('--engine dsp')."
            ) from e

        # 2. Validate and Load ONNX Model File
        if not self.model_path:
            raise TTSModelLoadError(
                "Cannot initialize ONNXNeuralEngine: 'model_path' was not provided. "
                "Please provide a valid .onnx model file path (e.g. '--model vits_ko.onnx') or use '--engine dsp'."
            )

        if not os.path.exists(self.model_path) or not os.path.isfile(self.model_path):
            raise TTSModelLoadError(
                f"Cannot initialize ONNXNeuralEngine: Model file '{self.model_path}' does not exist."
            )

        self.model_name = os.path.basename(self.model_path)
        self.session, self.backend = self._create_session()

    def _create_session(self):
        providers = []
        cpu_backend = _detect_cpu_backend()
        backend_name = f"ONNX_{cpu_backend}"

        if self.requested_device in ("vulkan", "gpu"):
            if self.doctor.is_vulkan_available:
                providers.append("VulkanExecutionProvider")
                backend_name = "ONNX_VULKAN_GPU"
            else:
                raise VulkanInitializationError(
                    f"[FAIL-FAST] Explicit GPU backend requested ('{self.requested_device}'), "
                    "but Vulkan hardware runtime is unavailable. Use '--device cpu' or '--device auto'."
                )
        elif self.requested_device == "auto":
            if self.doctor.is_vulkan_available:
                providers.append("VulkanExecutionProvider")
                backend_name = "ONNX_VULKAN_GPU"

        providers.append("CPUExecutionProvider")

        sess_options = self._ort.SessionOptions()
        sess_options.graph_optimization_level = self._ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = 4

        try:
            session = self._ort.InferenceSession(self.model_path, sess_options=sess_options, providers=providers)
            return session, backend_name
        except Exception as e:
            raise TTSModelLoadError(f"Failed to create ONNX Runtime session for '{self.model_path}': {e}") from e

    def synthesize(self, text: str, output: Optional[str] = None, speed: float = 1.0, preset: Optional[str] = None) -> ONNXResult:
        if self._is_closed:
            raise TTSInferenceError("Cannot synthesize: ONNX session is closed.")

        if not text or not text.strip():
            raise TTSInferenceError("Input text cannot be empty or whitespace only.")

        if speed <= 0.1 or speed > 3.0:
            raise TTSInferenceError(f"Speed multiplier must be in range (0.1, 3.0], got {speed}")

        t0 = time.perf_counter()
        token_ids = self.tokenizer.tokenize(text)
        if not token_ids:
            raise TTSInferenceError("Phonetic tokenization produced zero valid tokens.")

        # Prepare ONNX Tensor Inputs
        input_ids = np.array([token_ids], dtype=np.int64)
        input_lengths = np.array([len(token_ids)], dtype=np.int64)
        scales = np.array([0.667, 1.0 / speed, 0.8], dtype=np.float32)

        # Inspect model input signatures dynamically
        input_names = [inp.name for inp in self.session.get_inputs()]
        ort_inputs = {}

        if len(input_names) == 1:
            ort_inputs[input_names[0]] = input_ids
        else:
            for name in input_names:
                if "length" in name.lower():
                    ort_inputs[name] = input_lengths
                elif "scale" in name.lower():
                    ort_inputs[name] = scales
                else:
                    ort_inputs[name] = input_ids

        try:
            outputs = self.session.run(None, ort_inputs)
        except Exception as e:
            raise TTSInferenceError(f"ONNX Neural forward pass inference failed: {e}") from e

        # Extract waveform array
        raw_output = outputs[0]
        samples = np.squeeze(raw_output).astype(np.float32)

        elapsed_sec = time.perf_counter() - t0
        elapsed_ms = elapsed_sec * 1000.0

        audio_buf = AudioBuffer(samples, sample_rate=self.sample_rate)
        duration = audio_buf.duration_seconds
        rtf = elapsed_sec / max(duration, 0.001)

        if output:
            audio_buf.save(output)

        detected_device = (
            self.diag_info.get("DeviceModel")
            or self.diag_info.get("DeviceName")
            or f"{platform.system()} {platform.machine()}"
        )

        return ONNXResult(
            text=text,
            audio_buffer=audio_buf,
            sample_rate=self.sample_rate,
            duration_sec=duration,
            elapsed_ms=elapsed_ms,
            rtf=rtf,
            model_name=self.model_name,
            preset=preset or self.preset,
            backend=self.backend,
            device_model=detected_device
        )

    def close(self) -> None:
        self._is_closed = True
        self.session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

