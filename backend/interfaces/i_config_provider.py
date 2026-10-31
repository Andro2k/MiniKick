# backend\interfaces\i_config_provider.py

import logging
import threading
from abc import ABC, abstractmethod
from typing import Iterable, Mapping

logger = logging.getLogger("minikick.interfaces.config")

ConfigValue = str | bool | int | float

_MISSING = object()
_TRUE_TEXT = frozenset({"1", "true"})


class IConfigProvider(ABC):
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._data: dict[str, ConfigValue] | None = None

    @abstractmethod
    def _load(self) -> dict[str, ConfigValue]: ...

    @abstractmethod
    def _store(self, data: Mapping[str, ConfigValue]) -> None: ...

    def load_string(self, key: str, default: str | None = "") -> str | None:
        value = self._snapshot().get(key, _MISSING)
        return default if value is _MISSING else _as_text(value)

    def save_string(self, key: str, value: str) -> None:
        self._commit({key: _normalize(value)})

    def load_bool(self, key: str, default: bool = False) -> bool:
        value = self._snapshot().get(key, _MISSING)
        return default if value is _MISSING else _as_bool(value)

    def save_bool(self, key: str, value: bool) -> None:
        self._commit({key: bool(value)})

    def get_all(self) -> dict:
        return {key: _legacy_flag(value) for key, value in self._snapshot().items()}

    def save_all(self, settings: Mapping) -> None:
        if settings:
            self._commit({key: _normalize(value) for key, value in settings.items()})

    def delete_key_prefix(self, prefix: str) -> None:
        stale = [key for key in self._snapshot() if key.startswith(prefix)]
        if stale:
            self._commit(removed=stale)

    def _snapshot(self) -> dict[str, ConfigValue]:
        with self._lock:
            if self._data is None:
                try:
                    self._data = dict(self._load())
                except Exception as err:
                    logger.error("[Config] Could not load configuration, starting empty: %s", err)
                    self._data = {}
            return self._data

    def _commit(self, updates: Mapping[str, ConfigValue] | None = None, removed: Iterable[str] = ()) -> None:
        with self._lock:
            dropped = set(removed)
            new_data = {key: value for key, value in self._snapshot().items() if key not in dropped}
            new_data.update(updates or {})
            try:
                self._store(new_data)
            except Exception as err:
                logger.error("[Config] Could not persist configuration: %s", err)
                return
            self._data = new_data


def _normalize(value) -> ConfigValue:
    if isinstance(value, (str, bool, int, float)):
        return value
    return "" if value is None else str(value)


def _as_text(value: ConfigValue) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def _as_bool(value: ConfigValue) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in _TRUE_TEXT
    return value == 1


def _legacy_flag(value: ConfigValue) -> ConfigValue:
    if isinstance(value, str) and value in ("1", "0"):
        return value == "1"
    return value
