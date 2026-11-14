# backend\services\updates\__init__.py
"""Update and release-notes services."""

from .updater_service import GithubUpdateProvider, WindowsInstaller, UpdateManager
from .whats_new_service import WhatsNewService

__all__ = [
    "GithubUpdateProvider",
    "WindowsInstaller",
    "UpdateManager",
    "WhatsNewService",
]
