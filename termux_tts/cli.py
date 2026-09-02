"""
Command-Line Interface for termux-tts:
- termux-tts synth : Option A Deep Learning Neural Synthesis to File
- termux-tts speak : Option B Android System Native Immediate Voice Output
- termux-tts doctor: 12-Stage Vulkan GPU Hardware Diagnostics
"""

import sys
import argparse
from .engine import load, doctor

def main():
    parser = argparse.ArgumentParser(
        prog="termux-tts",
        description="Termux Neural & Native Text-to-Speech Engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # 1. Synth (Option A: DSP Formant or ONNX Neural Vocoder to File)
    synth_parser = subparsers.add_parser("synth", help="Synthesize text to audio WAV file (DSP / ONNX)")
    synth_parser.add_argument("-t", "--text", required=True, help="Input text to synthesize")
    synth_parser.add_argument("-o", "--output", default="output.wav", help="Output WAV filepath")
    synth_parser.add_argument("-l", "--lang", default="ko", help="Language code (ko, en)")
    synth_parser.add_argument("-e", "--engine", default="auto", choices=["auto", "dsp", "onnx"], help="Synthesis engine (dsp=zero-dependency, onnx=deep learning)")
    synth_parser.add_argument("-m", "--model", default=None, help="Path to .onnx model file (required for onnx engine)")
    synth_parser.add_argument("-p", "--preset", default="balanced", choices=["fast", "balanced", "expressive", "ultra"])
    synth_parser.add_argument("-d", "--device", default="auto", choices=["auto", "gpu", "vulkan", "cpu"])
    synth_parser.add_argument("-s", "--speed", type=float, default=1.0, help="Speech speed multiplier (0.5 to 2.0)")

    # 2. Speak (Option B: Native Samsung/Google System Voice)
    speak_parser = subparsers.add_parser("speak", help="Speak text directly through device speaker (Option B: Native)")
    speak_parser.add_argument("-t", "--text", required=True, help="Input text to speak")
    speak_parser.add_argument("-l", "--lang", default="ko", help="Language code (ko, en)")
    speak_parser.add_argument("-s", "--stream", default="MUSIC", help="Audio stream (MUSIC, NOTIFICATION, ALARM)")

    # 3. Doctor (Diagnostics)
    subparsers.add_parser("doctor", help="Run 12-stage Vulkan GPU hardware diagnostics")

    args = parser.parse_args()

    if args.command == "synth":
        with load(model=args.model, language=args.lang, preset=args.preset, device=args.device, engine=args.engine) as engine:
            res = engine.synthesize(args.text, output=args.output, speed=args.speed)
            print(f"[SUCCESS] Synthesized via {res.backend} ({res.model_name}) -> {args.output}")
            print(f"  Duration: {res.duration_sec:.2f}s | Elapsed: {res.elapsed_ms:.1f}ms | RTF: {res.rtf:.4f}x")

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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
