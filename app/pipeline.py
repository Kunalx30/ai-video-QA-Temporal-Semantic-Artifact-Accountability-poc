"""End-to-end execution pipeline for Member 8 QA Module."""

from pathlib import Path
from typing import Optional

from app.artifacts import ArtifactDetector
from app.config import QAConfig
from app.decision import DecisionEngine
from app.media.frame_extractor import FrameExtractor
from app.provenance import ProvenanceTracker, generate_qa_run_id, generate_video_id
from app.schemas.input import GenerationMetadata, VideoQAInput
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
from app.semantic import PromptAlignmentEvaluator
from app.technical import FFprobeValidator


class VideoQAPipeline:
    """Orchestrates end-to-end video quality assurance analysis."""

    def __init__(self, config: Optional[QAConfig] = None):
        self.config = config or QAConfig()
        self.technical_validator = FFprobeValidator(self.config.technical)
        self.frame_extractor = FrameExtractor()
        self.temporal_analyzer = TemporalAnalyzer(self.config.temporal) if self.config.temporal.enabled else None
        self.artifact_detector = ArtifactDetector(self.config.artifacts) if self.config.artifacts.enabled else None
        self.semantic_evaluator = (
            PromptAlignmentEvaluator(self.config.semantic) if self.config.semantic.enabled else None
        )
        self.provenance_tracker = ProvenanceTracker(self.config.provenance)
        self.decision_engine = DecisionEngine(self.config.decision)

    def run(
        self,
        video_path: str | Path,
        prompt: str,
        video_id: Optional[str] = None,
        metadata: Optional[GenerationMetadata] = None,
        expected_sha256: Optional[str] = None,
    ) -> QAReport:
        qa_run_id = generate_qa_run_id()
        p = Path(video_path)

        # 1. Provenance
        prov_result = self.provenance_tracker.track(
            video_path=p,
            video_id=video_id,
            expected_sha256=expected_sha256,
            qa_run_id=qa_run_id,
        )
        vid = prov_result.video_id

        # 2. Technical Validation
        tech_result = self.technical_validator.validate(p, expected_meta=metadata)

        # Early exit if file unreadable / technical validation hard failed
        if tech_result.status == CheckStatus.FAIL:
            temp_result = TemporalResult(
                status=CheckStatus.SKIPPED,
                evidence={"skipped_reason": "Technical validation failed; frames could not be extracted"},
            )
            art_result = ArtifactResult(
                status=CheckStatus.SKIPPED,
                evidence={"skipped_reason": "Technical validation failed"},
            )
            sem_result = SemanticResult(
                status=CheckStatus.SKIPPED,
                evidence={"skipped_reason": "Technical validation failed"},
            )
            decision, reasons = self.decision_engine.decide(
                tech_result, temp_result, sem_result, art_result, prov_result
            )
            return QAReport(
                video_id=vid,
                qa_run_id=qa_run_id,
                decision=decision,
                technical=tech_result,
                temporal=temp_result,
                semantic=sem_result,
                artifacts=art_result,
                provenance=prov_result,
                reason_codes=reasons,
            )

        # 3. Extract frames
        try:
            frames = list(self.frame_extractor.iter_frames(p))
        except Exception as e:
            frames = []
            tech_result.status = CheckStatus.FAIL
            tech_result.reason_codes.append(ReasonCode.TECHNICAL_INVALID_MEDIA)
            tech_result.evidence["frame_extraction_error"] = str(e)

        if not frames:
            temp_result = TemporalResult(status=CheckStatus.FAIL, score=0.0)
            art_result = ArtifactResult(status=CheckStatus.FAIL)
            sem_result = SemanticResult(status=CheckStatus.FAIL, score=0.0)
            decision, reasons = self.decision_engine.decide(
                tech_result, temp_result, sem_result, art_result, prov_result
            )
            return QAReport(
                video_id=vid,
                qa_run_id=qa_run_id,
                decision=decision,
                technical=tech_result,
                temporal=temp_result,
                semantic=sem_result,
                artifacts=art_result,
                provenance=prov_result,
                reason_codes=reasons,
            )

        # 4. Temporal QA
        temp_result = (
            self.temporal_analyzer.analyze(frames)
            if self.temporal_analyzer
            else TemporalResult(status=CheckStatus.SKIPPED)
        )

        # 5. Artifact QA
        art_result = (
            self.artifact_detector.detect(frames)
            if self.artifact_detector
            else ArtifactResult(status=CheckStatus.SKIPPED)
        )

        # 6. Semantic QA
        sem_result = (
            self.semantic_evaluator.evaluate(frames, prompt)
            if self.semantic_evaluator
            else SemanticResult(status=CheckStatus.SKIPPED)
        )

        # 7. Decision Engine
        decision, reasons = self.decision_engine.decide(
            tech_result, temp_result, sem_result, art_result, prov_result
        )

        return QAReport(
            video_id=vid,
            qa_run_id=qa_run_id,
            decision=decision,
            technical=tech_result,
            temporal=temp_result,
            semantic=sem_result,
            artifacts=art_result,
            provenance=prov_result,
            reason_codes=reasons,
        )


# Import TemporalAnalyzer inside module after definition
from app.temporal import TemporalAnalyzer


def run_video_qa(
    video_path: str | Path,
    prompt: str = "",
    video_id: Optional[str] = None,
    metadata: Optional[GenerationMetadata] = None,
    config: Optional[QAConfig] = None,
) -> QAReport:
    """Convenience functional API to run video QA on a single file."""
    pipeline = VideoQAPipeline(config=config)
    return pipeline.run(video_path=video_path, prompt=prompt, video_id=video_id, metadata=metadata)
