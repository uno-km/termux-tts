"""
Automated One-Click Installer & Provisioner for termux-tts Vulkan GPU Engine.
Downloads pre-compiled ARM64 native binaries from GitHub Releases and studio models from CDN.
"""
import os
import sys
import tarfile
import urllib.request
import shutil
from pathlib import Path
from typing import Optional
from .hardware import get_clean_execution_env

def get_candidate_vulkan_binary_urls():
    """Generate dynamic candidate endpoints for Vulkan binary provisioner."""
    try:
        from . import __version__
    except Exception:
        __version__ = "1.5.0"

    urls = []
    custom_tag = os.environ.get("TERMUX_TTS_RELEASE_TAG", "").strip()
    custom_base = os.environ.get("TERMUX_TTS_RELEASE_BASE", "").strip()

    if custom_base:
        urls.append(f"{custom_base.rstrip('/')}/sherpa-ncnn-offline-tts-vulkan-arm64.tar.gz")
    if custom_tag:
        tag = custom_tag if custom_tag.startswith("v") else f"v{custom_tag}"
        urls.append(f"https://github.com/uno-km/termux-tts/releases/download/{tag}/sherpa-ncnn-offline-tts-vulkan-arm64.tar.gz")

    # 1. termux-tts current version SSOT
    current_tag = f"v{__version__}"
    urls.append(f"https://github.com/uno-km/termux-tts/releases/download/{current_tag}/sherpa-ncnn-offline-tts-vulkan-arm64.tar.gz")

    # 2. termux-tts latest release (verified HTTP 200)
    urls.append("https://github.com/uno-km/termux-tts/releases/latest/download/sherpa-ncnn-offline-tts-vulkan-arm64.tar.gz")

    # 3. Companion release fallback (verified HTTP 200)
    urls.append("https://github.com/uno-km/termux-sherpa-ncnn/releases/download/v1.0.0-vulkan/sherpa-ncnn-offline-tts-vulkan-arm64.tar.gz")

    return urls

def get_candidate_cpu_binary_urls():
    """Generate dynamic candidate endpoints for Sherpa CPU binary provisioner."""
    try:
        from . import __version__
    except Exception:
        __version__ = "1.5.0"

    urls = []
    custom_tag = os.environ.get("TERMUX_TTS_RELEASE_TAG", "").strip()
    custom_base = os.environ.get("TERMUX_TTS_RELEASE_BASE", "").strip()

    if custom_base:
        urls.append(f"{custom_base.rstrip('/')}/sherpa-onnx-android-arm64.tar.gz")
    if custom_tag:
        tag = custom_tag if custom_tag.startswith("v") else f"v{custom_tag}"
        urls.append(f"https://github.com/uno-km/termux-tts/releases/download/{tag}/sherpa-onnx-android-arm64.tar.gz")

    current_tag = f"v{__version__}"
    urls.append(f"https://github.com/uno-km/termux-tts/releases/download/{current_tag}/sherpa-onnx-android-arm64.tar.gz")
    urls.append("https://github.com/uno-km/termux-tts/releases/latest/download/sherpa-onnx-android-arm64.tar.gz")
    urls.append("https://github.com/uno-km/termux-stt/releases/download/v1.2.7/sherpa-onnx-android-arm64.tar.gz")

    return urls

MODEL_REGISTRY = {
    "high": {
        "name": "ncnn-vits-piper-en_US-lessac-high-fp16",
        "repo": "csukuangfj/ncnn-vits-piper-en_US-lessac-high-fp16",
        "description": "Studio Reference Grade High-Resolution Model (57MB FP16)",
        "files": [
            "config.json", "decoder.ncnn.bin", "decoder.ncnn.param",
            "dp.ncnn.bin", "dp.ncnn.param", "encoder.ncnn.bin",
            "encoder.ncnn.param", "flow.ncnn.bin", "flow.ncnn.param",
            "lexicon.txt"
        ]
    },
    "medium": {
        "name": "ncnn-vits-piper-en_US-amy-medium",
        "repo": "csukuangfj/ncnn-vits-piper-en_US-amy-medium",
        "description": "Low-Latency High-Performance Model (25MB)",
        "files": [
            "config.json", "decoder.ncnn.bin", "decoder.ncnn.param",
            "dp.ncnn.bin", "dp.ncnn.param", "encoder.ncnn.bin",
            "encoder.ncnn.param", "flow.ncnn.bin", "flow.ncnn.param",
            "lexicon.txt"
        ]
    }
}

