"""Freeze frame sequence detection."""

from typing import Any, Dict, List, Tuple
from app.config import TemporalConfig


def detect_freeze(
    diffs: List[Dict[str, Any]],
    config: TemporalConfig,
) -> Tuple[bool, float, List[Dict[str, Any]], Dict[str, Any]]:
    """Detect extended frozen sequences where consecutive frames show no motion."""
    if not diffs:
        return False, 0.0, [], {}

    freeze_runs: List[Dict[str, Any]] = []
    current_run_start: int | None = None
    current_run_len = 0
    total_frozen_frames = 0

    for d in diffs:
        is_identical = d["l1_diff"] <= config.duplicate_diff_threshold and d["psnr"] >= config.duplicate_threshold_psnr
        if is_identical:
            if current_run_start is None:
                current_run_start = d["frame_from"]
            current_run_len += 1
        else:
            if current_run_len >= config.freeze_consecutive_frames and current_run_start is not None:
                freeze_runs.append({
                    "start_frame": current_run_start,
                    "end_frame": current_run_start + current_run_len,
                    "frozen_frames_count": current_run_len,
                })
                total_frozen_frames += current_run_len
            current_run_start = None
            current_run_len = 0

    if current_run_len >= config.freeze_consecutive_frames and current_run_start is not None:
        freeze_runs.append({
            "start_frame": current_run_start,
            "end_frame": current_run_start + current_run_len,
            "frozen_frames_count": current_run_len,
        })
        total_frozen_frames += current_run_len

    total_pairs = len(diffs)
    freeze_ratio = total_frozen_frames / total_pairs if total_pairs > 0 else 0.0
    has_defect = len(freeze_runs) > 0

    evidence = {
        "freeze_runs": freeze_runs,
        "total_frozen_frames": total_frozen_frames,
        "freeze_ratio": round(freeze_ratio, 4),
    }

    return has_defect, freeze_ratio, freeze_runs, evidence
