"""Shot boundary detection and temporal discontinuity classification."""

from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np

from app.config import TemporalConfig
from app.media.frame_extractor import FrameInfo


class ShotBoundaryDetector:
    """Detects camera/shot boundaries and classifies abrupt temporal discontinuities."""

    def __init__(self, config: Optional[TemporalConfig] = None):
        self.config = config or TemporalConfig()
        self._orb = cv2.ORB_create(nfeatures=500)
        self._bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def compute_hist_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compute 2D HSV (Hue, Saturation) color histogram correlation [-1.0 to 1.0]."""
        if img1 is None or img2 is None:
            return 0.0
        hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV) if img1.ndim == 3 else img1
        hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV) if img2.ndim == 3 else img2

        hist1 = cv2.calcHist([hsv1], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(hist1, hist1)
        hist2 = cv2.calcHist([hsv2], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(hist2, hist2)

        corr = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return float(np.clip(corr, -1.0, 1.0))

    def compute_feature_matches(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        max_distance: float = 40.0,
    ) -> int:
        """Count good ORB feature matches between two frames."""
        if img1 is None or img2 is None:
            return 0
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY) if img1.ndim == 3 else img1
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY) if img2.ndim == 3 else img2

        kp1, des1 = self._orb.detectAndCompute(gray1, None)
        kp2, des2 = self._orb.detectAndCompute(gray2, None)

        if des1 is None or des2 is None or len(des1) == 0 or len(des2) == 0:
            return 0

        try:
            matches = self._bf.match(des1, des2)
            good_matches = [m for m in matches if m.distance < max_distance]
            return len(good_matches)
        except Exception:
            return 0

    def compute_frame_diff(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compute normalized L1 pixel difference [0.0 - 1.0]."""
        if img1 is None or img2 is None:
            return 0.0
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY) if img1.ndim == 3 else img1
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY) if img2.ndim == 3 else img2
        return float(np.mean(np.abs(gray2.astype(np.float32) - gray1.astype(np.float32))) / 255.0)

    def classify_discontinuity(
        self,
        frame_prev: np.ndarray,
        frame_curr: np.ndarray,
        frame_next: Optional[np.ndarray],
        baseline_diff: float,
        spike_ratio: float,
        candidate_frame: int,
        previous_frame: int,
        next_frame: Optional[int],
    ) -> Dict[str, Any]:
        """Classify a candidate discontinuity into SHOT_BOUNDARY, DROPPED_FRAME, or UNCERTAIN.

        Evaluates:
        - diff(N-1, N): previous to current
        - diff(N, N+1): current to next (if available)
        - diff(N-1, N+1): previous to next (if available)
        - histogram similarity & ORB feature matches
        """
        diff_pc = self.compute_frame_diff(frame_prev, frame_curr)
        diff_cn = self.compute_frame_diff(frame_curr, frame_next) if frame_next is not None else None
        diff_pn = self.compute_frame_diff(frame_prev, frame_next) if frame_next is not None else None

        hist_sim_pc = self.compute_hist_similarity(frame_prev, frame_curr)
        hist_sim_pn = self.compute_hist_similarity(frame_prev, frame_next) if frame_next is not None else None
        hist_sim_cn = self.compute_hist_similarity(frame_curr, frame_next) if frame_next is not None else None

        matches_pc = self.compute_feature_matches(frame_prev, frame_curr)
        matches_cn = self.compute_feature_matches(frame_curr, frame_next) if frame_next is not None else None

        cfg = self.config
        classification = "UNCERTAIN"
        confidence = 0.5
        reason = "Ambiguous discontinuity: insufficient evidence to distinguish fast motion/occlusion from dropped frame"

        # Case A: Isolated Dropped / Glitched Frame
        # Adjacent frames (N-1 and N+1) are visually consistent, but frame N is an abnormal outlier
        if (
            diff_cn is not None
            and diff_pn is not None
            and hist_sim_pn is not None
            and diff_pc > baseline_diff * 1.8
            and diff_cn > baseline_diff * 1.5
            and (
                diff_pn <= max(baseline_diff * 1.5, 0.015)
                or diff_pn < cfg.dropped_frame_isolation_ratio * min(diff_pc, diff_cn)
            )
            and hist_sim_pn >= cfg.shot_boundary_hist_threshold
        ):
            classification = "DROPPED_FRAME"
            confidence = 0.95
            reason = "Isolated frame anomaly: adjacent frames (N-1, N+1) are visually consistent while frame N is an outlier"

        # Case B: Shot Boundary / Camera Transition
        # Frame N marks a cut to a new scene:
        # Cross-boundary difference is large, difference continues across (N-1 to N+1), and scene cues indicate transition
        elif (
            diff_pc >= cfg.shot_boundary_diff_threshold
            and (diff_pn is None or diff_pn >= cfg.shot_boundary_diff_threshold * 0.75)
            and (
                hist_sim_pc < cfg.shot_boundary_hist_threshold
                or (hist_sim_pn is not None and hist_sim_pn < cfg.shot_boundary_hist_threshold)
                or (matches_cn is not None and matches_pc < cfg.shot_boundary_min_feature_matches and matches_cn >= cfg.shot_boundary_min_feature_matches * 1.5)
            )
        ):
            classification = "SHOT_BOUNDARY"
            confidence = 0.90
            reason = "Scene transition detected: visual discontinuity across shots with color histogram shift and feature drop"

        # Case B2: Multi-frame cut transition (all pairwise diffs large and scene changed)
        elif (
            diff_cn is not None
            and diff_pn is not None
            and diff_pc >= cfg.shot_boundary_diff_threshold
            and diff_cn >= cfg.shot_boundary_diff_threshold * 0.75
            and diff_pn >= cfg.shot_boundary_diff_threshold * 0.75
            and (hist_sim_pn is not None and hist_sim_pn < 0.95)
        ):
            classification = "SHOT_BOUNDARY"
            confidence = 0.85
            reason = "Multi-frame scene transition: persistent high difference across neighboring frames"

        # Case C: Intra-shot Dropped Frame / Skip (e.g. dropped_frames.mp4)
        # Abrupt motion jump within the exact same scene (high histogram similarity, low absolute cut difference)
        elif (
            spike_ratio >= 2.5
            and (diff_pc - baseline_diff) > 0.005
            and hist_sim_pc >= 0.95
            and diff_pc < cfg.shot_boundary_diff_threshold
        ):
            classification = "DROPPED_FRAME"
            confidence = 0.85
            reason = "Intra-shot frame skip: motion discontinuity within identical scene (high histogram correlation, low cut difference)"

        return {
            "candidate_frame": candidate_frame,
            "previous_frame": previous_frame,
            "next_frame": next_frame,
            "diff_previous_current": round(diff_pc, 4),
            "diff_current_next": round(diff_cn, 4) if diff_cn is not None else None,
            "diff_previous_next": round(diff_pn, 4) if diff_pn is not None else None,
            "histogram_similarity": round(hist_sim_pc, 4),
            "histogram_similarity_prev_next": round(hist_sim_pn, 4) if hist_sim_pn is not None else None,
            "feature_match_count": matches_pc,
            "classification": classification,
            "confidence": round(confidence, 2),
            "reason": reason,
        }


def detect_shot_boundaries(
    frames: List[FrameInfo],
    config: Optional[TemporalConfig] = None,
) -> List[Dict[str, Any]]:
    """Scan frame sequence and return detected shot boundaries."""
    if len(frames) < 2:
        return []
    detector = ShotBoundaryDetector(config)
    boundaries = []
    for i in range(len(frames) - 1):
        f_p = frames[i].image
        f_c = frames[i + 1].image
        diff = detector.compute_frame_diff(f_p, f_c)
        if diff >= (config or TemporalConfig()).shot_boundary_diff_threshold:
            hist_sim = detector.compute_hist_similarity(f_p, f_c)
            if hist_sim < (config or TemporalConfig()).shot_boundary_hist_threshold:
                boundaries.append({
                    "frame_from": frames[i].frame_index,
                    "frame_to": frames[i + 1].frame_index,
                    "diff": round(diff, 4),
                    "hist_similarity": round(hist_sim, 4),
                })
    return boundaries
