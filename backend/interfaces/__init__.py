# backend\interfaces\__init__.py
"""Contratos de las interfaces del backend."""

from .auth_interface import TokenStorage, TokenProvider, TransientAuthError
from .secrets_interface import SecretCipher, TokenEncryptionError
from .config_provider_interface import ConfigValue, IConfigProvider
from .tts_interface import ITTSProvider
from .updater_interface import IUpdateChecker, IUpdateDownloader, IUpdateInstaller
from .music_provider_interface import IMusicProvider
from .music_chat_context_interface import IMusicChatContext
from .music_playlist_interface import IMusicPlaylistStorage
from .alerts_interface import AlertStorageProtocol
from .webhooks_interface import (
    CRITICAL_EVENT_TYPES,
    DEFAULT_PLATFORMS,
    EVENT_TYPES,
    PLATFORM_APP,
    DeliveryJob,
    DeliveryResponse,
    IEventSink,
    IPayloadFormatter,
    IWebhookTransport,
    WebhookEndpointConfig,
    WebhookEvent,
)

__all__ = [
    "TokenStorage",
    "TokenProvider",
    "TransientAuthError",
    "SecretCipher",
    "ConfigValue",
    "IConfigProvider",
    "ITTSProvider",
    "IUpdateChecker",
    "IUpdateDownloader",
    "IUpdateInstaller",
    "IMusicProvider",
    "IMusicChatContext",
    "IMusicPlaylistStorage",
    "AlertStorageProtocol",
    "TokenEncryptionError",
    "CRITICAL_EVENT_TYPES",
    "DEFAULT_PLATFORMS",
    "EVENT_TYPES",
    "PLATFORM_APP",
    "DeliveryJob",
    "DeliveryResponse",
    "IEventSink",
    "IPayloadFormatter",
    "IWebhookTransport",
    "WebhookEndpointConfig",
    "WebhookEvent",
]