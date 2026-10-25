# resources\tests\test_architecture_boundaries.py

import ast
import importlib
import os
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _find_repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "backend").is_dir() and (candidate / "frontend").is_dir():
            return candidate
    raise RuntimeError("No se encontró la raíz del repositorio (carpeta con backend/ y frontend/)")

REPO_ROOT = _find_repo_root()
class BackendDoesNotImportFrontendTest(unittest.TestCase):
    def test_no_frontend_imports_anywhere_in_backend(self) -> None:
        offenders = []
        files = sorted((REPO_ROOT / "backend").rglob("*.py"))
        self.assertGreater(len(files), 20, "el test no está escaneando backend/ (¿ruta incorrecta?)")
        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module or ""]
                else:
                    continue
                if any(n == "frontend" or n.startswith("frontend.") for n in names):
                    offenders.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{node.lineno}")
        self.assertEqual(offenders, [], "backend/ no debe importar frontend/: " + ", ".join(offenders))

class ResourcePathTest(unittest.TestCase):
    def test_single_implementation_shared_by_all_layers(self) -> None:
        from backend.utils.paths import resource_path
        import frontend.common as common
        from backend.services.overlay import overlay_routes
        self.assertIs(common.resource_path, resource_path)
        self.assertIs(overlay_routes.get_resource_path, resource_path)

    def test_points_to_the_project_regardless_of_working_directory(self) -> None:
        from backend.utils.paths import resource_path
        expected = os.path.join(str(REPO_ROOT), "assets")
        self.assertTrue(os.path.isdir(expected))
        previous = os.getcwd()
        with tempfile.TemporaryDirectory() as other_dir:
            try:
                os.chdir(other_dir)
                self.assertEqual(os.path.normcase(resource_path("assets")), os.path.normcase(expected))
            finally:
                os.chdir(previous)

class MainWindowMoveTest(unittest.TestCase):
    def test_main_window_lives_in_frontend(self) -> None:
        module = importlib.import_module("frontend.main_window")
        self.assertTrue(hasattr(module, "MainWindowCore"))
        backend_core = importlib.import_module("backend.core")
        self.assertFalse(hasattr(backend_core, "MainWindowCore"))
        self.assertFalse((REPO_ROOT / "backend" / "core" / "main_window_core.py").exists())
        self.assertTrue((REPO_ROOT / "frontend" / "main_window.py").is_file())

    def test_updater_controller_has_no_presentation_code(self) -> None:
        from backend.controllers.updater_controller import UpdaterController
        self.assertFalse(hasattr(UpdaterController, "show_update_dialog"))

class PiperDialogDelegationTest(unittest.TestCase):
    def test_handler_delegates_dialog_to_the_view(self) -> None:
        from PySide6.QtCore import QObject
        from backend.handlers.tts_handler import TTSVoiceHandler
        controller = QObject()
        view, service = mock.MagicMock(), mock.MagicMock()
        handler = TTSVoiceHandler(controller, view, service, None, mock.MagicMock())
        handler.load_voices = mock.MagicMock()
        with mock.patch("backend.services.chat.PiperVoiceManager") as manager_cls, \
                mock.patch("backend.services.chat.PiperVoiceDownloadWorker") as worker_cls:
            handler.open_piper_voices_dialog()
        args, kwargs = view.show_piper_voices_dialog.call_args
        self.assertEqual(args, (service, manager_cls.return_value, worker_cls))
        kwargs["on_voices_updated"]()
        handler.load_voices.assert_called_once_with("piper")

    def test_handler_without_view_does_nothing(self) -> None:
        from PySide6.QtCore import QObject
        from backend.handlers.tts_handler import TTSVoiceHandler
        controller = QObject()
        handler = TTSVoiceHandler(controller, None, mock.MagicMock(), None, mock.MagicMock())
        with mock.patch("backend.services.chat.PiperVoiceManager"), mock.patch("backend.services.chat.PiperVoiceDownloadWorker"):
            handler.open_piper_voices_dialog()

    def test_view_builds_and_runs_the_dialog(self) -> None:
        from frontend.views.chat_view import ChatView
        fake_view = types.SimpleNamespace(i18n="I18N")
        callback = mock.MagicMock()
        with mock.patch("frontend.dialogs.PiperVoicesDialog") as dialog_cls:
            ChatView.show_piper_voices_dialog(fake_view, "svc", "mgr", "worker", on_voices_updated=callback)
        dialog_cls.assert_called_once_with("I18N", "svc", parent=fake_view, manager="mgr", worker_class="worker")
        dialog = dialog_cls.return_value
        dialog.voices_updated.connect.assert_called_once_with(callback)
        dialog.exec.assert_called_once_with()

class UpdateFlowTest(unittest.TestCase):
    def _controller(self):
        from PySide6.QtCore import QObject, Signal

        class FakeController(QObject):
            update_found = Signal(object)
            no_update = Signal()
            error = Signal(str)
            download_progress = Signal(int)
            download_finished = Signal(bool)

        controller = FakeController()
        controller.start_update_check = mock.MagicMock()
        controller.start_download = mock.MagicMock()
        controller.install_update = mock.MagicMock()
        return controller

    def test_dialog_is_driven_by_controller_signals(self) -> None:
        from frontend.dialogs.update_flow import present_update_dialog
        controller = self._controller()
        restart = mock.MagicMock()
        with mock.patch("frontend.dialogs.update_flow.UpdateDialog") as dialog_cls:
            dialog = dialog_cls.return_value

            def fake_exec():
                controller.update_found.emit({"download_url": "http://x/y.exe", "version": "9.9.9"})
                dialog.show_update_available.assert_called_once_with("9.9.9")
                dialog.download_requested.connect.call_args[0][0]()
                controller.start_download.assert_called_once_with("http://x/y.exe")
                dialog.show_downloading.assert_called_once_with()
                controller.download_finished.emit(True)
                dialog.show_complete.assert_called_once_with()
                dialog.restart_requested.connect.call_args[0][0]()
                dialog.accept.assert_called_once_with()
                controller.install_update.assert_called_once_with()
                restart.assert_called_once_with()

            dialog.exec.side_effect = fake_exec
            present_update_dialog(controller, None, "I18N", on_restart_callback=restart)

        controller.start_update_check.assert_called_once_with()
        dialog.exec.assert_called_once_with()

if __name__ == "__main__":
    unittest.main()
