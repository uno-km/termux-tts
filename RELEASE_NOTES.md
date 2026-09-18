# Release Notes - termux-tts v1.5.4

**Release Tag**: `v1.5.4`  
**Distribution Channels**: PyPI (`termux-tts`), NPM (`termux-tts`), GitHub Releases  
**Target Platform**: Android Termux (ARM64 / aarch64 Bionic)  
**License**: Apache-2.0  

---

## Highlights & Key Architectural Changes

### 1. 100% Zero-Hardcoding Dynamic Provisioning Architecture
- **Eradicated Static Version Fallbacks**: Permanently purged hardcoded release version strings (`v1.5.0`, `v1.2.7`) from `termux_tts/installer.py`.
- **3-Tier Latest-First Resolution Protocol**:
  1. **Tier 1 (Explicit Environment Overrides)**: Prioritizes `TERMUX_TTS_RELEASE_BASE` and `TERMUX_TTS_RELEASE_TAG` for staging and internal mirrors.
  2. **Tier 2 (GitHub Releases Latest Canonical SSOT)**: Directly fetches canonical unversioned binaries from `https://github.com/uno-km/termux-tts/releases/latest/download/sherpa-onnx-android-arm64.tar.gz` via HTTP 302 invariant redirection.
  3. **Tier 3 (Runtime Dynamic Version Resolution)**: Leverages `_resolve_package_version()` using `importlib.metadata` to bind to currently installed package version tags dynamically.
- **Dynamic HTTP User-Agent**: Replaced static user-agent headers with dynamic package version introspection (`termux-tts-installer/{ver}`).

### 2. Neural Voice Model Zero-Interruption Provisioning
- **Streamlined Candidate Endpoints**: Applied the same unified 3-Tier fallback hierarchy to all studio neural models (`vits-mimic3-ko_KO-kss_low`, `kokoro-multi-v1_0`, `vits-piper-en_US-lessac_low`).
- **Zero Silent Fallback**: Enforces strict Fail-Fast validation on corrupted downloads with actionable error reporting and hash integrity checks.

### 3. Unified Pip & NPM Packaging Parity
- **Full SemVer Synchronization**: Synchronized `pyproject.toml`, `setup.py`, `termux_tts/__init__.py`, and `package.json` to `1.5.4`.
- **Node.js Dual Engine CLI**: `npx termux-tts` seamlessly routes to native Bionic Sherpa-ONNX runtime with zero compilation delays.

---

## Detailed Changelog

### Changed
- `termux_tts/installer.py`: Replaced static release URLs with prioritized 3-Tier candidate URL generator.
- `termux_tts/installer.py`: Removed residual `__version__ = "1.5.0"` fallback in `download_with_progress`.
- `CHANGELOG.md`: Added release summary for `v1.5.4`.
- Package manifests (`pyproject.toml`, `package.json`, `setup.py`, `termux_tts/__init__.py`) bumped to `1.5.4`.

### Removed
- Legacy static URL candidates pointing to deprecated staging releases or third-party repositories.
