"""
Unified 4-Tier Multi-Backend TTS Gateway for termux-tts:
- Tier 1: Pure Parametric DSP Formant Synthesizer Engine (ParametricDSPEngine - 0MB Zero-Dependency)
- Tier 2: Android System Native Samsung/Google Voice Engine Bridge (NativeAndroidEngine - 0MB OS IPC)
- Tier 3: Authentic C++ Isolated Sherpa-ONNX VITS Neural Vocoder (SherpaNeuralEngine - Deep Learning)
- Tier 4: Pure On-Device Expressive Emotional Synthesizer (ExpressiveEngine - Conversational Tags)

Strict Zero-Silent-Fallback Protocol:
- If caller explicitly requests 'neural' and assets are missing -> Raise TTSModelLoadError (FAIL-FAST)
- If caller explicitly requests 'native' and termux-api is missing -> Raise TTSInferenceError (FAIL-FAST)
- Never swallow exceptions or mask failures with robotic buzzers without explicit instruction.
"""
from __future__ import annotations

import logging
import os
from typing import Optional, Union, Dict, Any

from .exceptions import TTSInferenceError, TTSModelLoadError, VulkanInitializationError
from .engine_native import NativeAndroidEngine, NativeResult
from .engine_dsp import ParametricDSPEngine, DSPResult, QUALITY_PRESETS
from .engine_sherpa import SherpaNeuralEngine, SherpaResult
from .engine_vulkan import VulkanNeuralEngine, VulkanResult
from .engine_expressive import ExpressiveEngine, ExpressiveResult
from .vulkan_probe import VulkanDoctor

logger = logging.getLogger("termux_tts.engine")


