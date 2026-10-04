"""Tests for Prompt <-> Video Aspect Ratio Validation (Issue #3)."""

from pathlib import Path
import pytest

from app.pipeline import VideoQAPipeline, run_video_qa
from app.schemas.results import CheckStatus, DecisionType, ReasonCode
from app.technical.aspect_ratio import (
    calculate_aspect_ratio,
    parse_prompt_aspect_ratio,
    validate_aspect_ratio,
)
from app.technical.ffprobe_validator import FFprobeValidator


# =========================================================================
# Unit Tests: Prompt Aspect Ratio Parsing
# =========================================================================

def test_parse_prompt_standard_numeric_ratios():
    """Test standard ratio notation across 16:9, 9:16, 1:1."""
    assert parse_prompt_aspect_ratio("A cinematic sunset in 16:9")["requested_aspect_ratio"] == "16:9"
    assert parse_prompt_aspect_ratio("A tall portrait in 9:16")["requested_aspect_ratio"] == "9:16"
    assert parse_prompt_aspect_ratio("A centered icon in 1:1")["requested_aspect_ratio"] == "1:1"


def test_parse_prompt_aspect_ratio_directive():
    """Requirement 8: 'aspect ratio 16:9' -> correctly parsed."""
    assert parse_prompt_aspect_ratio("Generate a video, aspect ratio 16:9")["requested_aspect_ratio"] == "16:9"
    assert parse_prompt_aspect_ratio("aspect ratio: 16:9, cinematic")["requested_aspect_ratio"] == "16:9"
    assert parse_prompt_aspect_ratio("aspect-ratio 9:16")["requested_aspect_ratio"] == "9:16"


def test_parse_prompt_by_notation():
    """Requirement 9: '16 by 9' -> correctly parsed."""
    assert parse_prompt_aspect_ratio("video in 16 by 9 format")["requested_aspect_ratio"] == "16:9"
    assert parse_prompt_aspect_ratio("render 9 by 16 vertical video")["requested_aspect_ratio"] == "9:16"
    assert parse_prompt_aspect_ratio("generate 1 by 1 square")["requested_aspect_ratio"] == "1:1"


def test_parse_prompt_vertical_notation():
    """Requirement 10: 'vertical 9:16' -> correctly parsed."""
    assert parse_prompt_aspect_ratio("create a vertical 9:16 story")["requested_aspect_ratio"] == "9:16"
    assert parse_prompt_aspect_ratio("portrait 9:16 format")["requested_aspect_ratio"] == "9:16"
    assert parse_prompt_aspect_ratio("square 1:1 profile")["requested_aspect_ratio"] == "1:1"


def test_parse_prompt_case_and_spacing_variations():
    """Requirement 11: Case and spacing variations -> correctly handled."""
    assert parse_prompt_aspect_ratio("ASPECT RATIO 16 : 9")["requested_aspect_ratio"] == "16:9"
    assert parse_prompt_aspect_ratio("ar:  9:16")["requested_aspect_ratio"] == "9:16"
    assert parse_prompt_aspect_ratio("--ar 16:9")["requested_aspect_ratio"] == "16:9"
    assert parse_prompt_aspect_ratio("16  by  9")["requested_aspect_ratio"] == "16:9"
    assert parse_prompt_aspect_ratio("aspect ratio: vertical")["requested_aspect_ratio"] == "9:16"
    assert parse_prompt_aspect_ratio("aspect ratio: square")["requested_aspect_ratio"] == "1:1"
    assert parse_prompt_aspect_ratio("aspect ratio: landscape")["requested_aspect_ratio"] == "16:9"


def test_parse_prompt_no_aspect_ratio():
    """Requirement 7: No aspect ratio in prompt -> returns None without false positives."""
    assert parse_prompt_aspect_ratio("A golden glowing orb traveling smoothly across an evening sky.")["requested_aspect_ratio"] is None
    assert parse_prompt_aspect_ratio("A girl standing in Times Square holding balloons")["requested_aspect_ratio"] is None
    assert parse_prompt_aspect_ratio("A beautiful portrait of an astronaut on Mars")["requested_aspect_ratio"] is None
    assert parse_prompt_aspect_ratio("")["requested_aspect_ratio"] is None
    assert parse_prompt_aspect_ratio(None)["requested_aspect_ratio"] is None


