"""Tests for Day 2 shared contracts (ClipMetadata and QAResult)."""

import json
import pytest
from pydantic import ValidationError

from app.schemas.contract import ClipMetadata, QAResult
from app.schemas.report import QAReport
from app.schemas.results import (
    ArtifactResult,
    CheckStatus,
    DecisionType,
    ProvenanceResult,
    ReasonCode,
    SemanticResult,
    TechnicalResult,
    TemporalResult,
)


def test_clip_metadata_valid_instantiation():
    """Verify ClipMetadata requires and preserves all required Day 2 contract fields."""
    meta = ClipMetadata(
        clip_id="CLIP_S01_SH02_T2V_01",
        shot_id="S01_SH02",
        mode="T2V",
        source_type="MOCK",
        file="mock_data/media/M8_CLEAN_001.mp4",
        duration_s=4.0,
        fps=24.0,
        width=1280,
        height=720,
        aspect_ratio="16:9",
        codec="h264",
        model="mock-engine",
        settings={"sampler": "euler"},
        reference_ids=["REF_001"],
        motion_controls={"camera_pan": "left"},
        seed=42,
        status="OK",
        failure_reason=None,
        checksum_sha256="abcdef1234567890" * 4,
    )

    data = meta.model_dump()
    assert data["clip_id"] == "CLIP_S01_SH02_T2V_01"
    assert data["shot_id"] == "S01_SH02"
    assert data["mode"] == "T2V"
    assert data["source_type"] == "MOCK"
    assert data["fps"] == 24.0
    assert data["width"] == 1280
    assert data["height"] == 720
    assert data["aspect_ratio"] == "16:9"
    assert data["codec"] == "h264"
    assert data["status"] == "OK"
    assert data["seed"] == 42
    assert len(data["checksum_sha256"]) == 64


def test_clip_metadata_missing_required_fields_fails():
    """Verify validation error when required fields are missing."""
    with pytest.raises(ValidationError):
        # Missing required fields like clip_id, shot_id, etc.
        ClipMetadata(file="test.mp4")


def test_clip_metadata_to_generation_metadata_adapter():
    """Verify adapter method converts ClipMetadata to Day 1 GenerationMetadata."""
    meta = ClipMetadata(
        clip_id="CLIP_S01_SH01_T2V_01",
        shot_id="S01_SH01",
        mode="T2V",
        source_type="MOCK",
        file="mock_data/media/good.mp4",
        duration_s=2.5,
        fps=24.0,
        width=640,
        height=360,
        aspect_ratio="16:9",
        codec="h264",
        seed=42,
    )
    gen_meta = meta.to_generation_metadata()
    assert gen_meta.generation_id == "CLIP_S01_SH01_T2V_01"
    assert gen_meta.fps == 24.0
    assert gen_meta.width == 640
    assert gen_meta.height == 360
    assert gen_meta.extra["shot_id"] == "S01_SH01"


def test_qa_result_valid_instantiation():
    """Verify QAResult conforms to shared output contract specification."""
    res = QAResult(
        qa_id="QA_S01_SH01_001",
        clip_id="CLIP_S01_SH01_T2V_01",
        qa_type="TEMPORAL_SEMANTIC",
        component_scores={
            "technical": 1.0,
            "temporal": 1.0,
            "artifacts": 1.0,
            "semantic": 0.85,
            "provenance": 1.0,
        },
        reason_codes=[],
        decision="PASS",
        evidence_files=["evidence/M8_CLEAN_001_evidence.json"],
    )

    data = res.model_dump()
    assert data["qa_id"] == "QA_S01_SH01_001"
    assert data["clip_id"] == "CLIP_S01_SH01_T2V_01"
    assert data["qa_type"] == "TEMPORAL_SEMANTIC"
    assert data["decision"] == "PASS"
    assert data["component_scores"]["technical"] == 1.0
    assert data["component_scores"]["semantic"] == 0.85
    assert len(data["evidence_files"]) == 1


def test_qa_report_to_contract():
    """Verify QAReport.to_contract() correctly converts to QAResult."""
    report = QAReport(
        video_id="CLIP_001",
        qa_run_id="RUN_001",
        decision=DecisionType.AUTO_RETRY,
        technical=TechnicalResult(status=CheckStatus.PASS),
        temporal=TemporalResult(status=CheckStatus.FAIL, score=0.25, reason_codes=[ReasonCode.TEMPORAL_DUPLICATE_FRAMES]),
        semantic=SemanticResult(status=CheckStatus.PASS, score=0.88),
        artifacts=ArtifactResult(status=CheckStatus.PASS),
        provenance=ProvenanceResult(status=CheckStatus.PASS, sha256="abc", video_id="CLIP_001"),
        reason_codes=[ReasonCode.TEMPORAL_DUPLICATE_FRAMES],
    )

    contract = report.to_contract()
    assert isinstance(contract, QAResult)
    assert contract.clip_id == "CLIP_001"
    assert contract.decision == "AUTO_RETRY"
    assert "TEMPORAL_DUPLICATE_FRAMES" in contract.reason_codes
    assert contract.component_scores["temporal"] == 0.25
    assert contract.component_scores["technical"] == 1.0
    assert contract.component_scores["semantic"] == 0.88
    assert contract.component_scores["provenance"] == 1.0


def test_invalid_decision_vocabulary_rejected():
    """Verify decisions outside PASS, AUTO_RETRY, HUMAN_REVIEW are rejected."""
    with pytest.raises(ValidationError):
        QAResult(
            qa_id="QA_01",
            clip_id="CLIP_01",
            decision="APPROVED",  # Invalid decision vocabulary
        )
