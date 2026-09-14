# backend\interfaces\i_browser.py

from typing import Protocol

class IBrowserService(Protocol):
    def get_installed_browsers(self, force_refresh: bool = False) -> list[dict[str, str]]:
        ...

    def get_browser_path(self) -> str:
        ...

    def set_browser_path(self, path: str) -> None:
        ...

    def open_url(self, url: str) -> bool:
        ...
