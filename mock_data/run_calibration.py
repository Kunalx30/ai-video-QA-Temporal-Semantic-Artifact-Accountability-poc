"""Calibration script evaluating all fixtures against expected outcomes.

Computes detection rate on defect fixtures, false-reject rate on clean controls,
and outputs calibration_report.md.
"""

import json
from pathlib import Path
import sys
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.pipeline import VideoQAPipeline
from app.schemas.contract import ClipMetadata


def run_calibration() -> List[Dict[str, Any]]:
    """Run full QA pipeline across all fixtures in manifest and compare against expected results."""
    manifest_path = Path("mock_data/manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    fixtures = manifest.get("fixtures", {})
    results = []
    pipeline = VideoQAPipeline()

    for fix_id, meta in fixtures.items():
        video_path = meta.get("video_path") or meta.get("video")
        prompt = meta.get("prompt_text") or meta.get("prompt", "A golden glowing orb traveling smoothly across an evening sky.")
        if prompt.endswith(".json"):
            prompt_file = Path("mock_data") / prompt
            if prompt_file.exists():
                with open(prompt_file, "r", encoding="utf-8") as pf:
                    prompt = json.load(pf).get("prompt", "A golden glowing orb traveling smoothly across an evening sky.")

        expected_decision = meta.get("expected_decision", "PASS")
        exp_reasons = meta.get("expected_reason_codes") or ([meta["reason_code"]] if meta.get("reason_code") else [])

        # Load input metadata if available
        input_file = Path("mock_data") / (meta.get("input_metadata") or f"inputs/{fix_id}.json")
        clip_meta = None
        if input_file.exists():
            try:
                with open(input_file, "r", encoding="utf-8") as inf:
                    clip_meta = ClipMetadata(**json.load(inf))
            except Exception:
                clip_meta = None

        report = pipeline.run(
            video_path=video_path,
            prompt=prompt,
            video_id=fix_id,
            metadata=clip_meta,
        )
        actual_decision = report.decision.value
        actual_reasons = [r.value for r in report.reason_codes]

        # Determine if matched
        decision_match = (actual_decision == expected_decision)
        reason_match = True
        if expected_decision == "PASS":
            reason_match = (len(actual_reasons) == 0)
        elif exp_reasons:
            reason_match = any(r in actual_reasons for r in exp_reasons)

        is_success = decision_match and reason_match

        # False positive: Expected PASS but got failure / rejection
        # False negative: Expected FAIL but got PASS
        fp = (expected_decision == "PASS" and actual_decision != "PASS")
        fn = (expected_decision != "PASS" and actual_decision == "PASS")

        record = {
            "fixture_id": fix_id,
            "filename": meta.get("filename", Path(video_path).name),
            "defect": meta.get("defect", "None"),
            "expected_decision": expected_decision,
            "actual_decision": actual_decision,
            "expected_reasons": exp_reasons,
            "actual_reasons": actual_reasons,
            "temporal_score": report.temporal.score,
            "semantic_score": report.semantic.score,
            "blur_score": report.artifacts.blur_score,
            "black_frames": report.artifacts.black_frame_count,
            "false_positive": fp,
            "false_negative": fn,
            "status": "PASS" if is_success else "FAIL",
            "is_control": (expected_decision == "PASS"),
        }
        results.append(record)

    return results


def generate_calibration_markdown(results: List[Dict[str, Any]]) -> str:
    """Format calibration results into a GitHub-flavored Markdown report."""
    md = []
    md.append("# Member 8 QA Module — Calibration Report\n")
    md.append(
        "Comprehensive empirical evaluation measuring detector sensitivity, "
        "reason code attribution, defect detection rates, and clean-control false rejection rates.\n"
    )

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    defects = [r for r in results if not r["is_control"]]
    controls = [r for r in results if r["is_control"]]

    defect_detected = sum(1 for r in defects if r["actual_decision"] != "PASS" and r["status"] == "PASS")
    detection_rate = (defect_detected / len(defects) * 100.0) if defects else 100.0

    control_rejected = sum(1 for r in controls if r["false_positive"])
    false_reject_rate = (control_rejected / len(controls) * 100.0) if controls else 0.0

    accuracy = (passed / total) * 100.0 if total > 0 else 0.0

    md.append("## Summary Metrics\n")
    md.append(f"- **Total Fixtures Evaluated**: {total}")
    md.append(f"- **Total Defect Fixtures**: {len(defects)}")
    md.append(f"- **Total Clean Controls**: {len(controls)}")
    md.append(f"- **Defect Detection Rate**: {defect_detected}/{len(defects)} ({detection_rate:.1f}%)")
    md.append(f"- **Clean Control False-Reject Rate**: {control_rejected}/{len(controls)} ({false_reject_rate:.1f}%)")
    md.append(f"- **Overall Classification Accuracy**: {passed}/{total} ({accuracy:.1f}%)\n")

    md.append("## Detailed Calibration Matrix\n")
    md.append("| Fixture | Defect Description | Expected Decision | Actual Decision | Expected Reason | Actual Reasons | Outcome |")
    md.append("|---|---|---|---|---|---|---|")

    for r in results:
        status_icon = "PASS" if r["status"] == "PASS" else "FAIL"
        reasons_str = ", ".join(r["actual_reasons"]) if r["actual_reasons"] else "None"
        exp_reason = ", ".join(r["expected_reasons"]) if r["expected_reasons"] else "None"
        md.append(f"| `{r['fixture_id']}` | {r['defect']} | **{r['expected_decision']}** | **{r['actual_decision']}** | `{exp_reason}` | `{reasons_str}` | {status_icon} |")

    md.append("\n## Key Calibrated Thresholds\n")
    md.append("- **Temporal Flicker**: Luminance second-order difference threshold = `15.0`")
    md.append("- **Duplicate Frames**: PSNR threshold = `45.0` dB, L1 normalized diff <= `0.0005`")
    md.append("- **Freeze Sequences**: Consecutive identical frames >= `6`")
    md.append("- **Dropped Frames**: Motion jump spike ratio >= `2.6x` with delta > `0.005`")
    md.append("- **Motion Anomalies**: Sudden acceleration jump ratio > `3.5x`")
    md.append("- **Black Frames**: Mean luminance <= `2.0` or >= `98%` dark pixels")
    md.append("- **Blur**: Laplacian variance threshold = `25.0`")
    md.append("- **Semantic Alignment**: Pass threshold = `0.22`, Uncertain threshold = `0.18`")

    return "\n".join(md)


if __name__ == "__main__":
    records = run_calibration()
    report_md = generate_calibration_markdown(records)
    out_file = Path("calibration_report.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"Calibration completed: wrote {out_file}")
