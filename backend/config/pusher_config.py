# backend\config\pusher_config.py

from dataclasses import dataclass


@dataclass(frozen=True)
class PusherConfig:
    cluster: str
    keys: tuple[str, ...]

KICK_PUSHER = PusherConfig(
    cluster="us2",
    keys=("34bf7a0ff419a2a775b9", "32cbd69e4b950bf97679"),
)
