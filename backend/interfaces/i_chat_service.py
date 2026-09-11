# backend\interfaces\chat_service.py

from typing import Protocol, runtime_checkable

@runtime_checkable
class IChatService(Protocol):
    def process_chat_message(self, user: str, text: str, badges: list) -> None:
        ...

    def get_settings(self) -> dict:
        ...

    def set_volume(self, volume: int) -> None:
        ...

    def set_provider(self, provider: str) -> None:
        ...
