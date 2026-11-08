# resources\tests\test_config_fallback.py

import subprocess
import sys
import unittest
from pathlib import Path


def _find_repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "backend").is_dir():
            return candidate
    raise RuntimeError("No se encontró la raíz del repositorio (carpeta con backend/)")

REPO_ROOT = _find_repo_root()
class ConfigFallbackTest(unittest.TestCase):
    def test_backend_config_imports_without_api_keys(self) -> None:
        code = (
            "import sys; sys.modules['backend.config.api_keys'] = None; "
            "import backend.config as c; "
            "assert c.KICK_CLIENT_ID == '' and c.TWITCH_CLIENT_SECRET == '' and c.SIGN_API_KEY == ''; "
            "assert c.KICK_PUSHER.cluster == 'us2' and len(c.KICK_PUSHER.keys) >= 1; "
            "print('OK')"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OK", result.stdout)

    def test_pusher_uses_the_centralized_local_settings(self) -> None:
        code = (
            "import sys, types; "
            "keys = types.ModuleType('backend.config.api_keys'); "
            "keys.KICK_PUSHER_CLUSTER = 'eu1'; "
            "keys.KICK_PUSHER_KEY = 'configured-key'; "
            "sys.modules['backend.config.api_keys'] = keys; "
            "import backend.config as c; "
            "assert c.KICK_PUSHER.cluster == 'eu1'; "
            "assert c.KICK_PUSHER.keys == ('configured-key',)"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60
        )
        self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == "__main__":
    unittest.main()
