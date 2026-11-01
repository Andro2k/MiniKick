from collections.abc import Callable, Mapping
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, Slot


@dataclass(frozen=True)
class IntegrationStatus:
    connected: bool
    channel: str


class ConnectionHub(QObject):
    status_changed = Signal()

    def __init__(
        self,
        connections: Mapping[str, QObject],
        authenticated_providers: Mapping[str, Callable[[], bool]] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._connections = dict(connections)
        self._authenticated_providers = dict(authenticated_providers or {})

        for connection in self._connections.values():
            connection.state_changed.connect(self._on_connection_changed)

    def get_integration_statuses(self) -> dict[str, IntegrationStatus]:
        return {
            platform: IntegrationStatus(
                connected=connection.is_connected,
                channel=connection.channel,
            )
            for platform, connection in self._connections.items()
        }

    def get_connected_platforms(self) -> dict[str, bool]:
        statuses = self.get_integration_statuses()
        return {
            platform: statuses[platform].connected
            or self._is_authenticated(platform)
            for platform in self._connections
        }

    def _is_authenticated(self, platform: str) -> bool:
        provider = self._authenticated_providers.get(platform)
        return provider() if provider is not None else False

    @Slot()
    def _on_connection_changed(self) -> None:
        self.status_changed.emit()
