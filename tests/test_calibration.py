import json
from pathlib import Path
import pytest
from mock_data.run_calibration import run_calibration


def test_fixture_calibration_suite():
    # Source of truth for fixtures is mock_data/manifest.json
    manifest_path = Path("mock_data/manifest.json")
    assert manifest_path.exists(), "Manifest file must exist"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    manifest_fixtures = manifest.get("fixtures", {})
    assert len(manifest_fixtures) >= 20, f"Expected at least 20 fixtures in manifest, found {len(manifest_fixtures)}"

    records = run_calibration()

    # 1. Calibration returns records for the complete fixture suite
    assert len(records) == len(manifest_fixtures), (
        f"Calibration record count ({len(records)}) does not match manifest count ({len(manifest_fixtures)})"
    )

    # 2. All fixture IDs from manifest are present in records
    record_ids = {r["fixture_id"] for r in records}
    assert record_ids == set(manifest_fixtures.keys()), "Mismatch in fixture IDs between calibration and manifest"

    # 3. Defect fixtures and clean controls are both included
    defects = [r for r in records if not r["is_control"]]
    controls = [r for r in records if r["is_control"]]
    assert len(defects) >= 20, f"Expected at least 20 defect fixtures, found {len(defects)}"
    assert len(controls) >= 20, f"Expected at least 20 clean controls, found {len(controls)}"

    # 4. Expected and actual decisions are represented
    valid_decisions = {"PASS", "AUTO_RETRY", "HUMAN_REVIEW"}
    for r in records:
        assert r["expected_decision"] in valid_decisions, f"Invalid expected decision: {r['expected_decision']}"
        assert r["actual_decision"] in valid_decisions, f"Invalid actual decision: {r['actual_decision']}"
        assert r["status"] in {"PASS", "FAIL"}, f"Invalid status: {r['status']}"

    # 5. Calibration metrics remain correct (0 false positives, 0 false negatives, 100% accuracy)
    fps = [r for r in records if r["false_positive"]]
    fns = [r for r in records if r["false_negative"]]
    failed = [r for r in records if r["status"] != "PASS"]

    assert len(fps) == 0, f"False positives detected: {fps}"
    assert len(fns) == 0, f"False negatives detected: {fns}"
    assert len(failed) == 0, f"Failed fixtures: {failed}"

    # Verify detection rate on defects and false reject rate on clean controls
    defect_detected = sum(1 for r in defects if r["actual_decision"] != "PASS" and r["status"] == "PASS")
    assert defect_detected == len(defects), f"Expected 100% defect detection ({len(defects)}), got {defect_detected}"

    control_rejected = sum(1 for r in controls if r["false_positive"])
    assert control_rejected == 0, f"Expected 0 clean control rejections, got {control_rejected}"