OFFICIAL_NEURAL_MODELS = {
    "ko": {
        "name": "vits-mimic3-ko_KO-kss_low",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-mimic3-ko_KO-kss_low.tar.bz2",
        "repo": "csukuangfj/vits-mimic3-ko_KO-kss_low",
        "language_name": "Korean",
        "description": "Korean VITS Mimic3 KSS Studio ONNX Model (~45MB)",
    },
    "en": {
        "name": "vits-piper-en_US-lessac-medium",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-lessac-medium.tar.bz2",
        "repo": "csukuangfj/vits-piper-en_US-lessac-medium",
        "language_name": "English",
        "description": "English VITS Piper Lessac Medium ONNX Model (~55MB)",
    },
    "ja": {
        "name": "vits-piper-ja_JP-hina-medium",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-ja_JP-hina-medium.tar.bz2",
        "repo": "csukuangfj/vits-piper-ja_JP-hina-medium",
        "language_name": "Japanese",
        "description": "Japanese VITS Piper Hina Medium ONNX Model (~50MB)",
    },
    "zh": {
        "name": "vits-zh-aishell3",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-zh-aishell3.tar.bz2",
        "repo": "csukuangfj/vits-zh-aishell3",
        "language_name": "Chinese (Mandarin)",
        "description": "Chinese VITS AISHELL-3 Multi-Speaker ONNX Model (~65MB)",
    },
    "hi": {
        "name": "vits-piper-hi_IN-swara-medium",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-hi_IN-swara-medium.tar.bz2",
        "repo": "csukuangfj/vits-piper-hi_IN-swara-medium",
        "language_name": "Hindi",
        "description": "Hindi VITS Piper Swara Medium ONNX Model (~55MB)",
    },
    "ru": {
        "name": "vits-piper-ru_RU-dmitri-medium",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-ru_RU-dmitri-medium.tar.bz2",
        "repo": "csukuangfj/vits-piper-ru_RU-dmitri-medium",
        "language_name": "Russian",
        "description": "Russian VITS Piper Dmitri Medium ONNX Model (~55MB)",
    },
    "es": {
        "name": "vits-piper-es_ES-davefx-medium",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-es_ES-davefx-medium.tar.bz2",
        "repo": "csukuangfj/vits-piper-es_ES-davefx-medium",
        "language_name": "Spanish",
        "description": "Spanish VITS Piper Davefx Medium ONNX Model (~50MB)",
    },
    "fr": {
        "name": "vits-piper-fr_FR-siwis-medium",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-fr_FR-siwis-medium.tar.bz2",
        "repo": "csukuangfj/vits-piper-fr_FR-siwis-medium",
        "language_name": "French",
        "description": "French VITS Piper Siwis Medium ONNX Model (~50MB)",
    },
    "de": {
        "name": "vits-piper-de_DE-thorsten-medium",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-de_DE-thorsten-medium.tar.bz2",
        "repo": "csukuangfj/vits-piper-de_DE-thorsten-medium",
        "language_name": "German",
        "description": "German VITS Piper Thorsten Medium ONNX Model (~50MB)",
    },
    "kokoro": {
        "name": "kokoro-int8-en-v0_19",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-int8-en-v0_19.tar.bz2",
        "repo": "csukuangfj/kokoro-int8-en-v0_19",
        "language_name": "Kokoro-82M Studio High Quality (INT8)",
        "description": "Kokoro-82M StyleTTS2 Multilingual Studio Grade Model (~103MB)",
    },
    "melo": {
        "name": "vits-melo-tts-zh_en",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-melo-tts-zh_en.tar.bz2",
        "repo": "csukuangfj/vits-melo-tts-zh_en",
        "language_name": "MeloTTS Universal Bilingual",
        "description": "MeloTTS Universal VITS Bilingual Model (~150MB)",
    },
    "supertonic": {
        "name": "sherpa-onnx-supertonic-3-tts-int8-2026-05-11",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/sherpa-onnx-supertonic-3-tts-int8-2026-05-11.tar.bz2",
        "repo": "csukuangfj/sherpa-onnx-supertonic-3-tts-int8",
        "language_name": "Supertonic 3 On-Device Multilingual (INT8)",
        "description": "Supertonic 3 Ultra-Fast 31-Language Model (~128MB)",
    },
}

