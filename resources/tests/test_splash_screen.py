# resources\tests\test_splash_screen.py

import pytest
from PySide6.QtWidgets import QApplication, QWidget
from backend.services.system.translation_service import TranslationService
from frontend.dialogs.splash_screen import SplashScreen


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

def test_splash_screen_initialization(qapp):
    i18n = TranslationService()
    splash = SplashScreen(i18n=i18n, app_version="1.6.2")

    assert splash.lbl_title.text() == i18n.get("splash.title")
    assert splash.lbl_subtitle.text() == i18n.get("splash.subtitle")
    assert splash.lbl_version.text() == "v1.6.2"
    assert splash.progress_bar.value() == 0
    assert splash.progress_bar.property("role") == "splash_progress"
    assert splash.card.property("role") == "splash_card"
    assert splash.lbl_status.text() == i18n.get("splash.loading")

    splash.close()

def test_splash_screen_progress_and_clamping(qapp):
    i18n = TranslationService()
    splash = SplashScreen(i18n=i18n, app_version="1.6.2")

    msg = i18n.get("splash.init_services")
    splash.set_progress(55, msg)
    assert splash.progress_bar.value() == 55
    assert splash.lbl_status.text() == msg

    splash.set_progress(-10, "Negative")
    assert splash.progress_bar.value() == 0

    splash.set_progress(150, "Overflow")
    assert splash.progress_bar.value() == 100

    splash.close()

def test_splash_screen_finish_lifecycle(qapp):
    i18n = TranslationService()
    splash = SplashScreen(i18n=i18n, app_version="1.6.2")
    dummy_win = QWidget()

    assert not dummy_win.isVisible()
    splash.finish(dummy_win)

    assert dummy_win.isVisible()
    dummy_win.deleteLater()