def test_parse_prompt_invalid_unknown_text_does_not_crash():
    """Requirement 12: Invalid/unknown aspect-ratio text -> should not crash."""
    assert parse_prompt_aspect_ratio("aspect ratio: invalid_ratio_format")["requested_aspect_ratio"] is None
    assert parse_prompt_aspect_ratio("aspect ratio 999:0")["requested_aspect_ratio"] is None
    assert parse_prompt_aspect_ratio("ar: foo_bar_123")["requested_aspect_ratio"] is None
    assert parse_prompt_aspect_ratio("###@@@!!!")["requested_aspect_ratio"] is None


# =========================================================================
# Unit Tests: Dimension & Ratio Matching
# =========================================================================

def test_calculate_aspect_ratio():
    """Test ratio calculation for standard resolutions."""
    dec_16_9, name_16_9 = calculate_aspect_ratio(1920, 1080)
    assert abs(dec_16_9 - (16 / 9)) < 1e-4
    assert name_16_9 == "16:9"

    dec_9_16, name_9_16 = calculate_aspect_ratio(720, 1280)
    assert abs(dec_9_16 - (9 / 16)) < 1e-4
    assert name_9_16 == "9:16"

    dec_1_1, name_1_1 = calculate_aspect_ratio(512, 512)
    assert abs(dec_1_1 - 1.0) < 1e-4
    assert name_1_1 == "1:1"


def test_validate_aspect_ratio_16_9_pass():
    """Requirement 1: 16:9 prompt + 16:9 video -> PASS."""
    evidence, matched = validate_aspect_ratio(1920, 1080, "Cinematic scene in 16:9")
    assert matched is True
    assert evidence["requested_aspect_ratio"] == "16:9"
    assert evidence["actual_aspect_ratio"] == "16:9"
    assert evidence["matched"] is True


def test_validate_aspect_ratio_16_9_fail_on_9_16():
    """Requirement 2: 16:9 prompt + 9:16 video -> FAIL."""
    evidence, matched = validate_aspect_ratio(720, 1280, "Cinematic scene in 16:9")
    assert matched is False
    assert evidence["requested_aspect_ratio"] == "16:9"
    assert evidence["actual_aspect_ratio"] == "9:16"
    assert evidence["matched"] is False


def test_validate_aspect_ratio_9_16_pass():
    """Requirement 3: 9:16 prompt + 9:16 video -> PASS."""
    evidence, matched = validate_aspect_ratio(720, 1280, "Vertical reel in 9:16")
    assert matched is True
    assert evidence["requested_aspect_ratio"] == "9:16"
    assert evidence["actual_aspect_ratio"] == "9:16"
    assert evidence["matched"] is True


def test_validate_aspect_ratio_9_16_fail_on_16_9():
    """Requirement 4: 9:16 prompt + 16:9 video -> FAIL."""
    evidence, matched = validate_aspect_ratio(1920, 1080, "Vertical reel in 9:16")
    assert matched is False
    assert evidence["requested_aspect_ratio"] == "9:16"
    assert evidence["actual_aspect_ratio"] == "16:9"
    assert evidence["matched"] is False


def test_validate_aspect_ratio_1_1_pass():
    """Requirement 5: 1:1 prompt + 1:1 video -> PASS."""
    evidence, matched = validate_aspect_ratio(512, 512, "Square avatar in 1:1")
    assert matched is True
    assert evidence["requested_aspect_ratio"] == "1:1"
    assert evidence["actual_aspect_ratio"] == "1:1"
    assert evidence["matched"] is True


def test_validate_aspect_ratio_1_1_fail_on_16_9():
    """Requirement 6: 1:1 prompt + 16:9 video -> FAIL."""
    evidence, matched = validate_aspect_ratio(1920, 1080, "Square avatar in 1:1")
    assert matched is False
    assert evidence["requested_aspect_ratio"] == "1:1"
    assert evidence["actual_aspect_ratio"] == "16:9"
    assert evidence["matched"] is False


def test_validate_aspect_ratio_no_prompt_directive():
    """Requirement 7: Prompt with no aspect ratio directive -> PASS and matched=True."""
    evidence, matched = validate_aspect_ratio(720, 1280, "A girl walking a dog in Hyderabad")
    assert matched is True
    assert evidence["requested_aspect_ratio"] is None
    assert evidence["actual_aspect_ratio"] == "9:16"
    assert evidence["matched"] is True


# =========================================================================
# Integration Tests: FFprobeValidator & Real Video (Requirement 8)
# =========================================================================

