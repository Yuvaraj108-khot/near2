import json
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature
from config import AUTHORITY_SEED_HEX

def canonicalize(data: dict) -> bytes:
    """Produces deterministic canonical UTF-8 bytes for cryptographic attestation."""
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8')

def get_authority_private_key() -> ed25519.Ed25519PrivateKey:
    seed_bytes = bytes.fromhex(AUTHORITY_SEED_HEX)
    return ed25519.Ed25519PrivateKey.from_private_bytes(seed_bytes)

def get_authority_public_key_hex() -> str:
    priv = get_authority_private_key()
    pub = priv.public_key()
    return pub.public_bytes_raw().hex()

def sign_manifest(manifest: dict) -> dict:
    priv = get_authority_private_key()
    pub = priv.public_key()
    data = canonicalize(manifest)
    sig = priv.sign(data)
    return {
        "manifest": manifest,
        "authority_key": pub.public_bytes_raw().hex(),
        "signature": sig.hex()
    }

def verify_manifest_signature(manifest: dict, authority_key_hex: str, signature_hex: str) -> bool:
    try:
        expected_authority = get_authority_public_key_hex()
        if authority_key_hex.lower() != expected_authority.lower():
            return False

        pub_bytes = bytes.fromhex(authority_key_hex)
        sig_bytes = bytes.fromhex(signature_hex)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        data = canonicalize(manifest)
        public_key.verify(sig_bytes, data)
        return True
    except (ValueError, InvalidSignature, TypeError):
        return False
