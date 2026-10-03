"""Temporal quality analysis package."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from app.config import TemporalConfig
from app.media.frame_extractor import FrameExtractor, FrameInfo
from app.schemas.results import CheckStatus, ReasonCode, TemporalResult
from app.temporal.duplicate_frames import detect_duplicates
from app.temporal.flicker import detect_flicker
from app.temporal.frame_difference import compute_frame_diff, compute_sequence_diffs
from app.temporal.frame_drop import detect_frame_drops
from app.temporal.freeze_detection import detect_freeze
from app.temporal.motion_anomaly import detect_motion_anomalies
from app.temporal.shot_boundary import ShotBoundaryDetector, detect_shot_boundaries
from app.temporal.optical_flow import (
    FarnebackFlowEstimator,
    OpticalFlowEstimator,
    RAFTFlowEstimator,
    get_optical_flow_estimator,
)


class TemporalAnalyzer:
    """Evaluates temporal quality, motion consistency, and temporal defects."""

    def __init__(self, config: Optional[TemporalConfig] = None):
        self.config = config or TemporalConfig()
        self.flow_estimator = get_optical_flow_estimator(self.config.optical_flow_mode)

    def analyze(self, frames: List[FrameInfo]) -> TemporalResult:
        if len(frames) < 2:
            return TemporalResult(
                status=CheckStatus.FAIL,
                score=0.0,
                evidence={"error": "Insufficient frames for temporal analysis (need >= 2)"},
                reason_codes=[ReasonCode.TEMPORAL_FRAME_DROP],
            )

        # 1. Compute frame differences
        diffs = compute_sequence_diffs(frames)

        # 2. Check for duplicates
        has_dup, dup_ratio, dup_frames, dup_ev = detect_duplicates(diffs, self.config)

        # 3. Check for freeze
        has_freeze, freeze_ratio, freeze_runs, freeze_ev = detect_freeze(diffs, self.config)

        # 4. Check for flicker
        has_flicker, flicker_score, flicker_frames, flicker_ev = detect_flicker(diffs, self.config)

        # 5. Check for dropped frames (with shot-boundary awareness)
        has_drops, drop_frames, drop_ev = detect_frame_drops(diffs, self.config, frames=frames)

        # 6. Optional optical flow sampling (every 3rd frame to optimize speed)
        flow_magnitudes = []
        flow_smoothness_scores = []
        if self.config.use_optical_flow and len(frames) >= 2:
            sample_step = max(1, len(frames) // 20)
            for i in range(0, len(frames) - 1, sample_step):
                flow = self.flow_estimator.estimate_flow(frames[i].image, frames[i + 1].image)
                metrics = self.flow_estimator.compute_flow_metrics(flow)
                flow_magnitudes.append(metrics["mean_magnitude"])
                flow_smoothness_scores.append(metrics["smoothness_energy"])

        # 7. Check motion anomalies
        has_motion_anomaly, anomaly_frames, anomaly_ev = detect_motion_anomalies(
            diffs, flow_magnitudes=flow_magnitudes, config=self.config
        )

        reason_codes: List[ReasonCode] = []
        if has_dup:
            reason_codes.append(ReasonCode.TEMPORAL_DUPLICATE_FRAMES)
        if has_freeze:
            reason_codes.append(ReasonCode.TEMPORAL_FREEZE)
        if has_flicker:
            reason_codes.append(ReasonCode.TEMPORAL_FLICKER)
        if has_drops:
            reason_codes.append(ReasonCode.TEMPORAL_FRAME_DROP)
        if has_motion_anomaly:
            reason_codes.append(ReasonCode.TEMPORAL_MOTION_ANOMALY)

        # Compute normalized score [0.0 - 1.0]
        # Base starts at 1.0, penalties applied for detected defects
        penalties = 0.0
        if has_dup:
            penalties += min(0.4, dup_ratio * 0.8)
        if has_freeze:
            penalties += min(0.5, freeze_ratio * 0.9)
        if has_flicker:
            penalties += min(0.4, flicker_score / 50.0)
        if has_drops:
            penalties += 0.35
        if has_motion_anomaly:
            penalties += 0.30

        temporal_score = max(0.0, round(1.0 - penalties, 3))
        status = CheckStatus.PASS if len(reason_codes) == 0 else CheckStatus.FAIL

        mean_smoothness = float(np.mean(flow_smoothness_scores)) if flow_smoothness_scores else 1.0
        motion_smoothness = round(1.0 / (1.0 + mean_smoothness / 100.0), 3)

        evidence: Dict[str, Any] = {
            "duplicate_evidence": dup_ev,
            "freeze_evidence": freeze_ev,
            "flicker_evidence": flicker_ev,
            "drop_evidence": drop_ev,
            "motion_anomaly_evidence": anomaly_ev,
            "optical_flow_mode": self.config.optical_flow_mode,
            "total_frames_analyzed": len(frames),
        }

        return TemporalResult(
            status=status,
            score=temporal_score,
            flicker_score=round(flicker_score, 3),
            duplicate_ratio=round(dup_ratio, 4),
            freeze_ratio=round(freeze_ratio, 4),
            motion_smoothness=motion_smoothness,
            evidence=evidence,
            reason_codes=reason_codes,
        )


__all__ = [
    "TemporalAnalyzer",
    "compute_frame_diff",
    "compute_sequence_diffs",
    "detect_duplicates",
    "detect_freeze",
    "detect_flicker",
    "detect_frame_drops",
    "detect_motion_anomalies",
    "ShotBoundaryDetector",
    "detect_shot_boundaries",
    "OpticalFlowEstimator",
    "FarnebackFlowEstimator",
    "RAFTFlowEstimator",
    "get_optical_flow_estimator",
]
