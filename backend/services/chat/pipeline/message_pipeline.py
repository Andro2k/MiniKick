# backend\services\chat\pipeline\message_pipeline.py

from typing import Callable
from backend.services.chat.pipeline.chat_dto import ChatMessageDTO

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