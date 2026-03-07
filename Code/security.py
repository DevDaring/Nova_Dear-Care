#!/usr/bin/env python3
"""
security.py - Security module for Pocket ASHA System
PIN authentication and AES-256 data encryption.
"""

import os
import hashlib
import secrets
from pathlib import Path

# AES encryption via cryptography library
_ENCRYPTION_KEY = None
_KEY_FILE = Path(__file__).parent / "data" / ".keyfile"


def hash_pin(pin: str) -> str:
    """Hash a PIN using SHA-256 with salt."""
    salt = "pocket_asha_salt_v1"
    return hashlib.sha256(f"{salt}{pin}".encode()).hexdigest()


def set_pin(pin: str):
    """Set the ASHA worker PIN by writing hash to .env."""
    pin_hash = hash_pin(pin)
    env_path = Path(__file__).parent / ".env"
    content = env_path.read_text()
    if "ASHA_PIN_HASH=" in content:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("ASHA_PIN_HASH="):
                lines[i] = f"ASHA_PIN_HASH={pin_hash}"
                break
        env_path.write_text("\n".join(lines))
    else:
        with open(env_path, "a") as f:
            f.write(f"\nASHA_PIN_HASH={pin_hash}\n")
    print("[SECURITY] PIN set successfully")


def verify_pin(pin: str) -> bool:
    """Verify PIN against stored hash."""
    from config import ASHA_PIN_HASH
    if not ASHA_PIN_HASH:
        return True  # No PIN configured, allow access
    return hash_pin(pin) == ASHA_PIN_HASH


def authenticate() -> bool:
    """Interactive PIN authentication. Returns True if authenticated."""
    from config import ASHA_PIN_HASH
    if not ASHA_PIN_HASH:
        print("[SECURITY] No PIN configured. Access granted.")
        print("[SECURITY] Set a PIN with: python3 -c \"from security import set_pin; set_pin('1234')\"")
        return True

    for attempt in range(3):
        pin = input(f"Enter PIN ({3 - attempt} attempts remaining): ").strip()
        if verify_pin(pin):
            print("[SECURITY] Access granted.")
            return True
        print("[SECURITY] Incorrect PIN.")
    print("[SECURITY] Access denied. Too many failed attempts.")
    return False


def _get_encryption_key() -> bytes:
    """Get or generate AES-256 encryption key."""
    global _ENCRYPTION_KEY
    if _ENCRYPTION_KEY:
        return _ENCRYPTION_KEY

    _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if _KEY_FILE.exists():
        _ENCRYPTION_KEY = _KEY_FILE.read_bytes()
    else:
        _ENCRYPTION_KEY = secrets.token_bytes(32)
        _KEY_FILE.write_bytes(_ENCRYPTION_KEY)
        os.chmod(str(_KEY_FILE), 0o600)
    return _ENCRYPTION_KEY


def encrypt_file(file_path: str) -> bool:
    """Encrypt a file in-place using AES-256-GCM."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = _get_encryption_key()
        data = Path(file_path).read_bytes()
        nonce = secrets.token_bytes(12)
        aesgcm = AESGCM(key)
        encrypted = aesgcm.encrypt(nonce, data, None)
        Path(file_path).write_bytes(nonce + encrypted)
        return True
    except Exception as e:
        print(f"[SECURITY] Encryption error: {e}")
        return False


def decrypt_file(file_path: str) -> bytes:
    """Decrypt an AES-256-GCM encrypted file. Returns decrypted bytes."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = _get_encryption_key()
        raw = Path(file_path).read_bytes()
        nonce = raw[:12]
        ciphertext = raw[12:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as e:
        print(f"[SECURITY] Decryption error: {e}")
        return b""
