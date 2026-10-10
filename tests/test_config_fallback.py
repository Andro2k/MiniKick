# tests\test_config_fallback.py

import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class ConfigFallbackTest(unittest.TestCase):
    def test_backend_config_imports_without_api_keys(self) -> None:
        # Subproceso aparte: simula que api_keys.py no existe sin tocar los módulos de este proceso.
        code = (
            "import sys; sys.modules['backend.config.api_keys'] = None; "
            "import backend.config as c; "
            "assert c.KICK_CLIENT_ID == '' and c.TWITCH_CLIENT_SECRET == '' and c.SIGN_API_KEY == ''; "
            "assert c.KICK_PUSHER_CLUSTER == 'us2' and c.KICK_PUSHER_KEY; "
            "print('OK')"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
