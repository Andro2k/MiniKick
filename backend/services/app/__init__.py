# backend\services\app\__init__.py
"""Application-level services: identity, instance lock, clock, browser, backup and DB maintenance."""

from .identity_service import pick_primary_identity, resolve_primary_identity
from .instance_service import SocketInstanceProvider
from .browser_service import BrowserService
from .backup_service import BackupService
from .db_maintenance_service import DatabaseMaintenance, DatabaseStats

__all__ = [
    "pick_primary_identity",
    "resolve_primary_identity",
    "SocketInstanceProvider",
    "BrowserService",
    "BackupService",
    "DatabaseMaintenance",
    "DatabaseStats",
]
