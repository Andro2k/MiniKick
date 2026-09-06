# frontend\widgets\color_picker.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit, QColorDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from frontend.common import RADIUS_SM, get_swatch_qss, MARGIN_NONE, SPACING_MD, SPACING_XS

DEFAULT_PRESET_COLORS = [
    "#00E701", "#00F0FF", "#9146FF", "#FF4655", "#FFB800", "#FFFFFF"
]

class ModernColorPicker(QWidget):
    color_changed = Signal(str)

    def __init__(
        self,
        initial_color: str = "#00e701",
        tooltip: str = "",
        presets: list[str] | None = None,
        parent: QWidget | None = None
    ):
        super().__init__(parent)
        self._current_color = initial_color if QColor.isValidColorName(initial_color) else "#00e701"
        self._tooltip = tooltip
        self._presets = presets if presets is not None else DEFAULT_PRESET_COLORS
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*MARGIN_NONE)
        layout.setSpacing(SPACING_MD)

        self.btn_swatch = QPushButton(self)
        self.btn_swatch.setFixedSize(32, 32)
        self.btn_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        if self._tooltip:
            self.btn_swatch.setToolTip(self._tooltip)
        self.btn_swatch.clicked.connect(self._open_color_dialog)

        self.txt_color = QLineEdit(self._current_color, self)
        self.txt_color.setMaxLength(7)
        self.txt_color.textChanged.connect(self._on_text_changed)

        layout.addWidget(self.btn_swatch)
        layout.addWidget(self.txt_color, stretch=1)

        if self._presets:
            presets_layout = QHBoxLayout()
            presets_layout.setSpacing(SPACING_XS)
            for hex_code in self._presets:
                btn_p = QPushButton(self)
                btn_p.setFixedSize(22, 22)
                btn_p.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_p.setStyleSheet(get_swatch_qss(hex_code, border_width=1, radius=RADIUS_SM))
                btn_p.clicked.connect(lambda _, c=hex_code: self.set_color(c))
                presets_layout.addWidget(btn_p)
            layout.addLayout(presets_layout)

        self._update_swatch_style(self._current_color)

    def _open_color_dialog(self):
        title = self._tooltip or "Select Color"
        color = QColorDialog.getColor(QColor(self._current_color), self, title)
        if color.isValid():
            self.set_color(color.name())

    def _on_text_changed(self, text: str):
        if QColor.isValidColorName(text):
            self._current_color = text
            self._update_swatch_style(text)
            self.color_changed.emit(text)

    def _update_swatch_style(self, hex_code: str):
        self.btn_swatch.setStyleSheet(get_swatch_qss(hex_code, border_width=1, radius=RADIUS_SM))

    def set_color(self, hex_code: str):
        if not hex_code or not QColor.isValidColorName(hex_code):
            return
        self._current_color = hex_code
        self.txt_color.blockSignals(True)
        self.txt_color.setText(hex_code)
        self.txt_color.blockSignals(False)
        self._update_swatch_style(hex_code)
        self.color_changed.emit(hex_code)

    def color(self) -> str:
        return self._current_color

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.btn_swatch.setEnabled(enabled)
        self.txt_color.setEnabled(enabled)
