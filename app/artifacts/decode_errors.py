"""Decode failure and corrupted frame detection."""

from typing import Any, Dict, List, Tuple
from app.config import ArtifactConfig
from app.media.frame_extractor import FrameInfo


def detect_decode_errors(
    frames: List[FrameInfo],
    config: ArtifactConfig,
) -> Tuple[bool, int, List[int], Dict[str, Any]]:
    """Detect unreadable or corrupt frames that failed decoder execution."""
    corrupt_indices: List[int] = []

    for f in frames:
        if f.image is None or f.image.size == 0:
            corrupt_indices.append(f.frame_index)

    error_count = len(corrupt_indices)
    has_defect = error_count > config.max_decode_errors

    evidence = {
        "decode_error_count": error_count,
        "corrupt_frames": corrupt_indices,
    }

    return has_defect, error_count, corrupt_indices, evidence
