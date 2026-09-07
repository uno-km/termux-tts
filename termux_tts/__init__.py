"""
termux-tts: Production-Grade 4-Tier TTS Framework for Android Termux.
- Tier 1: Parametric DSP Formant Synthesizer Engine (0MB Zero-Dependency)
- Tier 2: Android System Native Voice Engine Bridge (Samsung / Google Voice)
- Tier 3: Authentic C++ Subprocess-Isolated Sherpa-ONNX Neural Vocoder (VITS Deep Learning)
- Tier 4: Pure On-Device Expressive Emotional Synthesizer (Conversational Tags)
"""

from .engine import TTSEngine, load, doctor
from .engine_native import NativeAndroidEngine, NativeResult
from .engine_dsp import ParametricDSPEngine, DSPResult, QUALITY_PRESETS, DSPSynthesizer
from .engine_sherpa import SherpaNeuralEngine, SherpaResult
from .engine_vulkan import VulkanNeuralEngine, VulkanResult
from .engine_expressive import ExpressiveEngine, ExpressiveResult
from .installer import run_installation
from .tokenizer import PhoneticTokenizer, EXPRESSIVE_TAGS
from .g2p_korean import KoreanG2PEngine, korean_text_to_phonemes
from .audio import AudioBuffer
from .exceptions import (
    TTSError,
    TTSModelLoadError,
    TTSInferenceError,
    VulkanInitializationError,
    TTSAudioEncodingError,
    TTSLanguageNotSupportedError
)

# Backward-compatibility alias
ONNXNeuralEngine = SherpaNeuralEngine
ONNXResult = SherpaResult

__version__ = "1.4.2"
__all__ = [
    "TTSEngine",
    "load",
    "doctor",
    "ParametricDSPEngine",
    "DSPSynthesizer",
    "DSPResult",
    "NativeAndroidEngine",
    "NativeResult",
    "SherpaNeuralEngine",
    "SherpaResult",
    "VulkanNeuralEngine",
    "VulkanResult",
    "ExpressiveEngine",
    "ExpressiveResult",
    "run_installation",
    "ONNXNeuralEngine",
    "ONNXResult",
    "QUALITY_PRESETS",
    "PhoneticTokenizer",
    "KoreanG2PEngine",
    "korean_text_to_phonemes",
    "EXPRESSIVE_TAGS",
    "AudioBuffer",
    "TTSError",
    "TTSModelLoadError",
    "TTSInferenceError",
    "VulkanInitializationError",
    "TTSAudioEncodingError",
    "TTSLanguageNotSupportedError"
]

