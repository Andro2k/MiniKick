# resources\tests\test_locales_ftl.py
"""Los .ftl de assets/i18n deben coincidir con los JSON de assets/locales (ida y vuelta con Fluent)."""

import json
import re

import pytest
from fluent.runtime import FluentBundle, FluentResource
from fluent.syntax import FluentParser, ast

from resources.tools import project_locales_ftl_tool as tool

LANGS = tool.languages()
_VARS = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _json_flat(lang):
    with open(tool.source_path(lang), encoding="utf-8") as handle:
        return dict(tool.flatten(json.load(handle)))


def _ftl_text(lang):
    with open(tool.target_path(lang), encoding="utf-8", newline="") as handle:
        return handle.read()


def test_languages_include_en_and_es():
    assert {"en", "es"} <= set(LANGS)


@pytest.mark.parametrize("lang", LANGS)
def test_ftl_is_up_to_date_with_json(lang):
    assert _ftl_text(lang) == tool.generate(lang), f"Ejecuta {tool.__name__} para regenerar {lang}"


@pytest.mark.parametrize("lang", LANGS)
def test_ftl_has_no_syntax_errors(lang):
    resource = FluentParser().parse(_ftl_text(lang))
    junk = [entry for entry in resource.body if isinstance(entry, ast.Junk)]
    assert not junk, f"{lang}: {len(junk)} entradas invalidas, primera: {junk[0].content[:80]!r}"


@pytest.mark.parametrize("lang", LANGS)
def test_every_message_round_trips_to_the_json_value(lang):
    bundle = FluentBundle([lang], use_isolating=False)
    bundle.add_resource(FluentResource(_ftl_text(lang)))
    mismatches = []
    for key, expected in _json_flat(lang).items():
        name = tool.ftl_id(key)
        if not bundle.has_message(name):
            mismatches.append(f"{key}: falta en el .ftl")
            continue
        args = {var: "{%s}" % var for var in _VARS.findall(expected)}
        text, errors = bundle.format_pattern(bundle.get_message(name).value, args)
        if errors or text != expected:
            mismatches.append(f"{key}: {text!r} != {expected!r} {errors}")
    assert not mismatches, f"{lang}: {len(mismatches)} difieren, primera: {mismatches[0]}"


def test_locales_share_the_same_keys_and_variables():
    base = _json_flat("en")
    for lang in LANGS:
        other = _json_flat(lang)
        assert set(other) == set(base), f"{lang}: claves distintas a en"
        wrong = [k for k in base if set(_VARS.findall(other[k])) != set(_VARS.findall(base[k]))]
        assert not wrong, f"{lang}: variables distintas en {wrong[:3]}"
