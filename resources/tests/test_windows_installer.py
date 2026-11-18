# resources\tests\test_windows_installer.py
"""Pruebas del instalador de Windows (ruta del instalador por entorno)."""

from unittest import mock


def test_installer_path_is_passed_by_env_not_interpolated_in_command():
    from backend.services.updates.updater_service import WindowsInstaller

    hostile = r"C:\Temp\evil & calc.exe\MiniKick-Setup.exe"
    with mock.patch("backend.services.updates.updater_service.subprocess.Popen") as popen:
        WindowsInstaller().install_and_restart(hostile)

    args, kwargs = popen.call_args
    assert hostile not in args[0]
    assert kwargs["env"]["MINIKICK_INSTALLER"] == hostile


def test_installer_runs_silent_with_relaunch_and_log():
    from backend.services.updates.updater_service import WindowsInstaller

    with mock.patch("backend.services.updates.updater_service.subprocess.Popen") as popen:
        WindowsInstaller().install_and_restart(r"C:\Temp\minikick_update.exe")

    args, kwargs = popen.call_args
    for flag in ("/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/relaunch=1"):
        assert flag in args[0]
    assert kwargs["env"]["MINIKICK_SETUP_LOG"].endswith("minikick_setup.log")
