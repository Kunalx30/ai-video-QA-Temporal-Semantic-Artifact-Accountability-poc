"""Input schemas for Member 8 QA module."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class GenerationMetadata(BaseModel):
    """Optional generation metadata supplied with the input video."""
    generation_id: Optional[str] = Field(default=None, description="Generation identifier")
    model: Optional[str] = Field(default=None, description="Model identifier if known")
    fps: Optional[float] = Field(default=None, description="Expected frames per second")
    width: Optional[int] = Field(default=None, description="Expected video width")
    height: Optional[int] = Field(default=None, description="Expected video height")
    seed: Optional[int] = Field(default=None, description="Generation seed if known")
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional custom metadata")


class VideoQAInput(BaseModel):
    """Input contract for video quality assurance evaluation."""
    video_path: str = Field(..., description="Path to video file (.mp4, etc.)")
    prompt: str = Field(..., description="Text prompt used to generate video")
    video_id: Optional[str] = Field(default=None, description="Optional existing video identifier")
    metadata: Optional[GenerationMetadata] = Field(
        default_factory=GenerationMetadata,
        description="Optional generation metadata"
    )
