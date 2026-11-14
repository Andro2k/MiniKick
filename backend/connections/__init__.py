# backend\connections\__init__.py
"""Conexiones de plataformas y coordinación de trabajadores."""

from .kick_connection import KickConnection
from .connection_hub import ConnectionHub, IntegrationStatus
from .live_chat_connection import LiveChatConnection, TikTokConnection, YouTubeConnection
from .twitch_connection import TwitchConnection
from .worker_shutdown import WorkerShutdownCoordinator, is_worker_running
from .worker_slot import WorkerSlot

__all__ = [
    "KickConnection",
    "ConnectionHub",
    "IntegrationStatus",
    "LiveChatConnection",
    "TikTokConnection",
    "TwitchConnection",
    "WorkerShutdownCoordinator",
    "WorkerSlot",
    "YouTubeConnection",
    "is_worker_running",
]
