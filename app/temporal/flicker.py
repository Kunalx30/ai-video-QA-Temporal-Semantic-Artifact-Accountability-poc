"""Luminance flicker detection."""

from typing import Any, Dict, List, Tuple
import numpy as np
from app.config import TemporalConfig


def detect_flicker(
    diffs: List[Dict[str, Any]],
    config: TemporalConfig,
) -> Tuple[bool, float, List[int], Dict[str, Any]]:
    """Detect rapid luminance oscillation and brightness flicker between consecutive frames."""
    if len(diffs) < 3:
        return False, 0.0, [], {}

    luminances = [diffs[0]["lum1"]] + [d["lum2"] for d in diffs]
    lum_deltas = np.diff(luminances)

    # 1. High frequency oscillation: alternating signs with significant amplitude
    sign_flips = 0
    flickering_frames: List[int] = []
    oscillation_magnitudes: List[float] = []

    for i in range(len(lum_deltas) - 1):
        d1 = lum_deltas[i]
        d2 = lum_deltas[i + 1]
        # Opposite signs and both have noticeable magnitude (> 5.0 in 8-bit scale)
        if (d1 * d2 < -1e-5) and (abs(d1) > 5.0 or abs(d2) > 5.0):
            sign_flips += 1
            flickering_frames.append(diffs[i + 1]["frame_to"])
            oscillation_magnitudes.append(float(abs(d1 - d2)))

    # Second-order luminance acceleration
    if len(luminances) >= 3:
        second_diff = np.diff(lum_deltas)
        mean_second_diff = float(np.mean(np.abs(second_diff)))
        max_second_diff = float(np.max(np.abs(second_diff)))
    else:
        mean_second_diff = 0.0
        max_second_diff = 0.0

    # Composite flicker score
    flicker_score = mean_second_diff

    # Defect condition: flicker score exceeds configured threshold or high alternating sign flips
    has_defect = flicker_score >= config.flicker_threshold or (sign_flips >= 4 and max_second_diff > 25.0)

    evidence = {
        "flicker_score": round(flicker_score, 3),
        "mean_second_order_diff": round(mean_second_diff, 3),
        "max_second_order_diff": round(max_second_diff, 3),
        "alternating_sign_flips": sign_flips,
        "affected_frames": sorted(list(set(flickering_frames)))[:30],
    }

    return has_defect, flicker_score, flickering_frames, evidence
