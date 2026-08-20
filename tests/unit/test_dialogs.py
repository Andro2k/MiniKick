# tests\unit\test_dialogs.py

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent

from backend.services.system.translation_service import TranslationService
from frontend.dialogs.base_dialog import ModernFramelessShell
from frontend.dialogs.already_running_dialog import AlreadyRunningDialog
from frontend.dialogs.timer_dialog import TimerConfigWizard

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture
def i18n():
    return TranslationService()

def test_modern_frameless_shell_ignores_enter_keys(qapp):
    dialog = ModernFramelessShell(width=400)
    
    event_return = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
    event_enter = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Enter, Qt.KeyboardModifier.NoModifier)
    
    dialog.keyPressEvent(event_return)
    assert not event_return.isAccepted()
    assert dialog.result() == 0

    dialog.keyPressEvent(event_enter)
    assert not event_enter.isAccepted()
    assert dialog.result() == 0

def test_already_running_dialog_instantiation(qapp, i18n):
    dialog = AlreadyRunningDialog(i18n=i18n)
    assert dialog is not None
    assert dialog.title_lbl.text() == i18n.get("dialogs.already_running.title")
    assert dialog.lbl_desc.text() == i18n.get("dialogs.already_running.desc")
    assert hasattr(dialog, "lbl_desc")

def test_timer_config_wizard_category_enter_press(qapp, i18n):
    wizard = TimerConfigWizard(i18n=i18n)
    assert wizard is not None
    assert hasattr(wizard, "search_category")
    assert hasattr(wizard, "txt_categories")
    
    wizard.search_category.setText("Just Chatting")
    wizard._on_category_search_return_pressed()
    
    assert "Just Chatting" in wizard.txt_categories.text()
    assert wizard.search_category.text() == ""
    
    wizard.search_category.setText("Valorant")
    wizard._on_category_search_return_pressed()
    assert "Just Chatting, Valorant" in wizard.txt_categories.text()
