# Changelog

All notable changes to this project will be documented in this file.

## [1.4.4] - 2026-09-14

### Added
- **Multilingual Neural Orchestrator**: Integrated `MultilingualNeuralEngine` capable of dynamic cross-language code-switching across 9 official languages (ko, en, ja, zh, hi, ru, es, fr, de).
- **Resident C-API Acceleration**: Implemented `SherpaResidentManager` and `SherpaCapiSession` for in-memory model caching via direct C-API bindings, achieving sub-0.18x RTF and eliminating subprocess invocation overhead.
- **Zero-Config CLI Ergonomics**: Promoted speech synthesis (`synth`) as the default top-level subcommand; allows direct positional text (`termux-tts "text" --play`); eliminated necessity of `-e multilingual` flag.
- **Universal Unicode Script Classifier**: Built `MultilingualTokenizer` covering Hangul, Latin, Devanagari (Hindi), Cyrillic (Russian), CJK, and Arabic scripts with 50ms smooth pause padding.
- **On-Demand Model Provisioning & Self-Healing**: Enhanced `termux-tts install` to provision English/Korean by default, with on-demand flags (`--models hi/ja/ru/zh/all`) and actionable English guidance with absolute paths for uninstalled models.
- **Defensive Path Resolution**: Hardened path parsing across `AudioBuffer.save()` and CLI entrypoints with automatic directory creation and `Path.expanduser()` resolution.

---

## [1.4.3] - 2026-09-07

### Added
- **Multi-Tier Dynamic Candidate Resolution**: Replaced single hardcoded `v1.0.0-vulkan` URL in `installer.py` with 4-tier candidate resolution (`TERMUX_TTS_RELEASE_TAG`, `v{__version__}`, `releases/latest/download`, `uno-km/ameva-runtime` SSOT fallback, and companion fallback).
- **Dual-Path Installation**: Installs and links precompiled Vulkan binary `sherpa-ncnn-offline-tts` to both `~/.local/bin` and `$PREFIX/bin` for instant global PATH resolution.
- **Dynamic SSOT User-Agent**: Injects dynamic package version into download requests.

---

## [1.4.2] - 2026-09-07

### Added
- Complete 12-tier enterprise English documentation overhaul for PyPI and GitHub/NPM.
- Detailed empirical mobile hardware benchmarks (Snapdragon 8 Elite / Adreno 830, Exynos 1380 / Mali-G68 MP5).
- Full GPU interconnect architecture documentation with SPIR-V compute shader details.
- Comprehensive CPU vs. GPU thermal dissipation and latency trade-off analysis.
- 3-stage 24/7 unattended background execution guide (Termux wake-lock, battery optimization, ADB phantom process killer).
- Expanded technical SEO metadata keywords (34 keywords).

---

## [1.4.1] - 2026-09-07

### Fixed
- Fixed npm package.json bin path specification (removed './' prefix).
- Integrated GitHub Actions automated CI/CD release workflow.

---

## [1.4.0] - 2026-09-07

### Added
- Direct integration with `TtsAdapter` from `ameva_runtime.adapters` SSOT.
- Dual-tier VITS Vulkan neural engine routing with strict Fail-Fast error semantics.
- English localization for all diagnostics, logs, and exception messages.

---

## [1.1.5] - 2026-09-05

### Changed
- Synchronized install.sh hardware diagnostics binding to ameva-runtime.
- Modernized 12-stage hardware diagnostic bridge and documentation architecture diagrams.

---

## [1.1.4] - 2026-09-05

### Changed
- Migrated hardware acceleration dependency to unified `ameva-runtime>=2.0.0` and `@ameva/runtime>=2.0.0`.
- Synchronized Python and npm package versions to v1.1.4.