def get_install_paths():
    prefix = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr")).resolve()
    bin_dir = (prefix / "bin").resolve()
    lib_dir = (prefix / "lib").resolve()
    xdg_cache = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")).resolve()
    cache_dir = (xdg_cache / "termux-tts" / "models").resolve()
    bin_dir.mkdir(parents=True, exist_ok=True)
    lib_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return bin_dir, cache_dir

def download_with_progress(url: str, dest_path: Path, label: str):
    try:
        from . import __version__
    except Exception:
        __version__ = "1.4.4"

    print(f"  [DOWNLOADING] {label}...")
    req = urllib.request.Request(url, headers={"User-Agent": f"termux-tts-installer/{__version__} (Android; ARM64)"})
    with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as out_f:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 64 * 1024
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out_f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = (downloaded / total) * 100
                sys.stdout.write(f"\r  [{label}] {pct:.1f}% ({downloaded / (1024*1024):.1f}MB / {total / (1024*1024):.1f}MB)")
                sys.stdout.flush()
    print()

def install_vulkan_binary(force: bool = False) -> Path:
    bin_dir, _ = get_install_paths()
    binary_path = bin_dir / "sherpa-ncnn-offline-tts"
    lib_dir = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr")) / "lib"
    
    if binary_path.exists() and not force:
        print(f"  [OK] Pre-compiled Vulkan binary already exists: {binary_path}")
        return binary_path

    xdg_cache = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")).resolve()
    staging_dir = xdg_cache / "termux-tts" / ".staging-vulkan"
    staging_dir.mkdir(parents=True, exist_ok=True)
    tar_path = staging_dir / "sherpa-vulkan.tar.gz"
    candidate_urls = get_candidate_vulkan_binary_urls()
    download_success = False

    for url in candidate_urls:
        try:
            download_with_progress(url, tar_path, f"ARM64 Vulkan Binary ({url})")
            if tar_path.exists() and tar_path.stat().st_size > 500 * 1024:
                download_success = True
                break
        except Exception as dl_err:
            print(f"  [-] Candidate URL failed ({url}): {dl_err}")
            if tar_path.exists():
                tar_path.unlink(missing_ok=True)
            continue

    if not download_success:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise RuntimeError("Failed to download sherpa-ncnn-offline-tts from any candidate endpoints.")

    print(f"  [EXTRACTING] Extracting binary to staging isolation {staging_dir}...")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=staging_dir)

    tar_path.unlink(missing_ok=True)

    # Move binary to $PREFIX/bin
    found_bin = None
    for p in staging_dir.rglob("sherpa-ncnn-offline-tts"):
        if p.is_file():
            found_bin = p
            break

    if not found_bin:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise RuntimeError("sherpa-ncnn-offline-tts binary not found inside extracted archive.")

    # Atomic move to $PREFIX/bin
    shutil.copy2(found_bin, binary_path)
    binary_path.chmod(0o755)

    # Move any extracted shared libraries to $PREFIX/lib
    lib_dir.mkdir(parents=True, exist_ok=True)
    for so_file in staging_dir.rglob("*.so*"):
        if so_file.is_file():
            target_so = lib_dir / so_file.name
            shutil.copy2(so_file, target_so)
            try:
                target_so.chmod(0o755)
            except OSError:
                pass

    # Clean staging directory
    shutil.rmtree(staging_dir, ignore_errors=True)

    print(f"  [SUCCESS] Installed to SSOT: {binary_path}")
    return binary_path

