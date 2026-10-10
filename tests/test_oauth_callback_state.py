# tests\test_oauth_callback_state.py

import socket
import threading
import time
import unittest
import urllib.error
import urllib.request

from backend.services.auth.auth_service import OAuthCallbackServer

STATE = "expected-state-123"


class _FakeBrowser:
    def open_url(self, url: str) -> bool:
        return True


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _get_full(port: int, query: str) -> tuple[int, str]:
    url = f"http://127.0.0.1:{port}/?{query}"
    for _ in range(50):
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            try:
                return e.code, e.read().decode("utf-8", "replace")
            finally:
                e.close()
        except (urllib.error.URLError, ConnectionRefusedError):
            time.sleep(0.1)
    raise AssertionError("callback server never came up")


def _get(port: int, query: str) -> int:
    return _get_full(port, query)[0]


class OAuthCallbackStateTest(unittest.TestCase):
    def _start(self) -> tuple[int, dict, threading.Thread]:
        port = _free_port()
        result: dict = {}

        def run() -> None:
            result["code"] = OAuthCallbackServer.capture_auth_code(
                "http://auth.example", port, "", timeout_seconds=10,
                provider="kick", browser_service=_FakeBrowser(), expected_state=STATE,
            )

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return port, result, thread

    def test_forged_callbacks_do_not_cancel_the_login(self) -> None:
        port, result, thread = self._start()
        self.assertEqual(_get(port, "code=evil&state=wrong"), 400)
        self.assertEqual(_get(port, "error=access_denied"), 400)
        self.assertEqual(_get(port, "code=evil"), 400)
        self.assertTrue(thread.is_alive(), "el servidor debe seguir esperando")
        status, body = _get_full(port, f"code=good&state={STATE}")
        self.assertEqual(status, 200)
        self.assertIn("exitosa", body, "la página de éxito debe renderizarse completa")
        thread.join(5)
        self.assertEqual(result["code"], "good")

    def test_provider_error_with_valid_state_ends_the_flow(self) -> None:
        port, result, thread = self._start()
        self.assertEqual(_get(port, f"error=access_denied&state={STATE}"), 200)
        thread.join(5)
        self.assertEqual(result["code"], "")


if __name__ == "__main__":
    unittest.main()
