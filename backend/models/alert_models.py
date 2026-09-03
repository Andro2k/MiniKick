# backend\models\alert_models.py

from dataclasses import dataclass, field, asdict
from enum import Enum
import time

class AlertType(str, Enum):
    FOLLOW = "follow"
    SUBSCRIPTION = "subscription"
    RESUB = "resub"
    SUB_GIFT = "sub_gift"
    RAID = "raid"
    CHEER = "cheer"

@dataclass(slots=True, frozen=True)
class AlertEvent:
    event_id: str
    platform: str
    alert_type: AlertType
    username: str
    display_name: str = ""
    message: str = ""
    amount: int = 1
    tier: str = "1"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["alert_type"] = self.alert_type.value
        return data

@dataclass(slots=True)
class AlertConfig:
    platform: str
    alert_type: str
    enabled: bool = True
    sound_path: str = ""
    media_path: str = ""
    text_template: str = "{user} se unió a la comunidad!"
    duration_ms: int = 5000
    sound_volume: float = 0.8
    tts_read: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AlertConfig":
        return cls(
            platform=str(data.get("platform", "")),
            alert_type=str(data.get("alert_type", "")),
            enabled=bool(data.get("enabled", True)),
            sound_path=str(data.get("sound_path", "")),
            media_path=str(data.get("media_path", "")),
            text_template=str(data.get("text_template", "{user}")),
            duration_ms=int(data.get("duration_ms", 5000)),
            sound_volume=float(data.get("sound_volume", 0.8)),
            tts_read=bool(data.get("tts_read", False))
        )
