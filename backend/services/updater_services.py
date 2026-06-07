# backend/services/updater_services.py

import requests
import subprocess
from backend.interfaces.updater_interfaces import (
    IUpdateChecker, IUpdateDownloader, IUpdateInstaller
)

class GithubUpdateProvider(IUpdateChecker, IUpdateDownloader):
    """
    Proveedor real que consulta la API de GitHub y descarga los binarios.
    """
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

    def download_file(self, url: str, destination_path: str) -> bool:
        try:
            response = requests.get(url, stream=True, timeout=15)
            response.raise_for_status()
            
            with open(destination_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception:
            return False

class WindowsInstaller(IUpdateInstaller):
    """
    Se encarga exclusivamente de ejecutar el archivo en el sistema operativo.
    """
    def install_and_restart(self, installer_path: str) -> None:
        DETACHED_PROCESS = 0x00000008
        
        subprocess.Popen(
            [installer_path, "/SILENT"],
            creationflags=DETACHED_PROCESS,
            close_fds=True 
        )