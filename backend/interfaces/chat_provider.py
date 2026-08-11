# backend\interfaces\chat_provider.py

from typing import Protocol, runtime_checkable, Callable

@runtime_checkable
class IChatProvider(Protocol):
    def connect(self, channel_name: str, on_message: Callable) -> None:
        ...

    def disconnect(self) -> None:
        ...

    def send_message(self, content: str, as_bot: bool = True) -> bool:
        ...

    def delete_message(self, message_id: str) -> bool:
        ...

    def timeout_user(self, username: str, duration_seconds: int, reason: str = "") -> bool:
        ...

    def ban_user(self, username: str, reason: str = "") -> bool:
        ...
