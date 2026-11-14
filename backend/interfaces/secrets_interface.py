# backend\interfaces\secrets_interface.py
"""Contrato para cifrar secretos (cifrar y descifrar) y error de cifrado."""

from typing import Protocol

class SecretCipher(Protocol):
    def encrypt(self, plaintext: str) -> str: ...

    def decrypt(self, ciphertext: str) -> str: ...


class TokenEncryptionError(Exception):
    pass
