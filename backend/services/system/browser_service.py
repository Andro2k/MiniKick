# backend\services\system\browser_service.py

import logging
import os
import subprocess
import sys
import webbrowser
from typing import Optional
from backend.interfaces.settings_interfaces import SettingsStorage

logger = logging.getLogger("minikick.services.browser")

DEFAULT_BROWSER_KEY = "default"
SETTING_BROWSER_PATH = "app_browser_path"

class BrowserService:
    def __init__(self, settings_storage: Optional[SettingsStorage] = None):
        self.storage = settings_storage
        self._installed_cache: list[dict[str, str]] | None = None

    def get_browser_path(self) -> str:
        if self.storage:
            return self.storage.load_string(SETTING_BROWSER_PATH, DEFAULT_BROWSER_KEY)
        return DEFAULT_BROWSER_KEY

    def set_browser_path(self, path: str) -> None:
        clean_path = (path or DEFAULT_BROWSER_KEY).strip()
        if self.storage:
            self.storage.save_string(SETTING_BROWSER_PATH, clean_path)
        logger.info("[BrowserService] Configured browser set to: '%s'", clean_path)

    def get_installed_browsers(self, force_refresh: bool = False) -> list[dict[str, str]]:
        if self._installed_cache is not None and not force_refresh:
            return list(self._installed_cache)

        browsers: list[dict[str, str]] = []
        seen_paths: set[str] = set()

        if sys.platform == "win32":
            self._detect_windows_browsers(browsers, seen_paths)
        else:
            self._detect_unix_browsers(browsers, seen_paths)

        browsers.sort(key=lambda b: b.get("name", "").lower())
        self._installed_cache = browsers
        return list(browsers)

    def _detect_windows_browsers(self, browsers: list[dict[str, str]], seen_paths: set[str]) -> None:
        try:
            import winreg

            roots = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Clients\StartMenuInternet"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Clients\StartMenuInternet"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Clients\StartMenuInternet"),
            ]

            for root, base_path in roots:
                try:
                    with winreg.OpenKey(root, base_path) as key:
                        num_subkeys, _, _ = winreg.QueryInfoKey(key)
                        for i in range(num_subkeys):
                            subkey_name = winreg.EnumKey(key, i)
                            self._extract_windows_registry_browser(root, base_path, subkey_name, browsers, seen_paths)
                except OSError:
                    continue
        except ImportError:
            logger.warning("[BrowserService] winreg module unavailable on this platform.")

        known_browsers = [
            ("Google Chrome", [
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            ]),
            ("Microsoft Edge", [
                os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
                os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
            ]),
            ("Mozilla Firefox", [
                os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe"),
            ]),
            ("Brave", [
                os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
                os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            ]),
            ("Opera", [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera\launcher.exe"),
            ]),
            ("Opera GX", [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera GX\launcher.exe"),
            ]),
            ("Vivaldi", [
                os.path.expandvars(r"%LOCALAPPDATA%\Vivaldi\Application\vivaldi.exe"),
            ]),
        ]

        for b_name, paths in known_browsers:
            for p in paths:
                norm_p = os.path.normpath(p).lower()
                if norm_p not in seen_paths and os.path.exists(p):
                    seen_paths.add(norm_p)
                    browsers.append({
                        "id": os.path.splitext(os.path.basename(p))[0],
                        "name": b_name,
                        "path": os.path.normpath(p),
                    })

    @staticmethod
    def _extract_windows_registry_browser(
        root, base_path: str, subkey_name: str, browsers: list[dict[str, str]], seen_paths: set[str]
    ) -> None:
        import winreg

        try:
            with winreg.OpenKey(root, f"{base_path}\\{subkey_name}") as subkey:
                try:
                    name, _ = winreg.QueryValueEx(subkey, None)
                except OSError:
                    name = subkey_name

            with winreg.OpenKey(root, f"{base_path}\\{subkey_name}\\shell\\open\\command") as cmd_key:
                cmd, _ = winreg.QueryValueEx(cmd_key, None)
                if not cmd:
                    return

                cmd = cmd.strip()
                if cmd.startswith('"'):
                    exe_path = cmd[1:].split('"')[0]
                else:
                    exe_path = cmd.split()[0]

                if not exe_path or not os.path.exists(exe_path):
                    return

                norm_path = os.path.normpath(exe_path).lower()
                if norm_path not in seen_paths:
                    seen_paths.add(norm_path)
                    browsers.append({
                        "id": subkey_name,
                        "name": str(name).strip(),
                        "path": os.path.normpath(exe_path),
                    })
        except Exception as e:
            logger.debug("[BrowserService] Could not parse registry browser %s: %s", subkey_name, e)

    def _detect_unix_browsers(self, browsers: list[dict[str, str]], seen_paths: set[str]) -> None:
        import shutil

        candidates = [
            ("Google Chrome", "google-chrome"),
            ("Chromium", "chromium"),
            ("Mozilla Firefox", "firefox"),
            ("Brave", "brave-browser"),
            ("Microsoft Edge", "microsoft-edge"),
            ("Opera", "opera"),
        ]

        for b_name, binary_name in candidates:
            bin_path = shutil.which(binary_name)
            if bin_path and os.path.exists(bin_path):
                norm_p = os.path.normpath(bin_path).lower()
                if norm_p not in seen_paths:
                    seen_paths.add(norm_p)
                    browsers.append({
                        "id": binary_name,
                        "name": b_name,
                        "path": bin_path,
                    })

    def open_url(self, url: str) -> bool:
        if not url:
            return False

        browser_path = self.get_browser_path()
        if not browser_path or browser_path == DEFAULT_BROWSER_KEY:
            return self._open_default(url)

        if not os.path.exists(browser_path):
            logger.warning(
                "[BrowserService] Selected browser executable does not exist: '%s'. Falling back to default browser.",
                browser_path,
            )
            return self._open_default(url)

        try:
            logger.info("[BrowserService] Launching URL with browser '%s': %s", browser_path, url)
            subprocess.Popen([browser_path, url])
            return True
        except Exception as e:
            logger.error(
                "[BrowserService] Error executing browser '%s': %s. Falling back to default browser.",
                browser_path,
                e,
            )
            return self._open_default(url)

    @staticmethod
    def _open_default(url: str) -> bool:
        try:
            logger.info("[BrowserService] Opening URL with system default browser: %s", url)
            return webbrowser.open(url)
        except Exception as e:
            logger.error("[BrowserService] Failed to open default browser: %s", e)
            return False
