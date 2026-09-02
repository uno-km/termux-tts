"""
termux_tts.control.status
AMEVA Component Protocol v1 — TTS 상태 파일 Writer + Heartbeat

상태 파일 갱신 트리거:
  - Worker 시작
  - 모델 활성화/비활성화
  - Job 시작 (active_jobs++) / 종료 (active_jobs--)
  - 엔진 오류 발생 (ready=false, errors 기록)
  - 정상 종료 (remove() 호출)
  - Heartbeat 주기 (10초)

stale 판정: 현재 시각 - updated_at_unix_ms > stale_threshold_ms
마지막 정상 상태를 계속 정상으로 표시하면 안 됩니다.
"""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Any

from ameva_component import ComponentStateFile, now_timestamps
from ameva_component.identity import PROTOCOL_STATUS

COMPONENT_ID = "termux-tts"
HEARTBEAT_INTERVAL_S = 10


class TTSStatusWriter:
    """
    termux-tts 상태 파일을 원자적으로 갱신합니다.

    ComponentStateFile을 내부적으로 보유하고, 상태 변화 시마다
    protocol / component_id / updated_at* / ready 필드를 갱신합니다.
    """

    def __init__(self, state_dir: Path | None = None) -> None:
        self._sf = ComponentStateFile(COMPONENT_ID, state_dir=state_dir)
        self._lock = threading.Lock()
        self._active_model_id: str | None = None
        self._active_voice_id: str | None = None
        self._active_engine: str | None = None   # "dsp" | "onnx" | "native"
        self._active_jobs: int = 0
        self._last_error: str | None = None
        self._pid: int = os.getpid()
        self._heartbeat_thread: threading.Thread | None = None
        self._stop_heartbeat = threading.Event()

    # ------------------------------------------------------------------
    # 상태 파일 경로 조회
    # ------------------------------------------------------------------

    @property
    def path(self) -> Path:
        return self._sf.path

    # ------------------------------------------------------------------
    # 쓰기 헬퍼
    # ------------------------------------------------------------------

    def _build_payload(self, *, ready: bool, degraded: bool = False) -> dict[str, Any]:
        ts = now_timestamps()
        return {
            "protocol": PROTOCOL_STATUS,
            "component_id": COMPONENT_ID,
            "ready": ready,
            "degraded": degraded,
            "pid": self._pid,
            "active_model_id": self._active_model_id,
            "active_voice_id": self._active_voice_id,
            "active_engine": self._active_engine,
            "active_jobs": self._active_jobs,
            "last_error": self._last_error,
            **ts,
        }

    def _write(self, *, ready: bool, degraded: bool = False) -> None:
        """Lock 안에서 호출하는 저수준 쓰기 메서드."""
        self._sf.write(self._build_payload(ready=ready, degraded=degraded))

    # ------------------------------------------------------------------
    # 공개 API — 각 트리거 시점에 호출
    # ------------------------------------------------------------------

    def on_start(self, *, engine: str | None = None) -> None:
        """Worker 시작 시 호출합니다."""
        with self._lock:
            self._active_engine = engine
            self._write(ready=True)

    def on_model_activated(
        self,
        model_id: str,
        *,
        voice_id: str | None = None,
        engine: str | None = None,
    ) -> None:
        """모델 활성화 완료 시 호출합니다."""
        with self._lock:
            self._active_model_id = model_id
            self._active_voice_id = voice_id
            if engine:
                self._active_engine = engine
            self._last_error = None
            self._write(ready=True)

    def on_model_deactivated(self) -> None:
        """모델 비활성화 시 호출합니다."""
        with self._lock:
            self._active_model_id = None
            self._active_voice_id = None
            self._active_engine = None
            self._write(ready=True)

    def on_job_start(self) -> None:
        """Job 시작 시 호출합니다 (active_jobs++)."""
        with self._lock:
            self._active_jobs += 1
            self._write(ready=True)

    def on_job_end(self) -> None:
        """Job 종료 시 호출합니다 (active_jobs--)."""
        with self._lock:
            self._active_jobs = max(0, self._active_jobs - 1)
            self._write(ready=True)

    def on_engine_error(self, error: str) -> None:
        """엔진 오류 발생 시 호출합니다 (ready=false)."""
        with self._lock:
            self._last_error = error
            self._write(ready=False, degraded=True)

    def on_shutdown(self) -> None:
        """정상 종료 시 호출합니다. 상태 파일을 제거합니다."""
        self.stop_heartbeat()
        self._sf.remove()

    def heartbeat(self) -> None:
        """Heartbeat 주기(10초)에 호출합니다."""
        with self._lock:
            self._write(ready=True)

    # ------------------------------------------------------------------
    # Heartbeat 백그라운드 스레드
    # ------------------------------------------------------------------

    def start_heartbeat(self) -> None:
        """백그라운드 Heartbeat 스레드를 시작합니다."""
        if self._heartbeat_thread is not None and self._heartbeat_thread.is_alive():
            return
        self._stop_heartbeat.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="tts-heartbeat",
        )
        self._heartbeat_thread.start()

    def stop_heartbeat(self) -> None:
        """Heartbeat 스레드를 중단합니다."""
        self._stop_heartbeat.set()
        if self._heartbeat_thread is not None:
            self._heartbeat_thread.join(timeout=HEARTBEAT_INTERVAL_S + 1)
            self._heartbeat_thread = None

    def _heartbeat_loop(self) -> None:
        while not self._stop_heartbeat.wait(timeout=HEARTBEAT_INTERVAL_S):
            try:
                self.heartbeat()
            except Exception:
                pass   # Heartbeat 실패가 프로세스를 죽이면 안 됨
