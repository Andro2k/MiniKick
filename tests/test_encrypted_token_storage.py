# tests\test_encrypted_token_storage.py

import unittest

from backend.database.encrypted_token_storage import EncryptedTokenStorage
from backend.interfaces import TokenEncryptionError

class FakeCipher:
    def encrypt(self, plaintext: str) -> str:
        return plaintext[::-1]

    def decrypt(self, ciphertext: str) -> str:
        return ciphertext[::-1]


class FailingCipher:
    def encrypt(self, plaintext: str) -> str:
        raise OSError("dpapi down")

    def decrypt(self, ciphertext: str) -> str:
        raise OSError("different user")


class InMemoryTokenStorage:
    def __init__(self, data: dict | None = None) -> None:
        self.data = data
        self.save_calls = 0

    def load(self) -> dict | None:
        return dict(self.data) if self.data else None

    def save(self, tokens: dict) -> None:
        self.save_calls += 1
        self.data = dict(tokens)

    def clear(self) -> None:
        self.data = None


class EncryptedTokenStorageTest(unittest.TestCase):
    def test_save_encrypts_only_sensitive_fields(self) -> None:
        inner = InMemoryTokenStorage()
        EncryptedTokenStorage(inner, FakeCipher()).save(
            {"access_token": "abc", "refresh_token": "xyz", "expires_at": 123}
        )
        self.assertEqual(inner.data["access_token"], "enc:v1:cba")
        self.assertEqual(inner.data["refresh_token"], "enc:v1:zyx")
        self.assertEqual(inner.data["expires_at"], 123)

    def test_round_trip(self) -> None:
        storage = EncryptedTokenStorage(InMemoryTokenStorage(), FakeCipher())
        storage.save({"access_token": "abc", "refresh_token": "xyz"})
        self.assertEqual(storage.load(), {"access_token": "abc", "refresh_token": "xyz"})

    def test_legacy_plaintext_is_migrated_on_load(self) -> None:
        inner = InMemoryTokenStorage({"access_token": "abc", "refresh_token": "xyz"})
        loaded = EncryptedTokenStorage(inner, FakeCipher()).load()
        self.assertEqual(loaded["access_token"], "abc")
        self.assertTrue(inner.data["access_token"].startswith("enc:v1:"))
        self.assertTrue(inner.data["refresh_token"].startswith("enc:v1:"))

    def test_encrypt_failure_raises_and_saves_nothing(self) -> None:
        inner = InMemoryTokenStorage()
        storage = EncryptedTokenStorage(inner, FailingCipher())
        with self.assertRaises(TokenEncryptionError):
            storage.save({"access_token": "abc", "refresh_token": "xyz"})
        self.assertEqual(inner.save_calls, 0)
        self.assertIsNone(inner.data)

    def test_decrypt_failure_discards_session(self) -> None:
        inner = InMemoryTokenStorage({"access_token": "enc:v1:cba", "refresh_token": "enc:v1:zyx"})
        self.assertIsNone(EncryptedTokenStorage(inner, FailingCipher()).load())

    def test_empty_storage_returns_none(self) -> None:
        self.assertIsNone(EncryptedTokenStorage(InMemoryTokenStorage(), FakeCipher()).load())


if __name__ == "__main__":
    unittest.main()