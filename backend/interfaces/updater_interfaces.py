# backend/interfaces/updater_interfaces.py

from abc import ABC, abstractmethod
from typing import Optional, Dict

class IUpdateChecker(ABC):
    @abstractmethod
    def get_latest_version_info(self) -> Optional[Dict[str, str]]:
        """Debe retornar un diccionario con 'version' y 'download_url' o None."""
        pass

class IUpdateDownloader(ABC):
    @abstractmethod
    def download_file(self, url: str, destination_path: str) -> bool:
        """Descarga el archivo y retorna True si fue exitoso."""
        pass

class IUpdateInstaller(ABC):
    @abstractmethod
    def install_and_restart(self, installer_path: str) -> None:
        """Ejecuta el instalador y cierra la aplicación actual."""
        pass