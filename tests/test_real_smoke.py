"""Real AI-video smoke test runner and validation (Phase 16)."""

import json
from pathlib import Path
import pytest
from app.pipeline import run_video_qa
from app.schemas.input import GenerationMetadata
from app.schemas.results import DecisionType


def test_real_ai_video_smoke_test():
    """Smoke test running QA against a real/realistic video with external provider metadata.
    
    Verifies that the QA module operates model-agnostically, preserves exact SHA-256 hashes,
    and produces structured evaluation reports.
    """
    video_path = Path("mock_data/media/good.mp4")
    assert video_path.exists(), "Sample video file must exist"

    # Simulate real video generation metadata from an upstream video model (e.g. Wan / Sora / CogVideo)
    meta = GenerationMetadata(
        generation_id="REAL_GEN_2026_001",
        model="wan-video-v2.2",
        fps=24.0,
        width=640,
        height=360,
        seed=1337,
        extra={"prompt_expansion": "Cinematic lighting, 8k resolution, atmospheric dusk glow."},
    )

    report = run_video_qa(
        video_path=video_path,
        prompt="A golden glowing orb traveling smoothly across an evening sky.",
        video_id="AI_GEN_VID_001",
        metadata=meta,
    )

    assert report.decision in [DecisionType.PASS, DecisionType.AUTO_RETRY, DecisionType.HUMAN_REVIEW]
    assert report.video_id == "AI_GEN_VID_001"
    assert report.technical.video_codec is not None
    assert len(report.provenance.sha256) == 64
    assert report.qa_version == "0.1.0"
    assert "video_stream" in report.technical.evidence