def test_ffprobe_validator_aspect_ratio_on_good_fixture():
    """Test good.mp4 (640x360 = 16:9) with matching and mismatching prompts."""
    validator = FFprobeValidator()
    video_path = Path("mock_data/media/good.mp4")
    if not video_path.exists():
        pytest.skip("good.mp4 fixture missing")

    # 1. 16:9 prompt on 16:9 video -> PASS
    res_pass = validator.validate(video_path, prompt="A landscape video in 16:9")
    assert res_pass.status == CheckStatus.PASS
    assert ReasonCode.PROMPT_ASPECT_RATIO_MISMATCH not in res_pass.reason_codes
    assert res_pass.aspect_ratio == "16:9"
    assert res_pass.evidence["aspect_ratio_evidence"]["matched"] is True

    # 2. 9:16 prompt on 16:9 video -> FAIL with PROMPT_ASPECT_RATIO_MISMATCH
    res_fail = validator.validate(video_path, prompt="A vertical video in 9:16")
    assert res_fail.status == CheckStatus.FAIL
    assert ReasonCode.PROMPT_ASPECT_RATIO_MISMATCH in res_fail.reason_codes
    assert res_fail.evidence["aspect_ratio_evidence"]["matched"] is False


def test_real_720x1280_video_aspect_ratio_validation():
    """Requirement 8: Real 720x1280 video (hitech_girl.mp4) testing.

    1. Prompt containing '16:9' -> status FAIL, reason code PROMPT_ASPECT_RATIO_MISMATCH
    2. Prompt containing '9:16' -> PASS
    3. Prompt with no aspect-ratio instruction -> No aspect-ratio mismatch
    """
    video_path = Path("mock_data/media/hitech_girl.mp4")
    if not video_path.exists():
        pytest.skip("hitech_girl.mp4 not found")

    validator = FFprobeValidator()

    # 1. Test 16:9 prompt -> FAIL, PROMPT_ASPECT_RATIO_MISMATCH
    res_mismatch = validator.validate(video_path, prompt="Generate a cinematic video in 16:9")
    assert res_mismatch.status == CheckStatus.FAIL
    assert ReasonCode.PROMPT_ASPECT_RATIO_MISMATCH in res_mismatch.reason_codes
    ev = res_mismatch.evidence["aspect_ratio_evidence"]
    assert ev["requested_aspect_ratio"] == "16:9"
    assert ev["actual_aspect_ratio"] == "9:16"
    assert ev["width"] == 720
    assert ev["height"] == 1280
    assert ev["matched"] is False

    # 2. Test 9:16 prompt -> PASS
    res_match = validator.validate(video_path, prompt="Generate a portrait video in 9:16")
    assert res_match.status == CheckStatus.PASS
    assert ReasonCode.PROMPT_ASPECT_RATIO_MISMATCH not in res_match.reason_codes
    assert res_match.aspect_ratio == "9:16"
    assert res_match.evidence["aspect_ratio_evidence"]["matched"] is True

    # 3. Test prompt with no aspect-ratio instruction -> No aspect-ratio mismatch
    res_neutral = validator.validate(video_path, prompt="A girl walking with her dog in Hyderabad")
    assert res_neutral.status == CheckStatus.PASS
    assert ReasonCode.PROMPT_ASPECT_RATIO_MISMATCH not in res_neutral.reason_codes
    assert res_neutral.evidence["aspect_ratio_evidence"]["requested_aspect_ratio"] is None
    assert res_neutral.evidence["aspect_ratio_evidence"]["matched"] is True


def test_pipeline_decision_on_aspect_ratio_mismatch():
    """Requirement 10: Decision engine integration on aspect ratio mismatch."""
    video_path = Path("mock_data/media/hitech_girl.mp4")
    if not video_path.exists():
        pytest.skip("hitech_girl.mp4 not found")

    # Mismatched prompt should fail technical QA and trigger decision policy
    report = run_video_qa(
        video_path=video_path,
        prompt="A futuristic scene in 16:9 widescreen",
    )
    assert report.technical.status == CheckStatus.FAIL
    assert ReasonCode.PROMPT_ASPECT_RATIO_MISMATCH in report.reason_codes
    assert ReasonCode.PROMPT_ASPECT_RATIO_MISMATCH in report.technical.reason_codes
    # Decision engine applies existing policy for technical failure
    assert report.decision != DecisionType.PASS
