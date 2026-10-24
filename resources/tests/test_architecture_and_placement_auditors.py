# resources\tests\test_architecture_and_placement_auditors.py

import ast
from resources.tools.architecture_boundary_auditor import ArchitectureASTVisitor, audit_architecture_boundaries
from resources.tools.file_placement_auditor import audit_file_placements, FOLDER_PURITY_RULES, REVERSE_PLACEMENT_RULES
import fnmatch


def test_architecture_boundary_visitor_detects_ui_to_db_import():
    code = """
import sqlite3
from backend.database import DatabaseManager

class MyView:
    def load(self):
        conn = sqlite3.connect("test.db")
"""
    lines = code.splitlines()
    tree = ast.parse(code)
    visitor = ArchitectureASTVisitor("frontend/views/test_view.py", lines)
    visitor.visit(tree)

    rule_ids = [v.rule_id for v in visitor.violations]
    assert "SOR_UI_DB" in rule_ids
    assert len(visitor.violations) >= 2

def test_architecture_boundary_visitor_detects_db_qt_import():
    code = """
from PySide6.QtCore import Signal
import sqlite3

class BadStorage:
    pass
"""
    lines = code.splitlines()
    tree = ast.parse(code)
    visitor = ArchitectureASTVisitor("backend/database/bad_storage.py", lines)
    visitor.visit(tree)

    rule_ids = [v.rule_id for v in visitor.violations]
    assert "SOR_DB_QT" in rule_ids

def test_architecture_boundary_visitor_detects_core_widgets_import():
    code = """
from PySide6.QtWidgets import QMessageBox

class MyService:
    def alert_user(self):
        QMessageBox.warning(None, "Error", "Fail")
"""
    lines = code.splitlines()
    tree = ast.parse(code)
    visitor = ArchitectureASTVisitor("backend/services/chat/bad_service.py", lines)
    visitor.visit(tree)

    rule_ids = [v.rule_id for v in visitor.violations]
    assert "SOR_CORE_WIDGETS" in rule_ids

def test_architecture_boundary_visitor_detects_banned_json_import():
    code = """
import json

def process_data():
    return json.loads("{}")
"""
    lines = code.splitlines()
    tree = ast.parse(code)
    visitor = ArchitectureASTVisitor("backend/controllers/test_controller.py", lines)
    visitor.visit(tree)

    rule_ids = [v.rule_id for v in visitor.violations]
    assert "BANNED_JSON_IMPORT" in rule_ids

def test_architecture_boundary_visitor_detects_banned_print():
    code = """
def process():
    print("Debug message")
"""
    lines = code.splitlines()
    tree = ast.parse(code)
    visitor = ArchitectureASTVisitor("backend/services/system/test_service.py", lines)
    visitor.visit(tree)

    rule_ids = [v.rule_id for v in visitor.violations]
    assert "BANNED_PRINT" in rule_ids

def test_architecture_boundary_visitor_detects_blocking_sleep():
    code = """
import time

class MyController:
    def freeze(self):
        time.sleep(5)
"""
    lines = code.splitlines()
    tree = ast.parse(code)
    visitor = ArchitectureASTVisitor("backend/controllers/freeze_controller.py", lines)
    visitor.visit(tree)

    rule_ids = [v.rule_id for v in visitor.violations]
    assert "BLOCKING_SLEEP" in rule_ids

def test_architecture_boundary_clean_code_passes():
    code = """
import logging
from backend.utils import fast_loads, fast_dumps
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger("minikick.services.clean")

class CleanService(QObject):
    data_ready = Signal(dict)

    def process(self, raw: str):
        logger.info("Processing payload cleanly")
        data = fast_loads(raw)
        self.data_ready.emit(data)
"""
    lines = code.splitlines()
    tree = ast.parse(code)
    visitor = ArchitectureASTVisitor("backend/services/chat/clean_service.py", lines)
    visitor.visit(tree)

    assert len(visitor.violations) == 0

def test_file_placement_rule_definitions():
    assert "backend/workers" in FOLDER_PURITY_RULES
    assert "*_worker.py" in FOLDER_PURITY_RULES["backend/workers"]
    assert REVERSE_PLACEMENT_RULES["*_worker.py"] == "backend/workers"

    assert "backend/controllers" in FOLDER_PURITY_RULES
    assert "*_controller.py" in FOLDER_PURITY_RULES["backend/controllers"]
    assert REVERSE_PLACEMENT_RULES["*_controller.py"] == "backend/controllers"

    bad_worker_file = "worker_utils.py"
    allowed_in_workers = FOLDER_PURITY_RULES["backend/workers"]
    matches_allowed = any(fnmatch.fnmatch(bad_worker_file, pat) for pat in allowed_in_workers)
    assert not matches_allowed, "worker_utils.py no debe considerarse un worker válido en backend/workers"

def test_current_codebase_is_100_percent_architecture_and_placement_compliant():
    arch_violations = audit_architecture_boundaries()
    assert len(arch_violations) == 0, f"Violaciones de arquitectura encontradas: {arch_violations}"

    placement_violations = audit_file_placements()
    assert len(placement_violations) == 0, f"Violaciones de ubicación encontradas: {placement_violations}"
