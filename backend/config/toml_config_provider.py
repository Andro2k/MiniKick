# backend\config\toml_config_provider.py

import contextlib
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Mapping

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import tomli_w

from backend.interfaces.i_config_provider import ConfigValue, IConfigProvider

logger = logging.getLogger("minikick.config.toml")

_REPLACE_ATTEMPTS = 5
_REPLACE_RETRY_DELAY_S = 0.02


class TomlConfigProvider(IConfigProvider):
    def __init__(self, path: str | Path) -> None:
        super().__init__()
        self._path = Path(path)

    def _load(self) -> dict[str, ConfigValue]:
        try:
            with open(self._path, "rb") as handle:
                return tomllib.load(handle)
        except FileNotFoundError:
            return {}
        except tomllib.TOMLDecodeError as err:
            self._quarantine(err)
            return {}

    def _store(self, data: Mapping[str, ConfigValue]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(dir=self._path.parent, prefix=f"{self._path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as handle:
                tomli_w.dump(dict(data), handle)
            self._replace(temp_name)
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(temp_name)
            raise

    def _replace(self, temp_name: str) -> None:
        for attempt in range(_REPLACE_ATTEMPTS):
            try:
                os.replace(temp_name, self._path)
                return
            except PermissionError:
                if attempt == _REPLACE_ATTEMPTS - 1:
                    raise
                time.sleep(_REPLACE_RETRY_DELAY_S)

    def _quarantine(self, error: Exception) -> None:
        backup = self._path.with_name(f"{self._path.name}.corrupt-{datetime.now():%Y%m%d-%H%M%S}")
        with contextlib.suppress(OSError):
            os.replace(self._path, backup)
        logger.error("[Config] %s is not valid TOML (%s); it was moved to %s and defaults will be used.",
                     self._path.name, error, backup.name)
