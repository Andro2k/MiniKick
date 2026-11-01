# backend\connections\__init__.py

from .kick import KickConnection
from .live_chat import LiveChatConnection, TikTokConnection, YouTubeConnection
from .twitch import TwitchConnection
from .worker_shutdown import WorkerShutdownCoordinator, is_worker_running
from .worker_slot import WorkerSlot

__all__ = [
    "KickConnection",
    "LiveChatConnection",
    "TikTokConnection",
    "TwitchConnection",
    "WorkerShutdownCoordinator",
    "WorkerSlot",
    "YouTubeConnection",
    "is_worker_running",
]
