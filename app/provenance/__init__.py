"""Provenance and accountability package."""

from pathlib import Path
from typing import Any, Dict, Optional

from app.config import ProvenanceConfig
from app.provenance.checksum import compute_file_sha256, verify_file_sha256
from app.provenance.identity import generate_qa_run_id, generate_video_id
from app.provenance.manifest import ProvenanceManifest, create_manifest
from app.provenance.signing import generate_key_pair, sign_payload, verify_signature
from app.schemas.results import CheckStatus, ProvenanceResult, ReasonCode


class ProvenanceTracker:
    """Tracks identity, cryptographic hashes, and provenance manifests for QA accountability."""

    def __init__(self, config: Optional[ProvenanceConfig] = None):
        self.config = config or ProvenanceConfig()

    def track(
        self,
        video_path: str | Path,
        video_id: Optional[str] = None,
        expected_sha256: Optional[str] = None,
        qa_run_id: Optional[str] = None,
    ) -> ProvenanceResult:
        p = Path(video_path)
        if not p.exists() or not p.is_file():
            return ProvenanceResult(
                status=CheckStatus.FAIL,
                sha256="",
                video_id=video_id or "UNKNOWN",
                qa_run_id=qa_run_id or generate_qa_run_id(),
                evidence={"error": f"Video file not found: {video_path}"},
                reason_codes=[ReasonCode.PROVENANCE_METADATA_FAILURE],
            )

        sha256_hash = compute_file_sha256(p)
        vid = generate_video_id(existing_id=video_id, sha256_hash=sha256_hash)
        run_id = qa_run_id or generate_qa_run_id()

        reason_codes = []
        is_fail = False

        if expected_sha256:
            if not verify_file_sha256(p, expected_sha256):
                is_fail = True
                reason_codes.append(ReasonCode.PROVENANCE_HASH_FAILURE)

        manifest = create_manifest(
            video_path=p,
            video_id=vid,
            qa_run_id=run_id,
        )

        status = CheckStatus.FAIL if is_fail else CheckStatus.PASS
        evidence: Dict[str, Any] = {
            "video_id": vid,
            "qa_run_id": run_id,
            "sha256": sha256_hash,
            "file_size_bytes": manifest.file_size_bytes,
            "hash_algorithm": "SHA-256",
            "manifest": manifest.model_dump(),
        }
        if expected_sha256 and is_fail:
            evidence["expected_sha256"] = expected_sha256
            evidence["actual_sha256"] = sha256_hash

        return ProvenanceResult(
            status=status,
            sha256=sha256_hash,
            video_id=vid,
            qa_run_id=run_id,
            signature=manifest.signature,
            evidence=evidence,
            reason_codes=reason_codes,
        )


__all__ = [
    "compute_file_sha256",
    "verify_file_sha256",
    "generate_video_id",
    "generate_qa_run_id",
    "generate_key_pair",
    "sign_payload",
    "verify_signature",
    "ProvenanceManifest",
    "create_manifest",
    "ProvenanceTracker",
]
