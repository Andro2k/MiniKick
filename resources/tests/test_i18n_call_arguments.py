# resources\tests\test_i18n_call_arguments.py
"""Cada get(clave, nombre=valor) debe pasar exactamente las variables que el mensaje .ftl declara."""

import ast
import os

from fluent.syntax import FluentParser, ast as fluent_ast
from fluent.syntax.visitor import Visitor

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


class _Variables(Visitor):
    def __init__(self):
        super().__init__()
        self.names = set()

    def visit_VariableReference(self, node):
        self.names.add(node.id.name)


def _message_variables():
    with open(os.path.join(ROOT, "assets", "i18n", "en", "main.ftl"), encoding="utf-8") as handle:
        resource = FluentParser().parse(handle.read())
    result = {}
    for entry in resource.body:
        if isinstance(entry, fluent_ast.Message):
            found = _Variables()
            found.visit(entry)
            result[entry.id.name.replace("-", ".")] = found.names
    return result


def _calls_with_kwargs():
    for folder in ("backend", "frontend"):
        for current, _, files in os.walk(os.path.join(ROOT, folder)):
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(current, name)
                with open(path, encoding="utf-8") as handle:
                    tree = ast.parse(handle.read())
                for node in ast.walk(tree):
                    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                        continue
                    if node.func.attr != "get" or not ast.unparse(node.func.value).endswith("i18n"):
                        continue
                    if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
                        continue
                    if not node.keywords or any(kw.arg is None for kw in node.keywords):
                        continue
                    yield f"{os.path.relpath(path, ROOT)}:{node.lineno}", node.args[0].value, {kw.arg for kw in node.keywords}


def test_i18n_calls_with_kwargs_match_the_message_variables():
    variables = _message_variables()
    problems = []
    for where, key, passed in _calls_with_kwargs():
        if key not in variables:
            continue
        missing, unknown = variables[key] - passed, passed - variables[key]
        if missing or unknown:
            problems.append(f"{where} {key}: faltan {sorted(missing)} sobran {sorted(unknown)}")
    assert not problems, "\n".join(problems)
