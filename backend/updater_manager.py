# backend/updater_manager.py
import os
from backend.interfaces.updater_interfaces import (
    IUpdateChecker, 
    IUpdateDownloader, 
    IUpdateInstaller
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
        if info and info["version"] > self.current_version: # Lógica simple de versión
            return info
        return None

    def perform_update(self, download_url: str) -> bool:
        temp_path = os.path.join(os.getenv('TEMP'), "minikick_update.exe")
        
        if self.downloader.download_file(download_url, temp_path):
            self.installer.install_and_restart(temp_path)
            return True
        return False