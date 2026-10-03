"""Tests for mock data and fixture generator (Phase 2)."""

import json
from pathlib import Path
import cv2
import pytest
from mock_data.generate_fixtures import generate_all_fixtures


def test_fixture_generation_and_manifest():
    manifest_path = Path("mock_data/manifest.json")
    assert manifest_path.exists(), "Manifest should exist after fixture generation"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    fixtures = manifest["fixtures"]
    assert "good" in fixtures
    assert "duplicate_frames" in fixtures
    assert "dropped_frames" in fixtures
    assert "flicker" in fixtures
    assert "freeze" in fixtures
    assert "speed_jump" in fixtures
    assert "black_frame" in fixtures
    assert "blur" in fixtures
    assert "resolution_change" in fixtures
    assert "text_overlay" in fixtures
    assert "corrupted_metadata" in fixtures

    for fix_id, meta in fixtures.items():
        media_path = Path(meta["video_path"])
        assert media_path.exists(), f"Media file {media_path} must exist"
        assert (Path("mock_data/inputs") / f"{fix_id}.json").exists()
        assert (Path("mock_data/expected") / f"{fix_id}.json").exists()
        assert (Path("mock_data/metadata") / f"{fix_id}.json").exists()


def test_good_fixture_validity():
    cap = cv2.VideoCapture("mock_data/media/good.mp4")
    assert cap.isOpened(), "good.mp4 should be openable"
    ret, frame = cap.read()
    assert ret is True
    assert frame is not None
    assert frame.shape == (360, 640, 3)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    assert frame_count == 60
    cap.release()
