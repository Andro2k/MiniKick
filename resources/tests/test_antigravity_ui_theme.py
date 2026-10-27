# resources\tests\test_antigravity_ui_theme.py

from PySide6.QtWidgets import QLabel, QPushButton
from frontend.common import GLOBAL_QSS, get_global_qss, Palette
from frontend.widgets import SectionHeader, SettingRow, ModernCard, ModernDivider
from frontend.views.settings_view import SettingsView
from frontend.navigation import Sidebar
from backend.services.system import TranslationService


def test_global_qss_contains_antigravity_tokens():
    qss = get_global_qss(13)
    assert 'role="section_header"' in qss
    assert 'role="action_danger_solid"' in qss
    assert 'role="card"' in qss
    assert 'role="nav_button"' in qss
    assert Palette.NEUTRAL_950 in qss
    assert Palette.NEUTRAL_950 in qss

def test_section_header_and_setting_row(qapp):
    header = SectionHeader("Test Section")
    assert header.lbl.text() == "Test Section"
    assert header.lbl.property("role") == "section_header"
    header.setText("Updated Section")
    assert header.lbl.text() == "Updated Section"

    dummy_btn = QPushButton("Click")
    row = SettingRow(
        icon_name="globe-filled.svg",
        title_text="Language",
        desc_text="Select your preferred language",
        right_widget=dummy_btn
    )
    assert row.lbl_desc.text() == "Select your preferred language"
    row.set_description("New description")
    assert row.lbl_desc.text() == "New description"

def test_modern_card_separators(qapp):
    card = ModernCard()
    assert card.property("role") == "card"

    widget1 = QLabel("Widget 1")
    widget2 = QLabel("Widget 2")
    card.addWidget(widget1)
    card.add_separator()
    card.addWidget(widget2)

    assert card.card_layout.count() == 3

def test_settings_view_antigravity_structure(qapp):
    i18n = TranslationService(default_lang="es")
    view = SettingsView(i18n=i18n)

    assert hasattr(view, "btn_kick_integration")
    assert hasattr(view, "combo_lang")
    assert hasattr(view, "combo_font")
    assert hasattr(view, "combo_browser")

    view.set_integrations_status(kick_connected=True, kick_channel="TestStreamer")
    assert view.btn_kick_integration.property("role") == "action_danger_solid"

    view.set_integrations_status(kick_connected=False)
    assert view.btn_kick_integration.property("role") == "action_outlined"

def test_sidebar_antigravity_nav_tabs(qapp):
    i18n = TranslationService(default_lang="es")
    sidebar = Sidebar(i18n=i18n, app_version="1.6.0")

    sidebar.add_tab("Dashboard", "element-filled.svg", is_active=True, position="top")
    sidebar.add_tab("Settings", "gear-filled.svg", is_active=False, position="bottom")

    assert len(sidebar.nav_buttons) == 2
    btn_dash = sidebar.nav_buttons[0]
    btn_settings = sidebar.nav_buttons[1]

    assert btn_dash.isChecked() is True
    assert btn_settings.isChecked() is False
    assert btn_dash.property("role") == "nav_button"

def test_theme_tokens_clean_and_complete():
    import re
    import inspect
    from frontend.common import theme, Size
    for m in (Size.Margin.SEC_HDR, Size.Margin.MRG_HXS, Size.Margin.MRG_MED, Size.Margin.MRG_XXS, Size.Margin.SEC_BDG):
        assert isinstance(m, tuple)
        assert len(m) == 4
        assert all(isinstance(v, int) for v in m)

    builder_funcs = [
        theme._build_button_qss,
        theme._build_input_qss,
        theme._build_surface_qss,
        theme._build_complex_qss,
    ]
    hex_pattern = re.compile(r'#[0-9a-fA-F]{3,8}\b')
    for fn in builder_funcs:
        source = inspect.getsource(fn)
        matches = hex_pattern.findall(source)
        assert len(matches) == 0, f"Raw hex codes found in {fn.__name__}: {matches}"

