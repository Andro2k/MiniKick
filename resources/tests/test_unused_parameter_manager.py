# resources\tests\test_unused_parameter_manager.py

import ast
from resources.tools.project_unused_parameter_auditor import ParameterUsageVisitor


def test_unused_parameter_visitor_detects_categories():
    code = """
class BaseHandler:
    def validate(self, step_index: int) -> bool:
        return True

    def on_custom_event(self, event):
        pass

class ConcreteHandler(BaseHandler):
    def resizeEvent(self, event):
        self.do_something()

    def process(self, data: dict, unused_flag: bool):
        return data["value"]
"""
    lines = code.splitlines()
    tree = ast.parse(code)
    visitor = ParameterUsageVisitor("test_file.py", lines)
    visitor.visit(tree)

    occurrences = visitor.occurrences
    param_map = {(o.func_name, o.param_name): o.category for o in occurrences}

    assert param_map.get(("validate", "step_index")) == "CONTRACT_HOOK"

    assert param_map.get(("resizeEvent", "event")) == "QT_OVERRIDE"

    assert param_map.get(("process", "unused_flag")) == "DEAD_PARAMETER"

    assert ("process", "data") not in param_map

def test_unused_parameter_visitor_ignores_pep8_escaped_names():
    code = """
def callback(_data: dict, _index: int):
    return 42
"""
    lines = code.splitlines()
    tree = ast.parse(code)
    visitor = ParameterUsageVisitor("test_file.py", lines)
    visitor.visit(tree)

    assert len(visitor.occurrences) == 0
