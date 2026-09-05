"""
Unit and Integration Tests for Real ONNX Neural Inference Engine & Gateway Routing.
"""

import os
import pytest
import numpy as np

import termux_tts as tts
from termux_tts.engine_onnx import ONNXNeuralEngine
from termux_tts.engine_dsp import ParametricDSPEngine
from termux_tts.exceptions import TTSModelLoadError, TTSInferenceError

def test_onnx_engine_missing_model_fail_fast():
    """Verify ONNXNeuralEngine raises TTSModelLoadError when model_path is None or onnxruntime missing."""
    with pytest.raises(TTSModelLoadError) as excinfo:
        ONNXNeuralEngine(model_path=None)
    err_str = str(excinfo.value)
    assert any(k in err_str for k in ("model_path", "onnxruntime", "binary", "assets"))

def test_onnx_engine_nonexistent_file_fail_fast():
    """Verify ONNXNeuralEngine raises TTSModelLoadError when file does not exist or binary missing."""
    with pytest.raises(TTSModelLoadError) as excinfo:
        ONNXNeuralEngine(model_path="nonexistent_vits_model.onnx")
    err_str = str(excinfo.value)
    assert any(k in err_str for k in ("does not exist", "not found", "onnxruntime", "binary", "assets"))

def test_dsp_engine_explicit_execution():
    """Verify ParametricDSPEngine executes with zero model dependencies."""
    with tts.load(engine="dsp", language="ko") as engine:
        assert isinstance(engine.synth_engine, ParametricDSPEngine)
        res = engine.synthesize("DSP 포먼트 엔진 단독 구동 테스트입니다.")
        assert res.duration_sec > 0.3
        assert res.model_name == "parametric-formant-dsp"

def test_gateway_auto_routing_to_dsp():
    """Verify TTSEngine defaults to ParametricDSPEngine in auto mode when no model file is given."""
    with tts.load(engine="auto", language="ko") as engine:
        assert isinstance(engine.synth_engine, ParametricDSPEngine)
        res = engine.synthesize("자동 라우팅 테스트입니다.")
        assert res.duration_sec > 0.3

def test_gateway_explicit_onnx_mode_requires_model():
    """Verify tts.load(engine='onnx') fails fast if no model file is given."""
    with pytest.raises(TTSModelLoadError):
        with tts.load(engine="onnx", language="ko") as engine:
            engine.synthesize("신경망 테스트")

