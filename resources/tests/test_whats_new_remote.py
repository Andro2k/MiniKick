import json
from unittest import mock

from backend.services.system import GithubUpdateProvider
from backend.services.system.whats_new_service import WhatsNewService
from backend.workers.updater_worker import WhatsNewWorker


class _SettingsStorage:
    def __init__(self, state=None):
        self.values = {}
        if state is not None:
            self.values[WhatsNewService.SETTING_STATE] = json.dumps(state)

    def load_string(self, key, default=None):
        return self.values.get(key, default)

    def save_string(self, key, value):
        self.values[key] = value


def test_whats_new_service_uses_cached_highlights_for_matching_version(monkeypatch):
    with mock.patch("pathlib.Path.read_text", side_effect=AssertionError("should not read local docs")):
        service = WhatsNewService(
            _SettingsStorage({
                "version": "1.6.6",
                "modal_seen": False,
                "highlights": [{"title": "Cached", "target_section": "Dashboard"}],
            }),
            app_version="v1.6.6",
        )

    assert service.get_highlights() == [{"title": "Cached", "target_section": "Dashboard"}]


def test_whats_new_service_does_not_use_highlights_cached_for_another_version():
    service = WhatsNewService(
        _SettingsStorage({
            "version": "1.6.5",
            "modal_seen": True,
            "highlights": [{"title": "Old release", "target_section": "Dashboard"}],
        }),
        app_version="v1.6.6",
    )

    assert service.get_highlights() == []
    assert service.should_show_modal()


def test_setting_remote_highlights_resets_seen_state_for_new_version():
    storage = _SettingsStorage({
        "version": "1.6.5",
        "modal_seen": True,
        "seen": ["Dashboard"],
        "highlights": [{"title": "Old release", "target_section": "Dashboard"}],
    })
    service = WhatsNewService(storage, app_version="v1.6.6")
    highlights = [{"title": "New release", "target_section": "Chat"}]

    service.set_highlights(highlights)

    state = json.loads(storage.values[WhatsNewService.SETTING_STATE])
    assert state["version"] == "1.6.6"
    assert state["modal_seen"] is False
    assert state["seen"] == []
    assert service.get_highlights() == highlights


def test_fetch_release_for_version_never_returns_a_different_latest_release():
    provider = GithubUpdateProvider("Andro2k", "MiniKick")
    with (
        mock.patch.object(provider, "fetch_release_by_tag", return_value=None),
        mock.patch.object(
            provider,
            "fetch_latest_release",
            return_value={"tag_name": "v1.6.7", "body": "Other version"},
        ),
    ):
        assert provider.fetch_release_for_version("1.6.6") is None


def test_whats_new_worker_parses_the_requested_github_release(monkeypatch):
    release = {
        "tag_name": "v1.6.6",
        "body": (
            "## Novedades\n"
            "| Sección | Funcionalidad | Descripción |\n"
            "|---|---|---|\n"
            "| Dashboard | Panel nuevo | Muestra datos en vivo |\n"
        ),
    }
    provider = mock.MagicMock()
    provider.fetch_release_for_version.return_value = release
    monkeypatch.setattr(
        "backend.services.system.GithubUpdateProvider",
        lambda *_args, **_kwargs: provider,
    )
    worker = WhatsNewWorker("v1.6.6")
    fetched = []
    worker.highlights_fetched.connect(fetched.append)

    worker.run()

    provider.fetch_release_for_version.assert_called_once_with("v1.6.6")
    assert fetched == [[{
        "icon": "element-filled.svg",
        "title": "Panel nuevo",
        "desc": "Muestra datos en vivo",
        "target_section": "Dashboard",
    }]]


def test_whats_new_presenter_shows_cached_highlights_when_github_fails():
    from frontend.window.whats_new import WhatsNewPresenter

    highlights = [{"title": "Cached release", "target_section": "Dashboard"}]
    service = mock.MagicMock()
    service.should_show_modal.return_value = True
    service.is_first_launch.return_value = False
    service.get_highlights.return_value = highlights
    slot = mock.MagicMock()
    presenter = WhatsNewPresenter(
        parent=mock.MagicMock(),
        service=service,
        sidebar=mock.MagicMock(),
        i18n=mock.MagicMock(),
        app_version="1.6.6",
        slot=slot,
        is_shutting_down=lambda: False,
    )

    presenter.check_dialog()
    slot.start.assert_called_once_with(presenter._create_worker)

    with mock.patch("frontend.window.whats_new.WhatsNewDialog") as dialog_class:
        presenter.on_remote_error("GitHub unavailable")

    dialog_class.assert_called_once()
    service.mark_version_seen.assert_called_once_with()
