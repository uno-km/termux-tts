# Release Notes - termux-tts v1.5.5

**Release Tag**: `v1.5.5`  
**Distribution Channels**: PyPI (`termux-tts`), NPM (`termux-tts`), GitHub Releases  
**Target Platform**: Android Termux (ARM64 / aarch64 Bionic)  
**License**: Apache-2.0  

---

## Highlights & Key Architectural Changes

### 1. Unified 5-Backend Standardization
- **Ecosystem Parameter Whitelist**: Aligned synthesis command choices to standard 5-set `["auto", "gpu", "vulkan", "opencl", "cpu"]`.
- **Fail-Fast Policy**: Eliminates unsupported or ambiguous arguments immediately.

### 2. Full Test Pass Verification
- **Test Suite Integrity**: Validated 54 passing unit tests across G2P phonemizers, DSP formant synthesizers, and multilingual neural vocoders.
