# backend\services\updates\__init__.py
"""Servicios de actualización y notas de versión."""

from .updater_service import GithubUpdateProvider, WindowsInstaller, UpdateManager
from .whats_new_service import WhatsNewService

__all__ = [
    "GithubUpdateProvider",
    "WindowsInstaller",
    "UpdateManager",
    "WhatsNewService",
]
