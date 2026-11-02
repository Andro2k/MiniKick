# resources\tests\test_obs_banner_rows.py

from resources.tests.test_chat_voice_rows import _icon_labels, _roles
from backend.services.system import TranslationService
from frontend.components.alerts.overlay_card import AlertsOverlayCard
from frontend.components.chat.overlay_settings import ChatOverlaySettingsPanel
from frontend.views.rewards_view import RewardsView
from frontend.widgets import SettingRow


def _assert_clean_banner(rows: list[SettingRow], expected: int) -> None:
    assert len(rows) == expected
    for row in rows:
        assert not _icon_labels(row)
        assert {"setting_title", "caption"} <= set(_roles(row).values())


def test_alerts_overlay_banner_is_clean(qapp):
    card = AlertsOverlayCard("http://localhost/alerts", TranslationService(default_lang="es"))
    _assert_clean_banner(card.findChildren(SettingRow), 1)


def test_chat_overlay_banner_is_clean(qapp):
    panel = ChatOverlaySettingsPanel(TranslationService(default_lang="es"))
    _assert_clean_banner([panel.row_copy_obs], 1)


def test_rewards_obs_banner_is_clean(qapp):
    view = RewardsView(TranslationService(default_lang="es"))
    _assert_clean_banner(view.findChildren(SettingRow), 1)
