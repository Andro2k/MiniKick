# frontend/components/log_controls.py

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QComboBox, QBoxLayout
from PySide6.QtCore import Qt, Signal
from frontend.widgets.controls_component import ModernButton
from frontend.common.utils import get_icon_colored
from frontend.common.theme import COLOR_BLACK, COLOR_TEXT_PRIMARY

class LogControlsPanel(QFrame):
    search_changed = Signal(str)
    filter_changed = Signal(str)
    folder_requested = Signal()
    load_requested = Signal()
    live_requested = Signal()
    clear_requested = Signal()
    report_requested = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setProperty("role", "card")
        self._setup_ui()

    def _setup_ui(self):
        self.controls_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.controls_layout.setContentsMargins(8, 8, 8, 8)
        self.controls_layout.setSpacing(6)

        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(self.i18n.get("log.controls.search_placeholder"))
        self.txt_search.textChanged.connect(self.search_changed.emit)
        search_layout.addWidget(self.txt_search, stretch=1)

        self.combo_filter = QComboBox()
        self.combo_filter.addItems([
            self.i18n.get("log.controls.filter_all"), 
            "INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"
        ])
        self.combo_filter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_filter.currentTextChanged.connect(self.filter_changed.emit)
        search_layout.addWidget(self.combo_filter)

        self.controls_layout.addLayout(search_layout, stretch=1)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        self.btn_open_folder = ModernButton(self.i18n.get("log.controls.btn_folder"), role="action_outlined")
        self.btn_open_folder.setIcon(get_icon_colored("folder-open.svg", COLOR_TEXT_PRIMARY, 16))
        self.btn_open_folder.setToolTip(self.i18n.get("log.controls.tooltip_folder"))
        self.btn_open_folder.clicked.connect(self.folder_requested.emit)

        self.btn_load_file = ModernButton(self.i18n.get("log.controls.btn_load"), role="action_outlined")
        self.btn_load_file.setIcon(get_icon_colored("file-text.svg", COLOR_TEXT_PRIMARY, 16))
        self.btn_load_file.clicked.connect(self.load_requested.emit)

        self.btn_live = ModernButton(self.i18n.get("log.controls.btn_live"), role="action_accent")
        self.btn_live.setIcon(get_icon_colored("play.svg", COLOR_BLACK, 16))
        self.btn_live.clicked.connect(self.live_requested.emit)
        self.btn_live.setVisible(False)

        self.btn_clear = ModernButton(self.i18n.get("log.controls.btn_clear"), role="action_outlined")
        self.btn_clear.setIcon(get_icon_colored("trash.svg", COLOR_TEXT_PRIMARY, 16))
        self.btn_clear.clicked.connect(self.clear_requested.emit)

        self.btn_report = ModernButton(self.i18n.get("log.controls.btn_report"), role="action_accent")
        self.btn_report.setIcon(get_icon_colored("help.svg", COLOR_BLACK, 16))
        self.btn_report.clicked.connect(self.report_requested.emit)

        actions_layout.addWidget(self.btn_open_folder)
        actions_layout.addWidget(self.btn_load_file)
        actions_layout.addWidget(self.btn_live)
        actions_layout.addWidget(self.btn_clear)
        actions_layout.addWidget(self.btn_report)

        self.controls_layout.addLayout(actions_layout)

    def set_historical_mode(self, is_historical: bool):
        self.btn_live.setVisible(is_historical)
        self.btn_clear.setEnabled(not is_historical)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() < 800:
            self.controls_layout.setDirection(QBoxLayout.Direction.TopToBottom)
        else:
            self.controls_layout.setDirection(QBoxLayout.Direction.LeftToRight)