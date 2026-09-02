"""
12-Stage Vulkan GPU Hardware Probe and ameva-vulkan-runtime Integration Layer.
Delegates 100% to official 'ameva-vulkan-runtime' SDK (Doctor / TtsAdapter / VulkanContext).
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("termux_tts.vulkan_probe")

class VulkanDoctor:
    """12-Stage Vulkan GPU Diagnostics & ameva-vulkan-runtime TtsAdapter Bridge."""

    def __init__(self):
        self.is_vulkan_available = False
        self.ameva_runtime_bound = False
        self.report = None
        self._check_ameva_runtime()

    def _check_ameva_runtime(self) -> None:
        """Attempt to bind with the official ameva-vulkan-runtime SDK."""
        try:
            import ameva_vulkan_runtime as avr
            from ameva_vulkan_runtime.adapters import TtsAdapter
            doc = avr.Doctor()
            report = doc.run_self_test(verbose=False)
            self.report = report
            if getattr(report, "overall_success", False):
                self.is_vulkan_available = True
                self.ameva_runtime_bound = True
            else:
                self.is_vulkan_available = False
                self.ameva_runtime_bound = False
        except Exception as e:
            logger.debug("[termux-tts] ameva-vulkan-runtime probing exception: %s", e)
            self.is_vulkan_available = False
            self.ameva_runtime_bound = False

    def probe_all(self) -> Dict[str, Any]:
        """Execute full 12-stage validation suite (V0~V11) via ameva-vulkan-runtime."""
        results: Dict[str, Any] = {}
        if self.report is not None:
            results["DeviceModel"] = self.report.device_name or "Generic ARM64 Device"
            results["AmevaVulkanRuntime"] = "BOUND (TtsAdapter)" if self.ameva_runtime_bound else "FALLBACK_CPU"
            results["OverallSuccess"] = "PASS" if self.report.overall_success else "FAIL"
            for stage in self.report.stages:
                results[f"V{stage.stage_id}_{stage.stage_name}"] = stage.result
        else:
            results["AmevaVulkanRuntime"] = "UNAVAILABLE"
            results["OverallSuccess"] = "FAIL"
        return results