def test_dashboard_view_profile_cards_and_margins(qapp):
    from frontend.views.dashboard_view import DashboardView
    from frontend.common import Size
    for m in (Size.Margin.MRG_LRG, Size.Margin.MRG_LRG):
        assert isinstance(m, tuple)
        assert len(m) == 4
        assert all(isinstance(v, int) for v in m)

    i18n = TranslationService(default_lang="es")
    view = DashboardView(i18n=i18n)

    assert hasattr(view, "welcome_card")
    assert hasattr(view, "distribution_panel")
    assert hasattr(view, "channel_badges_container")
    assert len(view.channel_badge_cards) == 4
    assert view.channel_badges_container.parentWidget() is view.scroll_content
    assert hasattr(view, "card_kick")
    assert hasattr(view, "card_twitch")
    assert hasattr(view, "card_youtube")
    assert hasattr(view, "card_tiktok")

    margins = view.distribution_panel.layout().contentsMargins()
    assert (margins.left(), margins.top(), margins.right(), margins.bottom()) == Size.Margin.MRG_MED

def test_chat_view_and_subpanels_antigravity_standard(qapp):
    from frontend.views.chat_view import ChatView
    from frontend.common import Size

    i18n = TranslationService(default_lang="es")
    chat_view = ChatView(i18n=i18n)

    assert chat_view.body_layout.spacing() == Size.SPACING_MD
    assert chat_view.tts_settings_panel.property("role") == "tab_panel"
    assert chat_view.bot_panel.property("role") == "tab_panel"
    assert chat_view.overlay_settings_panel.property("role") == "tab_panel"

    assert hasattr(chat_view.tts_settings_panel, "chk_tts")
    assert hasattr(chat_view.tts_settings_panel, "combo_provider")
    assert hasattr(chat_view.bot_panel, "sw_cmd_mute")
    assert hasattr(chat_view.bot_panel, "sw_cmd_block")
    assert hasattr(chat_view.overlay_settings_panel, "mockup_widget")

    margins = chat_view.tts_settings_panel.panel_layout.contentsMargins()
    assert margins.left() == margins.right() == 8

    from frontend.widgets import SectionHeader
    header_first = SectionHeader("Test", first=True)
    header_regular = SectionHeader("Test", first=False)
    assert header_first.layout().contentsMargins().top() == 0
    assert header_regular.layout().contentsMargins().top() == 12

def test_expandable_card_unification_and_seamless_dividers(qapp):
    from frontend.widgets import ExpandableCard, ExpandableSettingCard, ModernDivider
    from frontend.components.widgets import WidgetCard
    from frontend.views.widgets_view import WidgetsView
    from frontend.components.chat.spam_panel import ChatSpamPanel
    from frontend.common import Size

    card = ExpandableCard("Title", "Description", "star-filled.svg")
    assert isinstance(card.divider, ModernDivider)
    assert card.body_widget.isHidden()
    assert card.divider.isHidden()
    assert card.switch is card.switch_enable

    card.toggle_expand()
    assert not card.body_widget.isHidden()
    assert not card.divider.isHidden()

    card.toggle_expand()
    assert card.body_widget.isHidden()
    assert card.divider.isHidden()

    i18n = TranslationService(default_lang="es")
    widget_card = WidgetCard("shoutout", "Shoutout", "Desc", "star-filled.svg", i18n)
    assert isinstance(widget_card, ExpandableCard)
    assert isinstance(widget_card.divider, ModernDivider)
    assert widget_card.divider.isHidden()

    widget_card.toggle_expand()
    assert not widget_card.body_widget.isHidden()
    assert not widget_card.divider.isHidden()

    spam_card = ExpandableSettingCard("caps_protection", "Caps", "Desc", "star-filled.svg", i18n=i18n)
    assert isinstance(spam_card, ExpandableCard)
    assert isinstance(spam_card.divider, ModernDivider)

    spam_card.toggle_expand()
    assert not spam_card.body_widget.isHidden()
    assert not spam_card.divider.isHidden()

    w_view = WidgetsView(i18n)
    assert w_view.body_layout.spacing() == Size.SPACING_MD
    assert w_view.columns_layout.spacing() == Size.SPACING_MD

    s_panel = ChatSpamPanel(i18n)
    assert s_panel.panel_layout.spacing() == Size.SPACING_MD

