"""Tests for Day 2 QA Harness runner, comparator, and determinism."""

import json
from pathlib import Path
import pytest

from qa_harness.comparator import QAComparator
from qa_harness.runner import QAHarnessRunner
from app.schemas.contract import QAResult


def test_qa_comparator_pass_matching():
    """Verify comparator marks clean fixture as PASS when expected and actual match."""
    actual = QAResult(
        qa_id="QA_001",
        clip_id="CLIP_001",
        decision="PASS",
        reason_codes=[],
    )
    expected = {"expected_decision": "PASS", "expected_reason_codes": []}

    res = QAComparator.compare(actual, expected)
    assert res.passed is True
    assert res.decision_matched is True
    assert res.reasons_matched is True


def test_qa_comparator_defect_matching():
    """Verify comparator validates expected defect reason code presence."""
    actual = QAResult(
        qa_id="QA_002",
        clip_id="CLIP_002",
        decision="AUTO_RETRY",
        reason_codes=["TEMPORAL_DUPLICATE_FRAMES", "TEMPORAL_MOTION_ANOMALY"],
    )
    expected = {
        "expected_decision": "AUTO_RETRY",
        "expected_reason_codes": ["TEMPORAL_DUPLICATE_FRAMES"],
    }

    res = QAComparator.compare(actual, expected)
    assert res.passed is True
    assert res.decision_matched is True
    assert res.reasons_matched is True


def test_qa_comparator_mismatch_detected():
    """Verify comparator catches wrong decision."""
    actual = QAResult(
        qa_id="QA_003",
        clip_id="CLIP_003",
        decision="PASS",
        reason_codes=[],
    )
    expected = {
        "expected_decision": "AUTO_RETRY",
        "expected_reason_codes": ["TEMPORAL_FLICKER"],
    }

    res = QAComparator.compare(actual, expected)
    assert res.passed is False
    assert res.decision_matched is False


def test_qa_harness_single_fixture():
    """Verify QAHarnessRunner executes a fixture, writes evidence, and produces valid QAResult."""
    runner = QAHarnessRunner()
    meta = {
        "fixture_id": "M8_CLEAN_001",
        "video_path": "mock_data/media/M8_CLEAN_001.mp4",
        "expected_decision": "PASS",
        "expected_reason_codes": [],
        "prompt": "inputs/M8_CLEAN_001_prompt.json",
        "input_metadata": "inputs/M8_CLEAN_001.json",
    }
    result = runner.run_fixture("M8_CLEAN_001", meta)

    assert result.qa_result.decision == "PASS"
    assert result.comparison.passed is True
    assert len(result.evidence_files) > 0
    # Check that evidence file actually exists on disk
    ev_path = Path(result.evidence_files[0])
    assert ev_path.exists()
    with open(ev_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["fixture_id"] == "M8_CLEAN_001"
        assert "technical" in data
        assert "temporal" in data


def test_qa_harness_determinism():
    """Verify running the same fixture twice produces identical decision, reasons, and checksum."""
    runner = QAHarnessRunner()
    meta = {
        "fixture_id": "M8_TEMP_001",
        "video_path": "mock_data/media/M8_TEMP_001.mp4",
        "expected_decision": "AUTO_RETRY",
        "expected_reason_codes": ["TEMPORAL_DUPLICATE_FRAMES"],
        "prompt": "inputs/M8_TEMP_001_prompt.json",
        "input_metadata": "inputs/M8_TEMP_001.json",
    }

    run1 = runner.run_fixture("M8_TEMP_001", meta)
    run2 = runner.run_fixture("M8_TEMP_001", meta)

    assert run1.qa_result.decision == run2.qa_result.decision
    assert run1.qa_result.reason_codes == run2.qa_result.reason_codes
    assert run1.report.provenance.sha256 == run2.report.provenance.sha256
    assert run1.comparison.passed == run2.comparison.passed
