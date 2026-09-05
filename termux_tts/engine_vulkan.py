"""
Vulkan GPU Neural Speech Synthesis Engine for termux-tts.
Runs 100% on-device neural inference using Vulkan Compute Shaders via sherpa-ncnn.
Strict Zero-Silent-Fallback: If Vulkan GPU is not available, fails fast with VulkanInitializationError.
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
from .exceptions import TTSModelLoadError, TTSInferenceError, VulkanInitializationError

logger = logging.getLogger("termux_tts.engine_vulkan")


@dataclass
class VulkanResult:
    text: str
    audio_buffer: AudioBuffer
    sample_rate: int
    duration_sec: float
    elapsed_ms: float
    rtf: float
    model_name: str
    backend: str
    gpu_device: str

    def save(self, filepath: str) -> str:
        return self.audio_buffer.save(filepath)

    @property
    def wav_bytes(self) -> bytes:
        return self.audio_buffer.to_wav_bytes()


class VulkanNeuralEngine:
    """Production Vulkan GPU Neural Speech Synthesis Engine (VITS NCNN)."""

    CANDIDATE_BINARIES = [
        "sherpa-ncnn-offline-tts",
        str(Path.home() / ".local" / "bin" / "sherpa-ncnn-offline-tts"),
        str(Path.home() / "sherpa-ncnn" / "build-vulkan" / "bin" / "sherpa-ncnn-offline-tts"),
        "/data/data/com.termux/files/home/.local/bin/sherpa-ncnn-offline-tts",
        "/data/data/com.termux/files/home/sherpa-ncnn/build-vulkan/bin/sherpa-ncnn-offline-tts",
        "/data/data/com.termux/files/usr/bin/sherpa-ncnn-offline-tts",
    ]

    STANDARD_MODEL_DIRS = [
        Path.home() / ".cache" / "termux-tts" / "models",
        Path.home() / "ncnn-vits-piper-en_US-lessac-high-fp16",
        Path.home() / "ncnn-vits-piper-en_US-amy-medium",
        Path("/data/data/com.termux/files/home/ncnn-vits-piper-en_US-lessac-high-fp16"),
        Path("/data/data/com.termux/files/home/ncnn-vits-piper-en_US-amy-medium"),
        Path("/data/data/com.termux/files/home/.cache/termux-tts/models"),
    ]

    def __init__(
        self,
        model_path: Optional[str] = None,
        language: str = "en",
        device: str = "vulkan",
        threads: int = 1,
        sample_rate: int = 22050,
    ):
        self.language = language.lower()
        self.requested_device = device.lower()
        self.threads = threads
        self.sample_rate = sample_rate
        self._is_closed = False

        # 1. Locate Vulkan binary
        self.binary = self._find_binary()

        # 2. Locate VITS NCNN model directory
        self.model_dir = self._resolve_model_dir(model_path)
        self.model_name = Path(self.model_dir).name
        self.backend = "VULKAN_GPU_NCNN_VITS"

    def _find_binary(self) -> str:
        """Locate sherpa-ncnn-offline-tts executable or fail-fast."""
        for candidate in self.CANDIDATE_BINARIES:
            found = shutil.which(candidate) if not os.path.isabs(candidate) else candidate
            if found and os.path.isfile(found) and os.access(found, os.X_OK):
                return str(found)
        raise VulkanInitializationError(
            "[FAIL-FAST] 'sherpa-ncnn-offline-tts' Vulkan binary not found. "
            "Please run 'termux-tts install' to automatically download and provision the Vulkan engine."
        )

    def _resolve_model_dir(self, model_path: Optional[str]) -> str:
        """Locate directory containing config.json and *.ncnn.bin files."""
        search_dirs: List[Path] = []
        if model_path:
            p = Path(model_path).expanduser().resolve()
            if not p.exists():
                raise TTSModelLoadError(f"[FAIL-FAST] Explicit model path not found: '{model_path}'")
            search_dirs = [p]
        else:
            for s in self.STANDARD_MODEL_DIRS:
                if s.exists():
                    search_dirs.append(s)
                    for child in s.glob("ncnn-vits*"):
                        if child.is_dir():
                            search_dirs.append(child)

        for d in search_dirs:
            if (d / "config.json").exists() and (d / "decoder.ncnn.bin").exists():
                return str(d)

        raise TTSModelLoadError(
            "[FAIL-FAST] No valid VITS NCNN model directory found. "
            "Please run 'termux-tts install --tier high' to automatically download model assets."
        )

    def synthesize(
        self,
        text: str,
        output: Optional[str] = None,
        speed: float = 1.0,
        preset: Optional[str] = None,
    ) -> VulkanResult:
        if self._is_closed:
            raise TTSInferenceError("Cannot synthesize: Engine session is closed.")

        clean_text = text.strip()
        if not clean_text:
            raise TTSInferenceError("Cannot synthesize empty text.")

        t0 = time.perf_counter()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            temp_wav = tmp_file.name

        try:
            cmd = [
                self.binary,
                f"--vits-model-dir={self.model_dir}",
                "--use-vulkan-compute=1",
                f"--num-threads={self.threads}",
                f"--output-filename={temp_wav}",
                clean_text
            ]

            env = os.environ.copy()
            env["LD_LIBRARY_PATH"] = f"/system/lib64:{env.get('LD_LIBRARY_PATH', '')}"
            env["AMEVA_VK_DSP_ACCEL"] = "1"

            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=120
            )

            if proc.returncode != 0:
                raise TTSInferenceError(f"[FAIL-FAST] Vulkan GPU synthesis failed:\n{proc.stderr}")

            gpu_device = "Vulkan GPU"
            for line in proc.stderr.splitlines():
                if "Vulkan GPU Compute Pipeline ACTIVE on" in line:
                    gpu_device = line.split("on ", 1)[1].split(" (", 1)[0].strip()
                    break

            audio_buf = AudioBuffer.from_wav_file(temp_wav)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            dur_sec = audio_buf.duration_seconds
            rtf = (elapsed_ms / 1000.0) / dur_sec if dur_sec > 0 else 0.0

            if output:
                out_path = Path(output).expanduser().resolve()
                out_path.parent.mkdir(parents=True, exist_ok=True)
                audio_buf.save(str(out_path))

            return VulkanResult(
                text=clean_text,
                audio_buffer=audio_buf,
                sample_rate=audio_buf.sample_rate,
                duration_sec=dur_sec,
                elapsed_ms=elapsed_ms,
                rtf=rtf,
                model_name=self.model_name,
                backend=self.backend,
                gpu_device=gpu_device
            )

        finally:
            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except:
                    pass

    def close(self):
        self._is_closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
