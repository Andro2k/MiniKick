# backend\services\chat\pipeline.py

from dataclasses import dataclass
from typing import Callable

@dataclass
class ChatMessageDTO:
    user: str
    content: str
    badges: list
    color: str
    msg_id: str
    sender_id: int
    timestamp: str = ""
    platform: str = "kick"
    is_cancelled: bool = False
    emotes_tag: str = ""
    is_command: bool = False

class MessagePipeline:
    def __init__(self):
        self._middlewares: list[Callable[[ChatMessageDTO], None]] = []

    def register(self, middleware: Callable[[ChatMessageDTO], None]) -> 'MessagePipeline':
        self._middlewares.append(middleware)
        return self

    def execute(self, dto: ChatMessageDTO):
        for middleware in self._middlewares:
            if dto.is_cancelled:
                break
            middleware(dto)