def test_music_view_and_subpanels_antigravity_standard(qapp):
    from frontend.views.music_view import MusicView
    from frontend.components.music import MusicStatsPanel, MusicPlayerSettingsPanel, MusicCommandsPanel, MusicSettingsPanel
    from frontend.common import Size
    from frontend.widgets import ModernDivider

    i18n = TranslationService(default_lang="es")
    music_view = MusicView(i18n)

    assert music_view.body_layout.spacing() == Size.SPACING_MD
    assert music_view.columns_layout.spacing() == Size.SPACING_MD
    assert music_view.stats_panel.stats_grid.spacing() == Size.SPACING_MD

    for panel in (music_view.player_panel, music_view.commands_panel, music_view.settings_panel):
        assert panel.property("role") == "tab_panel"
        m = panel.panel_layout.contentsMargins()
        assert (m.left(), m.top(), m.right(), m.bottom()) == Size.Margin.MRG_MED
        assert panel.panel_layout.spacing() == Size.SPACING_MD

    cmd_dividers = [music_view.commands_panel.card_cmds.card_layout.itemAt(i).widget()
                    for i in range(music_view.commands_panel.card_cmds.card_layout.count())
                    if isinstance(music_view.commands_panel.card_cmds.card_layout.itemAt(i).widget(), ModernDivider)]
    assert len(cmd_dividers) == 6

    setting_dividers = [music_view.settings_panel.card_settings.card_layout.itemAt(i).widget()
                        for i in range(music_view.settings_panel.card_settings.card_layout.count())
                        if isinstance(music_view.settings_panel.card_settings.card_layout.itemAt(i).widget(), ModernDivider)]
    assert len(setting_dividers) == 5

def test_alerts_view_and_expandable_cards_standard(qapp):
    from frontend.views.alerts_view import AlertsView
    from frontend.components.alerts.event_card import AlertEventCard
    from frontend.widgets import ExpandableCard, ModernDivider
    from frontend.common import Size

    i18n = TranslationService(default_lang="es")
    alerts_view = AlertsView(i18n)

    m_overlay = alerts_view.overlay_card.card_layout.contentsMargins()
    assert (m_overlay.left(), m_overlay.top(), m_overlay.right(), m_overlay.bottom()) == Size.Margin.MRG_MED

    m_banner = alerts_view.notice_banner.card_layout.contentsMargins()
    assert (m_banner.left(), m_banner.top(), m_banner.right(), m_banner.bottom()) == Size.Margin.MRG_MED

    card = alerts_view._get_or_create_card("twitch", "follow")
    assert isinstance(card, AlertEventCard)

    for section_card in (card.card_general, card.card_design, card.card_typography, card.card_media):
        assert isinstance(section_card, ExpandableCard)
        assert isinstance(section_card.divider, ModernDivider)

    assert card.card_general.is_expanded() is True
    assert card.card_design.is_expanded() is False
    assert card.card_typography.is_expanded() is True
    assert card.card_media.is_expanded() is False
    assert card.body_box.spacing() == Size.SPACING_MD

    card.card_design.toggle_expand()
    assert card.card_design.is_expanded() is True
    assert not card.card_design.body_widget.isHidden()
    assert not card.card_design.divider.isHidden()

    card.card_design.toggle_expand()
    assert card.card_design.is_expanded() is False
    assert card.card_design.body_widget.isHidden()
    assert card.card_design.divider.isHidden()

    assert card.btn_discard.text() == ""
    assert bool(card.btn_discard.toolTip()) is True
    assert card.btn_duplicate.text() == ""
    assert bool(card.btn_duplicate.toolTip()) is True
    assert card.btn_test.text() == "Probar"
    assert card.btn_save.text() == "Guardar"

    m_prev = card.w_preview.card_layout.contentsMargins()
    assert (m_prev.left(), m_prev.top(), m_prev.right(), m_prev.bottom()) == (0, 0, 0, 0)

    assert not alerts_view.overlay_card.btn_copy_url.isHidden()
    assert alerts_view.overlay_card.edit_overlay_url.isHidden()
    assert alerts_view.overlay_card.btn_open_browser.isHidden()

