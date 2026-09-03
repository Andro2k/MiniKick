# backend\interfaces\alert_interfaces.py

from typing import Protocol
from backend.models.alert_models import AlertConfig

class AlertStorageProtocol(Protocol):
    def load_all(self) -> dict[tuple[str, str], AlertConfig]:
        ...

    def get_config(self, platform: str, alert_type: str) -> AlertConfig | None:
        ...

    def save_config(self, config: AlertConfig) -> bool:
        ...

    def save_all(self, configs: list[AlertConfig]) -> bool:
        ...
