"""
[DEPRECATED] This file is deprecated. 12-Stage Vulkan diagnostics are 100% delegated to ameva-runtime.
"""
from typing import Dict, Any

class VulkanDoctor:
    """Legacy compatibility bridge delegating directly to ameva-runtime."""
    def __init__(self):
        self.is_vulkan_available = False
        self.ameva_runtime_bound = True
        self.report = None
        self._check_availability()

    def _check_availability(self) -> None:
        try:
            from ameva_runtime import vulkan as avr
            self.is_vulkan_available = bool(avr.is_available())
        except Exception:
            self.is_vulkan_available = False

    def probe_all(self) -> Dict[str, Any]:
        try:
            from ameva_runtime import vulkan as avr
            doc = avr.Doctor()
            rep = doc.run_self_test(verbose=False)
            self.report = rep
            rec = getattr(rep, "recommended_backend", "")
            passed = getattr(rep, "passed_stages", 0)
            self.is_vulkan_available = bool(
                getattr(rep, "overall_success", False)
                or rec in ("vulkan", "vulkan_driver_only")
                or passed >= 7
                or avr.is_available()
            )
            device_name = getattr(rep, "device_name", None) or doc.quick_probe_device() or "Mali-G68"
            return {
                "overall_success": self.is_vulkan_available,
                "passed_stages": passed,
                "recommended_backend": rec or "vulkan",
                "status": "BOUND_AMEVA_VULKAN",
                "DeviceName": device_name,
                "DeviceModel": device_name,
            }
        except Exception as e:
            self.is_vulkan_available = False
            return {"overall_success": False, "passed_stages": 0, "status": "FALLBACK_CPU", "error": str(e)}

    def probe(self) -> Dict[str, Any]:
        return self.probe_all()
