from backend.services.system import TranslationService
from frontend.components.alerts.overlay_card import AlertsOverlayCard
from frontend.widgets import SettingRow


def test_overlay_url_copy_button_feedback(qapp):
    i18n = TranslationService(default_lang="es")
    card = AlertsOverlayCard("http://localhost:8090/alerts", i18n)
    assert isinstance(card.btn_copy_url.parentWidget(), SettingRow)
    copy_requests = []
    card.copy_url_requested.connect(lambda: copy_requests.append(True))

    card.btn_copy_url.click()

    assert copy_requests == [True]
    assert card.btn_copy_url.text() == i18n.get("rewards.obs.copied")
    assert not card.btn_copy_url.isEnabled()

    card._reset_copy_button(i18n.get("common.buttons.copy"))

    assert card.btn_copy_url.text() == i18n.get("common.buttons.copy")
    assert card.btn_copy_url.isEnabled()


def test_overlay_url_copy_button_does_nothing_without_url(qapp):
    i18n = TranslationService(default_lang="es")
    card = AlertsOverlayCard("", i18n)
    copy_requests = []
    card.copy_url_requested.connect(lambda: copy_requests.append(True))

    card.btn_copy_url.click()

    assert not copy_requests
    assert card.btn_copy_url.isEnabled()
    assert card.btn_copy_url.text() == i18n.get("common.buttons.copy")
