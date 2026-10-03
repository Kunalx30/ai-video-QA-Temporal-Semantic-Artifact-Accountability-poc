"""Calibration script evaluating all fixtures against expected outcomes."""

import json
from pathlib import Path
import sys
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.pipeline import run_video_qa


def run_calibration() -> List[Dict[str, Any]]:
    """Run full QA pipeline across all 11 curated fixtures and compare against expected results."""
    manifest_path = Path("mock_data/manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    fixtures = manifest["fixtures"]
    results = []

    for fix_id, meta in fixtures.items():
        video_path = meta["video_path"]
        prompt = meta.get("prompt", "A golden glowing orb traveling smoothly across an evening sky.")
        expected_decision = meta["expected_decision"]
        expected_reason = meta["reason_code"]

        report = run_video_qa(video_path=video_path, prompt=prompt)
        actual_decision = report.decision.value
        actual_reasons = [r.value for r in report.reason_codes]

        # Determine if matched
        decision_match = (actual_decision == expected_decision)
        reason_match = True
        if expected_reason:
            reason_match = expected_reason in actual_reasons

        is_success = decision_match and reason_match

        # False positive: Expected PASS but got failure
        # False negative: Expected FAIL but got PASS
        fp = (expected_decision == "PASS" and actual_decision != "PASS")
        fn = (expected_decision != "PASS" and actual_decision == "PASS")

        record = {
            "fixture_id": fix_id,
            "filename": meta["filename"],
            "defect": meta["defect"],
            "expected_decision": expected_decision,
            "actual_decision": actual_decision,
            "expected_reason": expected_reason,
            "actual_reasons": actual_reasons,
            "temporal_score": report.temporal.score,
            "semantic_score": report.semantic.score,
            "blur_score": report.artifacts.blur_score,
            "black_frames": report.artifacts.black_frame_count,
            "false_positive": fp,
            "false_negative": fn,
            "status": "PASS" if is_success else "FAIL",
        }
        results.append(record)

    return results


def generate_calibration_markdown(results: List[Dict[str, Any]]) -> str:
    """Format calibration results into a GitHub-flavored Markdown report."""
    md = []
    md.append("# Member 8 QA Module — Calibration Report\n")
    md.append("Comprehensive evaluation across all 11 curated fixtures measuring detector sensitivity, reason code attribution, and classification accuracy.\n")

    md.append("## Summary Metrics\n")
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    fps = sum(1 for r in results if r["false_positive"])
    fns = sum(1 for r in results if r["false_negative"])
    accuracy = (passed / total) * 100.0

    md.append(f"- **Total Fixtures Evaluated**: {total}")
    md.append(f"- **Correct Classifications**: {passed}/{total} ({accuracy:.1f}%)")
    md.append(f"- **False Positives (Clean flagged as defect)**: {fps}")
    md.append(f"- **False Negatives (Defect missed as PASS)**: {fns}\n")

    md.append("## Detailed Calibration Matrix\n")
    md.append("| Fixture | Injected Defect | Expected Decision | Actual Decision | Expected Reason | Actual Reasons | Outcome |")
    md.append("|---|---|---|---|---|---|---|")

    for r in results:
        status_icon = "PASS" if r["status"] == "PASS" else "FAIL"
        reasons_str = ", ".join(r["actual_reasons"]) if r["actual_reasons"] else "None"
        exp_reason = r["expected_reason"] or "None"
        md.append(f"| `{r['filename']}` | {r['defect']} | **{r['expected_decision']}** | **{r['actual_decision']}** | `{exp_reason}` | `{reasons_str}` | {status_icon} |")

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
