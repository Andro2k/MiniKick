# frontend\dialogs\timer_dialog.py

import threading
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QSpinBox, QWidget, QScrollArea, QFrame, QCheckBox, QListWidgetItem)
from PySide6.QtCore import Qt, QSize, QTimer, QPoint
from PySide6.QtGui import QColor
from .base_dialog import ModernWizardPanel, ModernModal
from frontend.widgets import ModernButton, ModernSwitch, VariableTextEdit, UnifiedSearchBar
from frontend.components.schedule.quick_change_panel import CategorySuggestionsPopup
from frontend.common.theme import COLOR_RED, COLOR_GREEN
from frontend.common import get_icon_colored, get_assets_path

class TimerConfigWizard(ModernWizardPanel):
    def __init__(self, i18n, parent=None, existing_config=None):
        self.i18n = i18n
        title_steps = [self.i18n.get("timer.dialog.title"), self.i18n.get("timer.dialog.title")]
        subtitle_steps = [self.i18n.get("timer.dialog.subtitle"), self.i18n.get("timer.dialog.categories_desc")]
        super().__init__(title_steps=title_steps, subtitle_steps=subtitle_steps, i18n=i18n, width=750, parent=parent)        
        self.existing_config = existing_config
        self.timer_id = existing_config.get("id") if existing_config else None
        self.message_rows = []       
        
        self._icon_edit = get_icon_colored("edit.svg", COLOR_GREEN, 14)
        self._icon_trash = get_icon_colored("trash.svg", COLOR_RED, 14)
        
        self._setup_ui()
        if self.existing_config:
            self._load_existing()
        else:
            self._add_message_field()            
        self.start_wizard()

    def _setup_ui(self):
        self.tab_basic = QWidget()
        basic_main_layout = QHBoxLayout(self.tab_basic)
        basic_main_layout.setContentsMargins(0, 0, 0, 0)
        basic_main_layout.setSpacing(20)

        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        lbl_name = QLabel(self.i18n.get("timer.dialog.name_label"))
        lbl_name.setProperty("role", "h3")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText(self.i18n.get("timer.dialog.name_placeholder"))
        self.txt_name.textChanged.connect(self._update_btn_next_state)
        left_layout.addWidget(lbl_name)
        left_layout.addWidget(self.txt_name)

        lbl_platforms = QLabel(self.i18n.get("timer.dialog.platforms_label"))
        lbl_platforms.setProperty("role", "h3")
        left_layout.addWidget(lbl_platforms)

        platforms_row = QWidget()
        platforms_layout = QHBoxLayout(platforms_row)
        platforms_layout.setContentsMargins(0, 0, 0, 0)
        platforms_layout.setSpacing(16)

        kick_box = QHBoxLayout()
        lbl_kick = QLabel(self.i18n.get("spam.card.platform_kick"))
        lbl_kick.setProperty("role", "body")
        self.switch_kick = ModernSwitch()
        self.switch_kick.setChecked(True)
        self.switch_kick.toggled.connect(self._update_btn_next_state)
        kick_box.addWidget(lbl_kick)
        kick_box.addWidget(self.switch_kick)

        twitch_box = QHBoxLayout()
        lbl_twitch = QLabel(self.i18n.get("spam.card.platform_twitch"))
        lbl_twitch.setProperty("role", "body")
        self.switch_twitch = ModernSwitch()
        self.switch_twitch.setChecked(True)
        self.switch_twitch.toggled.connect(self._update_btn_next_state)
        twitch_box.addWidget(lbl_twitch)
        twitch_box.addWidget(self.switch_twitch)

        platforms_layout.addLayout(kick_box)
        platforms_layout.addLayout(twitch_box)
        platforms_layout.addStretch()
        left_layout.addWidget(platforms_row)

        lbl_response = QLabel(self.i18n.get("timer.dialog.response_label"))
        lbl_response.setProperty("role", "h3")
        left_layout.addWidget(lbl_response)

        self.scroll_messages = QScrollArea()
        self.scroll_messages.setWidgetResizable(True)
        self.scroll_messages.setMinimumHeight(150)
        self.scroll_messages.setFrameShape(QFrame.Shape.NoFrame)
        
        self.scroll_messages_content = QWidget()
        self.messages_layout = QVBoxLayout(self.scroll_messages_content)
        self.messages_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        
        self.scroll_messages.setWidget(self.scroll_messages_content)
        left_layout.addWidget(self.scroll_messages)

        self.btn_add_msg = ModernButton(self.i18n.get("timer.dialog.btn_add_message"), role="action_accent_border")
        self.btn_add_msg.clicked.connect(lambda: self._add_message_field())
        left_layout.addWidget(self.btn_add_msg)

        basic_main_layout.addWidget(left_col, stretch=1)

        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(14)

        self.chk_online = QCheckBox(self.i18n.get("timer.dialog.online_interval_label"))
        self.chk_online.setChecked(True)
        self.spin_online = QSpinBox()
        self.spin_online.setRange(1, 120)
        self.spin_online.setValue(5)
        self.spin_online.setSuffix(" min")
        self.spin_online.setFixedHeight(34)
        self.chk_online.toggled.connect(self.spin_online.setEnabled)
        self.chk_online.toggled.connect(self._update_btn_next_state)
        right_layout.addWidget(self.chk_online)
        right_layout.addWidget(self.spin_online)

        self.chk_offline = QCheckBox(self.i18n.get("timer.dialog.offline_interval_label"))
        self.chk_offline.setChecked(True)
        self.spin_offline = QSpinBox()
        self.spin_offline.setRange(1, 480)
        self.spin_offline.setValue(30)
        self.spin_offline.setSuffix(" min")
        self.spin_offline.setFixedHeight(34)
        self.chk_offline.toggled.connect(self.spin_offline.setEnabled)
        self.chk_offline.toggled.connect(self._update_btn_next_state)
        right_layout.addWidget(self.chk_offline)
        right_layout.addWidget(self.spin_offline)

        self.chk_lines = QCheckBox(self.i18n.get("timer.dialog.chat_lines_label"))
        self.chk_lines.setChecked(True)
        self.spin_lines = QSpinBox()
        self.spin_lines.setRange(0, 500)
        self.spin_lines.setValue(5)
        self.spin_lines.setSuffix(" líneas")
        self.spin_lines.setFixedHeight(34)
        self.chk_lines.toggled.connect(self.spin_lines.setEnabled)
        right_layout.addWidget(self.chk_lines)
        right_layout.addWidget(self.spin_lines)
        
        lbl_lines_desc = QLabel(self.i18n.get("timer.dialog.chat_lines_desc"))
        lbl_lines_desc.setProperty("role", "caption")
        lbl_lines_desc.setWordWrap(True)
        right_layout.addWidget(lbl_lines_desc)

        right_layout.addStretch()
        basic_main_layout.addWidget(right_col, stretch=1)

        self.tab_filters = QWidget()
        filters_main_layout = QHBoxLayout(self.tab_filters)
        filters_main_layout.setContentsMargins(0, 0, 0, 0)
        filters_main_layout.setSpacing(20)

        left_filt_col = QWidget()
        left_filt_layout = QVBoxLayout(left_filt_col)
        left_filt_layout.setContentsMargins(0, 0, 0, 0)
        left_filt_layout.setSpacing(12)

        lbl_keywords = QLabel(self.i18n.get("timer.dialog.keywords_label"))
        lbl_keywords.setProperty("role", "h3")
        self.txt_keywords = QLineEdit()
        self.txt_keywords.setPlaceholderText(self.i18n.get("timer.dialog.keywords_placeholder"))
        left_filt_layout.addWidget(lbl_keywords)
        left_filt_layout.addWidget(self.txt_keywords)
        
        lbl_keywords_desc = QLabel(self.i18n.get("timer.dialog.keywords_desc"))
        lbl_keywords_desc.setProperty("role", "caption")
        lbl_keywords_desc.setWordWrap(True)
        left_filt_layout.addWidget(lbl_keywords_desc)

        lbl_categories = QLabel(self.i18n.get("timer.dialog.categories_label"))
        lbl_categories.setProperty("role", "h3")
        left_filt_layout.addWidget(lbl_categories)

        self.search_category = UnifiedSearchBar(
            placeholder=self.i18n.get("stream_info.quick_change.category_placeholder"),
            parent=self
        )
        left_filt_layout.addWidget(self.search_category)

        self.popup_suggestions = CategorySuggestionsPopup(self.search_category, parent=self)
        self.popup_suggestions.category_selected.connect(self._on_category_selected)

        self._cached_subcategories = []
        self._category_search_timer = QTimer(self)
        self._category_search_timer.setSingleShot(True)
        self._category_search_timer.setInterval(350)
        self._category_search_timer.timeout.connect(self._on_category_search_timeout)
        self.search_category.textChanged.connect(self._on_category_search_text_changed)
        self.search_category.returnPressed.connect(self._on_category_search_return_pressed)

        self.txt_categories = QLineEdit()
        self.txt_categories.setPlaceholderText(self.i18n.get("timer.dialog.categories_placeholder"))
        left_filt_layout.addWidget(self.txt_categories)
        
        lbl_cat_desc = QLabel(self.i18n.get("timer.dialog.categories_desc"))
        lbl_cat_desc.setProperty("role", "caption")
        lbl_cat_desc.setWordWrap(True)
        left_filt_layout.addWidget(lbl_cat_desc)
        left_filt_layout.addStretch()

        filters_main_layout.addWidget(left_filt_col, stretch=1)

        right_filt_col = QFrame()
        right_filt_col.setProperty("role", "card")
        right_filt_layout = QVBoxLayout(right_filt_col)
        right_filt_layout.setContentsMargins(12, 12, 12, 12)
        
        lbl_help_title = QLabel(self.i18n.get("timer.dialog.title"))
        lbl_help_title.setProperty("role", "h3")
        lbl_help_desc = QLabel(self.i18n.get("timer.dialog.help_desc"))
        lbl_help_desc.setWordWrap(True)
        lbl_help_desc.setProperty("role", "body")
        
        right_filt_layout.addWidget(lbl_help_title)
        right_filt_layout.addWidget(lbl_help_desc)
        right_filt_layout.addStretch()
        
        filters_main_layout.addWidget(right_filt_col, stretch=1)

        self.add_page(self.tab_basic)
        self.add_page(self.tab_filters)

    def _on_category_search_text_changed(self, text: str):
        if len(text.strip()) >= 2:
            self._category_search_timer.start()
        else:
            self._category_search_timer.stop()
            if hasattr(self, 'popup_suggestions'):
                self.popup_suggestions.hide()

    def _on_category_search_return_pressed(self):
        text = self.search_category.text().strip()
        if text:
            current_cats = [c.strip() for c in self.txt_categories.text().split(",") if c.strip()]
            if text not in current_cats:
                current_cats.append(text)
            self.txt_categories.setText(", ".join(current_cats))
            self.search_category.clear()
            if hasattr(self, 'popup_suggestions'):
                self.popup_suggestions.hide()

    def _on_category_search_timeout(self):
        query = self.search_category.text().strip()
        if len(query) < 2:
            return
        
        if self._cached_subcategories:
            q_lower = query.lower()
            filtered = [
                item for item in self._cached_subcategories
                if q_lower in item.get("name", "").lower()
            ]
            self._display_category_results(filtered)
            return

        def _search_worker():
            results = []
            try:
                from backend.providers.chat.kick_client import ScraperFactory
                s = ScraperFactory.create()
                resp = s.get("https://kick.com/api/v1/subcategories", params={"page": 1, "limit": 100}, timeout=5)
                if resp.status_code == 200:
                    res_data = resp.json()
                    items = res_data.get("data", []) if isinstance(res_data, dict) else res_data
                    if isinstance(items, list):
                        all_subcats = []
                        for item in items:
                            if isinstance(item, dict) and item.get("name"):
                                all_subcats.append({
                                    "platform": "kick",
                                    "id": item.get("id"),
                                    "name": item.get("name", "")
                                })
                        self._cached_subcategories = all_subcats
                        q_lower = query.lower()
                        results = [cat for cat in all_subcats if q_lower in cat.get("name", "").lower()]
            except Exception:
                pass
            
            QTimer.singleShot(0, lambda: self._display_category_results(results))

        threading.Thread(target=_search_worker, daemon=True).start()

    def _display_category_results(self, results: list[dict]):
        if hasattr(self, 'popup_suggestions') and self.search_category.isVisible():
            self.popup_suggestions.clear()
            if not results:
                self.popup_suggestions.hide()
                return
            for item in results[:8]:
                plat = item.get("platform", "kick")
                name = item.get("name", "")
                list_item = QListWidgetItem(f"[{plat.upper()}] {name}")
                list_item.setData(Qt.ItemDataRole.UserRole, item)
                self.popup_suggestions.addItem(list_item)
            
            global_pos = self.search_category.mapToGlobal(QPoint(0, self.search_category.height() + 2))
            self.popup_suggestions.move(global_pos)
            self.popup_suggestions.setFixedWidth(max(self.search_category.width(), 240))
            item_count = min(len(results), 8)
            self.popup_suggestions.setFixedHeight(item_count * 34 + 8)
            self.popup_suggestions.show()

    def _on_category_selected(self, data: dict):
        cat_name = data.get("name", "")
        if cat_name:
            current_cats = [c.strip() for c in self.txt_categories.text().split(",") if c.strip()]
            if cat_name not in current_cats:
                current_cats.append(cat_name)
            self.txt_categories.setText(", ".join(current_cats))
            self.search_category.clear()

    def hideEvent(self, event):
        super().hideEvent(event)
        if hasattr(self, 'popup_suggestions'):
            self.popup_suggestions.hide()

    def _add_message_field(self, text=""):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        
        txt = QLineEdit()
        txt.setPlaceholderText(self.i18n.get("timer.dialog.response_placeholder"))
        txt.setText(text)
        txt.textChanged.connect(self._update_btn_next_state)
        row_layout.addWidget(txt)
        
        btn_edit = ModernButton("", role="action_accent_border")
        btn_edit.setFixedSize(26, 26)
        btn_edit.setIcon(self._icon_edit)
        btn_edit.setIconSize(QSize(14, 14))
        btn_edit.clicked.connect(lambda checked=False, line_edit=txt: self._open_message_editor(line_edit))
        row_layout.addWidget(btn_edit)
        
        btn_del = ModernButton("", role="action_danger_border")
        btn_del.setFixedSize(26, 26)
        btn_del.setIcon(self._icon_trash)
        btn_del.setIconSize(QSize(14, 14))
        btn_del.clicked.connect(lambda: self._remove_message_row(row))
        row_layout.addWidget(btn_del)
        
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, row)
        self.message_rows.append((row, txt))

    def _remove_message_row(self, row_widget):
        if len(self.message_rows) <= 1:
            return
        for item in list(self.message_rows):
            if item[0] == row_widget:
                self.message_rows.remove(item)
                self.messages_layout.removeWidget(row_widget)
                row_widget.deleteLater()
                break
        self._update_btn_next_state()

    def _open_message_editor(self, line_edit: QLineEdit):
        dialog = MessageEditorDialog(line_edit.text(), self.i18n, parent=self)
        if dialog.exec():
            line_edit.setText(dialog.get_text())

    def validate_step(self, step_index: int) -> bool:
        if step_index == 0:
            if not self.txt_name.text().strip():
                return False
            if not self.switch_kick.isChecked() and not self.switch_twitch.isChecked():
                return False
            messages = [txt.text().strip() for row, txt in self.message_rows if txt.text().strip()]
            if not messages:
                return False
            if any(len(m) > 492 for m in messages):
                return False
            if not self.chk_online.isChecked() and not self.chk_offline.isChecked():
                return False
        return True

    def _load_existing(self):
        self.txt_name.setText(self.existing_config.get("name", ""))
        self.switch_kick.setChecked(self.existing_config.get("apply_kick", True))
        self.switch_twitch.setChecked(self.existing_config.get("apply_twitch", True))
        
        messages = self.existing_config.get("messages", [])
        if not messages:
            self._add_message_field()
        else:
            for m in messages:
                self._add_message_field(m)
            
        online_min = self.existing_config.get("interval_online")
        has_online = online_min is not None and online_min > 0
        self.chk_online.setChecked(has_online)
        if has_online:
            self.spin_online.setValue(online_min)
        else:
            self.spin_online.setEnabled(False)

        offline_min = self.existing_config.get("interval_offline")
        has_offline = offline_min is not None and offline_min > 0
        self.chk_offline.setChecked(has_offline)
        if has_offline:
            self.spin_offline.setValue(offline_min)
        else:
            self.spin_offline.setEnabled(False)

        lines = self.existing_config.get("chat_lines", 0)
        has_lines = lines is not None and lines > 0
        self.chk_lines.setChecked(has_lines)
        if has_lines:
            self.spin_lines.setValue(lines)
        else:
            self.spin_lines.setEnabled(False)

        keywords = self.existing_config.get("keywords", [])
        self.txt_keywords.setText(", ".join(keywords))
        
        categories = self.existing_config.get("categories", [])
        self.txt_categories.setText(", ".join(categories))

    def get_timer_data(self):
        messages = [txt.text().strip() for row, txt in self.message_rows if txt.text().strip()]
        keywords = [kw.strip() for kw in self.txt_keywords.text().split(",") if kw.strip()]
        categories = [cat.strip() for cat in self.txt_categories.text().split(",") if cat.strip()]
        
        interval_online = self.spin_online.value() if self.chk_online.isChecked() else None
        interval_offline = self.spin_offline.value() if self.chk_offline.isChecked() else None
        chat_lines = self.spin_lines.value() if self.chk_lines.isChecked() else 0
        
        is_active = self.existing_config.get("is_active", True) if self.existing_config else True

        return {
            "timer_id": self.timer_id,
            "name": self.txt_name.text().strip(),
            "messages": messages,
            "is_active": is_active,
            "interval_online": interval_online,
            "interval_offline": interval_offline,
            "chat_lines": chat_lines,
            "keywords": keywords,
            "categories": categories,
            "apply_kick": self.switch_kick.isChecked(),
            "apply_twitch": self.switch_twitch.isChecked()
        }

    def _update_step_ui(self):
        super()._update_step_ui()
        self._update_btn_next_state()

    def _update_btn_next_state(self):
        self.btn_next.setEnabled(self.validate_step(self.current_step))
        if self.current_step == 0:
            for row, txt in self.message_rows:
                is_invalid = len(txt.text().strip()) > 492
                txt.setProperty("state", "error" if is_invalid else "normal")
                txt.style().unpolish(txt)
                txt.style().polish(txt)


