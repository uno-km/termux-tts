"""
Domain Specific Exceptions for termux-tts (Strict Fail-Fast Protocol).
Adheres to AOSF-ENG-STD-2026-V1 No-Fallback Governance.
"""

class TTSError(Exception):
    """Base exception for all termux-tts domain errors."""
    pass

class TTSModelLoadError(TTSError):
    """Raised when the neural TTS model file cannot be loaded or is corrupted."""
    pass

class TTSInferenceError(TTSError):
    """Raised when tensor forward pass or audio synthesis fails."""
    pass

class VulkanInitializationError(TTSInferenceError):
    """Raised when Vulkan GPU is explicitly requested but unavailable (Strict Fail-Fast)."""
    pass

class TTSAudioEncodingError(TTSError):
    """Raised when raw PCM cannot be encoded to standard WAV."""
    pass

class TTSLanguageNotSupportedError(TTSError):
    """Raised when the requested language is not supported by the current tokenizer."""
    pass
