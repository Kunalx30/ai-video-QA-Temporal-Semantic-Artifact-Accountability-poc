"""Motion anomaly and speed jump detection."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from app.config import TemporalConfig


def detect_motion_anomalies(
    diffs: List[Dict[str, Any]],
    flow_magnitudes: Optional[List[float]] = None,
    config: Optional[TemporalConfig] = None,
) -> Tuple[bool, List[int], Dict[str, Any]]:
    """Detect erratic motion acceleration, unnatural speed jumps, or kinetic instability."""
    if flow_magnitudes and len(flow_magnitudes) >= 3:
        speeds = np.array(flow_magnitudes, dtype=np.float32)
    elif diffs and len(diffs) >= 3:
        speeds = np.array([d["l1_diff"] for d in diffs], dtype=np.float32)
    else:
        return False, [], {}

    # Calculate frame-to-frame speed acceleration |v_{t+1} - v_t|
    accelerations = np.abs(np.diff(speeds))
    median_speed = max(0.005, float(np.median(speeds)))

    anomaly_indices: List[int] = []
    spike_magnitudes: List[float] = []

    for i in range(len(accelerations)):
        acc = accelerations[i]
        curr_speed = speeds[i + 1]
        prev_speed = speeds[i]

        # Sudden speed multiplication (> 3.5x jump in motion speed)
        speed_ratio = max(curr_speed, prev_speed) / max(0.005, min(curr_speed, prev_speed))
        if speed_ratio > 3.5 and acc > 0.08:
            frame_idx = diffs[i + 1]["frame_to"] if i + 1 < len(diffs) else i + 1
            anomaly_indices.append(frame_idx)
            spike_magnitudes.append(float(round(speed_ratio, 2)))

    has_defect = len(anomaly_indices) > 0

    evidence = {
        "median_motion_speed": round(median_speed, 4),
        "speed_anomaly_frames": anomaly_indices,
        "speed_jump_ratios": spike_magnitudes,
    }

    return has_defect, anomaly_indices, evidence
