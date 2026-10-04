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


def test_decision_pass_traceability_no_blocking_codes():
    """Section 3 & 6: Clean results produce PASS with no blocking reason codes."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    decision, reasons = engine.decide(tech, temp, sem, art, prov)

    assert decision == DecisionType.PASS
    assert len(reasons) == 0


def test_decision_auto_retry_traceability_temporal_frame_drop():
    """Section 4 & 6: Frame drop defect triggers AUTO_RETRY with exact reason code."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    temp.status = CheckStatus.FAIL
    temp.reason_codes = [ReasonCode.TEMPORAL_FRAME_DROP]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.AUTO_RETRY
    assert reasons == [ReasonCode.TEMPORAL_FRAME_DROP]


def test_decision_auto_retry_traceability_invalid_media():
    """Section 4 & 6: Technical invalid media triggers AUTO_RETRY."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    tech.status = CheckStatus.FAIL
    tech.reason_codes = [ReasonCode.TECHNICAL_INVALID_MEDIA]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.AUTO_RETRY
    assert ReasonCode.TECHNICAL_INVALID_MEDIA in reasons


def test_decision_human_review_on_provenance_failure():
    """Section 5 & 6: Cryptographic provenance failure triggers HUMAN_REVIEW."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    prov.status = CheckStatus.FAIL
    prov.reason_codes = [ReasonCode.PROVENANCE_HASH_FAILURE]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.HUMAN_REVIEW
    assert ReasonCode.PROVENANCE_HASH_FAILURE in reasons


def test_decision_human_review_on_metadata_mismatch():
    """Section 5 & 6: Technical metadata mismatch triggers HUMAN_REVIEW."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    tech.status = CheckStatus.WARN
    tech.reason_codes = [ReasonCode.TECHNICAL_METADATA_MISMATCH]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.HUMAN_REVIEW
    assert ReasonCode.TECHNICAL_METADATA_MISMATCH in reasons


def test_decision_human_review_on_component_warning_state():
    """Section 5: Any component in WARN status without hard FAIL triggers HUMAN_REVIEW."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    temp.status = CheckStatus.WARN

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.HUMAN_REVIEW


def test_decision_multiple_failures_priority_auto_retry_over_review():
    """Section 7: Multiple failures follow existing priority (AUTO_RETRY > HUMAN_REVIEW) with full traceability."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    temp.status = CheckStatus.FAIL
    temp.reason_codes = [ReasonCode.TEMPORAL_FRAME_DROP]

    sem.status = CheckStatus.WARN
    sem.reason_codes = [ReasonCode.SEMANTIC_UNCERTAIN]

    art.status = CheckStatus.WARN
    art.reason_codes = [ReasonCode.ARTIFACT_TEXT_OVERLAY]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    # Existing policy: auto-retry defect present -> AUTO_RETRY
    assert decision == DecisionType.AUTO_RETRY
    # Traceability: all component reason codes preserved
    assert ReasonCode.TEMPORAL_FRAME_DROP in reasons
    assert ReasonCode.SEMANTIC_UNCERTAIN in reasons
    assert ReasonCode.ARTIFACT_TEXT_OVERLAY in reasons


def test_decision_multiple_failures_technical_and_temporal():
    """Section 7: Multiple component failures preserve all triggered reason codes."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    tech.status = CheckStatus.FAIL
    tech.reason_codes = [ReasonCode.TECHNICAL_INVALID_MEDIA]

    temp.status = CheckStatus.FAIL
    temp.reason_codes = [ReasonCode.TEMPORAL_FRAME_DROP, ReasonCode.TEMPORAL_MOTION_ANOMALY]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.AUTO_RETRY
    assert reasons == [
        ReasonCode.TECHNICAL_INVALID_MEDIA,
        ReasonCode.TEMPORAL_FRAME_DROP,
        ReasonCode.TEMPORAL_MOTION_ANOMALY,
    ]


def test_decision_semantic_uncertain_policy():
    """Section 8: Semantic uncertainty maps to HUMAN_REVIEW per existing policy."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    sem.status = CheckStatus.WARN
    sem.reason_codes = [ReasonCode.SEMANTIC_UNCERTAIN]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.HUMAN_REVIEW
    assert reasons == [ReasonCode.SEMANTIC_UNCERTAIN]


# =========================================================================
# Section 11: Compact Decision Test Matrix
# =========================================================================

def test_decision_matrix_case1_all_pass():
    """Matrix Case 1: All PASS -> PASS."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.PASS
    assert len(reasons) == 0


