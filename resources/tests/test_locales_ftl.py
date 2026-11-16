# resources\tests\test_locales_ftl.py
"""Los .ftl de assets/i18n son la fuente de las traducciones: validos y con las mismas claves y variables."""

import os

import pytest
from fluent.syntax import FluentParser, ast
from fluent.syntax.visitor import Visitor

I18N_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "i18n")
LANGS = sorted(name for name in os.listdir(I18N_DIR) if os.path.isdir(os.path.join(I18N_DIR, name)))


class _Variables(Visitor):
    def __init__(self):
        super().__init__()
        self.names = set()

    def visit_VariableReference(self, node):
        self.names.add(node.id.name)


def _resource(lang):
    with open(os.path.join(I18N_DIR, lang, "main.ftl"), encoding="utf-8") as handle:
        return FluentParser().parse(handle.read())


def _messages(lang):
    result = {}
    for entry in _resource(lang).body:
        if isinstance(entry, ast.Message):
            found = _Variables()
            found.visit(entry)
            result[entry.id.name] = (entry.value is not None, found.names)
    return result


def test_languages_include_en_and_es():
    assert {"en", "es"} <= set(LANGS)


@pytest.mark.parametrize("lang", LANGS)
def test_ftl_has_no_syntax_errors(lang):
    junk = [entry for entry in _resource(lang).body if isinstance(entry, ast.Junk)]
    assert not junk, f"{lang}: {len(junk)} entradas invalidas, primera: {junk[0].content[:80]!r}"


@pytest.mark.parametrize("lang", LANGS)
def test_every_message_has_a_value_and_no_hyphen_ambiguity(lang):
    messages = _messages(lang)
    assert all(has_value for has_value, _ in messages.values())
    assert len({name.replace("-", ".") for name in messages}) == len(messages)


def test_locales_share_the_same_keys_and_variables():
    base = _messages("en")
    for lang in LANGS:
        other = _messages(lang)
        assert set(other) == set(base), f"{lang}: claves distintas a en"
        wrong = [key for key in base if other[key][1] != base[key][1]]
        assert not wrong, f"{lang}: variables distintas en {wrong[:3]}"