def test_schedule_view_and_subpanels_antigravity_standard(qapp):
    from frontend.views.schedule_view import ScheduleView
    from frontend.common import Size

    i18n = TranslationService(default_lang="es")
    schedule_view = ScheduleView(i18n)

    assert schedule_view.body_layout.spacing() == Size.SPACING_MD
    assert schedule_view.columns_layout.spacing() == Size.SPACING_MD

    qc = schedule_view.quick_change_panel
    assert qc.property("role") == "tab_panel"
    m_qc = qc.layout().contentsMargins()
    assert (m_qc.left(), m_qc.top(), m_qc.right(), m_qc.bottom()) == Size.Margin.MRG_MED
    assert qc.layout().spacing() == Size.SPACING_MD
    m_kick = qc.kick_card.card_layout.contentsMargins()
    assert (m_kick.left(), m_kick.top(), m_kick.right(), m_kick.bottom()) == Size.Margin.MRG_MED
    m_twitch = qc.twitch_card.card_layout.contentsMargins()
    assert (m_twitch.left(), m_twitch.top(), m_twitch.right(), m_twitch.bottom()) == Size.Margin.MRG_MED

    form = schedule_view.schedule_form_panel
    assert form.property("role") == "tab_panel"
    m_form = form.layout().contentsMargins()
    assert (m_form.left(), m_form.top(), m_form.right(), m_form.bottom()) == Size.Margin.MRG_MED
    assert form.layout().spacing() == Size.SPACING_MD

def test_table_cards_and_edge_to_edge_alignment(qapp):
    from PySide6.QtWidgets import QTableWidget
    from frontend.widgets import ModernTableCard, ModernDivider
    from frontend.views.commands_view import CommandView
    from frontend.views.rewards_view import RewardsView
    from frontend.views.timers_view import TimersView
    from frontend.views.logs_view import LogView

    i18n = TranslationService(default_lang="es")

    card = ModernTableCard(
        title_text="Test",
        headers=["A", "B"],
        search_placeholder="Search",
        add_button_text="Add"
    )
    assert card.table.selectionBehavior() == QTableWidget.SelectionBehavior.SelectRows
    assert card.table.selectionMode() == QTableWidget.SelectionMode.SingleSelection
    assert "QTableWidget::item:hover:!selected" not in GLOBAL_QSS
    assert f"QTableWidget::item:selected {{ background-color: {Palette.NEUTRAL_750};" in GLOBAL_QSS

    m = card.card_layout.contentsMargins()
    assert (m.left(), m.top(), m.right(), m.bottom()) == (0, 0, 0, 0)
    assert card.card_layout.spacing() == 0
    assert isinstance(card.divider, ModernDivider)

    cmd_view = CommandView(i18n)
    m_cmd = cmd_view.table_card.card_layout.contentsMargins()
    assert (m_cmd.left(), m_cmd.top(), m_cmd.right(), m_cmd.bottom()) == (0, 0, 0, 0)

    rew_view = RewardsView(i18n)
    m_rew = rew_view.table_card.card_layout.contentsMargins()
    assert (m_rew.left(), m_rew.top(), m_rew.right(), m_rew.bottom()) == (0, 0, 0, 0)

    tmr_view = TimersView(i18n)
    m_tmr = tmr_view.table_card.card_layout.contentsMargins()
    assert (m_tmr.left(), m_tmr.top(), m_tmr.right(), m_tmr.bottom()) == (0, 0, 0, 0)

    log_view = LogView(i18n)
    m_log = log_view.table_page.layout().contentsMargins()
    assert (m_log.left(), m_log.top(), m_log.right(), m_log.bottom()) == (0, 0, 0, 0)

def test_combobox_and_segmented_action_outlined_style(qapp):
    from frontend.common.theme import GLOBAL_QSS, Semantic, Borders
    assert f"QComboBox                           {{ background-color: {Semantic.NEUTRAL_900};" in GLOBAL_QSS
    assert f"border: {Borders.BRD_BASE};" in GLOBAL_QSS
    assert f"QComboBox:hover                     {{ background-color: {Semantic.NEUTRAL_750}; border: {Borders.BRD_HOVR};" in GLOBAL_QSS
    assert f'QFrame[role="segmented_control"] {{ background-color: {Semantic.NEUTRAL_950}; border: 1px solid {Semantic.NEUTRAL_700};' in GLOBAL_QSS
    assert f'QPushButton[role="segmented_item"]:checked {{ background-color: {Semantic.NEUTRAL_900}; border: 1px solid {Semantic.NEUTRAL_700};' in GLOBAL_QSS
    assert f'QFrame[role="segmented_pagination"] {{ background-color: {Semantic.NEUTRAL_900}; border: 1px solid {Semantic.NEUTRAL_700};' in GLOBAL_QSS

