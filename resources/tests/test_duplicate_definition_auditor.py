# resources\tests\test_duplicate_definition_auditor.py

import ast
import textwrap

from resources.tools.project_duplicate_definition_auditor import (
    VERDICT_DIVERGENT,
    VERDICT_IDENTICAL,
    DuplicateDefinitionScanner,
)


def _scan(source: str, is_test_file: bool = False):
    tree = ast.parse(textwrap.dedent(source))
    return DuplicateDefinitionScanner("sample.py", is_test_file).scan(tree)


def test_property_defined_twice_is_reported_as_divergent():
    findings = _scan('''
        class View:
            @property
            def theme(self):
                return self.a

            @property
            def theme(self):
                return self.b
    ''')
    assert [(f.kind, f.name, f.scope, f.verdict) for f in findings] == [
        ("property", "theme", "View", VERDICT_DIVERGENT)
    ]
    assert (findings[0].first_line, findings[0].second_line) == (4, 8)


def test_identical_duplicate_method_is_reported_as_identical():
    findings = _scan('''
        class Service:
            def run(self):
                return 1

            def run(self):
                return 1
    ''')
    assert [(f.kind, f.verdict) for f in findings] == [("method", VERDICT_IDENTICAL)]


def test_property_setter_overload_and_register_are_not_duplicates():
    findings = _scan('''
        from typing import overload

        class Config:
            @property
            def value(self):
                return self._v

            @value.setter
            def value(self, v):
                self._v = v

        @overload
        def parse(x: int) -> int: ...
        @overload
        def parse(x: str) -> str: ...
        def parse(x):
            return x

        @dispatcher.register
        def handle(x): ...
        @handle.register(int)
        def handle(x): ...
    ''')
    assert findings == []


def test_conditional_definitions_in_different_branches_are_not_duplicates():
    findings = _scan('''
        import sys

        if sys.platform == "win32":
            def helper():
                return 1
        else:
            def helper():
                return 2

        try:
            import fast
        except ImportError:
            def helper2(): ...
    ''')
    assert findings == []


def test_duplicate_test_function_is_reported_as_test_kind():
    findings = _scan('''
        def test_something():
            assert True

        def test_something():
            assert 1 == 1
    ''', is_test_file=True)
    assert [(f.kind, f.name) for f in findings] == [("test", "test_something")]


def test_class_attribute_and_dict_key_duplicates_are_reported():
    findings = _scan('''
        class Panel:
            changed = Signal()
            changed = Signal(int)

        COLORS = {"red": 1, "green": 2, "red": 1}
    ''')
    assert sorted((f.kind, f.name, f.verdict) for f in findings) == [
        ("attribute", "changed", VERDICT_DIVERGENT),
        ("dict_key", "'red'", VERDICT_IDENTICAL),
    ]


def test_dict_unpacking_and_non_constant_keys_are_ignored():
    findings = _scan('''
        data = {**base, **other, key: 1, key: 2}
    ''')
    assert findings == []
