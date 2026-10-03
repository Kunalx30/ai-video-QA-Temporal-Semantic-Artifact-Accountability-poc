"""Tests for artifact QA detectors (Phase 7)."""

import pytest
from app.artifacts import ArtifactDetector
from app.media.frame_extractor import FrameExtractor
from app.schemas.results import CheckStatus, ReasonCode


@pytest.fixture
def extractor():
    return FrameExtractor()


def test_good_fixture_passes_artifacts(extractor):
    frames = list(extractor.iter_frames("mock_data/media/good.mp4"))
    detector = ArtifactDetector()
    result = detector.detect(frames)

    assert result.status == CheckStatus.PASS
    assert result.black_frame_count == 0
    assert len(result.reason_codes) == 0


def test_black_frame_detected(extractor):
    frames = list(extractor.iter_frames("mock_data/media/black_frame.mp4"))
    detector = ArtifactDetector()
    result = detector.detect(frames)

    assert result.status == CheckStatus.FAIL
    assert ReasonCode.ARTIFACT_BLACK_FRAME in result.reason_codes
    assert result.black_frame_count >= 2


def test_blur_detected(extractor):
    frames = list(extractor.iter_frames("mock_data/media/blur.mp4"))
    detector = ArtifactDetector()
    result = detector.detect(frames)

    assert result.status == CheckStatus.FAIL
    assert ReasonCode.ARTIFACT_BLUR in result.reason_codes


def test_resolution_change_detected(extractor):
    frames = list(extractor.iter_frames("mock_data/media/resolution_change.mp4"))
    detector = ArtifactDetector()
    result = detector.detect(frames)

    assert result.status == CheckStatus.FAIL
    assert ReasonCode.ARTIFACT_RESOLUTION_CHANGE in result.reason_codes


def test_text_overlay_detected(extractor):
    frames = list(extractor.iter_frames("mock_data/media/text_overlay.mp4"))
    detector = ArtifactDetector()
    result = detector.detect(frames)

    assert result.status == CheckStatus.WARN
    assert ReasonCode.ARTIFACT_TEXT_OVERLAY in result.reason_codes
