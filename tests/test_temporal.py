from pathlib import Path
import cv2
import numpy as np
import pytest
from app.config import TemporalConfig
from app.media.frame_extractor import FrameExtractor
from app.schemas.results import CheckStatus, ReasonCode
from app.temporal import (
    FarnebackFlowEstimator,
    RAFTFlowEstimator,
    ShotBoundaryDetector,
    TemporalAnalyzer,
    detect_shot_boundaries,
    get_optical_flow_estimator,
)


@pytest.fixture
def extractor():
    return FrameExtractor()


def test_good_fixture_passes_temporal(extractor):
    frames = list(extractor.iter_frames("mock_data/media/good.mp4"))
    analyzer = TemporalAnalyzer()
    result = analyzer.analyze(frames)

    assert result.status == CheckStatus.PASS
    assert result.score is not None and result.score >= 0.85
    assert len(result.reason_codes) == 0


def test_duplicate_frames_detected(extractor):
    frames = list(extractor.iter_frames("mock_data/media/duplicate_frames.mp4"))
    analyzer = TemporalAnalyzer()
    result = analyzer.analyze(frames)

    assert result.status == CheckStatus.FAIL
    assert ReasonCode.TEMPORAL_DUPLICATE_FRAMES in result.reason_codes
    assert result.duplicate_ratio is not None and result.duplicate_ratio > 0.05


def test_freeze_frames_detected(extractor):
    frames = list(extractor.iter_frames("mock_data/media/freeze.mp4"))
    analyzer = TemporalAnalyzer()
    result = analyzer.analyze(frames)

    assert result.status == CheckStatus.FAIL
    assert ReasonCode.TEMPORAL_FREEZE in result.reason_codes
    assert result.freeze_ratio is not None and result.freeze_ratio > 0.10


def test_flicker_detected(extractor):
    frames = list(extractor.iter_frames("mock_data/media/flicker.mp4"))
    analyzer = TemporalAnalyzer()
    result = analyzer.analyze(frames)

    assert result.status == CheckStatus.FAIL
    assert ReasonCode.TEMPORAL_FLICKER in result.reason_codes


def test_dropped_frames_detected(extractor):
    frames = list(extractor.iter_frames("mock_data/media/dropped_frames.mp4"))
    analyzer = TemporalAnalyzer()
    result = analyzer.analyze(frames)

    assert result.status == CheckStatus.FAIL
    assert ReasonCode.TEMPORAL_FRAME_DROP in result.reason_codes


def test_speed_jump_detected(extractor):
    frames = list(extractor.iter_frames("mock_data/media/speed_jump.mp4"))
    analyzer = TemporalAnalyzer()
    result = analyzer.analyze(frames)

    assert result.status == CheckStatus.FAIL
    assert ReasonCode.TEMPORAL_MOTION_ANOMALY in result.reason_codes


def test_optical_flow_farneback_and_raft(extractor):
    frames = list(extractor.iter_frames("mock_data/media/good.mp4", max_frames=3))
    assert len(frames) >= 2

    # Basic mode
    farneback = FarnebackFlowEstimator()
    flow1 = farneback.estimate_flow(frames[0].image, frames[1].image)
    assert flow1.shape == (360, 640, 2)
    metrics1 = farneback.compute_flow_metrics(flow1)
    assert "mean_magnitude" in metrics1

    # Advanced RAFT mode (CPU graceful execution / fallback)
    raft = RAFTFlowEstimator(use_gpu=False)
    flow2 = raft.estimate_flow(frames[0].image, frames[1].image)
    assert flow2.shape == (360, 640, 2)
    metrics2 = raft.compute_flow_metrics(flow2)
    assert "mean_magnitude" in metrics2


def test_temporal_analyzer_modes(extractor):
    frames = list(extractor.iter_frames("mock_data/media/good.mp4", max_frames=5))
    cfg_basic = TemporalConfig(optical_flow_mode="basic")
    cfg_adv = TemporalConfig(optical_flow_mode="advanced")

    res_basic = TemporalAnalyzer(cfg_basic).analyze(frames)
    res_adv = TemporalAnalyzer(cfg_adv).analyze(frames)

    assert res_basic.status == CheckStatus.PASS
    assert res_adv.status == CheckStatus.PASS


