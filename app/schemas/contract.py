"""Day 2 Shared Contracts for Member 8 QA Module.

Defines ClipMetadata (shared input contract) and QAResult (shared output contract)
as specified in DAY2.md Section 6.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.input import GenerationMetadata, VideoQAInput
from app.schemas.report import QAReport
from app.schemas.results import CheckStatus, DecisionType


class ClipMetadata(BaseModel):
    """Shared input contract representing a generated video clip and its production metadata."""
    clip_id: str = Field(..., description="Unique clip identifier, e.g. CLIP_S01_SH02_T2V_01")
    shot_id: str = Field(..., description="Shot identifier, e.g. S01_SH02")
    mode: Literal["T2V", "I2V"] = Field(..., description="Generation mode: T2V or I2V")
    source_type: Literal["MOCK", "REAL"] = Field(..., description="Source type: MOCK or REAL")
    file: str = Field(..., description="Relative or absolute path to MP4 video file")
    duration_s: float = Field(..., description="Video duration in seconds")
    fps: float = Field(..., description="Framerate in frames per second")
    width: int = Field(..., description="Video frame width in pixels")
    height: int = Field(..., description="Video frame height in pixels")
    aspect_ratio: str = Field(..., description="Aspect ratio string, e.g. 16:9")
    codec: str = Field(..., description="Video codec name, e.g. h264")
    model: str = Field(default="mock-engine", description="Model identifier used for generation")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Generation settings and hyperparameters")
    reference_ids: List[str] = Field(default_factory=list, description="Reference asset/image IDs")
    motion_controls: Dict[str, Any] = Field(default_factory=dict, description="Motion controls (I2V only)")
    seed: int = Field(default=42, description="Random seed used for generation")
    status: Literal["OK", "FAILED"] = Field(default="OK", description="Generation status: OK or FAILED")
    failure_reason: Optional[str] = Field(default=None, description="Generation failure reason if status is FAILED")
    checksum_sha256: str = Field(default="", description="Cryptographic SHA-256 hash of the video file")

    def to_generation_metadata(self) -> GenerationMetadata:
        """Adapter converting ClipMetadata to Day 1 GenerationMetadata."""
        return GenerationMetadata(
            generation_id=self.clip_id,
            model=self.model,
            fps=self.fps,
            width=self.width,
            height=self.height,
            seed=self.seed,
            extra={
                "shot_id": self.shot_id,
                "mode": self.mode,
                "source_type": self.source_type,
                "duration_s": self.duration_s,
                "aspect_ratio": self.aspect_ratio,
                "codec": self.codec,
                "settings": self.settings,
                "reference_ids": self.reference_ids,
                "motion_controls": self.motion_controls,
                "status": self.status,
                "failure_reason": self.failure_reason,
                "checksum_sha256": self.checksum_sha256,
            },
        )

    def to_video_qa_input(self, prompt: str) -> VideoQAInput:
        """Adapter converting ClipMetadata + prompt to Day 1 VideoQAInput."""
        return VideoQAInput(
            video_path=self.file,
            prompt=prompt,
            video_id=self.clip_id,
            metadata=self.to_generation_metadata(),
        )


class QAResult(BaseModel):
    """Shared output contract representing the machine-readable QA evaluation outcome."""
    qa_id: str = Field(..., description="Unique QA evaluation ID, e.g. QA_S01_SH01_001")
    clip_id: str = Field(..., description="Clip identifier being evaluated")
    qa_type: str = Field(default="TEMPORAL_SEMANTIC", description="Module QA type identifier")
    component_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Normalized component scores [0.0 - 1.0]: technical, temporal, artifacts, semantic, provenance",
    )
    reason_codes: List[str] = Field(default_factory=list, description="Machine-readable active reason codes")
    decision: Literal["PASS", "AUTO_RETRY", "HUMAN_REVIEW"] = Field(
        ...,
        description="Top-level QA decision: PASS, AUTO_RETRY, or HUMAN_REVIEW",
    )
    evidence_files: List[str] = Field(default_factory=list, description="Paths to generated evidence files")

    @classmethod
    def from_qa_report(
        cls,
        report: QAReport,
        clip_id: Optional[str] = None,
        qa_id: Optional[str] = None,
        evidence_files: Optional[List[str]] = None,
    ) -> "QAResult":
        """Construct a QAResult contract instance from an existing Day 1 QAReport."""
        c_id = clip_id or report.video_id
        q_id = qa_id or (report.qa_run_id if report.qa_run_id else f"QA_{c_id}")

        # Compute normalized component scores [0.0 - 1.0] from actual detector outputs
        def _score_for_status(status: CheckStatus, measured_score: Optional[float] = None) -> float:
            if measured_score is not None:
                return round(float(measured_score), 2)
            if status == CheckStatus.PASS:
                return 1.0
            elif status == CheckStatus.WARN:
                return 0.5
            elif status == CheckStatus.SKIPPED:
                return 0.0
            return 0.0

        scores = {
            "technical": _score_for_status(report.technical.status, report.technical.score),
            "temporal": _score_for_status(report.temporal.status, report.temporal.score),
            "artifacts": _score_for_status(report.artifacts.status, report.artifacts.score),
            "semantic": _score_for_status(report.semantic.status, report.semantic.score),
            "provenance": 1.0 if report.provenance.status == CheckStatus.PASS else 0.0,
        }

        reasons = [r.value if hasattr(r, "value") else str(r) for r in report.reason_codes]
        dec = report.decision.value if hasattr(report.decision, "value") else str(report.decision)

        return cls(
            qa_id=q_id,
            clip_id=c_id,
            qa_type="TEMPORAL_SEMANTIC",
            component_scores=scores,
            reason_codes=reasons,
            decision=dec,
            evidence_files=evidence_files or [],
        )
