"""
engine_onnx.py — Backward-compatibility redirect to SherpaNeuralEngine.
Python onnxruntime is permanently deprecated in favor of C++ isolated SherpaNeuralEngine.
"""
from .engine_sherpa import SherpaNeuralEngine as ONNXNeuralEngine
from .engine_sherpa import SherpaResult as ONNXResult
from .vulkan_probe import VulkanDoctor

__all__ = ["ONNXNeuralEngine", "ONNXResult", "VulkanDoctor"]
