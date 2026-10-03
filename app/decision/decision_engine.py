"""Decision engine combining multi-component QA results into actionable decisions."""

from typing import List, Optional, Tuple
from app.config import DecisionConfig
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


class DecisionEngine:
    """Evaluates component QA results against explicit policy rules to produce final decision."""

    def __init__(self, config: Optional[DecisionConfig] = None):
        self.config = config or DecisionConfig()

    def decide(
        self,
        technical: TechnicalResult,
        temporal: TemporalResult,
        semantic: SemanticResult,
        artifacts: ArtifactResult,
        provenance: ProvenanceResult,
    ) -> Tuple[DecisionType, List[ReasonCode]]:
        """Compute the final decision and aggregate all active reason codes."""
        # 1. Aggregate reason codes across all components
        all_reasons: List[ReasonCode] = []
        for comp in [technical, temporal, semantic, artifacts, provenance]:
            for r in comp.reason_codes:
                if r not in all_reasons:
                    all_reasons.append(r)

        # 2. Check for human review conditions first (ambiguous signals, warnings, security/hash defects)
        needs_human_review = False

        if ReasonCode.PROVENANCE_HASH_FAILURE in all_reasons or ReasonCode.PROVENANCE_METADATA_FAILURE in all_reasons:
            needs_human_review = True

        if ReasonCode.ARTIFACT_TEXT_OVERLAY in all_reasons:
            needs_human_review = True

        if ReasonCode.SEMANTIC_UNCERTAIN in all_reasons:
            needs_human_review = True

        if ReasonCode.TECHNICAL_METADATA_MISMATCH in all_reasons:
            needs_human_review = True

        # Check if any component is in WARN state
        statuses = [technical.status, temporal.status, semantic.status, artifacts.status, provenance.status]
        if any(s == CheckStatus.WARN for s in statuses) and not any(s == CheckStatus.FAIL for s in statuses):
            needs_human_review = True

        # 3. Check for auto-retryable defects (known, machine-detectable failures)
        auto_retry_codes = {
            ReasonCode.TEMPORAL_FLICKER,
            ReasonCode.TEMPORAL_DUPLICATE_FRAMES,
            ReasonCode.TEMPORAL_FREEZE,
            ReasonCode.TEMPORAL_FRAME_DROP,
            ReasonCode.TEMPORAL_MOTION_ANOMALY,
            ReasonCode.ARTIFACT_BLACK_FRAME,
            ReasonCode.ARTIFACT_BLUR,
            ReasonCode.ARTIFACT_RESOLUTION_CHANGE,
            ReasonCode.ARTIFACT_DECODE_FAILURE,
            ReasonCode.SEMANTIC_LOW_ALIGNMENT,
            ReasonCode.TECHNICAL_INVALID_MEDIA,
        }

        has_auto_retry_defect = any(r in auto_retry_codes for r in all_reasons)
        has_failure = any(s == CheckStatus.FAIL for s in statuses)

        if has_auto_retry_defect:
            return DecisionType.AUTO_RETRY, all_reasons

        if needs_human_review:
            return DecisionType.HUMAN_REVIEW, all_reasons

        if has_failure:
            # Unclassified failure falls back to configured uncertain_policy
            return DecisionType(self.config.uncertain_policy), all_reasons

        # All checks passed
        return DecisionType.PASS, all_reasons
