# resources\tests\test_translation_service.py
"""TranslationService sobre Fluent: claves con puntos, respaldo en ingles, numeros y plurales."""

import logging
import os

import pytest
from fluent.syntax import FluentParser, ast

from backend.services.settings.translation_service import TranslationService

LOGGER = "minikick.services.system.i18n"


def _service(tmp_path, files, lang):
    for code, text in files.items():
        folder = tmp_path / code
        folder.mkdir()
        (folder / "main.ftl").write_text(text, encoding="utf-8")
    return TranslationService(locales_dir=str(tmp_path), default_lang=lang)


def test_dotted_key_maps_to_the_flat_fluent_id(tmp_path):
    svc = _service(tmp_path, {"en": "a-b-c = Hello\n"}, "en")
    assert svc.get("a.b.c") == "Hello"


def test_placeholders_are_filled_without_bidi_marks(tmp_path):
    svc = _service(tmp_path, {"en": "greet = Hi { $name }!\n"}, "en")
    text = svc.get("greet", name="Ana")
    assert text == "Hi Ana!"
    assert "\u2068" not in text and "\u2069" not in text


def test_missing_key_falls_back_to_english(tmp_path):
    files = {"en": "only-en = English\nboth = One\n", "es": "both = Uno\n"}
    svc = _service(tmp_path, files, "es")
    assert svc.get("both") == "Uno"
    assert svc.get("only.en") == "English"


def test_missing_everywhere_returns_the_dotted_key_and_warns_once(tmp_path, caplog):
    svc = _service(tmp_path, {"en": "x = y\n"}, "en")
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        assert svc.get("nope.warn_once_key") == "nope.warn_once_key"
        assert svc.get("nope.warn_once_key") == "nope.warn_once_key"
    assert sum("nope.warn_once_key" in r.getMessage() for r in caplog.records) == 1


def test_missing_language_file_reports_false_and_uses_english(tmp_path):
    svc = _service(tmp_path, {"en": "hello = Hello\n"}, "fr")
    assert svc.load_language("fr") is False
    assert svc.current_lang == "fr"
    assert svc.get("hello") == "Hello"
    assert svc.load_language("en") is True


def test_numbers_keep_str_format_output(tmp_path):
    svc = _service(tmp_path, {"es": "n = { $v }\n"}, "es")
    assert svc.get("n", v=12345) == "12345"
    assert svc.get("n", v=-7) == "-7"
    assert svc.get("n", v=12.0) == "12.0"
    assert svc.get("n", v=0.333333) == "0.333333"
    assert svc.get("n", v=True) == "True"
    assert svc.get("n", v=None) == "None"
    assert svc.get("n", v=["a"]) == "['a']"


def test_integer_arguments_drive_plural_selectors(tmp_path):
    source = "songs = { $count ->\n    [one] { $count } cancion\n   *[other] { $count } canciones\n}\n"
    svc = _service(tmp_path, {"es": source}, "es")
    assert svc.get("songs", count=1) == "1 cancion"
    assert svc.get("songs", count=5) == "5 canciones"
    assert svc.get("songs", count=1000) == "1000 canciones"


def test_unfilled_variables_stay_literal_for_legacy_replace_callers(tmp_path):
    source = "ping = HTTP { $status } in { $ms } ms\nsongs = { $count ->\n    [one] { $count } song\n   *[other] { $count } songs\n}\n"
    svc = _service(tmp_path, {"en": source}, "en")
    assert svc.get("ping") == "HTTP {status} in {ms} ms"
    assert svc.get("ping").replace("{status}", "204").replace("{ms}", "9") == "HTTP 204 in 9 ms"
    assert svc.get("ping", status=204) == "HTTP 204 in {ms} ms"
    assert svc.get("songs") == "{count} songs"


def test_extra_kwargs_are_ignored(tmp_path):
    svc = _service(tmp_path, {"en": "plain = Text\n"}, "en")
    assert svc.get("plain", unused=1) == "Text"


def test_instances_share_the_parsed_bundle(tmp_path):
    first = _service(tmp_path, {"en": "k = v\n"}, "en")
    second = TranslationService(locales_dir=str(tmp_path), default_lang="en")
    assert first._bundle("en") is second._bundle("en")


@pytest.mark.parametrize("lang", ["es", "en"])
def test_real_locales_resolve_every_key(lang):
    svc = TranslationService(default_lang=lang)
    path = os.path.join(svc.locales_dir, lang, "main.ftl")
    with open(path, encoding="utf-8") as handle:
        resource = FluentParser().parse(handle.read())
    keys = [e.id.name.replace("-", ".") for e in resource.body if isinstance(e, ast.Message)]
    assert len(keys) > 1000
    unresolved = [key for key in keys if svc.get(key) == key]
    assert not unresolved, f"{lang}: {len(unresolved)} sin resolver, p. ej. {unresolved[:3]}"


def test_commands_help_labels_are_not_raw_keys():
    svc = TranslationService(default_lang="es")
    assert svc.get("chat.commands_help.sec_chat") != "chat.commands_help.sec_chat"
