# resources\tests\test_chat_voice_rows.py

from PySide6.QtWidgets import QLabel, QSlider, QWidget

from backend.services.system import TranslationService
from frontend.components.chat.tts_settings import ChatTtsSettingsPanel, PlatformToggleItem, VoiceSettingRow
from frontend.widgets import SearchableComboBox, SettingRow, SliderRow


def _inside_control(label: QLabel) -> bool:
    parent = label.parentWidget()
    while parent is not None:
        if isinstance(parent, SearchableComboBox):
            return True
        parent = parent.parentWidget()
    return False


def _icon_labels(widget: QWidget) -> list[QLabel]:
    return [
        lbl for lbl in widget.findChildren(QLabel)
        if lbl.pixmap() is not None and not lbl.pixmap().isNull() and not _inside_control(lbl)
    ]


def _roles(widget: QWidget) -> dict[str, str]:
    return {lbl.text(): lbl.property("role") for lbl in widget.findChildren(QLabel) if lbl.text()}


def test_setting_row_minimal_has_no_icon_and_uses_clean_roles(qapp):
    row = SettingRow.minimal("Título", "Descripción", QWidget())
    assert not _icon_labels(row)
    assert _roles(row) == {"Título": "setting_title", "Descripción": "caption"}


def test_slider_row_minimal_has_no_icon_and_uses_clean_roles(qapp):
    value = QLabel("50%")
    value.setProperty("role", "monospace")
    row = SliderRow.minimal("Volumen", "Ajusta el volumen", QSlider(), value)
    assert not _icon_labels(row)
    roles = _roles(row)
    assert roles["Volumen"] == "setting_title" and roles["Ajusta el volumen"] == "caption"


def test_slider_row_default_roles_are_backward_compatible(qapp):
    row = SliderRow("", "T", "D", QSlider(), QLabel("1"))
    assert _roles(row)["T"] == "h3" and _roles(row)["D"] == "body"


def test_chat_voice_panel_rows_have_no_icons_and_use_hierarchy(qapp):
    panel = ChatTtsSettingsPanel(TranslationService(default_lang="es"))

    rows = panel.findChildren(SettingRow) + panel.findChildren(SliderRow) + panel.findChildren(VoiceSettingRow)
    assert len(panel.findChildren(SettingRow)) == 4
    assert len(panel.findChildren(SliderRow)) == 2
    assert len(panel.findChildren(VoiceSettingRow)) == 6

    for row in rows:
        assert not _icon_labels(row), f"{type(row).__name__} aún muestra un ícono"
        assert "setting_title" in _roles(row).values()
        assert "h3" not in _roles(row).values()

    for row in panel.findChildren(SettingRow) + panel.findChildren(SliderRow):
        assert "caption" in _roles(row).values()


def test_platform_toggles_keep_their_brand_icons(qapp):
    panel = ChatTtsSettingsPanel(TranslationService(default_lang="es"))
    items = panel.findChildren(PlatformToggleItem)
    assert len(items) == 4
    assert all(_icon_labels(item) for item in items)