def test_dark_palette_and_popup_translucency_standards(qapp):
    from PySide6.QtGui import QPalette
    from PySide6.QtCore import Qt
    from frontend.common import create_dark_palette, GLOBAL_QSS, Palette
    from frontend.widgets import SearchableComboBox, VariableTextEdit, NoWheelDateEdit
    from frontend.widgets.category_search import CategorySuggestionsPopup

    pal = create_dark_palette()
    assert isinstance(pal, QPalette)
    assert pal.color(QPalette.ColorRole.Window).name().lower() == Palette.NEUTRAL_950.lower()
    assert pal.color(QPalette.ColorRole.Base).name().lower() == Palette.NEUTRAL_900.lower()
    assert pal.color(QPalette.ColorRole.WindowText).name().lower() == Palette.NEUTRAL_050.lower()

    combo = SearchableComboBox()
    assert combo._popup.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is True
    assert combo._popup.bg_frame.property("role") == "searchable_combo_popup"
    assert f'QFrame[role="searchable_combo_popup"] {{ background-color: {Palette.NEUTRAL_900};' in GLOBAL_QSS

    text_edit = VariableTextEdit()
    assert text_edit.popup_window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is True
    assert text_edit.popup.property("role") == "variable_autocomplete_popup"

    cat_popup = CategorySuggestionsPopup(combo)
    assert cat_popup.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is True

    assert 'QWidget#qt_datetimedit_calendar' in GLOBAL_QSS
    assert 'QListWidget[role="variable_autocomplete_popup"]' in GLOBAL_QSS
    assert 'QMenu' in GLOBAL_QSS
    assert 'QToolTip' in GLOBAL_QSS

    date_edit = NoWheelDateEdit()
    date_edit.setCalendarPopup(True)
    cal = date_edit.calendarWidget()
    assert cal.palette().color(QPalette.ColorRole.Window).name().lower() == Palette.NEUTRAL_950.lower()

def test_piper_voices_dialog_modern_structure_and_catalog(qapp):
    from unittest.mock import MagicMock
    from backend.services.chat.piper_manager import PIPER_VOICE_CATALOG
    from frontend.dialogs.piper_dialog import PiperVoicesDialog
    from frontend.widgets import ModernCard, ExpandableCard

    catalog_ids = set(PIPER_VOICE_CATALOG.keys())
    expected_ids = {
        "es_ES-glados-medium", "es_ES-miro-high",
        "es_MX-alicia-medium", "es_MX-mario-medium",
        "es-xp-medium", "es_MX-santaclosrmc-medium"
    }
    assert expected_ids.issubset(catalog_ids), f"Missing models: {expected_ids - catalog_ids}"

    categories = {v.get("category") for v in PIPER_VOICE_CATALOG.values()}
    assert "natural" in categories
    assert "stream" in categories

    for v in PIPER_VOICE_CATALOG.values():
        assert "id" in v and "name" in v and "lang" in v and "quality" in v
        assert "onnx_url" in v or "archive_url" in v

    mock_i18n = MagicMock()
    mock_i18n.get.side_effect = lambda k, **kwargs: f"[{k}]"
    mock_tts = MagicMock()
    mock_tts.get_synthesis_params.return_value = {"length_scale": 1.0, "noise_scale": 0.667, "noise_w": 0.8}
    mock_tts.piper_manager.is_voice_installed.return_value = False
    mock_tts.piper_manager.get_active_voice.return_value = "es_ES-davefx-medium"

    dialog = PiperVoicesDialog(mock_i18n, mock_tts)

    assert hasattr(dialog, "search_input")
    assert hasattr(dialog, "cat_group")
    assert len(dialog.cat_group.buttons()) == 4
    assert hasattr(dialog, "catalog_card")
    assert isinstance(dialog.catalog_card, ModernCard)
    assert hasattr(dialog, "synthesis_card")
    assert isinstance(dialog.synthesis_card, ExpandableCard)

    dialog._on_tab_toggled("stream", True)
    assert dialog._active_tab == "stream"

    dialog.search_input.setText("glados")
    dialog._apply_filter()

    for item, _ in dialog._item_entries:
        if item.voice_id == "es_ES-glados-medium":
            assert not item.isHidden()
        else:
            assert item.isHidden()

    dialog.search_input.clear()
    dialog._on_tab_toggled("all", True)
    dialog._apply_filter()
    assert dialog._active_tab == "all"

    for item, _ in dialog._item_entries:
        assert hasattr(item, "btn_delete")
        assert hasattr(item, "btn_download")
        assert hasattr(item, "btn_test")
        if item.is_default:
            assert item.btn_delete.isHidden()