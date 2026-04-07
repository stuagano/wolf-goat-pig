"""Unit tests for encryption_service — Fernet symmetric encryption of credentials."""

import os

import pytest

from app.services.encryption_service import decrypt, encrypt


# ── Roundtrip ────────────────────────────────────────────────────────────────

class TestRoundtrip:
    def test_encrypt_then_decrypt_returns_original(self):
        original = "my-secret-password"
        assert decrypt(encrypt(original)) == original

    def test_empty_string_roundtrip(self):
        assert decrypt(encrypt("")) == ""

    def test_unicode_roundtrip(self):
        original = "p@ssw0rd-🔐-日本語"
        assert decrypt(encrypt(original)) == original

    def test_long_string_roundtrip(self):
        original = "x" * 10_000
        assert decrypt(encrypt(original)) == original

    def test_special_characters_roundtrip(self):
        original = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        assert decrypt(encrypt(original)) == original

    def test_encrypt_produces_different_ciphertext_each_call(self):
        """Fernet uses random IV so every encryption is unique."""
        plaintext = "same-value"
        ct1 = encrypt(plaintext)
        ct2 = encrypt(plaintext)
        assert ct1 != ct2  # Different ciphertext, same plaintext

    def test_ciphertext_is_string(self):
        ct = encrypt("hello")
        assert isinstance(ct, str)

    def test_ciphertext_is_not_plaintext(self):
        plaintext = "super-secret"
        ct = encrypt(plaintext)
        assert plaintext not in ct


# ── Key derivation ────────────────────────────────────────────────────────────

class TestKeyDerivation:
    def test_uses_foretees_encryption_key_when_set(self, monkeypatch):
        monkeypatch.setenv("FORETEES_ENCRYPTION_KEY", "my-raw-key")
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        plaintext = "test-value"
        ct = encrypt(plaintext)
        assert decrypt(ct) == plaintext

    def test_falls_back_to_jwt_secret_key(self, monkeypatch):
        monkeypatch.delenv("FORETEES_ENCRYPTION_KEY", raising=False)
        monkeypatch.setenv("JWT_SECRET_KEY", "jwt-fallback-key")
        plaintext = "test-value"
        ct = encrypt(plaintext)
        assert decrypt(ct) == plaintext

    def test_uses_default_dev_key_when_nothing_set(self, monkeypatch):
        monkeypatch.delenv("FORETEES_ENCRYPTION_KEY", raising=False)
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        plaintext = "test-value"
        ct = encrypt(plaintext)
        assert decrypt(ct) == plaintext

    def test_44_char_base64_key_used_directly(self, monkeypatch):
        """A 44-char base64 string is a valid Fernet key and used as-is."""
        from cryptography.fernet import Fernet
        valid_key = Fernet.generate_key().decode()
        assert len(valid_key) == 44
        monkeypatch.setenv("FORETEES_ENCRYPTION_KEY", valid_key)
        plaintext = "secret"
        assert decrypt(encrypt(plaintext)) == plaintext

    def test_different_keys_produce_incompatible_ciphertexts(self, monkeypatch):
        """Ciphertext encrypted with key A cannot be decrypted with key B."""
        from cryptography.fernet import InvalidToken

        monkeypatch.setenv("FORETEES_ENCRYPTION_KEY", "key-alpha")
        ct = encrypt("hello")

        monkeypatch.setenv("FORETEES_ENCRYPTION_KEY", "key-beta")
        with pytest.raises(Exception):  # InvalidToken or similar
            decrypt(ct)
