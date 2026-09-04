"""
termux_tts.adapter
===================
AMEVA Component Protocol v1 — Orchestrator Adapter (v0.8.1 호환)
"""
from __future__ import annotations

from typing import Any, AsyncIterator

from ameva_component.adapter_base import BaseOrchestratorAdapter
from termux_tts.control.component import TTSControl


class TTSOrchestratorAdapter(BaseOrchestratorAdapter):
    """TTS (Text-to-Speech) Orchestrator Adapter.

    합성은 파일 기반으로 수행됩니다.
    infer()는 text를 받아 audio 파일 경로를 반환합니다.
    요청 모델과 실행 모델이 다르면 fallback_used=True를 명시합니다.
    """

    COMPONENT_ID = "termux-tts"

    def __init__(self, control: TTSControl | None = None) -> None:
        self._control = control or TTSControl()

    async def infer(self, request: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """TTS synthesis: text → audio file path.

        request 키:
            text (str): 합성할 텍스트 (필수)
            voice_id (str): 목소리 ID (선택)
            model_id (str): 모델 ID (선택)
            output_path (str): 출력 파일 경로 (선택, 없으면 임시 파일)

        반환 프레임:
            {"type": "audio", "audio_path": str, "final": bool, "fallback_used": bool}
            {"type": "error", "code": str, "message": str}
        """
        text = request.get("text", "").strip()
        if not text:
            yield {
                "type": "error",
                "ok": False,
                "error": {
                    "code": "TEXT_EMPTY",
                    "message": "text is required and must not be empty",
                    "operation": "infer",
                    "component_id": self.COMPONENT_ID,
                    "retryable": False,
                },
            }
            return

        if hasattr(self._control, "synthesize"):
            try:
                result = await self._control.synthesize(request)
                audio_path = result.get("audio_path", "")
                if not audio_path:
                    yield {
                        "type": "error",
                        "ok": False,
                        "error": {
                            "code": "SYNTHESIS_FAILED",
                            "message": "synthesize() returned no audio_path",
                            "operation": "infer",
                            "component_id": self.COMPONENT_ID,
                            "retryable": True,
                        },
                    }
                    return
                yield {
                    "type": "audio",
                    "audio_path": audio_path,
                    "final": True,
                    "fallback_used": result.get("fallback_used", False),
                    "requested_voice": result.get("requested_voice"),
                    "executed_voice": result.get("executed_voice"),
                    "ok": True,
                }
            except Exception as exc:
                yield {
                    "type": "error",
                    "ok": False,
                    "error": {
                        "code": "SYNTHESIS_FAILED",
                        "message": str(exc),
                        "operation": "infer",
                        "component_id": self.COMPONENT_ID,
                        "retryable": True,
                    },
                }
        else:
            yield self._not_supported("infer.synthesize")


def create_adapter() -> TTSOrchestratorAdapter:
    """Entry Point Factory."""
    return TTSOrchestratorAdapter()
