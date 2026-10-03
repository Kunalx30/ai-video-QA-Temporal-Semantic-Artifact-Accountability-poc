"""Artifact quality analysis package."""

from app.artifacts.artifact_detector import ArtifactDetector
from app.artifacts.black_frame import detect_black_frames
from app.artifacts.blur import detect_blur
from app.artifacts.decode_errors import detect_decode_errors
from app.artifacts.resolution_change import detect_resolution_change
from app.artifacts.text_overlay import detect_text_overlay

__all__ = [
    "ArtifactDetector",
    "detect_black_frames",
    "detect_blur",
    "detect_decode_errors",
    "detect_resolution_change",
    "detect_text_overlay",
]