class TTSEngine:
    """Production 4-Tier Multi-Backend Gateway supporting Synth, Native, Neural, and Expressive engines."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        language: str = "ko",
        preset: str = "balanced",
        device: str = "auto",
        threads: int = 4,
        sample_rate: Optional[int] = None,
        engine_type: str = "auto",
    ):
        self.language = language.lower()
        self.preset = preset.lower()
        self.requested_device = device.lower()
        self.requested_engine_type = engine_type.lower()
        self.model_path = model_path
        self.threads = threads
        self.sample_rate = sample_rate
        self.device = self.requested_device
        self.backend = "auto"
        self._is_closed = False

        if self.requested_device in ("vulkan", "gpu"):
            doc = VulkanDoctor()
            if not doc.is_vulkan_available:
                raise VulkanInitializationError(
                    f"[FAIL-FAST] Explicit GPU backend requested ('{self.requested_device}'), "
                    "but Vulkan hardware runtime is unavailable. Use '--device cpu' or '--device auto'."
                )

        # Attempt ameva-runtime hardware binding if available
        self._binding_plan = self._bind_hardware()

        self.native_engine = NativeAndroidEngine(language=language)
        self.synth_engine = self._resolve_synth_engine()

    def _bind_hardware(self):
        try:
            from ameva_runtime.adapters.tts import TtsAdapter
            binding = TtsAdapter.bind(engine=self, requested_backend=self.requested_device)
            return binding
        except Exception as e:
            logger.debug("Hardware adapter binding skipped: %s", e)
            return None

    def _resolve_synth_engine(self):
        t = self.requested_engine_type

        # Explicit Vulkan GPU Tier (Fail-Fast)
        if t in ("vulkan", "gpu", "ncnn") or (self.requested_device in ("vulkan", "gpu") and t in ("neural", "vits", "auto")):
            try:
                return VulkanNeuralEngine(
                    model_path=self.model_path,
                    language=self.language,
                    device=self.requested_device,
                    threads=self.threads,
                    sample_rate=self.sample_rate or 22050,
                )
            except (VulkanInitializationError, TTSModelLoadError) as err:
                if t in ("vulkan", "gpu", "ncnn") or self.requested_device in ("vulkan", "gpu"):
                    raise
                logger.debug("Vulkan neural engine not ready, trying fallback: %s", err)

        # Explicit Tier 3: Neural (Sherpa-ONNX CPU)
        if t in ("neural", "onnx", "sherpa", "vits"):
            return SherpaNeuralEngine(
                model_path=self.model_path,
                language=self.language,
                device=self.requested_device,
                threads=self.threads,
                sample_rate=self.sample_rate or 22050,
                model_type="vits",
            )

        # Explicit Tier 4: Expressive (Fail-Fast)
        elif t in ("expressive", "chat", "conversational"):
            return ExpressiveEngine(
                model_path=self.model_path,
                language=self.language,
                device=self.requested_device,
                threads=self.threads,
                sample_rate=self.sample_rate or 22050,
            )

        # Explicit Tier 1: Synth / DSP
        elif t in ("synth", "dsp", "formant"):
            return ParametricDSPEngine(
                model_path=self.model_path,
                language=self.language,
                preset=self.preset,
                device=self.requested_device,
                sample_rate=self.sample_rate,
            )

        # Explicit Tier 2: Native
        elif t == "native":
            return self.native_engine

        # Auto Mode
        elif t == "auto":
            # 1. Check if SherpaNeuralEngine assets exist
            try:
                return SherpaNeuralEngine(
                    model_path=self.model_path,
                    language=self.language,
                    device=self.requested_device,
                    threads=self.threads,
                    sample_rate=self.sample_rate or 22050,
                )
            except TTSModelLoadError as err:
                logger.info("Auto tier: Neural model assets not ready (%s). Probing native system voice...", err)

            # 2. Check if NativeAndroidEngine is available
            if self.native_engine.binary:
                return self.native_engine

            # 3. Fallback to zero-dependency DSP Synth
            return ParametricDSPEngine(
                model_path=self.model_path,
                language=self.language,
                preset=self.preset,
                device=self.requested_device,
                sample_rate=self.sample_rate,
            )
        else:
            raise TTSInferenceError(
                f"[FAIL-FAST] Unknown engine_type '{self.requested_engine_type}'. "
                f"Available tiers: ['auto', 'synth', 'native', 'neural', 'expressive']"
            )

    @property
    def active_backend(self) -> str:
        return getattr(self.synth_engine, "backend", "NATIVE_SYSTEM")

    @property
    def model_name(self) -> str:
        return getattr(self.synth_engine, "model_name", "native-system-voice")

    @property
    def binary(self) -> Optional[str]:
        return getattr(self.synth_engine, "binary", getattr(self.native_engine, "binary", None))

    def speak(self, text: str, stream: Optional[str] = None) -> NativeResult:
        """Speak text directly through physical Android speaker (Native Engine)."""
        if self._is_closed:
            raise TTSInferenceError("Cannot speak: Engine session is closed.")
        return self.native_engine.speak(text, stream=stream)

    def synthesize(
        self,
        text: str,
        output: Optional[str] = None,
        speed: float = 1.0,
        preset: Optional[str] = None,
    ) -> Union[DSPResult, SherpaResult, ExpressiveResult, NativeResult]:
        """Synthesize text into speech audio buffer / WAV file."""
        if self._is_closed:
            raise TTSInferenceError("Cannot synthesize: Engine session is closed.")
        if hasattr(self.synth_engine, "synthesize"):
            return self.synth_engine.synthesize(text, output=output, speed=speed, preset=preset)
        elif hasattr(self.synth_engine, "speak"):
            return self.synth_engine.speak(text)
        raise TTSInferenceError(f"Selected engine '{type(self.synth_engine).__name__}' does not support synthesize.")

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
    threads: int = 4,
    sample_rate: Optional[int] = None,
    engine: str = "auto",
) -> TTSEngine:
    return TTSEngine(
        model_path=model,
        language=language,
        preset=preset,
        device=device,
        threads=threads,
        sample_rate=sample_rate,
        engine_type=engine,
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
            "status": "DIAGNOSED_VIA_AMEVA",
        }
    except Exception as e:
        return {
            "doctor_report": None,
            "overall_success": False,
            "passed_stages": 0,
            "recommended_backend": "cpu_neon",
            "error": str(e),
            "status": "FALLBACK_CPU",
        }
