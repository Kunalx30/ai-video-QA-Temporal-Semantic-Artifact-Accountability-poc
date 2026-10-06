"""Tests for clean control fixtures ensuring zero false rejections."""

import json
from pathlib import Path
import pytest

from qa_harness.runner import QAHarnessRunner


def test_all_clean_controls_pass():
    """Verify clean control fixtures all evaluate to PASS with zero active reason codes."""
    manifest_path = Path("mock_data/manifest.json")
    assert manifest_path.exists(), "Manifest file must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    fixtures = manifest.get("fixtures", {})
    clean_fixtures = {
        k: v for k, v in fixtures.items()
        if "CLEAN" in k or k == "good"
    }

    assert len(clean_fixtures) >= 20, f"Expected at least 20 clean controls, found {len(clean_fixtures)}"

    runner = QAHarnessRunner()
    false_rejections = []

    for fix_id, meta in clean_fixtures.items():
        res = runner.run_fixture(fix_id, meta)
        if res.qa_result.decision != "PASS" or res.qa_result.reason_codes:
            false_rejections.append((fix_id, res.qa_result.decision, res.qa_result.reason_codes))

    assert len(false_rejections) == 0, f"Clean controls falsely rejected: {false_rejections}"
