import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings


def _key() -> bytes:
    settings = get_settings()
    return hashlib.sha256(settings.data_encryption_key.encode("utf-8")).digest()


def encrypt(plaintext: str) -> str:
    """Chiffre AES-256-GCM et retourne base64(nonce || ciphertext || tag)."""
    nonce = os.urandom(12)
    ciphertext = AESGCM(_key()).encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt(payload: str) -> str:
    """Déchiffre une charge chiffrée par `encrypt`."""
    raw = base64.b64decode(payload)
    nonce, ciphertext = raw[:12], raw[12:]
    return AESGCM(_key()).decrypt(nonce, ciphertext, None).decode("utf-8")
