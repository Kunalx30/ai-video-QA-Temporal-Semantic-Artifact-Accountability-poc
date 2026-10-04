"""Tests for Member 8 QA schemas and contracts (Phase 0)."""

import pytest
from pydantic import ValidationError

from app.schemas.input import GenerationMetadata, VideoQAInput
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
from app.schemas.report import QAReport


def test_video_qa_input_valid():
    inp = VideoQAInput(
        video_path="path/to/video.mp4",
        prompt="A car driving down a mountain road at dusk.",
        video_id="VID_123",
        metadata=GenerationMetadata(
            generation_id="GEN_01",
            fps=24.0,
            width=1280,
            height=720,
        ),
    )
    assert inp.video_path == "path/to/video.mp4"
    assert inp.prompt == "A car driving down a mountain road at dusk."
    assert inp.video_id == "VID_123"
    assert inp.metadata.fps == 24.0


def test_video_qa_input_minimal():
    inp = VideoQAInput(
        video_path="path/to/video.mp4",
        prompt="A dog jumping in grass.",
    )
    assert inp.video_id is None
    assert inp.metadata is not None
    assert inp.metadata.generation_id is None


def test_video_qa_input_missing_required():
    with pytest.raises(ValidationError):
        VideoQAInput(prompt="Missing video path")

    with pytest.raises(ValidationError):
        VideoQAInput(video_path="path/to/video.mp4")


def test_qa_report_serialization():
    report = QAReport(
        video_id="VID_TEST",
        decision=DecisionType.PASS,
        technical=TechnicalResult(status=CheckStatus.PASS, width=1920, height=1080),
        temporal=TemporalResult(status=CheckStatus.PASS, score=0.95),
        semantic=SemanticResult(status=CheckStatus.PASS, score=0.88),
        artifacts=ArtifactResult(status=CheckStatus.PASS),
        provenance=ProvenanceResult(
            status=CheckStatus.PASS,
            sha256="abc123hash",
            video_id="VID_TEST",
            qa_run_id="RUN_001",
        ),
        reason_codes=[],
    )
    data = report.model_dump()
    assert data["decision"] == "PASS"
    assert data["video_id"] == "VID_TEST"
    assert data["technical"]["width"] == 1920
    assert data["provenance"]["sha256"] == "abc123hash"

    # Round-trip check
    restored = QAReport.model_validate(data)
    assert restored.decision == DecisionType.PASS
    assert restored.temporal.score == 0.95


def test_reason_codes_and_decision_types():
    assert DecisionType.PASS.value == "PASS"
    assert DecisionType.AUTO_RETRY.value == "AUTO_RETRY"
    assert DecisionType.HUMAN_REVIEW.value == "HUMAN_REVIEW"
    assert ReasonCode.TEMPORAL_FLICKER.value == "TEMPORAL_FLICKER"
    assert ReasonCode.ARTIFACT_BLACK_FRAME.value == "ARTIFACT_BLACK_FRAME"
    assert ReasonCode.PROMPT_ASPECT_RATIO_MISMATCH.value == "PROMPT_ASPECT_RATIO_MISMATCH"
