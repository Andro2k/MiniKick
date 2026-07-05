# frontend\widgets\log_controls_component.py

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QLineEdit, QComboBox,
    QBoxLayout, QVBoxLayout, QSizePolicy,
)
from PySide6.QtCore import Signal
from frontend.widgets.controls_component import ModernButton
from frontend.common.utils import get_icon_colored
from frontend.common.theme import COLOR_TEXT_PRIMARY

class LogControlsPanel(QFrame):
    search_changed = Signal(str)
    filter_changed = Signal(str)
    folder_requested = Signal()
    load_requested = Signal()
    live_requested = Signal()
    clear_requested = Signal()
    report_requested = Signal()
    view_toggle_requested = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setProperty("role", "card")
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        self._search = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._search.setSpacing(6)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(self.i18n.get("log.controls.search_placeholder"))
        self.txt_search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.txt_search.textChanged.connect(self.search_changed.emit)

        self.combo_filter = QComboBox()
        self.combo_filter.addItems([
            self.i18n.get("log.controls.filter_all"),
            "INFO", "DEBUG", "WARNING", "ERROR",
        ])
        self.combo_filter.setMinimumWidth(110)
        self.combo_filter.currentTextChanged.connect(self.filter_changed.emit)

        self._search.addWidget(self.txt_search, 1)
        self._search.addWidget(self.combo_filter)
        root.addLayout(self._search)

        self._actions = QGridLayout()
        self._actions.setSpacing(6)
        root.addLayout(self._actions)

        specs = [
            ("btn_open_folder", self.i18n.get("log.controls.btn_folder"), "action_neutral_border",
             "folder-open.svg", COLOR_TEXT_PRIMARY, self.folder_requested.emit, True),
            ("btn_load_file", self.i18n.get("log.controls.btn_load"), "action_neutral_border",
             "file-text.svg", COLOR_TEXT_PRIMARY, self.load_requested.emit, True),
            ("btn_toggle_view", self.i18n.get("log.controls.btn_show_logs"), "action_neutral_border",
             "eye.svg", COLOR_TEXT_PRIMARY, self.view_toggle_requested.emit, True),
            ("btn_live", self.i18n.get("log.controls.btn_live"), "action_neutral_border",
             "play.svg", COLOR_TEXT_PRIMARY, self.live_requested.emit, False),
            ("btn_clear", self.i18n.get("log.controls.btn_clear"), "action_neutral_border",
             "trash.svg", COLOR_TEXT_PRIMARY, self.clear_requested.emit, True),
            ("btn_report", self.i18n.get("log.controls.btn_report"), "action_neutral_border",
             "help.svg", COLOR_TEXT_PRIMARY, self.report_requested.emit, True),
        ]

        self._buttons: list[ModernButton] = []
        for name, text, role, icon, color, slot, visible in specs:
            btn = ModernButton(text, role=role)
            btn.setParent(self)
            btn.setIcon(get_icon_colored(icon, color, 16))
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(slot)
            btn.setVisible(visible)
            setattr(self, name, btn)
            self._buttons.append(btn)
            if name == "btn_open_folder":
                btn.setToolTip(self.i18n.get("log.controls.tooltip_folder"))

        self._reflow_buttons()

    def minimumSizeHint(self) -> QSize:
        return QSize(100, 50)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow_buttons()

    def _reflow_buttons(self):
        width = max(self.width(), 320)
        visible = [b for b in self._buttons if not b.isHidden()]
        cols = max(1, min(len(visible), width // 120))

        while self._actions.count() > 0:
            self._actions.takeAt(0)

        for c in range(cols):
            self._actions.setColumnStretch(c, 1)

        for i, btn in enumerate(visible):
            self._actions.addWidget(btn, i // cols, i % cols)

    def set_historical_mode(self, is_historical: bool):
        self.btn_live.setVisible(is_historical)
        self.btn_toggle_view.setVisible(not is_historical)
        self.btn_clear.setEnabled(not is_historical)
        self._reflow_buttons()

    def set_streaming_controls_enabled(self, enabled: bool):
        self.txt_search.setEnabled(enabled)
        self.combo_filter.setEnabled(enabled)
        if not self.btn_live.isVisible():
            self.btn_clear.setEnabled(enabled)

    def set_view_toggle_state(self, logs_visible: bool):
        key = "log.controls.btn_hide_logs" if logs_visible else "log.controls.btn_show_logs"
        self.btn_toggle_view.setText(self.i18n.get(key))
        self.set_streaming_controls_enabled(logs_visible)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._search.setDirection(
            QBoxLayout.Direction.TopToBottom if self.width() < 480
            else QBoxLayout.Direction.LeftToRight
        )
        self._reflow_buttons()
