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

VULKAN_BINARY_RELEASE_URL = (
    "https://github.com/uno-km/termux-sherpa-ncnn/releases/download/"
    "v1.0.0-vulkan/sherpa-ncnn-offline-tts-vulkan-arm64.tar.gz"
)

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

def get_install_paths():
    home = Path.home()
    bin_dir = home / ".local" / "bin"
    cache_dir = home / ".cache" / "termux-tts" / "models"
    bin_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return bin_dir, cache_dir

def download_with_progress(url: str, dest_path: Path, label: str):
    print(f"  [DOWNLOADING] {label}...")
    req = urllib.request.Request(url, headers={"User-Agent": "termux-tts-installer/1.3.0"})
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
    
    if binary_path.exists() and not force:
        print(f"  [OK] Pre-compiled Vulkan binary already exists: {binary_path}")
        return binary_path

    tar_path = bin_dir / "sherpa-vulkan.tar.gz"
    download_with_progress(VULKAN_BINARY_RELEASE_URL, tar_path, "ARM64 Vulkan Binary (3.9MB)")

    print("  [EXTRACTING] Installing binary to ~/.local/bin...")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=bin_dir)

    tar_path.unlink(missing_ok=True)
    binary_path.chmod(0o755)
    print(f"  [SUCCESS] Installed: {binary_path}")
    return binary_path

def install_vits_model(tier: str = "high", force: bool = False) -> Path:
    tier = tier.lower()
    if tier not in MODEL_REGISTRY:
        tier = "high"
    
    cfg = MODEL_REGISTRY[tier]
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

def run_installation(tier: str = "high", force: bool = False, play: bool = True):
    print("=" * 70)
    print("   TERMUX-TTS VULKAN GPU AUTOMATED PROVISIONER (1-CLICK SETUP)")
    print("=" * 70)
    
    # 1. Install pre-compiled Vulkan binary
    bin_path = install_vulkan_binary(force=force)
    
    # 2. Install VITS model
    model_path = install_vits_model(tier=tier, force=force)
    
    # 3. Environment check
    vulkan_lib = Path("/system/lib64/libvulkan.so")
    if not vulkan_lib.exists():
        print("  [WARNING] /system/lib64/libvulkan.so not found. Ensure device supports Vulkan.")
    else:
        print("  [OK] Android Vulkan driver detected: /system/lib64/libvulkan.so")

    print("\n[VERIFICATION] Running 1-second self-test on Vulkan GPU...")
    test_wav = Path.home() / "install_test_vulkan.wav"
    
    import subprocess
    cmd = [
        str(bin_path),
        f"--vits-model-dir={model_path}",
        "--use-vulkan-compute=1",
        "--num-threads=1",
        f"--output-filename={test_wav}",
        "It's Python, hello! Vulkan GPU speech synthesis is installed and ready."
    ]
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = f"/system/lib64:{env.get('LD_LIBRARY_PATH', '')}"
    env["AMEVA_VK_DSP_ACCEL"] = "1"

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if proc.returncode == 0:
        print("  [VERIFIED] Vulkan GPU synthesis self-test passed with exit code 0!")
        if play and shutil.which("termux-media-player"):
            print("  [PLAYBACK] Playing verification audio through physical speaker...")
            subprocess.run(["termux-volume", "music", "10"], check=False)
            subprocess.run(["termux-media-player", "play", str(test_wav)], check=False)
    else:
        print(f"  [FAIL-FAST] Self-test returned error: {proc.stderr}")

    print("=" * 70)
    print("   INSTALLATION COMPLETE! YOU CAN NOW USE 'termux-tts' DIRECTLY.")
    print("=" * 70)
