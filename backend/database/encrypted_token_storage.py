# backend\database\encrypted_token_storage.py

import logging
import threading
from collections import OrderedDict

from backend.interfaces import SecretCipher, TokenEncryptionError, TokenStorage

logger = logging.getLogger("minikick.database.encrypted_token_storage")

_ENCRYPTED_PREFIX = "enc:v1:"
_DECRYPT_CACHE_SIZE = 4

class EncryptedTokenStorage:
    _SENSITIVE_FIELDS = ("access_token", "refresh_token")

    def __init__(self, inner: TokenStorage, cipher: SecretCipher) -> None:
        self._inner = inner
        self._cipher = cipher
        self._decrypt_cache: OrderedDict[str, str] = OrderedDict()
        self._decrypt_cache_lock = threading.Lock()

    def _decrypt_field(self, payload: str) -> str:
        with self._decrypt_cache_lock:
            cached = self._decrypt_cache.get(payload)
            if cached is not None:
                self._decrypt_cache.move_to_end(payload)
                return cached

        plaintext = self._cipher.decrypt(payload)

        with self._decrypt_cache_lock:
            self._decrypt_cache[payload] = plaintext
            while len(self._decrypt_cache) > _DECRYPT_CACHE_SIZE:
                self._decrypt_cache.popitem(last=False)
        return plaintext

    def _drop_decrypt_cache(self) -> None:
        with self._decrypt_cache_lock:
            self._decrypt_cache.clear()

    def _encrypt_field(self, field: str, value: str) -> str:
        try:
            return _ENCRYPTED_PREFIX + self._cipher.encrypt(value)
        except Exception as e:
            logger.error("[EncryptedTokenStorage] Could not encrypt '%s'; nothing was saved: %s", field, e)
            raise TokenEncryptionError(f"Could not encrypt '{field}'") from e

    def load(self) -> dict | None:
        tokens = self._inner.load()
        if not tokens:
            return None

        decrypted = dict(tokens)
        needs_migration = False
        for field in self._SENSITIVE_FIELDS:
            raw = decrypted.get(field)
            if not raw or not isinstance(raw, str):
                continue
            if raw.startswith(_ENCRYPTED_PREFIX):
                try:
                    decrypted[field] = self._decrypt_field(raw[len(_ENCRYPTED_PREFIX):])
                except Exception as e:
                    logger.error(
                        "[EncryptedTokenStorage] Could not decrypt '%s' (different Windows user/profile?). Session discarded: %s",
                        field, e,
                    )
                    return None
            else:
                needs_migration = True

        if needs_migration:
            logger.info("[EncryptedTokenStorage] Migrating legacy plaintext tokens to encrypted storage.")
            try:
                self.save(decrypted)
            except Exception as e:
                logger.warning("[EncryptedTokenStorage] Could not migrate legacy tokens: %s", e)

        return decrypted

    def save(self, tokens: dict) -> None:
        encrypted = dict(tokens)
        for field in self._SENSITIVE_FIELDS:
            value = encrypted.get(field)
            if value:
                encrypted[field] = self._encrypt_field(field, value)
        self._inner.save(encrypted)
        self._drop_decrypt_cache()

    def clear(self) -> None:
        self._inner.clear()
        self._drop_decrypt_cache()
