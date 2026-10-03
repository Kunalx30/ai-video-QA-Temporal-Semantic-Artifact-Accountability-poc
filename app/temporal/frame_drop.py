"""Frame drop and abrupt temporal discontinuity detection with shot-boundary awareness."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.config import TemporalConfig
from app.media.frame_extractor import FrameInfo
from app.temporal.shot_boundary import ShotBoundaryDetector


def detect_frame_drops(
    diffs: List[Dict[str, Any]],
    config: TemporalConfig,
    frames: Optional[List[FrameInfo]] = None,
) -> Tuple[bool, List[int], Dict[str, Any]]:
    """Detect dropped frames while distinguishing legitimate shot boundaries.

    Architecture:
    1. Large frame difference -> Candidate temporal discontinuity
    2. Check neighboring frames (N-1, N, N+1)
    3. Multi-cue validation:
       - DROPPED_FRAME (isolated frame anomaly or intra-shot skip)
       - SHOT_BOUNDARY (camera transition across different scenes)
       - UNCERTAIN (ambiguous evidence; does NOT cause false drop defect)
    4. Only confirmed dropped-frame candidates trigger TEMPORAL_FRAME_DROP
    """
    if len(diffs) < 3:
        return False, [], {}

    l1_diffs = np.array([d["l1_diff"] for d in diffs], dtype=np.float32)
    median_diff = float(np.median(l1_diffs))
    mean_diff = float(np.mean(l1_diffs))
    std_diff = float(np.std(l1_diffs))

    # Frame mapping for lookup if frames provided
    frame_map = {f.frame_index: f for f in frames} if frames else {}

    raw_candidate_indices: List[int] = []
    confirmed_dropped_frame_indices: List[int] = []
    shot_boundary_indices: List[int] = []
    uncertain_indices: List[int] = []
    spike_ratios: List[float] = []
    discontinuity_classifications: List[Dict[str, Any]] = []

    detector = ShotBoundaryDetector(config)

    # 1. Detect candidate abrupt jumps
    for i in range(len(l1_diffs)):
        val = l1_diffs[i]
        prev_val = l1_diffs[i - 1] if i > 0 else median_diff
        next_val = l1_diffs[i + 1] if i < len(l1_diffs) - 1 else median_diff
        baseline = max(0.005, (prev_val + next_val) / 2.0)

        spike_ratio = val / baseline
        cand_frame_to = diffs[i]["frame_to"]
        cand_frame_from = diffs[i]["frame_from"]

        # Jump above local baseline and absolute difference
        if (spike_ratio >= 2.6 and (val - baseline) > 0.005) or (val > 0.15 and spike_ratio >= 2.0):
            raw_candidate_indices.append(cand_frame_to)

            # 2. Inspect neighboring frames and classify discontinuity
            if frames and cand_frame_to in frame_map and cand_frame_from in frame_map:
                f_curr = frame_map[cand_frame_to].image
                f_prev = frame_map[cand_frame_from].image

                next_frame_idx = cand_frame_to + 1
                f_next = frame_map[next_frame_idx].image if next_frame_idx in frame_map else None

                classification_info = detector.classify_discontinuity(
                    frame_prev=f_prev,
                    frame_curr=f_curr,
                    frame_next=f_next,
                    baseline_diff=baseline,
                    spike_ratio=float(spike_ratio),
                    candidate_frame=cand_frame_to,
                    previous_frame=cand_frame_from,
                    next_frame=next_frame_idx if f_next is not None else None,
                )
            else:
                # Fallback if raw frames are unavailable: inspect diff sequence
                classification_info = {
                    "candidate_frame": cand_frame_to,
                    "previous_frame": cand_frame_from,
                    "next_frame": None,
                    "diff_previous_current": round(float(val), 4),
                    "diff_current_next": round(float(next_val), 4),
                    "diff_previous_next": None,
                    "histogram_similarity": None,
                    "feature_match_count": None,
                    "classification": "DROPPED_FRAME" if spike_ratio >= 3.0 else "UNCERTAIN",
                    "confidence": 0.6,
                    "reason": "Evaluated on diff sequence without raw frame images",
                }

            discontinuity_classifications.append(classification_info)

            # 3. Route according to classification
            cat = classification_info.get("classification")
            if cat == "DROPPED_FRAME":
                confirmed_dropped_frame_indices.append(cand_frame_to)
                spike_ratios.append(float(round(spike_ratio, 2)))
            elif cat == "SHOT_BOUNDARY":
                shot_boundary_indices.append(cand_frame_to)
            else:
                uncertain_indices.append(cand_frame_to)

    has_defect = len(confirmed_dropped_frame_indices) > 0

    evidence = {
        "median_diff": round(median_diff, 4),
        "mean_diff": round(mean_diff, 4),
        "std_diff": round(std_diff, 4),
        "dropped_frame_candidates": confirmed_dropped_frame_indices,
        "raw_discontinuity_candidates": raw_candidate_indices,
        "shot_boundary_candidates": shot_boundary_indices,
        "uncertain_candidates": uncertain_indices,
        "spike_ratios": spike_ratios,
        "discontinuity_classifications": discontinuity_classifications,
    }

    return has_defect, confirmed_dropped_frame_indices, evidence
