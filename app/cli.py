"""Command-line interface for Member 8 QA Module."""

import argparse
import shutil
import subprocess
import sys
from typing import Dict, Tuple


def check_doctor() -> int:
    """Run environment diagnostic checks."""
    checks: Dict[str, Tuple[bool, str]] = {}

    # 1. Python
    py_ok = sys.version_info >= (3, 10)
    checks["Python"] = (py_ok, f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # 2. FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        try:
            res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            checks["FFmpeg"] = (res.returncode == 0, "available")
        except Exception as e:
            checks["FFmpeg"] = (False, str(e))
    else:
        checks["FFmpeg"] = (False, "not found on PATH")

    # 3. ffprobe
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        try:
            res = subprocess.run(["ffprobe", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            checks["ffprobe"] = (res.returncode == 0, "available")
        except Exception as e:
            checks["ffprobe"] = (False, str(e))
    else:
        checks["ffprobe"] = (False, "not found on PATH")

    # 4. OpenCV
    try:
        import cv2
        checks["OpenCV"] = (True, cv2.__version__)
    except ImportError as e:
        checks["OpenCV"] = (False, str(e))

    # 5. PyTorch
    try:
        import torch
        checks["PyTorch"] = (True, torch.__version__)
    except ImportError as e:
        checks["PyTorch"] = (False, str(e))

    # 6. CLIP
    try:
        from transformers import CLIPModel, CLIPProcessor
        checks["CLIP"] = (True, "transformers")
    except ImportError as e:
        checks["CLIP"] = (False, str(e))

    # 7. RAFT
    try:
        import torchvision.models.optical_flow as of
        has_raft = hasattr(of, "raft_small") or hasattr(of, "raft_large")
        checks["RAFT"] = (has_raft, "torchvision")
    except ImportError as e:
        checks["RAFT"] = (False, str(e))

    # 8. Gradio
    try:
        import gradio
        checks["Gradio"] = (True, gradio.__version__)
    except ImportError as e:
        checks["Gradio"] = (False, str(e))

    print("========================================")
    print("MEMBER 8 QA ENVIRONMENT DIAGNOSTIC")
    print("========================================")

    all_passed = True
    for name, (ok, detail) in checks.items():
        status = "OK" if ok else "FAILED"
        if not ok and name in ["PyTorch", "CLIP", "RAFT", "Gradio"]:
            status = "OPTIONAL/MISSING"
        elif not ok:
            all_passed = False
        print(f"{name:<14} {status:<10} ({detail})")

    print("========================================")
    if all_passed:
        print("Status: Environment ready for QA execution.")
        return 0
    else:
        print("Status: Required dependencies missing.")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Member 8 QA Module CLI")
    parser.add_argument("--doctor", action="store_true", help="Run environment diagnostic check")

    subparsers = parser.add_subparsers(dest="command")

    # 'fixtures' subparser will be wired in Phase 2
    fixtures_parser = subparsers.add_parser("fixtures", help="Generate mock video fixtures")
    fixtures_parser.add_argument("--output-dir", default="mock_data", help="Output directory for fixtures")

    # 'qa' subparser will be wired in Phase 11 / 12
    qa_parser = subparsers.add_parser("qa", help="Run QA on a video")
    qa_parser.add_argument("--video", required=False, help="Path to video file")
    qa_parser.add_argument("--prompt", required=False, default="", help="Prompt text")
    qa_parser.add_argument("--json", action="store_true", help="Output JSON result")

    args = parser.parse_args()

    if args.doctor:
        sys.exit(check_doctor())

    if args.command == "fixtures":
        from mock_data.generate_fixtures import generate_all_fixtures
        generate_all_fixtures(output_dir=args.output_dir)
        sys.exit(0)

    if args.command == "qa":
        if not args.video:
            print("Error: --video path required for 'qa' command.")
            sys.exit(1)
        # Placeholder for full pipeline CLI execution
        from app.pipeline import run_video_qa
        report = run_video_qa(video_path=args.video, prompt=args.prompt)
        if args.json:
            print(report.model_dump_json(indent=2))
        else:
            print("========================================")
            print("AI VIDEO QA")
            print("========================================")
            print(f"Technical      : {report.technical.status.value}")
            print(f"Temporal       : {report.temporal.status.value}")
            print(f"Semantic       : {report.semantic.status.value}")
            print(f"Artifacts      : {report.artifacts.status.value}")
            print(f"Provenance     : {report.provenance.status.value}")
            print("")
            print(f"FINAL DECISION : {report.decision.value}")
            if report.reason_codes:
                print(f"Reason Codes   : {[r.value for r in report.reason_codes]}")
            print("========================================")
        sys.exit(0 if report.decision.value == "PASS" else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
