# resources\tests\test_linux_auth_and_toast.py

from unittest.mock import MagicMock, patch
import pytest
from PySide6.QtWidgets import QApplication
from backend.services.system.translation_service import TranslationService
from backend.controllers.dashboard_controller import DashboardController
from frontend.views.dashboard_view import DashboardView
from frontend.navigation.toast_component import ModernToast
from backend.services.system.browser_service import BrowserService


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

def test_dashboard_view_update_connection_status_keyword_args(qapp):
    i18n = TranslationService()
    view = DashboardView(i18n=i18n)

    view.update_connection_status(is_connecting=False, has_error=True, error_msg="Connection timed out on Linux")

    view.update_connection_status(is_connecting=True)

    view.deleteLater()

def test_dashboard_controller_handle_error_state(qapp):
    i18n = TranslationService()
    mock_view = MagicMock()

    controller = DashboardController(
        view=mock_view,
        avatar_service=None,
        i18n=i18n
    )

    controller.handle_error_state("OAuth timeout occurred")

    mock_view.update_connection_status.assert_called_once_with(
        is_connecting=False,
        has_error=True,
        error_msg="OAuth timeout occurred"
    )

def test_modern_toast_dynamic_geometry_scaling(qapp):
    toast_empty = ModernToast("Titulo", "", "info")
    assert toast_empty.height() == 58

    toast_short = ModernToast("Guardado", "Cambios aplicados con éxito.", "success")
    assert 65 <= toast_short.height() <= 90

    long_msg = "Ya hay una autenticación en curso en tu navegador. Por favor completa o cierra esa ventana antes de iniciar otra."
    toast_long = ModernToast("Autenticación en curso", long_msg, "warning")
    assert toast_long.height() >= 100, f"Expected height >= 100 to avoid clipping, got {toast_long.height()}"

    toast_empty.update_content("Autenticación en curso", long_msg, "warning")
    assert toast_empty.height() >= 100

    toast_empty.deleteLater()
    toast_short.deleteLater()
    toast_long.deleteLater()

def test_browser_service_resilient_launcher():
    assert not BrowserService._open_default("")

    with patch("sys.platform", "linux"):
        with patch("PySide6.QtGui.QDesktopServices.openUrl", return_value=False):
            with patch("shutil.which", return_value="/usr/bin/xdg-open"):
                with patch("subprocess.Popen") as mock_popen:
                    result = BrowserService._open_default("http://127.0.0.1:8080/auth")
                    assert result is True
                    mock_popen.assert_called_once()
                    call_args, call_kwargs = mock_popen.call_args
                    assert call_args[0] == ["/usr/bin/xdg-open", "http://127.0.0.1:8080/auth"]
                    assert call_kwargs.get("start_new_session") is True