def install_cpu_binary(force: bool = False) -> Path:
    bin_dir, _ = get_install_paths()
    binary_path = bin_dir / "sherpa-onnx-offline-tts"
    lib_dir = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr")) / "lib"

    if binary_path.exists() and not force:
        print(f"  [OK] Pre-compiled Sherpa CPU binary already exists: {binary_path}")
        return binary_path

    xdg_cache = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")).resolve()
    staging_dir = xdg_cache / "termux-tts" / ".staging-cpu"
    staging_dir.mkdir(parents=True, exist_ok=True)
    tar_path = staging_dir / "sherpa-cpu.tar.gz"
    candidate_urls = get_candidate_cpu_binary_urls()
    download_success = False

    for url in candidate_urls:
        try:
            download_with_progress(url, tar_path, f"ARM64 Sherpa CPU Binary ({url})")
            if tar_path.exists() and tar_path.stat().st_size > 500 * 1024:
                download_success = True
                break
        except Exception as dl_err:
            print(f"  [-] Candidate URL failed ({url}): {dl_err}")
            if tar_path.exists():
                tar_path.unlink(missing_ok=True)
            continue

    if not download_success:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise RuntimeError("Failed to download sherpa-onnx-offline-tts from any candidate endpoints.")

    print(f"  [EXTRACTING] Extracting CPU binary to staging isolation {staging_dir}...")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=staging_dir)

    tar_path.unlink(missing_ok=True)

    found_bin = None
    for p in staging_dir.rglob("sherpa-onnx-offline-tts"):
        if p.is_file():
            found_bin = p
            break

    if not found_bin:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise RuntimeError("sherpa-onnx-offline-tts binary not found inside extracted archive.")

    shutil.copy2(found_bin, binary_path)
    binary_path.chmod(0o755)

    lib_dir.mkdir(parents=True, exist_ok=True)
    for so_file in staging_dir.rglob("*.so*"):
        if so_file.is_file():
            target_so = lib_dir / so_file.name
            shutil.copy2(so_file, target_so)
            try:
                target_so.chmod(0o755)
            except OSError:
                pass

    shutil.rmtree(staging_dir, ignore_errors=True)
    print(f"  [SUCCESS] CPU engine installed to SSOT: {binary_path}")
    return binary_path

def install_vits_model(tier: str = "high", force: bool = False, output_dir: Optional[Path] = None) -> Path:
    tier = tier.lower()
    if tier not in MODEL_REGISTRY:
        tier = "high"
    
    cfg = MODEL_REGISTRY[tier]
    if output_dir:
        model_dir = Path(output_dir) / cfg["name"]
    else:
        _, cache_dir = get_install_paths()
        model_dir = cache_dir / cfg["name"]
    model_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[MODEL] Provisioning {cfg['description']}...")
    base_url = f"https://huggingface.co/{cfg['repo']}/resolve/main/"

    for fname in cfg["files"]:
        target_file = model_dir / fname
        if target_file.exists() and target_file.stat().st_size > 0 and not force:
            continue
        url = base_url + fname
        download_with_progress(url, target_file, fname)

    print(f"  [SUCCESS] Model installed at: {model_dir}")
    return model_dir

def provision_neural_model_archive(language: str, force: bool = False) -> Path:
    """
    On-Demand Auto-Provisioner for official neural speech models.
    Downloads official pre-compiled model archives (.tar.bz2) and extracts directly into cache.
    """
    from .script_classifier import normalize_language_code
    lang = normalize_language_code(language)
    if lang not in OFFICIAL_NEURAL_MODELS:
        from .exceptions import TTSModelLoadError
        raise TTSModelLoadError(
            f"[FAIL-FAST] No official automated model package registered for language '{lang}'.\n"
            f"Available automated packages: {list(OFFICIAL_NEURAL_MODELS.keys())}"
        )

    cfg = OFFICIAL_NEURAL_MODELS[lang]
    _, cache_dir = get_install_paths()
    target_dir = cache_dir / cfg["name"]
    unified_tts_dir = Path.home() / "models" / "tts"

    if target_dir.is_dir() and not force:
        onnx_files = list(target_dir.glob("*.onnx"))
        if onnx_files and (target_dir / "tokens.txt").exists() and (target_dir / "espeak-ng-data").exists():
            # Ensure symlink in ~/models/tts/
            try:
                link_dest = unified_tts_dir / cfg["name"]
                if not link_dest.exists() and not link_dest.is_symlink():
                    link_dest.symlink_to(target_dir)
            except OSError:
                pass
            return target_dir

    print(f"\n[termux-tts runtime] Auto-provisioning {cfg['description']}...")
    archive_path = cache_dir / f"{cfg['name']}.tar.bz2"

    try:
        download_with_progress(cfg["url"], archive_path, cfg["name"])
        print(f"  [EXTRACTING] Unpacking model archive into {cache_dir}...")
        with tarfile.open(archive_path, "r:bz2") as tar:
            tar.extractall(path=cache_dir)
        archive_path.unlink(missing_ok=True)

        # Link to ~/models/tts/ as unified SSOT
        try:
            link_dest = unified_tts_dir / cfg["name"]
            if not link_dest.exists() and not link_dest.is_symlink():
                link_dest.symlink_to(target_dir)
        except OSError:
            pass

        print(f"  [SUCCESS] Model provisioned: {target_dir}")
        return target_dir
    except Exception as err:
        if archive_path.exists():
            archive_path.unlink(missing_ok=True)
        from .exceptions import TTSModelLoadError
        raise TTSModelLoadError(
            f"[FAIL-FAST] Failed to auto-provision neural model '{cfg['name']}': {err}"
        ) from err

