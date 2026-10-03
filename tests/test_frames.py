"""Tests for frame extraction (Phase 4)."""

import pytest
from app.media.frame_extractor import FrameExtractor


def test_sequential_streaming():
    extractor = FrameExtractor()
    frames = list(extractor.iter_frames("mock_data/media/good.mp4"))

    assert len(frames) == 60
    assert frames[0].frame_index == 0
    assert frames[0].timestamp == 0.0
    assert frames[-1].frame_index == 59
    assert frames[0].image.shape == (360, 640, 3)

    # Test monotonic timestamps
    for i in range(1, len(frames)):
        assert frames[i].frame_index > frames[i - 1].frame_index
        assert frames[i].timestamp > frames[i - 1].timestamp


def test_step_and_max_frames():
    extractor = FrameExtractor()

    step_frames = list(extractor.iter_frames("mock_data/media/good.mp4", step=2))
    assert len(step_frames) == 30
    assert step_frames[1].frame_index == 2

    capped_frames = list(extractor.iter_frames("mock_data/media/good.mp4", max_frames=5))
    assert len(capped_frames) == 5


def test_fractional_sampling():
    extractor = FrameExtractor()
    sampled = extractor.sample_frames("mock_data/media/good.mp4", [0.0, 0.5, 1.0])

    assert len(sampled) == 3
    assert sampled[0].frame_index == 0
    assert sampled[1].frame_index in [29, 30]
    assert sampled[2].frame_index == 59


def test_invalid_video_raises():
    extractor = FrameExtractor()
    with pytest.raises(ValueError):
        list(extractor.iter_frames("non_existent_video_path.mp4"))
