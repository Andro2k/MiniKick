# backend\services\settings\translation_service.py
"""Carga el idioma de la interfaz (Fluent) y resuelve las claves de traducción."""

import logging
import os
import sys
import threading
from typing import Any, Dict, FrozenSet, Optional, Set, Tuple

from fluent.runtime import FluentBundle, FluentResource
from fluent.runtime.types import fluent_number
from fluent.syntax.visitor import Visitor

logger = logging.getLogger("minikick.services.system.i18n")

_FTL_FILENAME = "main.ftl"
_FALLBACK_LANG = "en"

# Un bundle por archivo, compartido entre instancias: parsear un idioma cuesta ~130 ms.
_BUNDLES: Dict[str, Optional[FluentBundle]] = {}
_BUNDLES_LOCK = threading.Lock()
_WARNED: Set[Tuple[str, str]] = set()
_VARIABLES: Dict[Tuple[str, str], FrozenSet[str]] = {}


def _warn_once(kind: str, detail: str) -> None:
    marker = (kind, detail)
    if marker in _WARNED:
        return
    _WARNED.add(marker)
    logger.warning("[i18n] %s: %s", kind, detail)


def _fluent_arg(value: Any) -> Any:
    """Mantiene la salida de str.format: enteros sin separador de miles; el resto, como texto."""
    if isinstance(value, int) and not isinstance(value, bool):
        return fluent_number(value, useGrouping=False)
    return value if isinstance(value, str) else str(value)


class _VariableCollector(Visitor):
    def __init__(self):
        super().__init__()
        self.names: Set[str] = set()

    def visit_VariableReference(self, node):
        self.names.add(node.id.name)


def _variable_names(bundle_key: str, message_id: str, message) -> FrozenSet[str]:
    cache_key = (bundle_key, message_id)
    names = _VARIABLES.get(cache_key)
    if names is None:
        collector = _VariableCollector()
        collector.visit(message)
        names = _VARIABLES[cache_key] = frozenset(collector.names)
    return names


class TranslationService:
    def __init__(self, locales_dir: str = os.path.join("assets", "i18n"), default_lang: str = _FALLBACK_LANG):
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

        self.locales_dir = os.path.join(base_dir, locales_dir)
        self.current_lang = default_lang
        self.load_language(default_lang)

    def load_language(self, lang_code: str) -> bool:
        """Activa el idioma; False si falta su .ftl (se usara el ingles como respaldo)."""
        self.current_lang = lang_code
        return self._bundle(lang_code) is not None

    def get(self, key: str, **kwargs) -> str:
        message_id = key.replace(".", "-")
        args = {name: _fluent_arg(value) for name, value in kwargs.items()} if kwargs else None

        text = self._format(self.current_lang, message_id, args)
        if text is None:
            _warn_once("falta la clave", f"{key} ({self.current_lang})")
            if self.current_lang != _FALLBACK_LANG:
                text = self._format(_FALLBACK_LANG, message_id, args)
        return key if text is None else text

    def _format(self, lang_code: str, message_id: str, args: Optional[Dict[str, Any]]) -> Optional[str]:
        bundle = self._bundle(lang_code)
        if bundle is None or not bundle.has_message(message_id):
            return None
        message = bundle.get_message(message_id)
        if message.value is None:
            return None
        names = _variable_names(self._path(lang_code), message_id, message)
        merged: Dict[str, Any] = {name: "{%s}" % name for name in names}
        if args:
            merged.update(args)
        text, errors = bundle.format_pattern(message.value, merged or None)
        for error in errors:
            _warn_once("no se pudo formatear", f"{message_id} ({lang_code}): {error}")
        return text

    def _path(self, lang_code: str) -> str:
        return os.path.join(self.locales_dir, lang_code, _FTL_FILENAME)

    def _bundle(self, lang_code: str) -> Optional[FluentBundle]:
        filepath = self._path(lang_code)
        with _BUNDLES_LOCK:
            if filepath not in _BUNDLES:
                _BUNDLES[filepath] = self._read_bundle(lang_code, filepath)
            return _BUNDLES[filepath]

    @staticmethod
    def _read_bundle(lang_code: str, filepath: str) -> Optional[FluentBundle]:
        try:
            with open(filepath, "r", encoding="utf-8") as handle:
                source = handle.read()
        except OSError:
            logger.warning("[i18n] No se pudo leer %s", filepath)
            return None
        bundle = FluentBundle([lang_code], use_isolating=False)
        bundle.add_resource(FluentResource(source))
        return bundle
