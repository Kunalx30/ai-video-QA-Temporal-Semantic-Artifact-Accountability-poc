"""Artificial text overlay and watermark detection."""

from typing import Any, Dict, List, Tuple
import numpy as np
from app.media.frame_extractor import FrameInfo


def detect_text_overlay(
    frames: List[FrameInfo],
) -> Tuple[bool, List[int], Dict[str, Any]]:
    """Detect artificial high-contrast watermarks or text overlays."""
    overlay_frames: List[int] = []

    for f in frames:
        img = f.image
        # Check pure saturated watermark text (e.g. red mask)
        red_mask = (img[:, :, 2] > 180) & (img[:, :, 0] < 70) & (img[:, :, 1] < 70)
        red_ratio = float(np.mean(red_mask))

        if red_ratio > 0.005:  # Noticeable artificial red text
            overlay_frames.append(f.frame_index)

    has_defect = len(overlay_frames) >= 5

    evidence = {
        "text_overlay_frames_count": len(overlay_frames),
        "affected_frames": overlay_frames[:30],
    }

    return has_defect, overlay_frames, evidence
