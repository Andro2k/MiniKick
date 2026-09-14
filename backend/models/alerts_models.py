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
    layout: str = "above"
    style: str = "compact"
    text_color: str = "#FFFFFF"
    highlight_color: str = ""
    font_family: str = "Outfit"
    font_size: int = 24
    text_align: str = "center"
    animation_in: str = "fade_in"
    animation_in_duration: float = 1.0
    animation_out: str = "fade_out"
    animation_out_duration: float = 1.0
    bg_color: str = "#121317"
    bg_opacity: int = 88
    border_radius: int = 20
    padding_px: int = 24
    spacing_px: int = 16
    box_shadow: bool = True
    font_weight: str = "bold"
    text_shadow: bool = True
    card_width: int = 560
    card_height: int = 0

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
            tts_read=bool(data.get("tts_read", False)),
            layout=str(data.get("layout", "above")),
            style=str(data.get("style", "compact")),
            text_color=str(data.get("text_color", "#FFFFFF")),
            highlight_color=str(data.get("highlight_color", "")),
            font_family=str(data.get("font_family", "Outfit")),
            font_size=int(data.get("font_size", 24)),
            text_align=str(data.get("text_align", "center")),
            animation_in=str(data.get("animation_in", "fade_in")),
            animation_in_duration=float(data.get("animation_in_duration", 1.0)),
            animation_out=str(data.get("animation_out", "fade_out")),
            animation_out_duration=float(data.get("animation_out_duration", 1.0)),
            bg_color=str(data.get("bg_color", "#121317")),
            bg_opacity=int(data.get("bg_opacity", 88)),
            border_radius=int(data.get("border_radius", 20)),
            padding_px=int(data.get("padding_px", 24)),
            spacing_px=int(data.get("spacing_px", 16)),
            box_shadow=bool(data.get("box_shadow", True)),
            font_weight=str(data.get("font_weight", "bold")),
            text_shadow=bool(data.get("text_shadow", True)),
            card_width=int(data.get("card_width", 560) or 560),
            card_height=int(data.get("card_height", 0) or 0)
        )


