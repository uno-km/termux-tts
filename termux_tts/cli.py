"""
Command-Line Interface for termux-tts:
- termux-tts synth : Option A Deep Learning Neural Synthesis to File
- termux-tts speak : Option B Android System Native Immediate Voice Output
- termux-tts doctor: 12-Stage Vulkan GPU Hardware Diagnostics
"""

import os
import sys
import argparse
from .engine import load, doctor

def main():
    parser = argparse.ArgumentParser(
        prog="termux-tts",
        description="Termux Neural & Native Text-to-Speech Engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # 1. Synth (4-Tier Speech Synthesis)
    synth_parser = subparsers.add_parser("synth", help="Synthesize text to audio WAV file (Synth, Neural, Expressive)")
    synth_parser.add_argument("-t", "--text", required=True, help="Input text to synthesize")
    synth_parser.add_argument("-o", "--output", default="output.wav", help="Output WAV filepath")
    synth_parser.add_argument("-l", "--lang", default="ko", help="Language code (ko, en)")
    synth_parser.add_argument(
        "-e", "--engine", default="auto",
        choices=["auto", "vulkan", "ncnn", "gpu", "synth", "dsp", "native", "neural", "onnx", "expressive"],
        help="Synthesis engine tier (vulkan=GPU NCNN, synth=0MB DSP, native=Android voice, neural=VITS C++, expressive=emotional)"
    )
    synth_parser.add_argument("-m", "--model", default=None, help="Path to model file or directory")
    synth_parser.add_argument("-p", "--preset", default="balanced", choices=["fast", "balanced", "expressive", "ultra"])
    synth_parser.add_argument("-d", "--device", default="auto", choices=["auto", "gpu", "vulkan", "cpu"], help="Compute target device")
    synth_parser.add_argument("-b", "--backend", dest="device", choices=["auto", "gpu", "vulkan", "cpu"], help="Alias for --device")
    synth_parser.add_argument("--gpu", dest="device", action="store_const", const="gpu", help="Enable hardware GPU acceleration")
    synth_parser.add_argument("--cpu", dest="device", action="store_const", const="cpu", help="Force CPU compute mode")
    synth_parser.add_argument("--tier", default=None, choices=["high", "medium", "balanced", "fast", "ultra"], help="Target model tier (high=Studio FP16, medium=Balanced)")
    synth_parser.add_argument("-s", "--speed", type=float, default=1.0, help="Speech speed multiplier (0.5 to 2.0)")
    synth_parser.add_argument("--threads", type=int, default=4, help="Compute worker threads (ARM NEON)")
    synth_parser.add_argument("--volume", type=int, default=None, help="Set Android media volume (1 to 15)")
    synth_parser.add_argument("--play", action="store_true", help="Play synthesized audio through physical speaker immediately")

    # 2. Speak (Option B: Native Samsung/Google System Voice)
    speak_parser = subparsers.add_parser("speak", help="Speak text directly through device speaker (Option B: Native)")
    speak_parser.add_argument("-t", "--text", required=True, help="Input text to speak")
    speak_parser.add_argument("-l", "--lang", default="ko", help="Language code (ko, en)")
    speak_parser.add_argument("-s", "--stream", default="MUSIC", help="Audio stream (MUSIC, NOTIFICATION, ALARM)")
    speak_parser.add_argument("--volume", type=int, default=None, help="Set Android media volume (1 to 15)")

    # 3. Doctor (Diagnostics)
    subparsers.add_parser("doctor", help="Run 12-stage Vulkan GPU hardware diagnostics")

    # 4. Install (One-Click Automated Provisioner)
    install_parser = subparsers.add_parser("install", help="1-Click download and provision precompiled Vulkan binary & VITS studio models")
    install_parser.add_argument("--tier", default="high", choices=["high", "medium"], help="Model resolution tier (high=57MB Studio FP16, medium=25MB Fast)")
    install_parser.add_argument("--force", action="store_true", help="Force overwrite existing binary and model assets")
    install_parser.add_argument("--no-play", action="store_true", help="Skip playback verification during self-test")

    # ── AMEVA Component Protocol v1 ─────────────────────────────────────────
    _protocol_available = False
    try:
        from ameva_component.cli_support import build_protocol_subcommands
        build_protocol_subcommands(subparsers)
        _protocol_available = True
    except ImportError as _proto_err:
        _protocol_available = False
    # ────────────────────────────────────────────────────────────────────────

    args = parser.parse_args()

    import subprocess
    import shutil

    if getattr(args, "volume", None) is not None:
        if shutil.which("termux-volume"):
            subprocess.run(["termux-volume", "music", str(args.volume)], check=False)

    if args.command == "synth":
        with load(
            model=args.model,
            language=args.lang,
            preset=args.preset,
            device=args.device,
            threads=args.threads,
            engine=args.engine,
            tier=getattr(args, "tier", None),
        ) as engine:
            res = engine.synthesize(args.text, output=args.output, speed=args.speed)
            backend_name = getattr(res, "backend", "UNKNOWN")
            model_name = getattr(res, "model_name", "model")
            dur = getattr(res, "duration_sec", 0.0)
            elapsed = getattr(res, "elapsed_ms", 0.0)
            rtf = getattr(res, "rtf", 0.0)
            print(f"[SUCCESS] Synthesized via {backend_name} ({model_name}) -> {args.output}")
            print(f"  Duration: {dur:.2f}s | Elapsed: {elapsed:.1f}ms | RTF: {rtf:.4f}x")

            if args.play and args.output and os.path.exists(args.output):
                if shutil.which("termux-media-player"):
                    subprocess.run(["termux-media-player", "play", args.output], check=False)
                elif shutil.which("play-audio"):
                    subprocess.run(["play-audio", args.output], check=False)

    elif args.command == "speak":
        with load(language=args.lang) as engine:
            res = engine.speak(args.text, stream=args.stream)
            print(f"[SUCCESS] Spoken via {res.engine_name} on stream {args.stream} ({res.elapsed_ms:.1f}ms)")

    elif args.command == "doctor":
        diag = doctor()
        print("=" * 60)
        print("   TERMUX-TTS 12-STAGE VULKAN HARDWARE DIAGNOSTICS")
        print("=" * 60)
        for k, v in diag.items():
            print(f"  - {k:30s}: {v}")
        print("=" * 60)

    elif args.command == "install":
        from .installer import run_installation
        run_installation(tier=args.tier, force=args.force, play=not args.no_play)

    elif args.command in ("component", "model", "instance") and _protocol_available:
        from ameva_component.cli_support import dispatch_protocol
        from termux_tts.control import TTSControl
        dispatch_protocol(args, TTSControl())
    elif args.command in ("component", "model", "instance"):
        print("[ERROR] ameva-component-sdk not installed.", file=sys.stderr)
        sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

