"""
Unified 3-Tier Multi-Backend TTS Gateway for termux-tts:
1. Pure Parametric DSP Formant Synthesizer Engine (ParametricDSPEngine - 0MB Zero-Dependency)
2. Authentic ONNX Runtime Neural Vocoder Engine (ONNXNeuralEngine - Deep Learning)
3. Android System Native Samsung/Google Voice Engine Bridge (NativeAndroidEngine)
"""

import os
from typing import Optional, Union, Dict, Any

from .exceptions import TTSInferenceError
from .engine_native import NativeAndroidEngine, NativeResult
from .engine_dsp import ParametricDSPEngine, DSPResult, QUALITY_PRESETS
from .engine_onnx import ONNXNeuralEngine, ONNXResult
from .vulkan_probe import VulkanDoctor

class TTSEngine:
    """Production Multi-Backend Gateway supporting DSP, ONNX, and Native speech engines."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        language: str = "ko",
        preset: str = "balanced",
        device: str = "auto",
        sample_rate: Optional[int] = None,
        engine_type: str = "auto"
    ):
        self.language = language.lower()
        self.preset = preset.lower()
        self.requested_device = device.lower()
        self.requested_engine_type = engine_type.lower()
        self.model_path = model_path
        self.sample_rate = sample_rate
        self._is_closed = False

        self.native_engine = NativeAndroidEngine(language=language)
        self.synth_engine = self._resolve_synth_engine()

    def _resolve_synth_engine(self):
        if self.requested_engine_type == "onnx":
            return ONNXNeuralEngine(
                model_path=self.model_path,
                language=self.language,
                preset=self.preset,
                device=self.requested_device,
                sample_rate=self.sample_rate or 22050
            )
        elif self.requested_engine_type in ("dsp", "formant"):
            return ParametricDSPEngine(
                model_path=self.model_path,
                language=self.language,
                preset=self.preset,
                device=self.requested_device,
                sample_rate=self.sample_rate
            )
        elif self.requested_engine_type == "native":
            return self.native_engine
        elif self.requested_engine_type == "auto":
            if self.model_path and os.path.isfile(self.model_path):
                try:
                    return ONNXNeuralEngine(
                        model_path=self.model_path,
                        language=self.language,
                        preset=self.preset,
                        device=self.requested_device,
                        sample_rate=self.sample_rate or 22050
                    )
                except (ImportError, RuntimeError, OSError) as _onnx_err:
                    import logging
                    logging.getLogger(__name__).info(
                        "tts: ONNXNeuralEngine load failed (%s: %s); falling back to ParametricDSPEngine.",
                        type(_onnx_err).__name__, _onnx_err,
                    )
            return ParametricDSPEngine(
                model_path=self.model_path,
                language=self.language,
                preset=self.preset,
                device=self.requested_device,
                sample_rate=self.sample_rate
            )
        else:
            raise TTSInferenceError(
                f"Unknown engine_type '{self.requested_engine_type}'. Available: ['auto', 'dsp', 'onnx', 'native']"
            )

    @property
    def active_backend(self) -> str:
        return getattr(self.synth_engine, "backend", "NATIVE_SYSTEM")

    @property
    def model_name(self) -> str:
        return getattr(self.synth_engine, "model_name", "native-system-voice")

    @property
    def binary(self) -> Optional[str]:
        return getattr(self.native_engine, "binary", None)

    def speak(self, text: str, stream: Optional[str] = None) -> NativeResult:
        """Speak text directly through physical Android speaker (Native Engine)."""
        if self._is_closed:
            raise TTSInferenceError("Cannot speak: Engine session is closed.")
        return self.native_engine.speak(text, stream=stream)

    def synthesize(self, text: str, output: Optional[str] = None, speed: float = 1.0, preset: Optional[str] = None) -> Union[DSPResult, ONNXResult]:
        """Synthesize text into speech audio buffer / WAV file (DSP or ONNX Engine)."""
        if self._is_closed:
            raise TTSInferenceError("Cannot synthesize: Engine session is closed.")
        return self.synth_engine.synthesize(text, output=output, speed=speed, preset=preset)

    def close(self) -> None:
        self._is_closed = True
        self.native_engine.close()
        if hasattr(self.synth_engine, "close"):
            self.synth_engine.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def load(
    model: Optional[str] = None,
    language: str = "ko",
    preset: str = "balanced",
    device: str = "auto",
    sample_rate: Optional[int] = None,
    engine: str = "auto"
) -> TTSEngine:
    return TTSEngine(
        model_path=model,
        language=language,
        preset=preset,
        device=device,
        sample_rate=sample_rate,
        engine_type=engine
    )

def doctor() -> Dict[str, Any]:
    try:
        from ameva_runtime import vulkan as avr
        from ameva_runtime.vulkan.adapters import TtsAdapter
        doc = avr.Doctor()
        rep = doc.run_self_test(verbose=False)
        return {
            "doctor_report": rep,
            "overall_success": getattr(rep, "overall_success", False),
            "passed_stages": getattr(rep, "passed_stages", 0),
            "recommended_backend": getattr(rep, "recommended_backend", "cpu"),
            "status": "DIAGNOSED_VIA_AMEVA"
        }
    except Exception as e:
        return {
            "doctor_report": None,
            "overall_success": False,
            "passed_stages": 0,
            "recommended_backend": "cpu_neon",
            "error": str(e),
            "status": "FALLBACK_CPU"
        }

