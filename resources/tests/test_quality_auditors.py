# resources\tests\test_quality_auditors.py

import ast
from resources.tools.frontend_hardcoded_text_auditor import AntiHardcodeVisitor
from resources.tools.frontend_qt_signal_lifecycle_auditor import SignalLeakVisitor
from resources.tools.project_code_duplication_auditor import DuplicationScanner
from resources.tools.frontend_design_token_auditor import audit_design_tokens


def test_anti_hardcode_visitor_detects_violations():
    code = """
class MyWidget:
    def __init__(self, i18n):
        self.i18n = i18n
        self.btn = QPushButton("Save Changes")
        self.lbl = QLabel("Welcome to MiniKick")
        self.entry.setPlaceholderText("Enter your username...")
        self.title = self.i18n.get("key") or "Default Fallback"
        
        self.valid_lbl = QLabel(self.i18n.get("common.welcome"))
        self.btn2 = QPushButton(self.i18n.get("common.save"))
"""
    lines = code.splitlines()
    tree = ast.parse(code)
    visitor = AntiHardcodeVisitor("frontend/views/test_view.py", lines)
    visitor.visit(tree)

    violations = visitor.violations
    types = [v.violation_type for v in violations]
    values = [v.raw_text for v in violations]

    assert "WIDGET_CONSTRUCTOR" in types
    assert "INLINE_FALLBACK" in types
    assert "Save Changes" in values
    assert "Welcome to MiniKick" in values
    assert "Enter your username..." in values
    assert "Default Fallback" in values

def test_anti_hardcode_visitor_ignores_technical_strings():
    code = """
class SafeWidget:
    def __init__(self, i18n):
        self.btn = QPushButton(self.i18n.get("common.save"))
        self.btn.setProperty("role", "primary")
        self.btn.setObjectName("btn_save")
        self.fmt = "{count} items"
"""
    lines = code.splitlines()
    tree = ast.parse(code)
    visitor = AntiHardcodeVisitor("frontend/views/test_view.py", lines)
    visitor.visit(tree)

    assert len(visitor.violations) == 0

def test_qt_signal_leak_visitor_detects_loop_and_render_connects():
    code = """
class DynamicListWidget:
    def render_rows(self, data):
        for item in data:
            self.shared_btn.clicked.connect(self.on_click)
            btn = QPushButton()
            btn.clicked.connect(lambda: self.on_click(item))

    def refresh_ui(self):
        self.action_btn.clicked.connect(self.on_action)
"""
    lines = code.splitlines()
    tree = ast.parse(code)
    visitor = SignalLeakVisitor("frontend/views/test_list.py", lines)
    visitor.visit(tree)

    violations = visitor.violations
    types = [v.violation_type for v in violations]
    assert "LOOP_CONNECT" in types
    assert "LATE_BINDING_LAMBDA" in types
    assert "REFRESH_METHOD_CONNECT" in types

def test_qt_signal_leak_visitor_allows_setup_connections():
    code = """
class StaticWidget:
    def __init__(self):
        self._connect_signals()

    def _connect_signals(self):
        self.btn1.clicked.connect(self.on_click)
        controls = [self.btn1, self.btn2]
        for control in controls:
            control.toggled.connect(self.on_toggle)
"""
    lines = code.splitlines()
    tree = ast.parse(code)
    visitor = SignalLeakVisitor("frontend/views/test_static.py", lines)
    visitor.visit(tree)

    assert len(visitor.violations) == 0

def test_dry_ast_normalizer_hashes_identical_logic_consistently():
    code1 = """
def process_data(a, b):
    res = a + b
    log_info(res)
    save_result(res)
    return res
"""
    code2 = """
def handle_input(x, y):
    val = x + y
    log_info(val)
    save_result(val)
    return val
"""
    t1 = ast.parse(code1).body[0]
    t2 = ast.parse(code2).body[0]

    scanner = DuplicationScanner(min_statements=4)
    h1 = scanner._canonical_ast_hash(t1.body)
    h2 = scanner._canonical_ast_hash(t2.body)

    assert h1 == h2

def test_design_token_auditor_detects_raw_hex_in_ui(tmp_path):
    sample_code = """
track_color = "#18171C"
# This is a comment with #FFFFFF
border = "#EF4444"
"""
    test_file = tmp_path / "mock_widget.py"
    test_file.write_text(sample_code, encoding="utf-8")

    violations = audit_design_tokens(str(tmp_path))
    hex_values = [v.detected_value.upper() for v in violations]

    assert "#18171C" in hex_values
    assert "#EF4444" in hex_values
    assert "#FFFFFF" not in hex_values