class MessageEditorDialog(ModernModal):
    def __init__(self, current_text: str, i18n, parent=None):
        super().__init__(
            title=i18n.get("timer.dialog.editor_title"),
            icon_path=get_assets_path("icons/clock.svg"),
            icon_bg_color=COLOR_GREEN,
            width=500,
            parent=parent
        )
        self.i18n = i18n
        self.set_dialog_state("accent", QColor(46, 205, 112, 60))
        
        self.text_edit = VariableTextEdit()
        self.text_edit.setPlaceholderText(self.i18n.get("timer.dialog.response_placeholder"))
        self.text_edit.setPlainText(current_text)
        self.text_edit.setMinimumHeight(150)
        self.text_edit.setAcceptRichText(False)
        self.content_layout.addWidget(self.text_edit)
        
        btn_cancel = ModernButton(self.i18n.get("common.buttons.cancel"), role="action_outlined")
        btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = ModernButton(self.i18n.get("common.buttons.save"), role="action_accent")
        self.btn_save.clicked.connect(self.accept)
        
        self.add_action_buttons(btn_cancel, self.btn_save)
        
        self.text_edit.textChanged.connect(self._validate_text_length)
        self._validate_text_length()
        
    def _validate_text_length(self):
        text = self.text_edit.toPlainText()
        is_invalid = len(text) > 492
        self.text_edit.setProperty("state", "error" if is_invalid else "normal")
        self.text_edit.style().unpolish(self.text_edit)
        self.text_edit.style().polish(self.text_edit)
        self.btn_save.setEnabled(not is_invalid)
        
    def get_text(self) -> str:
        return self.text_edit.toPlainText().replace("\n", " ").strip()
