"""Cifrado simétrico AES-256 (Fernet) para credenciales DNIT."""
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings
import base64, hashlib

def _get_fernet() -> Fernet:
    raw = settings.MASTER_KEY.encode()
    # Deriva clave válida Fernet (32 bytes urlsafe-b64) desde MASTER_KEY
    digest = hashlib.sha256(raw).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)

def encrypt_secret(plain: str) -> str:
    return _get_fernet().encrypt(plain.encode()).decode()

def decrypt_secret(token: str) -> str:
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except InvalidToken as e:
        raise ValueError("No se pudo descifrar (MASTER_KEY incorrecta)") from e
