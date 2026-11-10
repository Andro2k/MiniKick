# resources\\tests\\test_windows_installer.py

from unittest import mock


def test_installer_path_is_passed_by_env_not_interpolated_in_command():
    from backend.services.system.updater_service import WindowsInstaller

    hostile = r"C:\Temp\evil & calc.exe\MiniKick-Setup.exe"
    with mock.patch("backend.services.system.updater_service.subprocess.Popen") as popen:
        WindowsInstaller().install_and_restart(hostile)

    args, kwargs = popen.call_args
    assert hostile not in args[0]
    assert kwargs["env"]["MINIKICK_INSTALLER"] == hostile
