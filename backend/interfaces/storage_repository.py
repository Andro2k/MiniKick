# backend\interfaces\storage_repository.py

from typing import Protocol, Any, runtime_checkable

@runtime_checkable
class IStorageRepository(Protocol):
    def save_setting(self, key: str, value: Any) -> None:
        ...

    def get_setting(self, key: str, default: Any = None) -> Any:
        ...

    def load_bool(self, key: str, default: bool = False) -> bool:
        ...

    def save_bool(self, key: str, value: bool) -> None:
        ...
