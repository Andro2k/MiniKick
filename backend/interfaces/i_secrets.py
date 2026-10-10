# backend\interfaces\i_secrets.py

from typing import Protocol

class SecretCipher(Protocol):
    def encrypt(self, plaintext: str) -> str: ...

    def decrypt(self, ciphertext: str) -> str: ...