def test_classify_isolated_dropped_frame_pattern():
    """Unit test 1: N-1 similar to N+1, N abnormal -> DROPPED_FRAME."""
    detector = ShotBoundaryDetector()
    # Create synthetic frames: f_prev and f_next are nearly identical scene, f_curr is an abnormal glitch
    f_prev = np.full((120, 160, 3), 128, dtype=np.uint8)
    cv2.circle(f_prev, (50, 50), 20, (0, 255, 0), -1)

    f_next = f_prev.copy()
    cv2.circle(f_next, (52, 50), 20, (0, 255, 0), -1)  # small 2px motion

    f_curr = np.zeros((120, 160, 3), dtype=np.uint8)  # abnormal black/glitched frame

    ev = detector.classify_discontinuity(
        frame_prev=f_prev,
        frame_curr=f_curr,
        frame_next=f_next,
        baseline_diff=0.01,
        spike_ratio=15.0,
        candidate_frame=2,
        previous_frame=1,
        next_frame=3,
    )

    assert ev["classification"] == "DROPPED_FRAME"
    assert ev["candidate_frame"] == 2
    assert ev["diff_previous_current"] > 0.05
    assert ev["diff_previous_next"] < 0.02


def test_classify_shot_boundary_pattern():
    """Unit test 2: N-1 different from N+1 (scene cut) -> SHOT_BOUNDARY."""
    detector = ShotBoundaryDetector()
    # Shot 1: green outdoor scene
    f_prev = np.zeros((120, 160, 3), dtype=np.uint8)
    f_prev[:, :] = (30, 180, 40)
    cv2.putText(f_prev, "SHOT1", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    # Shot 2: blue sky scene
    f_curr = np.zeros((120, 160, 3), dtype=np.uint8)
    f_curr[:, :] = (200, 120, 20)
    cv2.putText(f_curr, "SHOT2", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    f_next = f_curr.copy()
    cv2.circle(f_next, (80, 80), 10, (255, 255, 255), -1)

    ev = detector.classify_discontinuity(
        frame_prev=f_prev,
        frame_curr=f_curr,
        frame_next=f_next,
        baseline_diff=0.02,
        spike_ratio=8.0,
        candidate_frame=2,
        previous_frame=1,
        next_frame=3,
    )

    assert ev["classification"] == "SHOT_BOUNDARY"
    assert ev["candidate_frame"] == 2
    assert ev["histogram_similarity"] < 0.92


def test_classify_ambiguous_case():
    """Unit test 3: Ambiguous difference without clear drop or cut -> UNCERTAIN."""
    detector = ShotBoundaryDetector()
    # Ambiguous pattern: moderate difference, moderate similarity, no clear cut or isolation
    f_prev = np.full((120, 160, 3), 100, dtype=np.uint8)
    f_curr = np.full((120, 160, 3), 112, dtype=np.uint8)
    f_next = np.full((120, 160, 3), 125, dtype=np.uint8)

    ev = detector.classify_discontinuity(
        frame_prev=f_prev,
        frame_curr=f_curr,
        frame_next=f_next,
        baseline_diff=0.02,
        spike_ratio=2.2,
        candidate_frame=2,
        previous_frame=1,
        next_frame=3,
    )

    assert ev["classification"] == "UNCERTAIN"


def test_hitech_girl_shot_boundaries_not_flagged_as_drops(extractor):
    """Unit test 6: Real hitech_girl.mp4 shot transitions must not trigger TEMPORAL_FRAME_DROP."""
    video_path = Path("mock_data/media/hitech_girl.mp4")
    if not video_path.exists():
        pytest.skip("hitech_girl.mp4 fixture not present in mock_data/media/")

    frames = list(extractor.iter_frames(str(video_path)))
    assert len(frames) == 240

    analyzer = TemporalAnalyzer()
    result = analyzer.analyze(frames)

    # Frame-drop defect must NOT be triggered
    assert ReasonCode.TEMPORAL_FRAME_DROP not in result.reason_codes

    drop_ev = result.evidence.get("drop_evidence", {})
    # Confirmed dropped frames must be empty
    assert drop_ev.get("dropped_frame_candidates") == []

    # Shot boundaries must be recognized
    shot_cands = set(drop_ev.get("shot_boundary_candidates", []))
    assert 65 in shot_cands
    assert 103 in shot_cands
    assert 170 in shot_cands


def test_detect_shot_boundaries_helper(extractor):
    """Test detect_shot_boundaries helper function."""
    video_path = Path("mock_data/media/hitech_girl.mp4")
    if not video_path.exists():
        pytest.skip("hitech_girl.mp4 fixture not present in mock_data/media/")

    frames = list(extractor.iter_frames(str(video_path), max_frames=80))
    boundaries = detect_shot_boundaries(frames)
    cut_targets = [b["frame_to"] for b in boundaries]
    assert 65 in cut_targets
