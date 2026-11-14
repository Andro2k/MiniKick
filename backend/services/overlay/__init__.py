# backend\services\overlay\__init__.py
"""Servicios de la superposición local."""

from .overlay_manager import OverlayServerManager
from .overlay_ws_client import WebSocketClient

__all__ = ["OverlayServerManager", "WebSocketClient"]
