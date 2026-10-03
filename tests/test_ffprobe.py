"""Tests for ffprobe technical media validator (Phase 3)."""

from pathlib import Path
import pytest
from app.schemas.input import GenerationMetadata
from app.schemas.results import CheckStatus, ReasonCode
from app.technical.ffprobe_validator import FFprobeValidator


def test_valid_video_passes():
    validator = FFprobeValidator()
    result = validator.validate("mock_data/media/good.mp4")

    assert result.status == CheckStatus.PASS
    assert result.width == 640
    assert result.height == 360
    assert result.fps == 24.0
    assert result.duration_seconds is not None and result.duration_seconds > 1.0
    assert result.video_codec is not None
    assert len(result.reason_codes) == 0


def test_corrupted_video_fails():
    validator = FFprobeValidator()
    result = validator.validate("mock_data/media/corrupted_metadata.mp4")

    assert result.status == CheckStatus.FAIL
    assert ReasonCode.TECHNICAL_INVALID_MEDIA in result.reason_codes
    assert "error" in result.evidence


def test_nonexistent_video_fails():
    validator = FFprobeValidator()
    result = validator.validate("mock_data/media/non_existent_file_xyz.mp4")

    assert result.status == CheckStatus.FAIL
    assert ReasonCode.TECHNICAL_FILE_NOT_FOUND in result.reason_codes


def test_metadata_mismatch_triggers_warning():
    validator = FFprobeValidator()
    mismatched_meta = GenerationMetadata(
        width=1920,
        height=1080,
        fps=60.0,
    )
    result = validator.validate("mock_data/media/good.mp4", expected_meta=mismatched_meta)

    assert result.status == CheckStatus.WARN
    assert ReasonCode.TECHNICAL_METADATA_MISMATCH in result.reason_codes
    assert "metadata_mismatches" in result.evidence
