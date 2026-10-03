"""Result models and reason codes for QA evaluation."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CheckStatus(str, Enum):
    """Status of an individual QA check."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


class DecisionType(str, Enum):
    """Allowed top-level QA decisions."""
    PASS = "PASS"
    AUTO_RETRY = "AUTO_RETRY"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class ReasonCode(str, Enum):
    """Stable machine-readable failure and warning reason codes."""
    # Technical
    TECHNICAL_INVALID_MEDIA = "TECHNICAL_INVALID_MEDIA"
    TECHNICAL_METADATA_MISMATCH = "TECHNICAL_METADATA_MISMATCH"
    TECHNICAL_FILE_NOT_FOUND = "TECHNICAL_FILE_NOT_FOUND"
    TECHNICAL_EXECUTION_ERROR = "TECHNICAL_EXECUTION_ERROR"

    # Temporal
    TEMPORAL_FLICKER = "TEMPORAL_FLICKER"
    TEMPORAL_DUPLICATE_FRAMES = "TEMPORAL_DUPLICATE_FRAMES"
    TEMPORAL_FREEZE = "TEMPORAL_FREEZE"
    TEMPORAL_FRAME_DROP = "TEMPORAL_FRAME_DROP"
    TEMPORAL_MOTION_ANOMALY = "TEMPORAL_MOTION_ANOMALY"

    # Semantic
    SEMANTIC_LOW_ALIGNMENT = "SEMANTIC_LOW_ALIGNMENT"
    SEMANTIC_UNCERTAIN = "SEMANTIC_UNCERTAIN"
    SEMANTIC_MODEL_UNAVAILABLE = "SEMANTIC_MODEL_UNAVAILABLE"

    # Artifacts
    ARTIFACT_BLACK_FRAME = "ARTIFACT_BLACK_FRAME"
    ARTIFACT_BLUR = "ARTIFACT_BLUR"
    ARTIFACT_RESOLUTION_CHANGE = "ARTIFACT_RESOLUTION_CHANGE"
    ARTIFACT_DECODE_FAILURE = "ARTIFACT_DECODE_FAILURE"
    ARTIFACT_CORRUPTION = "ARTIFACT_CORRUPTION"
    ARTIFACT_TEXT_OVERLAY = "ARTIFACT_TEXT_OVERLAY"

    # Provenance
    PROVENANCE_HASH_FAILURE = "PROVENANCE_HASH_FAILURE"
    PROVENANCE_METADATA_FAILURE = "PROVENANCE_METADATA_FAILURE"
    PROVENANCE_SIGNATURE_INVALID = "PROVENANCE_SIGNATURE_INVALID"


class ComponentResult(BaseModel):
    """Base model for component-level QA results."""
    status: CheckStatus = Field(default=CheckStatus.PASS, description="Status of this component check")
    score: Optional[float] = Field(default=None, description="Normalized score [0.0 - 1.0] if applicable")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Structured component evidence")
    reason_codes: List[ReasonCode] = Field(default_factory=list, description="Reason codes triggered")


class TechnicalResult(ComponentResult):
    """Results from ffprobe and technical container/stream checks."""
    width: Optional[int] = Field(default=None, description="Detected width")
    height: Optional[int] = Field(default=None, description="Detected height")
    fps: Optional[float] = Field(default=None, description="Detected framerate")
    duration_seconds: Optional[float] = Field(default=None, description="Detected duration in seconds")
    video_codec: Optional[str] = Field(default=None, description="Detected video codec")
    has_audio: Optional[bool] = Field(default=None, description="Whether audio stream is present")
    frame_count: Optional[int] = Field(default=None, description="Detected or counted frames")


class TemporalResult(ComponentResult):
    """Results from temporal consistency checks (flicker, drops, duplicates, optical flow)."""
    flicker_score: Optional[float] = None
    duplicate_ratio: Optional[float] = None
    freeze_ratio: Optional[float] = None
    motion_smoothness: Optional[float] = None


class SemanticResult(ComponentResult):
    """Results from prompt alignment and semantic consistency evaluation."""
    similarity_score: Optional[float] = None
    sampled_frame_scores: List[float] = Field(default_factory=list)


class ArtifactResult(ComponentResult):
    """Results from visual artifact detection (blur, black frames, decode glitches)."""
    black_frame_count: int = 0
    blur_score: Optional[float] = None
    decode_errors_count: int = 0


class ProvenanceResult(ComponentResult):
    """Results from provenance tracking and accountability."""
    sha256: str = Field(default="", description="Cryptographic SHA-256 hash of video file")
    video_id: str = Field(default="", description="Unique video identifier")
    qa_run_id: str = Field(default="", description="Unique QA execution run ID")
    signature: Optional[str] = Field(default=None, description="Optional digital signature")
