"""Tests for provenance tracking, hashing, manifests, and signatures (Phase 9)."""

import pytest
from app.provenance import (
    ProvenanceTracker,
    compute_file_sha256,
    generate_key_pair,
    sign_payload,
    verify_file_sha256,
    verify_signature,
)
from app.schemas.results import CheckStatus, ReasonCode


def test_sha256_computation():
    video_path = "mock_data/media/good.mp4"
    h1 = compute_file_sha256(video_path)
    assert len(h1) == 64
    assert all(c in "0123456789abcdef" for c in h1)

    assert verify_file_sha256(video_path, h1) is True
    assert verify_file_sha256(video_path, "0" * 64) is False


def test_provenance_tracker_success():
    tracker = ProvenanceTracker()
    res = tracker.track("mock_data/media/good.mp4", video_id="TEST_VID_01")

    assert res.status == CheckStatus.PASS
    assert res.video_id == "TEST_VID_01"
    assert res.qa_run_id.startswith("QA_")
    assert len(res.sha256) == 64
    assert len(res.reason_codes) == 0
    assert "manifest" in res.evidence


def test_provenance_tracker_hash_mismatch():
    tracker = ProvenanceTracker()
    res = tracker.track(
        "mock_data/media/good.mp4",
        expected_sha256="deadbeef" * 8,
    )

    assert res.status == CheckStatus.FAIL
    assert ReasonCode.PROVENANCE_HASH_FAILURE in res.reason_codes


def test_ed25519_signing_and_verification():
    priv_hex, pub_hex = generate_key_pair()
    payload = "VID_001:QA_123:abc456:1024"

    sig_hex = sign_payload(priv_hex, payload)
    assert len(sig_hex) == 128  # 64 bytes = 128 hex chars

    # Valid verification
    assert verify_signature(pub_hex, payload, sig_hex) is True

    # Tampered payload fails
    assert verify_signature(pub_hex, payload + "_tampered", sig_hex) is False

    # Invalid signature fails
    assert verify_signature(pub_hex, payload, "aa" * 64) is False
