"""Ed25519 digital signature signing and verification for audit manifests."""

from typing import Tuple


def generate_key_pair() -> Tuple[str, str]:
    """Generate an Ed25519 private and public key pair in hex format."""
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization

    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return priv_bytes.hex(), pub_bytes.hex()


def sign_payload(private_key_hex: str, payload: str | bytes) -> str:
    """Sign payload bytes using an Ed25519 private key."""
    from cryptography.hazmat.primitives.asymmetric import ed25519

    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
    signature = private_key.sign(data)
    return signature.hex()


def verify_signature(public_key_hex: str, payload: str | bytes, signature_hex: str) -> bool:
    """Verify an Ed25519 signature against payload bytes."""
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.exceptions import InvalidSignature

    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    public_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
    try:
        public_key.verify(bytes.fromhex(signature_hex), data)
        return True
    except (InvalidSignature, ValueError):
        return False
