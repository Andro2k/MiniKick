# backend\providers\chat\base_chat_provider.py

from abc import ABC, abstractmethod
from typing import Any

class BaseChatSocketProvider(ABC):
    @abstractmethod
    def start_socket(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop_socket(self) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def is_running(self) -> bool:
        raise NotImplementedError
