"""Tests for the QA decision engine (Phase 10)."""

import pytest
from app.decision import DecisionEngine
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


def make_clean_results():
    return (
        TechnicalResult(status=CheckStatus.PASS),
        TemporalResult(status=CheckStatus.PASS, score=0.95),
        SemanticResult(status=CheckStatus.PASS, score=0.88),
        ArtifactResult(status=CheckStatus.PASS),
        ProvenanceResult(status=CheckStatus.PASS, sha256="abc123hash"),
    )


def test_decision_pass():
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    decision, reasons = engine.decide(tech, temp, sem, art, prov)

    assert decision == DecisionType.PASS
    assert len(reasons) == 0


def test_decision_auto_retry_on_flicker():
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    temp.status = CheckStatus.FAIL
    temp.reason_codes = [ReasonCode.TEMPORAL_FLICKER]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.AUTO_RETRY
    assert ReasonCode.TEMPORAL_FLICKER in reasons


def test_decision_auto_retry_on_black_frame():
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    art.status = CheckStatus.FAIL
    art.reason_codes = [ReasonCode.ARTIFACT_BLACK_FRAME]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.AUTO_RETRY
    assert ReasonCode.ARTIFACT_BLACK_FRAME in reasons


def test_decision_auto_retry_on_low_semantic_alignment():
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    sem.status = CheckStatus.FAIL
    sem.reason_codes = [ReasonCode.SEMANTIC_LOW_ALIGNMENT]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.AUTO_RETRY
    assert ReasonCode.SEMANTIC_LOW_ALIGNMENT in reasons


def test_decision_human_review_on_uncertain_semantic():
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    sem.status = CheckStatus.WARN
    sem.reason_codes = [ReasonCode.SEMANTIC_UNCERTAIN]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.HUMAN_REVIEW
    assert ReasonCode.SEMANTIC_UNCERTAIN in reasons


def test_decision_human_review_on_text_overlay():
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    art.status = CheckStatus.WARN
    art.reason_codes = [ReasonCode.ARTIFACT_TEXT_OVERLAY]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.HUMAN_REVIEW
    assert ReasonCode.ARTIFACT_TEXT_OVERLAY in reasons
