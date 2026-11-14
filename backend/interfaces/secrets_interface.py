# backend\interfaces\secrets_interface.py
"""Secret cipher contract (encrypt/decrypt) and its encryption error."""

from typing import Protocol

class SecretCipher(Protocol):
    def encrypt(self, plaintext: str) -> str: ...

    def decrypt(self, ciphertext: str) -> str: ...


class TokenEncryptionError(Exception):
    """No se pudo cifrar un secreto; el valor NO debe persistirse en texto plano."""
