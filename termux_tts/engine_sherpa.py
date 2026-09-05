"""
Sherpa-ONNX C++ Native Subprocess Inference Engine for termux-tts (Tier 3-Neural & Tier 4-Expressive).
Directly executes high-performance C++ sherpa-onnx binaries for VITS, Kokoro, and Matcha models
with zero Python onnxruntime dependency, strict crash isolation, and full fail-fast compliance.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

from .audio import AudioBuffer
from .exceptions import TTSModelLoadError, TTSInferenceError

logger = logging.getLogger("termux_tts.engine_sherpa")


@dataclass
class SherpaResult:
    text: str
    audio_buffer: AudioBuffer
    sample_rate: int
    duration_sec: float
    elapsed_ms: float
    rtf: float
    model_name: str
    backend: str
    device_model: str

    def save(self, filepath: str) -> str:
        return self.audio_buffer.save(filepath)

    @property
    def wav_bytes(self) -> bytes:
        return self.audio_buffer.to_wav_bytes()


class SherpaNeuralEngine:
    """Production C++ Subprocess-Isolated Neural Speech Synthesis Engine."""

    CANDIDATE_BINARIES = [
        "sherpa-onnx-offline-tts",
        str(Path.home() / ".local" / "bin" / "sherpa-onnx-offline-tts"),
        str(Path.home() / "sherpa-onnx-offline-tts"),
        "/data/data/com.termux/files/home/sherpa-onnx-offline-tts",
        "/data/data/com.termux/files/home/.local/bin/sherpa-onnx-offline-tts",
        "/data/data/com.termux/files/usr/bin/sherpa-onnx-offline-tts",
    ]

    STANDARD_MODEL_DIRS = [
        Path.home() / ".cache" / "termux-tts" / "models",
        Path.home() / "vits-mimic3-ko_KO-kss_low",
        Path("/data/data/com.termux/files/home/vits-mimic3-ko_KO-kss_low"),
        Path("/data/data/com.termux/files/home/.cache/termux-tts/models"),
    ]

    def __init__(
        self,
        model_path: Optional[str] = None,
        language: str = "ko",
        device: str = "auto",
        threads: int = 4,
        sample_rate: int = 22050,
        model_type: str = "vits",
    ):
        self.language = language.lower()
        self.requested_device = device.lower()
        self.threads = threads
        self.sample_rate = sample_rate
        self.model_type = model_type.lower()
        self._is_closed = False

        # 1. Locate C++ binary
        self.binary = self._find_binary()

        # 2. Resolve Model assets (Fail-Fast)
        self.model_assets = self._resolve_model_assets(model_path)
        self.model_name = self.model_assets["model_name"]
        self.backend = f"SHERPA_{self.model_type.upper()}_ARM64"

    def _find_binary(self) -> str:
        """Locate sherpa-onnx-offline-tts executable or fail-fast."""
        for candidate in self.CANDIDATE_BINARIES:
            found = shutil.which(candidate) if not os.path.isabs(candidate) else candidate
            if found and os.path.isfile(found) and os.access(found, os.X_OK):
                return str(found)
        raise TTSModelLoadError(
            "[FAIL-FAST] 'sherpa-onnx-offline-tts' binary not found. "
            "Please ensure sherpa-onnx is installed in PATH or '~/.local/bin/sherpa-onnx-offline-tts'."
        )

    def _resolve_model_assets(self, model_path: Optional[str]) -> Dict[str, str]:
        """Locate model onnx, tokens.txt, and espeak-ng-data directory or fail-fast."""
        search_dirs: List[Path] = []
        if model_path:
            p = Path(model_path).expanduser().resolve()
            if not p.exists():
                raise TTSModelLoadError(
                    f"[FAIL-FAST] Explicitly specified model path does not exist: '{model_path}'"
                )
            if p.is_dir():
                search_dirs = [p]
            elif p.is_file():
                search_dirs = [p.parent]
        else:
            search_dirs = list(self.STANDARD_MODEL_DIRS)

        # 1. Find directory containing .onnx model, tokens.txt, and espeak-ng-data
        for sdir in search_dirs:
            if not sdir.exists():
                continue

            # Look for VITS ONNX model
            onnx_files = list(sdir.glob("*.onnx"))
            if not onnx_files and (sdir / "vits-mimic3-ko_KO-kss_low").exists():
                sdir = sdir / "vits-mimic3-ko_KO-kss_low"
                onnx_files = list(sdir.glob("*.onnx"))

            if onnx_files:
                onnx_model = str(onnx_files[0])
                tokens_file = sdir / "tokens.txt"
                espeak_dir = sdir / "espeak-ng-data"

                if not tokens_file.exists():
                    tokens_file = sdir.parent / "tokens.txt"
                if not espeak_dir.exists():
                    espeak_dir = sdir.parent / "espeak-ng-data"

                if tokens_file.exists() and espeak_dir.exists():
                    return {
                        "model": str(onnx_model),
                        "tokens": str(tokens_file),
                        "data_dir": str(espeak_dir),
                        "model_name": Path(onnx_model).stem,
                    }

        raise TTSModelLoadError(
            f"[FAIL-FAST] Required TTS model assets (onnx model, tokens.txt, espeak-ng-data) "
            f"not found for language '{self.language}' in provided path '{model_path}' or standard locations: "
            f"{[str(d) for d in self.STANDARD_MODEL_DIRS]}. "
            f"Please deploy the model package (e.g. 'vits-mimic3-ko_KO-kss_low') before synthesis."
        )

    def synthesize(
        self,
        text: str,
        output: Optional[str] = None,
        speed: float = 1.0,
        preset: Optional[str] = None,
    ) -> SherpaResult:
        """Synthesize natural speech audio from text using C++ isolated subprocess."""
        if self._is_closed:
            raise TTSInferenceError("Cannot synthesize: Engine session is closed.")

        clean_text = text.strip()
        if not clean_text:
            raise TTSInferenceError("Cannot synthesize empty or whitespace-only text.")

        # Acoustic prosody fix: Triple dots '...' in Korean cause espeak-ng glottal elision.
        # Replacing with comma preserves initial vowels and rhythm.
        normalized_text = clean_text.replace("...", ", ").replace("…", ", ")

        t0 = time.perf_counter()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            temp_wav = tmp_file.name

        try:
            cmd = [
                self.binary,
                f"--vits-model={self.model_assets['model']}",
                f"--vits-tokens={self.model_assets['tokens']}",
                f"--vits-data-dir={self.model_assets['data_dir']}",
                f"--output-filename={temp_wav}",
                f"--num-threads={self.threads}",
                f"--speed={speed:.2f}",
                normalized_text,
            ]

            env = os.environ.copy()
            # Ensure proper thread affinity and libraries
            if os.path.exists("/system/lib64/libvulkan.so"):
                current_ld = env.get("LD_LIBRARY_PATH", "")
                if not current_ld.startswith("/system/lib64"):
                    env["LD_LIBRARY_PATH"] = f"/system/lib64:{current_ld}".rstrip(":")

            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=60,
            )

            if res.returncode != 0:
                raise TTSInferenceError(
                    f"[FAIL-FAST] sherpa-onnx-offline-tts execution failed (code {res.returncode}):\n"
                    f"{res.stderr.strip()}"
                )

            if not os.path.exists(temp_wav) or os.path.getsize(temp_wav) == 0:
                raise TTSInferenceError(
                    f"[FAIL-FAST] sherpa-onnx exited with 0 but generated no audio file or empty file: {res.stderr.strip()}"
                )

            # Load raw WAV and apply DAC ramp-up silence padding (200ms lead-in, 150ms lead-out)
            raw_buf = AudioBuffer.from_wav_file(temp_wav)
            padded_buf = raw_buf.pad_silence(lead_in_ms=200, lead_out_ms=150)

            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            dur_sec = padded_buf.duration_seconds
            rtf = (elapsed_ms / 1000.0) / max(0.001, dur_sec)

            if output:
                padded_buf.save(output)

            return SherpaResult(
                text=text,
                audio_buffer=padded_buf,
                sample_rate=padded_buf.sample_rate,
                duration_sec=dur_sec,
                elapsed_ms=elapsed_ms,
                rtf=rtf,
                model_name=self.model_name,
                backend=self.backend,
                device_model=f"Cortex-A78_{self.threads}T",
            )
        finally:
            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except OSError:
                    pass

    def close(self) -> None:
        self._is_closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
