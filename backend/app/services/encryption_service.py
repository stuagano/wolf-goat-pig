"""Encryption service for securing sensitive data at rest.

Uses Fernet symmetric encryption (AES-128-CBC with HMAC-SHA256).
Key is derived from FORETEES_ENCRYPTION_KEY or falls back to JWT_SECRET_KEY.
"""

import base64
import hashlib
import os

from cryptography.fernet import Fernet


def _get_key() -> bytes:
    """Derive a valid Fernet key from environment configuration."""
    raw = os.getenv("FORETEES_ENCRYPTION_KEY", "")
    if raw:
        # If it's already a valid 44-char base64 Fernet key, use directly
        if len(raw) == 44:
            return raw.encode()
        # Otherwise derive a key from the raw string
        return base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())

    # Fallback: derive from JWT_SECRET_KEY
    fallback = os.getenv("JWT_SECRET_KEY", "default-dev-key")
    return base64.urlsafe_b64encode(hashlib.sha256(fallback.encode()).digest())


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string, returning a Fernet token string."""
    f = Fernet(_get_key())
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a Fernet token string back to plaintext."""
    f = Fernet(_get_key())
    return f.decrypt(ciphertext.encode()).decode()
