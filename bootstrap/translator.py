# bootstrap\translator.py\\

import logging
import os
import sys

logger = logging.getLogger("minikick.bootstrap.i18n")

DEFAULT_LANGUAGE = "es"
SUPPORTED_LANGUAGES = ("es", "en")
_INSTALL_LANG_FILE = ".install_lang"


class FallbackTranslator:
    def get(self, key: str, *args, **kwargs) -> str:
        return key


def load_translator(settings_storage=None):
    try:
        if settings_storage is None:
            settings_storage = _default_settings_storage()
        language = _resolve_language(settings_storage)

        from backend.services import TranslationService
        return TranslationService(default_lang=language)
    except Exception as e:
        logger.warning("[Bootstrap] i18n initialization failed: %s", e)
        return FallbackTranslator()


def _default_settings_storage():
    from backend.database import DatabaseManager, SQLiteSettingsStorage
    return SQLiteSettingsStorage(DatabaseManager())


def _resolve_language(storage) -> str:
    language = storage.load_string("app_language", DEFAULT_LANGUAGE)
    installed = _consume_install_language()
    if installed and installed != language:
        storage.save_string("app_language", installed)
        return installed
    return language


def _app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _consume_install_language() -> str | None:
    path = os.path.join(_app_dir(), _INSTALL_LANG_FILE)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            language = f.read().strip()
    except Exception as e:
        logger.debug("[Bootstrap] Notice reading %s: %s", _INSTALL_LANG_FILE, e)
        return None
    try:
        os.remove(path)
    except OSError:
        pass
    return language if language in SUPPORTED_LANGUAGES else None