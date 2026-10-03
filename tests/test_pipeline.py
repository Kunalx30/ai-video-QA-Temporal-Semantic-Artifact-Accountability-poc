"""End-to-end pipeline tests (Phase 11)."""

import pytest
from app import run_video_qa
from app.pipeline import VideoQAPipeline
from app.schemas.results import DecisionType, ReasonCode


def test_pipeline_on_good_video():
    prompt = "A golden glowing orb traveling smoothly across an evening sky."
    report = run_video_qa(
        video_path="mock_data/media/good.mp4",
        prompt=prompt,
        video_id="TEST_VID_GOOD",
    )

    assert report.decision == DecisionType.PASS
    assert report.video_id == "TEST_VID_GOOD"
    assert report.technical.status.value == "PASS"
    assert report.temporal.status.value == "PASS"
    assert report.semantic.status.value == "PASS"
    assert report.artifacts.status.value == "PASS"
    assert report.provenance.status.value == "PASS"
    assert len(report.reason_codes) == 0


def test_pipeline_on_corrupted_video():
    report = run_video_qa(
        video_path="mock_data/media/corrupted_metadata.mp4",
        prompt="A test video.",
    )

    assert report.decision == DecisionType.AUTO_RETRY
    assert ReasonCode.TECHNICAL_INVALID_MEDIA in report.reason_codes


def test_pipeline_on_flicker_video():
    report = run_video_qa(
        video_path="mock_data/media/flicker.mp4",
        prompt="A golden glowing orb traveling smoothly across an evening sky.",
    )

    assert report.decision == DecisionType.AUTO_RETRY
    assert ReasonCode.TEMPORAL_FLICKER in report.reason_codes


def test_pipeline_on_black_frame_video():
    report = run_video_qa(
        video_path="mock_data/media/black_frame.mp4",
        prompt="A golden glowing orb traveling smoothly across an evening sky.",
    )

    assert report.decision == DecisionType.AUTO_RETRY
    assert ReasonCode.ARTIFACT_BLACK_FRAME in report.reason_codes


def test_pipeline_on_text_overlay_video():
    report = run_video_qa(
        video_path="mock_data/media/text_overlay.mp4",
        prompt="A golden glowing orb traveling smoothly across an evening sky.",
    )

    assert report.decision == DecisionType.HUMAN_REVIEW
    assert ReasonCode.ARTIFACT_TEXT_OVERLAY in report.reason_codes
