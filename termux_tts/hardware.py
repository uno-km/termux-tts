"""
Hardware abstraction gateway and dynamic ameva-runtime soft-dependency resolver for termux-tts.
Provides strict Zero-Silent-Fallback [AMEVA-TTS-E001] compliance, hardware-agnostic routing,
and seamless fallback to Tier 1 DSP Formant / Tier 2 Native voice when running standalone.
"""
from __future__ import annotations

import importlib.util
import logging
import sys
from typing import Optional, Tuple, Any

from .exceptions import VulkanInitializationError

logger = logging.getLogger("termux_tts.hardware")

ERROR_AMEVA_TTS_E001 = (
    "[FAIL-FAST] [ERROR: AMEVA-TTS-E001] GPU acceleration requires 'ameva-runtime' and provisioned Vulkan assets.\n"
    "Cause: Hardware acceleration runtime or native Vulkan engine is not installed.\n"
    "Action Required: Run one-click provisioning via:\n"
    "  $ termux-tts install --tier high\n"
    "  (Or run without GPU: termux-tts synth -e dsp -t \"...\")\n"
    "Documentation: https://uno-km.vercel.app/lib/tts/"
)


def _resolve_ameva_runtime() -> Optional[Any]:
    """Check for ameva_runtime availability without top-level static dependency.

    Returns the ameva_runtime module if installed, otherwise None.
    """
    try:
        spec = importlib.util.find_spec("ameva_runtime")
        if spec is not None:
            import ameva_runtime
            return ameva_runtime
    except (ImportError, AttributeError):
        pass
    return None


def resolve_device_backend(
    requested_device: str,
    requested_engine: str = "auto",
) -> Tuple[str, str]:
    """Resolve user requested device/engine into (device, engine_type) with fail-fast compliance.

    Returns:
        Tuple[str, str]: (device, engine_type) e.g. ('vulkan', 'vulkan') or ('cpu', 'dsp')
    """
    req_dev = (requested_device or "auto").lower().strip()
    req_eng = (requested_engine or "auto").lower().strip()
    ameva_mod = _resolve_ameva_runtime()

    # Explicit GPU/Vulkan requested
    if req_dev in ("vulkan", "gpu") or req_eng in ("vulkan", "gpu", "ncnn"):
        if ameva_mod is None:
            raise VulkanInitializationError(ERROR_AMEVA_TTS_E001)

        # Check Vulkan doctor from ameva_runtime TtsAdapter
        try:
            from ameva_runtime.adapters import TtsAdapter
            adapter = TtsAdapter()
            report = adapter.resolve_diagnostic_report()
            is_vk = getattr(report, "overall_success", False) or getattr(report, "recommended_backend", "") == "vulkan"
            if not is_vk:
                raise VulkanInitializationError(
                    f"[FAIL-FAST] [ERROR: AMEVA-TTS-E002] Vulkan hardware acceleration is not supported on this device.\n"
                    f"Cause: No usable Vulkan physical device or ICD driver library found.\n"
                    f"Action Required: Use CPU or DSP synthesis via '--device cpu' or '--engine dsp'."
                )
        except VulkanInitializationError:
            raise
        except Exception as e:
            logger.debug("TtsAdapter diagnostic exception: %s", e)
            raise VulkanInitializationError(
                f"[FAIL-FAST] [ERROR: AMEVA-TTS-E002] Vulkan hardware acceleration check failed: {e}\n"
                f"Action Required: Use CPU or DSP synthesis via '--device cpu' or '--engine dsp'."
            ) from e

        return "vulkan", "vulkan"

    # Auto mode: probe if ameva-runtime is available
    if req_dev == "auto":
        if ameva_mod is None:
            sys.stdout.write(
                "[INFO] ameva-runtime GPU engine is not provisioned. Operating in Tier 1 (Parametric DSP Formant) mode.\n"
            )
            sys.stdout.flush()
            return "cpu", req_eng

        try:
            from ameva_runtime.adapters import TtsAdapter
            adapter = TtsAdapter()
            report = adapter.resolve_diagnostic_report()
            is_vk = getattr(report, "overall_success", False) or getattr(report, "recommended_backend", "") == "vulkan"
            bin_path = adapter.resolve_binary_path()
            if is_vk and bin_path and req_eng in ("auto", "neural", "vits"):
                return "vulkan", "vulkan"
        except Exception as e:
            logger.debug("TtsAdapter auto-routing probe exception: %s", e)

        return "cpu", req_eng

    # Explicit CPU
    return "cpu", req_eng


def bind_tts_hardware(engine: Any, requested_device: str) -> Optional[Any]:
    """Safely invoke AMEVA-Runtime TtsAdapter if present to configure engine instance."""
    ameva_mod = _resolve_ameva_runtime()
    if ameva_mod is None:
        return None

    try:
        from ameva_runtime.adapters.tts import TtsAdapter
        binding = TtsAdapter.bind(engine=engine, requested_backend=requested_device)
        return binding
    except Exception as e:
        logger.debug("Hardware adapter binding skipped: %s", e)
        return None
