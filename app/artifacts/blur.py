"""Blur and defocus artifact detection."""

from typing import Any, Dict, List, Tuple
import cv2
import numpy as np
from app.config import ArtifactConfig
from app.media.frame_extractor import FrameInfo


def detect_blur(
    frames: List[FrameInfo],
    config: ArtifactConfig,
) -> Tuple[bool, float, List[int], Dict[str, Any]]:
    """Detect severe blur, defocus, or loss of high-frequency visual detail."""
    if not frames:
        return False, 0.0, [], {}

    blur_scores: List[float] = []
    blurry_frames: List[int] = []

    for f in frames:
        gray = cv2.cvtColor(f.image, cv2.COLOR_BGR2GRAY) if f.image.ndim == 3 else f.image
        # Variance of the Laplacian: lower = more blurry
        score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        blur_scores.append(score)

        if score < config.blur_laplacian_threshold:
            blurry_frames.append(f.frame_index)

    mean_blur_score = float(np.mean(blur_scores)) if blur_scores else 0.0
    min_blur_score = float(np.min(blur_scores)) if blur_scores else 0.0

    # Defect triggered if consecutive blurry frames exist or > 10% of frames are blurry
    has_defect = len(blurry_frames) >= 3 or (len(blurry_frames) / len(frames) >= 0.10)

    evidence = {
        "mean_blur_score": round(mean_blur_score, 2),
        "min_blur_score": round(min_blur_score, 2),
        "blurry_frame_count": len(blurry_frames),
        "blurry_frames": blurry_frames[:30],
        "threshold": config.blur_laplacian_threshold,
    }

    return has_defect, mean_blur_score, blurry_frames, evidence
