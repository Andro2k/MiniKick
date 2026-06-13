# backend/interfaces/updater_interfaces.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Callable

class IUpdateChecker(ABC):
    @abstractmethod
    def get_latest_version_info(self) -> Optional[Dict[str, str]]:
        pass

class IUpdateDownloader(ABC):
    @abstractmethod
    def download_file(self, url: str, destination_path: str, progress_callback: Optional[Callable[[int], None]] = None) -> bool:
        pass

class IUpdateInstaller(ABC):
    @abstractmethod
    def install_and_restart(self, installer_path: str) -> None:
        pass