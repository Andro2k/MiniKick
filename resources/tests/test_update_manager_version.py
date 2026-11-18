# resources\tests\test_update_manager_version.py
"""Pruebas de la comparación numérica de versiones del actualizador."""

from unittest import mock

import pytest

from backend.services.updates.updater_service import UpdateManager


def _check(latest: str, current: str):
    checker = mock.Mock()
    checker.get_latest_version_info.return_value = {"version": latest, "download_url": "u"}
    manager = UpdateManager(current, checker, mock.Mock(), mock.Mock())
    return manager.check_for_updates()


@pytest.mark.parametrize(
    ("latest", "current"),
    [("v1.6.10", "v1.6.9"), ("v1.7.0", "v1.6.9"), ("v1.6.9", "1.6.8"), ("v2.0", "v1.9.9")],
)
def test_newer_version_is_detected(latest, current):
    assert _check(latest, current) is not None


@pytest.mark.parametrize(
    ("latest", "current"),
    [("v1.6.9", "v1.6.10"), ("v1.6.8", "v1.6.8"), ("v1.6", "v1.6.0"), ("latest", "v1.6.8")],
)
def test_same_or_older_version_is_ignored(latest, current):
    assert _check(latest, current) is None
