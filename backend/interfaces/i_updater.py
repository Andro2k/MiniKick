# backend\interfaces\updater_interfaces.py

from typing import Protocol, Optional, Dict, Callable

class IUpdateChecker(Protocol):
    def get_latest_version_info(self) -> Optional[Dict[str, str]]: ...

class IUpdateDownloader(Protocol):
    def download_file(self, url: str, destination_path: str, progress_callback: Optional[Callable[[int], None]] = None) -> bool: ...

class IUpdateInstaller(Protocol):
    def install_and_restart(self, installer_path: str) -> None: ...