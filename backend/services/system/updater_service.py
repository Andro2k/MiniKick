# backend\services\system\updater_service.py

import os
import tempfile
import logging
import subprocess
from backend.interfaces import IUpdateChecker, IUpdateDownloader, IUpdateInstaller

logger = logging.getLogger("minikick.services.updater")

class GithubUpdateProvider:
    def __init__(self, repo_owner: str, repo_name: str):
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    def get_latest_version_info(self) -> dict | None:
        try:
            import requests
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            version = data.get("tag_name", "")
            assets = data.get("assets", [])
            
            if not version or not assets:
                return None

            download_url = assets[0].get("browser_download_url")
            
            return {
                "version": version,
                "download_url": download_url
            }
        except Exception as e:
            logger.debug("[GithubUpdateProvider] Error checking latest release: %s", e)
            return None

    def fetch_latest_release(self) -> dict | None:
        try:
            import requests
            headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "MiniKick-App"}
            response = requests.get(self.api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            author_login = ""
            if isinstance(data.get("author"), dict):
                author_login = data.get("author", {}).get("login", "")

            return {
                "tag_name": data.get("tag_name", ""),
                "name": data.get("name", "") or data.get("tag_name", ""),
                "published_at": data.get("published_at", ""),
                "body": data.get("body", ""),
                "html_url": data.get("html_url", ""),
                "author": author_login,
                "assets": data.get("assets", [])
            }
        except Exception as e:
            logger.error("[GithubUpdateProvider] Error fetching release notes: %s", e)
            return None

    def download_file(self, url: str, destination_path: str, progress_callback=None) -> bool:
        try:
            import requests
            response = requests.get(url, stream=True, timeout=15)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(destination_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(int((downloaded / total_size) * 100))
            return True
        except Exception as e:
            logger.error("[GithubUpdateProvider] Error downloading update binary: %s", e)
            return False

class WindowsInstaller:
    def install_and_restart(self, installer_path: str) -> None:
        CREATE_NO_WINDOW = 0x08000000        
        cmd = f'ping 127.0.0.1 -n 2 > nul && start "" "{installer_path}" /SILENT'
        logger.info("[WindowsInstaller] Launching installer: %s", installer_path)
        subprocess.Popen(
            cmd,
            shell=True,
            creationflags=CREATE_NO_WINDOW,
            close_fds=True 
        )

class UpdateManager:
    def __init__(
        self, 
        current_version: str,
        checker: IUpdateChecker, 
        downloader: IUpdateDownloader, 
        installer: IUpdateInstaller
    ):
        self.current_version = current_version
        self.checker = checker
        self.downloader = downloader
        self.installer = installer

    def check_for_updates(self) -> dict | None:
        info = self.checker.get_latest_version_info()
        if info and info["version"] > self.current_version:
            logger.info("[UpdateManager] Found newer version: %s (current: %s)", info["version"], self.current_version)
            return info
        return None

    def perform_update(self, download_url: str, progress_callback=None) -> bool:
        temp_dir = os.getenv('TEMP') or tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, "minikick_update.exe")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.debug("[UpdateManager] Could not remove old installer: %s", e)
        logger.info("[UpdateManager] Downloading update to temp: %s", temp_path)
        return self.downloader.download_file(download_url, temp_path, progress_callback)

    def install_update(self) -> None:
        temp_dir = os.getenv('TEMP') or tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, "minikick_update.exe")
        if os.path.exists(temp_path):
            logger.info("[UpdateManager] Executing installer: %s", temp_path)
            self.installer.install_and_restart(temp_path)
        else:
            logger.error("[UpdateManager] Installer binary not found at %s", temp_path)