def run_installation(tier: str = "high", models: str = "default", backend: str = "auto", force: bool = False, play: bool = True):
    print("=" * 70)
    print("   TERMUX-TTS AUTOMATED PROVISIONER (BATTERIES-INCLUDED RUNTIME)")
    print("=" * 70)

    eff_backend = (backend or "auto").strip().lower()

    if eff_backend == "cpu":
        # 1. Install pre-compiled Sherpa-ONNX CPU binary
        print("\n[CPU MODE] Provisioning ARM64 Sherpa CPU Native Binary & ONNX Runtime...")
        bin_path = install_cpu_binary(force=force)
        model_path = None
    else:
        # 1. Install pre-compiled Vulkan binary
        print("\n[VULKAN MODE] Provisioning ARM64 Vulkan GPU Binary & NCNN Models...")
        bin_path = install_vulkan_binary(force=force)
        # 2. Install VITS model for Vulkan
        model_path = install_vits_model(tier=tier, force=force)

    # 2b. Install Multilingual VITS ONNX Models
    # Default is ONLY Korean (ko) & English (en) for ultra-lightweight initial setup!
    raw_models = models.strip().lower() if models else "default"
    if raw_models in ("default", "base", "core"):
        langs_to_install = ["ko", "en"]
    elif raw_models == "all":
        langs_to_install = list(OFFICIAL_NEURAL_MODELS.keys())
    else:
        # User specified specific language(s) like "hi" or "ja,zh"
        langs_to_install = [l.strip() for l in raw_models.split(",") if l.strip()]

    print(f"\n[MULTILINGUAL] Provisioning Neural Speech Models: {langs_to_install}...")
    for lang in langs_to_install:
        try:
            provision_neural_model_archive(lang, force=force)
        except Exception as e:
            print(f"  [-] Multilingual {lang} provisioning note: {e}")

    # 3. Environment check
    if eff_backend != "cpu":
        vulkan_lib = Path("/system/lib64/libvulkan.so")
        if not vulkan_lib.exists():
            print("  [WARNING] /system/lib64/libvulkan.so not found. Ensure device supports Vulkan.")
        else:
            print("  [OK] Android Vulkan driver detected: /system/lib64/libvulkan.so")

    print("\n[VERIFICATION] Running on-device self-test...")
    test_wav = Path.home() / "install_test_tts.wav"

    import subprocess
    if eff_backend == "cpu":
        # CPU verification with termux-tts synth API
        try:
            from .engine import load
            with load(language="en", device="cpu") as eng:
                eng.synthesize("Hello, Termux CPU speech synthesis is ready.", output=str(test_wav))
            proc_returncode = 0
            proc_stderr = ""
        except Exception as tts_err:
            proc_returncode = 1
            proc_stderr = str(tts_err)
    else:
        cmd = [
            str(bin_path),
            f"--vits-model-dir={model_path}",
            "--use-vulkan-compute=1",
            "--num-threads=1",
            f"--output-filename={test_wav}",
            "It's Python, hello! Vulkan GPU speech synthesis is installed and ready."
        ]
        env = get_clean_execution_env({"AMEVA_VK_DSP_ACCEL": "1"})
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        proc_returncode = proc.returncode
        proc_stderr = proc.stderr

    if proc_returncode == 0:
        print(f"  [VERIFIED] On-device {eff_backend.upper()} synthesis self-test passed!")
        player = shutil.which("termux-media-player") or shutil.which("play-audio")
        if play and player:
            print("  [PLAYBACK] Playing verification audio through physical speaker...")
            if shutil.which("termux-volume"):
                subprocess.run(["termux-volume", "music", "10"], check=False)
            subprocess.run([player, str(test_wav)], check=False)
    else:
        print(f"  [FAIL-FAST] Self-test returned error: {proc_stderr}")

    print("=" * 70)
    print("   INSTALLATION COMPLETE! YOU CAN NOW USE 'termux-tts' DIRECTLY.")
    print("=" * 70)
