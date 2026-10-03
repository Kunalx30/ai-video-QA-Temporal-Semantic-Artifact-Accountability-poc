"""CLI integration tests (Phase 12)."""

import json
import subprocess
import sys
import pytest


def test_cli_doctor():
    cmd = [sys.executable, "-m", "app.cli", "--doctor"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0
    assert "MEMBER 8 QA ENVIRONMENT DIAGNOSTIC" in res.stdout
    assert "Python" in res.stdout
    assert "FFmpeg" in res.stdout


def test_cli_qa_text_output():
    cmd = [
        sys.executable, "-m", "app.cli", "qa",
        "--video", "mock_data/media/good.mp4",
        "--prompt", "A golden glowing orb traveling smoothly across an evening sky.",
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0
    assert "AI VIDEO QA" in res.stdout
    assert "Technical      : PASS" in res.stdout
    assert "FINAL DECISION : PASS" in res.stdout


def test_cli_qa_json_output():
    cmd = [
        sys.executable, "-m", "app.cli", "qa",
        "--video", "mock_data/media/good.mp4",
        "--prompt", "A golden glowing orb traveling smoothly across an evening sky.",
        "--json",
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["decision"] == "PASS"
    assert data["technical"]["status"] == "PASS"
    assert len(data["provenance"]["sha256"]) == 64


def test_cli_qa_failure_exit_code():
    cmd = [
        sys.executable, "-m", "app.cli", "qa",
        "--video", "mock_data/media/flicker.mp4",
        "--prompt", "A test video.",
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode != 0
    assert "FINAL DECISION : AUTO_RETRY" in res.stdout
