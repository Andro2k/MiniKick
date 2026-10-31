# bootstrap\config.py

import logging
from pathlib import Path

from backend.config.toml_config_provider import TomlConfigProvider
from backend.interfaces import IConfigProvider

logger = logging.getLogger("minikick.bootstrap.config")

CONFIG_FILE_NAME = "config.toml"
_MIGRATION_MARKER = "settings_migrated_to_toml"


def create_config_provider(db_manager) -> IConfigProvider:
    path = Path(db_manager.db_name).with_name(CONFIG_FILE_NAME)
    is_first_run = not path.exists()
    provider = TomlConfigProvider(path)
    if is_first_run:
        _import_legacy_settings(db_manager, provider, path)
    return provider


def _import_legacy_settings(db_manager, provider: IConfigProvider, path: Path) -> None:
    try:
        with db_manager.get_connection() as conn:
            legacy = dict(conn.execute("SELECT key, value FROM settings").fetchall())
            if not legacy or _MIGRATION_MARKER in legacy:
                return

            provider.save_all(legacy)
            if not path.exists():
                logger.error("[Bootstrap] Legacy settings could not be written to %s; will retry next start.", path.name)
                return

            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, '1')", (_MIGRATION_MARKER,))
            conn.commit()
            logger.info("[Bootstrap] Imported %d settings from SQLite into %s.", len(legacy), path.name)
    except Exception:
        logger.exception("[Bootstrap] Could not import legacy settings; defaults will be used.")
