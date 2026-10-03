"""Duplicate frame detection."""

from typing import Any, Dict, List, Tuple
from app.config import TemporalConfig
from app.schemas.results import ReasonCode


def detect_duplicates(
    diffs: List[Dict[str, Any]],
    config: TemporalConfig,
) -> Tuple[bool, float, List[int], Dict[str, Any]]:
    """Detect repeated identical or near-identical consecutive frames."""
    if not diffs:
        return False, 0.0, [], {}

    duplicate_frames: List[int] = []
    consecutive_run = 0
    max_consecutive_run = 0

    for d in diffs:
        # Check against L1 diff threshold and PSNR threshold
        is_dup = (
            d["l1_diff"] <= config.duplicate_diff_threshold
            and d["psnr"] >= config.duplicate_threshold_psnr
        )
        if is_dup:
            duplicate_frames.append(d["frame_to"])
            consecutive_run += 1
            max_consecutive_run = max(max_consecutive_run, consecutive_run)
        else:
            consecutive_run = 0

    total_pairs = len(diffs)
    duplicate_ratio = len(duplicate_frames) / total_pairs if total_pairs > 0 else 0.0

    # Triggers if duplicate ratio > 10% or more than 4 consecutive duplicates
    has_defect = duplicate_ratio >= 0.10 or max_consecutive_run >= 4

    evidence = {
        "duplicate_count": len(duplicate_frames),
        "total_pairs": total_pairs,
        "duplicate_ratio": round(duplicate_ratio, 4),
        "max_consecutive_duplicates": max_consecutive_run,
        "affected_frames": duplicate_frames[:50],  # cap for readability
    }

    return has_defect, duplicate_ratio, duplicate_frames, evidence
