"""Tests for environment diagnostic and configuration (Phase 1)."""

import shutil
import sys
import pytest
from app.cli import check_doctor
from app.config import QAConfig


def test_doctor_passes():
    ret = check_doctor()
    assert ret == 0, "Doctor check should return 0 in configured environment"


def test_tools_available():
    assert sys.version_info >= (3, 10)
    assert shutil.which("ffmpeg") is not None
    assert shutil.which("ffprobe") is not None
    import cv2
    assert cv2.__version__ is not None
    import torch
    assert torch.__version__ is not None


def test_qa_config_defaults_and_yaml(tmp_path):
    config = QAConfig()
    assert config.technical.enabled is True
    assert config.temporal.duplicate_threshold_psnr == 45.0
    assert config.decision.uncertain_policy == "HUMAN_REVIEW"

    # Test YAML round-trip
    yaml_file = tmp_path / "test_config.yaml"
    config.save_to_yaml(yaml_file)
    assert yaml_file.exists()

    loaded = QAConfig.load_from_yaml(yaml_file)
    assert loaded.temporal.flicker_threshold == config.temporal.flicker_threshold
    assert loaded.semantic.pass_threshold == config.semantic.pass_threshold
