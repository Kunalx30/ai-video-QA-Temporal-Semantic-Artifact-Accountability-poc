"""Top-level QA report schema."""

from typing import List, Optional
from pydantic import BaseModel, Field

from app import __version__
from app.schemas.results import (
    ArtifactResult,
    DecisionType,
    ProvenanceResult,
    ReasonCode,
    SemanticResult,
    TechnicalResult,
    TemporalResult,
)


class QAReport(BaseModel):
    """Complete aggregated evaluation report produced by Member 8 QA Module."""
    video_id: str = Field(..., description="Unique video identifier")
    qa_run_id: Optional[str] = Field(default=None, description="Unique QA run identifier")
    decision: DecisionType = Field(..., description="Top-level decision: PASS, AUTO_RETRY, HUMAN_REVIEW")
    technical: TechnicalResult = Field(..., description="Technical media validation results")
    temporal: TemporalResult = Field(..., description="Temporal stability and continuity results")
    semantic: SemanticResult = Field(..., description="Semantic prompt alignment results")
    artifacts: ArtifactResult = Field(..., description="Visual artifact and defect detection results")
    provenance: ProvenanceResult = Field(..., description="Cryptographic provenance and audit identity")
    reason_codes: List[ReasonCode] = Field(default_factory=list, description="Aggregated reason codes across all checks")
    qa_version: str = Field(default=__version__, description="QA engine version string")

    def to_contract(
        self,
        clip_id: Optional[str] = None,
        qa_id: Optional[str] = None,
        evidence_files: Optional[List[str]] = None,
    ):
        """Export to Day 2 shared QAResult contract."""
        from app.schemas.contract import QAResult
        return QAResult.from_qa_report(self, clip_id=clip_id, qa_id=qa_id, evidence_files=evidence_files)

