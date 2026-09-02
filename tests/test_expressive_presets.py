"""
Expressive Presets & Non-Verbal Acoustic Tokens Audit Suite for termux-tts.
Tests Fast, Balanced, Expressive, Ultra presets and [laugh], [sigh], [breath], [clears_throat] tags.
"""

import time
import pytest
import numpy as np
import termux_tts as tts
from termux_tts.engine import QUALITY_PRESETS, load

def test_all_four_presets_synthesis():
    for preset_name in ["fast", "balanced", "expressive", "ultra"]:
        t0 = time.perf_counter()
        with load(language="ko", preset=preset_name) as engine:
            res = engine.synthesize(f"현재 {preset_name} 품질 프리셋으로 음성을 합성 중입니다.")
            assert res.preset == preset_name
            assert res.sample_rate == QUALITY_PRESETS[preset_name]["sample_rate"]
            assert res.duration_sec > 0.3
            assert len(res.wav_bytes) > 1000
            print(f"\n[PASS PRESET: {preset_name:10s}] Duration={res.duration_sec:.2f}s | Latency={res.elapsed_ms:.1f}ms | Rate={res.sample_rate}Hz")

def test_expressive_breath_and_laugh_tokens():
    expressive_text = "[clears_throat] 으흠! 안녕하세요 [laugh] 하하하! 오늘 날씨가 참 좋습니다 [sigh] 휴... [breath]"
    with load(language="ko", preset="expressive") as engine:
        res = engine.synthesize(expressive_text, output="expressive_demo.wav")
        assert res.duration_sec > 1.0
        assert res.sample_rate == 24000
        print(f"\n[PASS EXPRESSIVE SYNTHESIS] Synthesized in {res.elapsed_ms:.1f}ms | Duration={res.duration_sec:.2f}s")
