# frontend\components\log\log_controls.py

from PySide6.QtCore import Signal, QSize
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QBoxLayout, QGridLayout, QSizePolicy
)
from frontend.widgets import (
    ModernButton, UnifiedSearchBar, NoWheelComboBox
)
from frontend.common import (
    COLOR_NEUTRAL_400, get_icon_colored
)

class LogControlsPanel(QFrame):
    search_changed = Signal(str)
    filter_changed = Signal(str)
    date_changed = Signal(str)
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

        self.txt_search = UnifiedSearchBar(placeholder=self.i18n.get("log.controls.search_placeholder"))
        self.txt_search.textChanged.connect(self.search_changed.emit)

        self.combo_date = NoWheelComboBox()
        self.combo_date.addItem(self.i18n.get("log.controls.date_all"), "")
        self.combo_date.addItem(self.i18n.get("log.controls.date_1d"), "1d")
        self.combo_date.addItem(self.i18n.get("log.controls.date_3d"), "3d")
        self.combo_date.addItem(self.i18n.get("log.controls.date_7d"), "7d")
        self.combo_date.setMinimumWidth(125)
        self.combo_date.currentIndexChanged.connect(self._on_date_changed)

        self._search.addWidget(self.txt_search, 1)
        self._search.addWidget(self.combo_date)
        root.addLayout(self._search)

        self._actions = QGridLayout()
        self._actions.setSpacing(6)
        root.addLayout(self._actions)

        specs = [
            ("btn_open_folder", self.i18n.get("log.controls.btn_folder"), "action_neutral_border",
             "folder-open.svg", COLOR_NEUTRAL_400, self.folder_requested.emit, True),
            ("btn_load_file", self.i18n.get("log.controls.btn_load"), "action_neutral_border",
             "file-text.svg", COLOR_NEUTRAL_400, self.load_requested.emit, True),
            ("btn_toggle_view", self.i18n.get("log.controls.btn_show_logs"), "action_neutral_border",
             "eye.svg", COLOR_NEUTRAL_400, self.view_toggle_requested.emit, True),
            ("btn_live", self.i18n.get("log.controls.btn_live"), "action_neutral_border",
             "player-play.svg", COLOR_NEUTRAL_400, self.live_requested.emit, False),
            ("btn_clear", self.i18n.get("log.controls.btn_clear"), "action_neutral_border",
             "trash.svg", COLOR_NEUTRAL_400, self.clear_requested.emit, True),
            ("btn_report", self.i18n.get("log.controls.btn_report"), "action_neutral_border",
             "bug.svg", COLOR_NEUTRAL_400, self.report_requested.emit, True),
        ]

        self._buttons: list[ModernButton] = []
        for name, text, role, icon, color, slot, visible in specs:
            btn = ModernButton(text, role=role)
            btn.setParent(self)
            btn.setIcon(get_icon_colored(icon, color, 16))
            btn.setIconSize(QSize(16, 16))
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
        self._search.setDirection(
            QBoxLayout.Direction.TopToBottom if self.width() < 480
            else QBoxLayout.Direction.LeftToRight
        )

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
        self.combo_date.setEnabled(enabled)
        if not self.btn_live.isVisible():
            self.btn_clear.setEnabled(enabled)

    def set_view_toggle_state(self, logs_visible: bool):
        key = "log.controls.btn_hide_logs" if logs_visible else "log.controls.btn_show_logs"
        self.btn_toggle_view.setText(self.i18n.get(key))
        self.set_streaming_controls_enabled(logs_visible)

    def _on_date_changed(self, index: int):
        val = self.combo_date.itemData(index)
        self.date_changed.emit(val if val is not None else "")
