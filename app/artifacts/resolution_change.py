"""Resolution inconsistency, pixelation, and aspect ratio artifact detection."""

from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from app.config import ArtifactConfig
from app.media.frame_extractor import FrameInfo


def detect_resolution_change(
    frames: List[FrameInfo],
    config: Optional[ArtifactConfig] = None,
) -> Tuple[bool, List[int], Dict[str, Any]]:
    """Detect dynamic resolution changes, nearest-neighbor pixelation, or aspect ratio changes."""
    if len(frames) < 3:
        return False, [], {}

    base_w = frames[0].width
    base_h = frames[0].height

    dimension_anomalies: List[int] = []
    sharpness_scores: List[float] = []

    for f in frames:
        if f.width != base_w or f.height != base_h:
            dimension_anomalies.append(f.frame_index)

        gray = cv2.cvtColor(f.image, cv2.COLOR_BGR2GRAY) if f.image.ndim == 3 else f.image
        var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        sharpness_scores.append(var)

    # Detect abrupt structural jump in high-frequency variance (e.g. nearest-neighbor pixelation aliasing)
    sharpness_diffs = np.abs(np.diff(sharpness_scores))
    median_diff = max(0.5, float(np.median(sharpness_diffs)))

    step_change_frames: List[int] = []
    for i in range(len(sharpness_diffs)):
        # Jump > 10.0 and > 4x median frame-to-frame variance jump
        if sharpness_diffs[i] > 10.0 and sharpness_diffs[i] > 3.5 * median_diff:
            step_change_frames.append(frames[i + 1].frame_index)

    has_dimension_defect = len(dimension_anomalies) > 0
    has_step_defect = len(step_change_frames) >= 2  # Entering and exiting a resolution-shifted segment

    has_defect = has_dimension_defect or has_step_defect
    affected = dimension_anomalies or step_change_frames

    evidence = {
        "dimension_anomalies": dimension_anomalies,
        "sharpness_step_change_frames": step_change_frames,
        "base_resolution": f"{base_w}x{base_h}",
    }

    return has_defect, affected, evidence
