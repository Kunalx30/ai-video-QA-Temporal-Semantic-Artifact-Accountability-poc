"""Black frame and blank artifact detection."""

from typing import Any, Dict, List, Tuple
import numpy as np
from app.config import ArtifactConfig
from app.media.frame_extractor import FrameInfo


def detect_black_frames(
    frames: List[FrameInfo],
    config: ArtifactConfig,
) -> Tuple[bool, int, List[int], Dict[str, Any]]:
    """Detect black, blank, or completely dark frames."""
    black_frame_indices: List[int] = []
    mean_luminances: List[float] = []

    for f in frames:
        # Compute mean intensity across all channels
        mean_val = float(np.mean(f.image))
        mean_luminances.append(round(mean_val, 2))

        # Check if mean luminance is near zero
        if mean_val <= config.black_frame_luminance_threshold:
            black_frame_indices.append(f.frame_index)
        else:
            # Also check if >98% of pixels are pitch black
            dark_pixel_ratio = float(np.mean(f.image <= 2.0))
            if dark_pixel_ratio >= config.black_frame_pixel_ratio:
                black_frame_indices.append(f.frame_index)

    black_frame_count = len(black_frame_indices)
    has_defect = black_frame_count > 0

    evidence = {
        "black_frame_count": black_frame_count,
        "affected_frames": black_frame_indices,
        "luminance_threshold": config.black_frame_luminance_threshold,
    }

    return has_defect, black_frame_count, black_frame_indices, evidence