def test_decision_matrix_case2_retry_eligible():
    """Matrix Case 2: Retry-eligible failure -> AUTO_RETRY."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    art.status = CheckStatus.FAIL
    art.reason_codes = [ReasonCode.ARTIFACT_BLUR]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.AUTO_RETRY
    assert reasons == [ReasonCode.ARTIFACT_BLUR]


def test_decision_matrix_case3_review_uncertain():
    """Matrix Case 3: Review/uncertain condition -> HUMAN_REVIEW."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    sem.status = CheckStatus.WARN
    sem.reason_codes = [ReasonCode.SEMANTIC_UNCERTAIN]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.HUMAN_REVIEW
    assert reasons == [ReasonCode.SEMANTIC_UNCERTAIN]


def test_decision_matrix_case4_multiple_failures_priority():
    """Matrix Case 4: Multiple failures -> existing priority behavior."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    tech.status = CheckStatus.FAIL
    tech.reason_codes = [ReasonCode.TECHNICAL_INVALID_MEDIA]
    art.status = CheckStatus.WARN
    art.reason_codes = [ReasonCode.ARTIFACT_TEXT_OVERLAY]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.AUTO_RETRY
    assert ReasonCode.TECHNICAL_INVALID_MEDIA in reasons
    assert ReasonCode.ARTIFACT_TEXT_OVERLAY in reasons


def test_decision_matrix_case5_no_aspect_ratio_in_prompt():
    """Matrix Case 5: No aspect ratio in prompt -> no failure, PASS."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    assert decision == DecisionType.PASS
    assert ReasonCode.PROMPT_ASPECT_RATIO_MISMATCH not in reasons


def test_decision_matrix_case6_aspect_ratio_mismatch_policy():
    """Matrix Case 6: Aspect-ratio mismatch flows through technical failure decision policy."""
    engine = DecisionEngine()
    tech, temp, sem, art, prov = make_clean_results()
    tech.status = CheckStatus.FAIL
    tech.reason_codes = [ReasonCode.PROMPT_ASPECT_RATIO_MISMATCH]

    decision, reasons = engine.decide(tech, temp, sem, art, prov)
    # Existing unclassified failure policy falls back to uncertain_policy ("HUMAN_REVIEW")
    assert decision == DecisionType.HUMAN_REVIEW
    assert reasons == [ReasonCode.PROMPT_ASPECT_RATIO_MISMATCH]


# =========================================================================
# Section 10: Real Video Regression Test (hitech_girl.mp4)
# =========================================================================

def test_real_video_hitech_girl_end_to_end_decision_pass():
    """Section 10: hitech_girl.mp4 with valid prompt produces final PASS decision."""
    from pathlib import Path
    from app.pipeline import run_video_qa

    video_path = Path("mock_data/media/hitech_girl.mp4")
    if not video_path.exists():
        pytest.skip("hitech_girl.mp4 fixture missing")

    report = run_video_qa(
        video_path=video_path,
        prompt="a girl in hyderabad is walking with her dog in 9:16 portrait",
    )

    assert report.decision == DecisionType.PASS
    assert report.technical.status == CheckStatus.PASS
    assert report.temporal.status == CheckStatus.PASS
    assert report.semantic.status == CheckStatus.PASS
    assert report.artifacts.status == CheckStatus.PASS
    assert report.provenance.status == CheckStatus.PASS
    assert len(report.reason_codes) == 0


def test_real_video_hitech_girl_end_to_end_decision_aspect_mismatch():
    """Section 10: hitech_girl.mp4 with 16:9 prompt produces technical FAIL and HUMAN_REVIEW."""
    from pathlib import Path
    from app.pipeline import run_video_qa

    video_path = Path("mock_data/media/hitech_girl.mp4")
    if not video_path.exists():
        pytest.skip("hitech_girl.mp4 fixture missing")

    report = run_video_qa(
        video_path=video_path,
        prompt="a girl in hyderabad in 16:9 widescreen",
    )

    assert report.decision == DecisionType.HUMAN_REVIEW
    assert report.technical.status == CheckStatus.FAIL
    assert report.reason_codes == [ReasonCode.PROMPT_ASPECT_RATIO_MISMATCH]

