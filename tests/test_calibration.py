"""Calibration suite test verifying 100% classification accuracy on curated fixtures (Phase 15)."""

import pytest
from mock_data.run_calibration import run_calibration


def test_fixture_calibration_suite():
    records = run_calibration()
    assert len(records) == 11

    # Zero false positives and zero false negatives
    fps = [r for r in records if r["false_positive"]]
    fns = [r for r in records if r["false_negative"]]
    failed = [r for r in records if r["status"] != "PASS"]

    assert len(fps) == 0, f"False positives detected: {fps}"
    assert len(fns) == 0, f"False negatives detected: {fns}"
    assert len(failed) == 0, f"Failed fixtures: {failed}"
