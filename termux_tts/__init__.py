"""
termux-tts: Production-Grade Dual-Engine TTS Framework for Android Termux.
- Option A: Deep Learning VITS ONNX Neural Vocoder (Vulkan GPU Accelerated)
- Option B: Android System Native Voice Engine Bridge (Samsung / Google Voice)
"""

from .engine import TTSEngine, load, doctor
from .engine_native import NativeAndroidEngine, NativeResult
from .engine_dsp import ParametricDSPEngine, DSPResult, QUALITY_PRESETS
from .engine_onnx import ONNXNeuralEngine, ONNXResult
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

__version__ = "0.1.0"
__all__ = [
    "TTSEngine",
    "load",
    "doctor",
    "ParametricDSPEngine",
    "DSPResult",
    "NativeAndroidEngine",
    "NativeResult",
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
