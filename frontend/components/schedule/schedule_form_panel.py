# frontend\components\schedule\schedule_form_panel.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QCalendarWidget)
from PySide6.QtGui import QTextCharFormat, QColor
from PySide6.QtCore import Qt, Signal, QTime, QDate, QTimer
from frontend.widgets import ModernCard, ModernButton, ModernSwitch, UnifiedSearchBar, NoWheelDateEdit, NoWheelTimeEdit
from frontend.components.schedule.quick_change_panel import CategorySuggestionsPopup
from frontend.common.theme import COLOR_NEUTRAL_200

class ScheduleFormPanel(QWidget):
    schedule_saved = Signal(object)
    form_cleared = Signal()
    search_category_requested = Signal(str, str)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.editing_schedule_id = None
        self._kick_cat_id = None
        self._twitch_cat_id = None

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        card = ModernCard(parent=self, margin=14, spacing=12)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        self.lbl_title = QLabel(self.i18n.get("stream_info.schedule_dialog.title_new"))
        self.lbl_title.setProperty("role", "h2")
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        card.addLayout(header_layout)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)

        lbl_name = QLabel(self.i18n.get("stream_info.schedule_dialog.name_label"))
        lbl_name.setProperty("role", "h3")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText(self.i18n.get("stream_info.schedule_dialog.name_placeholder"))
        form_layout.addWidget(lbl_name)
        form_layout.addWidget(self.txt_name)

        lbl_plat = QLabel(self.i18n.get("stream_info.schedule_dialog.platform_label"))
        lbl_plat.setProperty("role", "h3")
        form_layout.addWidget(lbl_plat)

        switches_row = QHBoxLayout()
        switches_row.setSpacing(24)

        kick_switch_box = QHBoxLayout()
        kick_switch_box.setSpacing(8)
        self.switch_kick = ModernSwitch()
        self.switch_kick.setChecked(True)
        lbl_kick = QLabel("Kick")
        lbl_kick.setProperty("role", "body")
        kick_switch_box.addWidget(self.switch_kick)
        kick_switch_box.addWidget(lbl_kick)
        switches_row.addLayout(kick_switch_box)

        twitch_switch_box = QHBoxLayout()
        twitch_switch_box.setSpacing(8)
        self.switch_twitch = ModernSwitch()
        self.switch_twitch.setChecked(True)
        lbl_twitch = QLabel("Twitch")
        lbl_twitch.setProperty("role", "body")
        twitch_switch_box.addWidget(self.switch_twitch)
        twitch_switch_box.addWidget(lbl_twitch)
        switches_row.addLayout(twitch_switch_box)
        switches_row.addStretch()

        form_layout.addLayout(switches_row)

        datetime_row = QHBoxLayout()
        datetime_row.setSpacing(16)

        date_box = QVBoxLayout()
        date_box.setSpacing(6)
        lbl_date = QLabel(self.i18n.get("stream_info.schedule_dialog.date_label"))
        lbl_date.setProperty("role", "h3")
        self.date_edit = NoWheelDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setFixedWidth(160)
        
        cal = self.date_edit.calendarWidget()
        if cal:
            cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
            cal.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
            neutral_fmt = QTextCharFormat()
            neutral_fmt.setForeground(QColor(COLOR_NEUTRAL_200))
            cal.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, neutral_fmt)
            cal.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, neutral_fmt)
            cal.setHeaderTextFormat(neutral_fmt)

        date_box.addWidget(lbl_date)
        date_box.addWidget(self.date_edit)
        datetime_row.addLayout(date_box)

        time_box = QVBoxLayout()
        time_box.setSpacing(6)
        lbl_time = QLabel(self.i18n.get("stream_info.schedule_dialog.time_label"))
        lbl_time.setProperty("role", "h3")
        self.time_edit = NoWheelTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setFixedWidth(150)
        time_box.addWidget(lbl_time)
        time_box.addWidget(self.time_edit)
        datetime_row.addLayout(time_box)
        datetime_row.addStretch()

        form_layout.addLayout(datetime_row)

        lbl_stream_title = QLabel(self.i18n.get("stream_info.schedule_dialog.stream_title_label"))
        lbl_stream_title.setProperty("role", "h3")
        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText(self.i18n.get("stream_info.schedule_dialog.stream_title_placeholder"))
        form_layout.addWidget(lbl_stream_title)
        form_layout.addWidget(self.txt_title)

        lbl_cat_kick = QLabel(self.i18n.get("stream_info.schedule_dialog.kick_category_label"))
        lbl_cat_kick.setProperty("role", "h3")
        self.search_kick_cat = UnifiedSearchBar(
            placeholder=self.i18n.get("stream_info.schedule_dialog.category_placeholder"),
            parent=self
        )
        form_layout.addWidget(lbl_cat_kick)
        form_layout.addWidget(self.search_kick_cat)

        self.popup_kick = CategorySuggestionsPopup(self.search_kick_cat, parent=self)
        self.popup_kick.category_selected.connect(self._on_kick_cat_selected)

        self.search_kick_timer = QTimer(self)
        self.search_kick_timer.setSingleShot(True)
        self.search_kick_timer.setInterval(400)
        self.search_kick_timer.timeout.connect(lambda: self._trigger_category_search("kick", self.search_kick_cat.text()))
        self.search_kick_cat.txt_input.textChanged.connect(self._on_kick_cat_text_changed)

        lbl_cat_twitch = QLabel(self.i18n.get("stream_info.schedule_dialog.twitch_category_label"))
        lbl_cat_twitch.setProperty("role", "h3")
        self.search_twitch_cat = UnifiedSearchBar(
            placeholder=self.i18n.get("stream_info.schedule_dialog.category_placeholder"),
            parent=self
        )
        form_layout.addWidget(lbl_cat_twitch)
        form_layout.addWidget(self.search_twitch_cat)

        self.popup_twitch = CategorySuggestionsPopup(self.search_twitch_cat, parent=self)
        self.popup_twitch.category_selected.connect(self._on_twitch_cat_selected)

        self.search_twitch_timer = QTimer(self)
        self.search_twitch_timer.setSingleShot(True)
        self.search_twitch_timer.setInterval(400)
        self.search_twitch_timer.timeout.connect(lambda: self._trigger_category_search("twitch", self.search_twitch_cat.text()))
        self.search_twitch_cat.txt_input.textChanged.connect(self._on_twitch_cat_text_changed)

        form_layout.addSpacing(6)
        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.btn_clear = QPushButton(self.i18n.get("stream_info.schedule_dialog.btn_clear"))
        self.btn_clear.setProperty("role", "action_outlined")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_form)

        self.btn_save = ModernButton(self.i18n.get("stream_info.schedule_dialog.btn_save"), role="action_accent")
        self.btn_save.clicked.connect(self._on_save)

        action_row.addWidget(self.btn_clear)
        action_row.addStretch()
        action_row.addWidget(self.btn_save)
        form_layout.addLayout(action_row)

        card.addLayout(form_layout)
        main_layout.addWidget(card)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.popup_kick.hide()
        self.popup_twitch.hide()

    def _get_target_platform(self) -> str:
        kick_on = self.switch_kick.isChecked()
        twitch_on = self.switch_twitch.isChecked()
        if kick_on and twitch_on:
            return "all"
        elif kick_on:
            return "kick"
        elif twitch_on:
            return "twitch"
        return "all"

    def _set_target_platform(self, platform_str: str):
        if platform_str == "kick":
            self.switch_kick.setChecked(True)
            self.switch_twitch.setChecked(False)
        elif platform_str == "twitch":
            self.switch_kick.setChecked(False)
            self.switch_twitch.setChecked(True)
        else:
            self.switch_kick.setChecked(True)
            self.switch_twitch.setChecked(True)

    def _on_kick_cat_text_changed(self, text: str):
        if len(text.strip()) >= 2:
            self.search_kick_timer.start()
        else:
            self.search_kick_timer.stop()
            self.popup_kick.hide()

    def _on_twitch_cat_text_changed(self, text: str):
        if len(text.strip()) >= 2:
            self.search_twitch_timer.start()
        else:
            self.search_twitch_timer.stop()
            self.popup_twitch.hide()

    def _trigger_category_search(self, platform: str, query: str):
        if query.strip():
            self.search_category_requested.emit(query.strip(), platform)

    def set_category_search_results(self, platform: str, results: list[dict]):
        if platform == "kick" and self.search_kick_cat.txt_input.hasFocus() and len(self.search_kick_cat.text().strip()) >= 2:
            self.popup_kick.show_results(platform, results)
        elif platform == "twitch" and self.search_twitch_cat.txt_input.hasFocus() and len(self.search_twitch_cat.text().strip()) >= 2:
            self.popup_twitch.show_results(platform, results)

    def _on_kick_cat_selected(self, data: dict):
        self.search_kick_timer.stop()
        name = data.get("name", "")
        self.search_kick_cat.txt_input.blockSignals(True)
        self.search_kick_cat.setText(name)
        self.search_kick_cat.txt_input.blockSignals(False)
        self.search_kick_cat.setFocus()
        self._kick_cat_id = data.get("id")
        self.popup_kick.hide()

    def _on_twitch_cat_selected(self, data: dict):
        self.search_twitch_timer.stop()
        name = data.get("name", "")
        self.search_twitch_cat.txt_input.blockSignals(True)
        self.search_twitch_cat.setText(name)
        self.search_twitch_cat.txt_input.blockSignals(False)
        self.search_twitch_cat.setFocus()
        self._twitch_cat_id = data.get("id")
        self.popup_twitch.hide()

    def load_schedule(self, schedule_data: dict):
        self.search_kick_timer.stop()
        self.search_twitch_timer.stop()
        self.popup_kick.hide()
        self.popup_twitch.hide()

        self.editing_schedule_id = schedule_data.get("id")
        self.lbl_title.setText(self.i18n.get("stream_info.schedule_dialog.title_edit"))

        self.txt_name.setText(schedule_data.get("name", ""))
        self._set_target_platform(schedule_data.get("target_platform", "all"))
        
        date_str = schedule_data.get("date_str", "")
        if date_str:
            qdate = QDate.fromString(date_str, "yyyy-MM-dd")
            if qdate.isValid():
                self.date_edit.setDate(qdate)

        time_str = schedule_data.get("time_str", "18:00")
        parts = time_str.split(":")
        if len(parts) == 2:
            try:
                self.time_edit.setTime(QTime(int(parts[0]), int(parts[1])))
            except ValueError:
                pass

        self.txt_title.setText(schedule_data.get("title", ""))

        self.search_kick_cat.txt_input.blockSignals(True)
        self.search_twitch_cat.txt_input.blockSignals(True)
        self.search_kick_cat.setText(schedule_data.get("kick_category_name", ""))
        self.search_twitch_cat.setText(schedule_data.get("twitch_category_name", ""))
        self.search_kick_cat.txt_input.blockSignals(False)
        self.search_twitch_cat.txt_input.blockSignals(False)

        self._kick_cat_id = schedule_data.get("kick_category_id")
        self._twitch_cat_id = schedule_data.get("twitch_category_id")

    def clear_form(self):
        self.search_kick_timer.stop()
        self.search_twitch_timer.stop()
        self.popup_kick.hide()
        self.popup_twitch.hide()

        self.editing_schedule_id = None
        self._kick_cat_id = None
        self._twitch_cat_id = None
        self.lbl_title.setText(self.i18n.get("stream_info.schedule_dialog.title_new"))
        self.txt_name.clear()
        self._set_target_platform("all")
        self.date_edit.setDate(QDate.currentDate())
        self.time_edit.setTime(QTime.currentTime())
        self.txt_title.clear()

        self.search_kick_cat.txt_input.blockSignals(True)
        self.search_twitch_cat.txt_input.blockSignals(True)
        self.search_kick_cat.clear()
        self.search_twitch_cat.clear()
        self.search_kick_cat.txt_input.blockSignals(False)
        self.search_twitch_cat.txt_input.blockSignals(False)

        self.form_cleared.emit()

    def _on_save(self):
        name = self.txt_name.text().strip()
        if not name:
            self.txt_name.setFocus()
            return

        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        time_str = self.time_edit.time().toString("HH:mm")
        title = self.txt_title.text().strip()
        kick_cat = self.search_kick_cat.text().strip()
        twitch_cat = self.search_twitch_cat.text().strip()

        data = {
            "name": name,
            "date_str": date_str,
            "time_str": time_str,
            "target_platform": self._get_target_platform(),
            "title": title,
            "kick_category_id": self._kick_cat_id,
            "kick_category_name": kick_cat,
            "twitch_category_id": self._twitch_cat_id,
            "twitch_category_name": twitch_cat,
            "is_active": True
        }
        if self.editing_schedule_id is not None:
            data["id"] = self.editing_schedule_id

        self.schedule_saved.emit(data)
        self.clear_form()
