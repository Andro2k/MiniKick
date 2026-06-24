# backend\services\system\updater_service.py

import os
import requests
import subprocess
from backend.interfaces.updater_interfaces import (
    IUpdateChecker, 
    IUpdateDownloader, 
    IUpdateInstaller
)

class GithubUpdateProvider(IUpdateChecker, IUpdateDownloader):
    def __init__(self, repo_owner: str, repo_name: str):
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    def get_latest_version_info(self) -> dict | None:
        try:
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
        except Exception:
            return None

    def download_file(self, url: str, destination_path: str, progress_callback=None) -> bool:
        try:
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
        except Exception:
            return False


class WindowsInstaller(IUpdateInstaller):
    def install_and_restart(self, installer_path: str) -> None:
        DETACHED_PROCESS = 0x00000008
        
        subprocess.Popen(
            [installer_path, "/SILENT"],
            creationflags=DETACHED_PROCESS,
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
            return info
        return None

    def perform_update(self, download_url: str, progress_callback=None) -> bool:
        temp_path = os.path.join(os.getenv('TEMP'), "minikick_update.exe")
        
        if self.downloader.download_file(download_url, temp_path, progress_callback):
            self.installer.install_and_restart(temp_path)
            return True
        return False