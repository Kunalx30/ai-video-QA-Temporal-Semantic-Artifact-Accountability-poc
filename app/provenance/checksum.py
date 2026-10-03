"""Cryptographic checksum utilities for video files."""

import hashlib
from pathlib import Path


def compute_file_sha256(file_path: str | Path, chunk_size: int = 65536) -> str:
    """Compute the SHA-256 hex digest of a file in chunks."""
    p = Path(file_path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"File not found for checksum computation: {file_path}")

    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_file_sha256(file_path: str | Path, expected_hash: str) -> bool:
    """Verify that file matches the expected SHA-256 digest."""
    actual_hash = compute_file_sha256(file_path)
    return actual_hash.lower() == expected_hash.strip().lower()
