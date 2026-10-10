# backend\services\system\secret_cipher.py

import base64
import ctypes
import logging
import sys

logger = logging.getLogger("minikick.services.system.secret_cipher")


class NoOpSecretCipher:
    _warned = False

    def encrypt(self, plaintext: str) -> str:
        self._warn_once()
        return plaintext

    def decrypt(self, ciphertext: str) -> str:
        self._warn_once()
        return ciphertext

    def _warn_once(self) -> None:
        if not NoOpSecretCipher._warned:
            NoOpSecretCipher._warned = True
            logger.warning(
                "[SecretCipher] DPAPI is unavailable on this platform; OAuth tokens are stored without encryption."
            )


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32), ("pbData", ctypes.c_void_p)]


class DPAPISecretCipher:
    CRYPTPROTECT_UI_FORBIDDEN = 0x1

    def __init__(self) -> None:
        self._crypt32 = ctypes.windll.crypt32
        self._kernel32 = ctypes.windll.kernel32
        self._crypt32.CryptProtectData.argtypes = [
            ctypes.POINTER(_DataBlob), ctypes.c_wchar_p, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(_DataBlob),
        ]
        self._crypt32.CryptProtectData.restype = ctypes.c_int
        self._crypt32.CryptUnprotectData.argtypes = [
            ctypes.POINTER(_DataBlob), ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(_DataBlob),
        ]
        self._crypt32.CryptUnprotectData.restype = ctypes.c_int
        self._kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        self._kernel32.LocalFree.restype = ctypes.c_void_p

    def _blob_in(self, data: bytes) -> tuple[ctypes.Array, _DataBlob]:
        buffer = ctypes.create_string_buffer(data, len(data))
        blob = _DataBlob(len(data), ctypes.cast(buffer, ctypes.c_void_p))
        return buffer, blob

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        raw = plaintext.encode("utf-8")
        _buffer, blob_in = self._blob_in(raw)
        blob_out = _DataBlob()
        ok = self._crypt32.CryptProtectData(
            ctypes.byref(blob_in), None, None, None, None,
            self.CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(blob_out),
        )
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            protected = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        finally:
            self._kernel32.LocalFree(blob_out.pbData)
        return base64.b64encode(protected).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        raw = base64.b64decode(ciphertext.encode("ascii"))
        _buffer, blob_in = self._blob_in(raw)
        blob_out = _DataBlob()
        ok = self._crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None,
            self.CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(blob_out),
        )
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            plain = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        finally:
            self._kernel32.LocalFree(blob_out.pbData)
        return plain.decode("utf-8")


def create_secret_cipher():
    if sys.platform == "win32":
        try:
            return DPAPISecretCipher()
        except Exception as e:
            logger.error("[SecretCipher] Failed to initialize DPAPI, falling back to no-op cipher: %s", e)
    return NoOpSecretCipher()
