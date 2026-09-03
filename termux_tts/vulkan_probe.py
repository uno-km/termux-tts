"""
[DEPRECATED] This file is deprecated. 12-Stage Vulkan diagnostics are 100% delegated to ameva-vulkan-runtime.
"""
from typing import Dict, Any

class VulkanDoctor:
    """Legacy compatibility bridge delegating directly to ameva-vulkan-runtime."""
    def __init__(self):
        self.is_vulkan_available = False
        self.ameva_runtime_bound = True
        self.report = None

    def probe_all(self) -> Dict[str, Any]:
        try:
            import ameva_vulkan_runtime as avr
            doc = avr.Doctor()
            rep = doc.run_self_test(verbose=False)
            return {
                "overall_success": getattr(rep, "overall_success", False),
                "passed_stages": getattr(rep, "passed_stages", 0),
                "recommended_backend": getattr(rep, "recommended_backend", "cpu"),
                "status": "BOUND_AMEVA_VULKAN"
            }
        except Exception as e:
            return {"overall_success": False, "passed_stages": 0, "status": "FALLBACK_CPU", "error": str(e)}
