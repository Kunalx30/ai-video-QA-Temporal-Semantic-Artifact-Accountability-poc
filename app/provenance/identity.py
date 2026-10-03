"""Unique identifier generation for videos and QA runs."""

import time
import uuid
from typing import Optional


def generate_video_id(existing_id: Optional[str] = None, sha256_hash: Optional[str] = None) -> str:
    """Generate or standardize a video identifier."""
    if existing_id and existing_id.strip():
        return existing_id.strip()
    if sha256_hash:
        return f"VID_{sha256_hash[:12].upper()}"
    return f"VID_{uuid.uuid4().hex[:12].upper()}"


def generate_qa_run_id() -> str:
    """Generate a unique QA run execution identifier with timestamp prefix."""
    ts = int(time.time())
    suffix = uuid.uuid4().hex[:8].upper()
    return f"QA_{ts}_{suffix}"
