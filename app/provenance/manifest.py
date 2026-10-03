"""Provenance manifest creation and audit trail record."""

import time
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from app import __version__
from app.provenance.checksum import compute_file_sha256
from app.provenance.identity import generate_qa_run_id, generate_video_id


class ProvenanceManifest(BaseModel):
    """Immutable audit manifest for an analyzed video file."""
    video_id: str = Field(..., description="Unique video identifier")
    qa_run_id: str = Field(..., description="Unique QA run identifier")
    sha256: str = Field(..., description="Cryptographic SHA-256 digest")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of QA analysis")
    file_size_bytes: int = Field(..., description="Exact file size in bytes")
    qa_version: str = Field(default=__version__, description="Member 8 QA version")
    signature: Optional[str] = Field(default=None, description="Optional Ed25519 signature")
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


def create_manifest(
    video_path: str | Path,
    video_id: Optional[str] = None,
    qa_run_id: Optional[str] = None,
    private_key_hex: Optional[str] = None,
) -> ProvenanceManifest:
    """Generate complete provenance manifest with optional cryptographic signature."""
    p = Path(video_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {video_path}")

    sha256_hash = compute_file_sha256(p)
    vid = generate_video_id(existing_id=video_id, sha256_hash=sha256_hash)
    run_id = qa_run_id or generate_qa_run_id()
    size = p.stat().st_size

    signature = None
    if private_key_hex:
        from app.provenance.signing import sign_payload
        # Sign canonical payload string
        payload = f"{vid}:{run_id}:{sha256_hash}:{size}"
        signature = sign_payload(private_key_hex, payload)

    return ProvenanceManifest(
        video_id=vid,
        qa_run_id=run_id,
        sha256=sha256_hash,
        file_size_bytes=size,
        signature=signature,
    )
