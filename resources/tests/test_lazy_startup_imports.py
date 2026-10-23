import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_dialog_and_core_packages_defer_heavy_module_imports():
    script = """
import sys
import backend.core
import frontend.dialogs

assert "backend.core.app_container_core" not in sys.modules
assert "frontend.dialogs.rewards_dialog" not in sys.modules
assert "frontend.dialogs.splash_screen" not in sys.modules

from backend.core import AppContainerCore
from frontend.dialogs import SplashScreen

assert AppContainerCore.__name__ == "AppContainerCore"
assert SplashScreen.__name__ == "SplashScreen"
"""
    subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
