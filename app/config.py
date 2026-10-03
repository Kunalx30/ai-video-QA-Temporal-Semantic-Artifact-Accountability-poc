"""Configuration settings for Member 8 QA Module."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import yaml


class TechnicalConfig(BaseModel):
    """Configuration for technical media checks."""
    enabled: bool = True
    min_width: int = 256
    min_height: int = 256
    min_fps: float = 1.0
    max_fps: float = 120.0
    min_duration_seconds: float = 0.5
    allowed_codecs: List[str] = Field(default_factory=lambda: ["h264", "hevc", "vp9", "av1", "prores", "mpeg4"])


class TemporalConfig(BaseModel):
    """Configuration for temporal quality checks."""
    enabled: bool = True
    flicker_threshold: float = 15.0  # Mean absolute luminance difference variance
    duplicate_threshold_psnr: float = 45.0  # PSNR above which frames are duplicates
    duplicate_diff_threshold: float = 0.0005  # Normalized pixel diff below which frames are duplicates
    freeze_consecutive_frames: int = 6  # Number of identical frames considered a freeze
    frame_drop_threshold: float = 0.25  # Abrupt discontinuity ratio
    use_optical_flow: bool = True
    optical_flow_mode: str = "basic"  # "basic" (OpenCV Farneback) or "advanced" (RAFT)
    # Shot-boundary aware frame drop parameters
    shot_boundary_diff_threshold: float = 0.08  # Normalized diff threshold indicating potential camera/shot cut
    shot_boundary_hist_threshold: float = 0.92  # 2D/3D HSV color histogram correlation below which shot cut is indicated
    shot_boundary_min_feature_matches: int = 25  # ORB feature match count below which shot transition is indicated
    dropped_frame_isolation_ratio: float = 0.50  # Max ratio of diff(prev, next) to min(diff(prev, curr), diff(curr, next)) for isolated dropped frame


class SemanticConfig(BaseModel):
    """Configuration for semantic prompt alignment."""
    enabled: bool = True
    model_name: str = "openai/clip-vit-base-patch32"
    sampling_strategy: str = "uniform"  # "uniform", "keyframe"
    sample_points: List[float] = Field(default_factory=lambda: [0.0, 0.25, 0.5, 0.75, 1.0])
    pass_threshold: float = 0.22  # Calibrated CLIP cosine similarity threshold
    uncertain_threshold: float = 0.18


class ArtifactConfig(BaseModel):
    """Configuration for visual defect checks."""
    enabled: bool = True
    black_frame_luminance_threshold: float = 2.0  # Max luminance mean to be classified black frame
    black_frame_pixel_ratio: float = 0.98  # Ratio of near-zero pixels
    blur_laplacian_threshold: float = 25.0  # Variance of Laplacian below which image is blurry
    max_decode_errors: int = 0


class ProvenanceConfig(BaseModel):
    """Configuration for provenance and signing."""
    enabled: bool = True
    hash_algorithm: str = "sha256"
    enable_ed25519: bool = False
    private_key_path: Optional[str] = None


class DecisionConfig(BaseModel):
    """Configuration for decision engine rules."""
    uncertain_policy: str = "HUMAN_REVIEW"  # "HUMAN_REVIEW" or "AUTO_RETRY"
    fail_on_technical_error: bool = True
    flicker_action: str = "AUTO_RETRY"
    duplicate_action: str = "AUTO_RETRY"
    freeze_action: str = "AUTO_RETRY"
    drop_action: str = "AUTO_RETRY"
    black_frame_action: str = "AUTO_RETRY"
    low_semantic_action: str = "AUTO_RETRY"


class QAConfig(BaseModel):
    """Master configuration for Member 8 QA pipeline."""
    technical: TechnicalConfig = Field(default_factory=TechnicalConfig)
    temporal: TemporalConfig = Field(default_factory=TemporalConfig)
    semantic: SemanticConfig = Field(default_factory=SemanticConfig)
    artifacts: ArtifactConfig = Field(default_factory=ArtifactConfig)
    provenance: ProvenanceConfig = Field(default_factory=ProvenanceConfig)
    decision: DecisionConfig = Field(default_factory=DecisionConfig)

    @classmethod
    def load_from_yaml(cls, path: str | Path) -> "QAConfig":
        p = Path(path)
        if not p.exists():
            return cls()
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        qa_data = data.get("qa", data)
        return cls.model_validate(qa_data)

    def save_to_yaml(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            yaml.safe_dump({"qa": self.model_dump()}, f, sort_keys=False)
