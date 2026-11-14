# backend\services\media\__init__.py
"""Media services: avatars and Giphy."""

from .avatar_service import AvatarService
from .giphy_service import GiphyService

__all__ = [
    "AvatarService",
    "GiphyService",
]
