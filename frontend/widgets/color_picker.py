# frontend\widgets\color_picker.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QColorDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from frontend.common import get_swatch_qss, Palette, BrandColors, Size

DEFAULT_PRESET_COLORS = [BrandColors.KICK_REWARDS, BrandColors.TIKTOK, BrandColors.TWITCH, BrandColors.RED, BrandColors.AMBER, Palette.NEUTRAL_000]

class ModernColorPicker(QWidget):
    color_changed = Signal(str)

    def __init__(
        self,
        initial_color: str = BrandColors.KICK_REWARDS,
        tooltip: str = "",
        presets: list[str] | None = None,
        is_vertical: bool = False,
        show_presets: bool = False,
        parent: QWidget | None = None
    ):
        super().__init__(parent)
        self._current_color = initial_color if QColor.isValidColorName(initial_color) else BrandColors.KICK_REWARDS
        self._tooltip = tooltip
        self._presets = presets if (presets is not None and show_presets) else ([] if not show_presets else DEFAULT_PRESET_COLORS)
        self._is_vertical = is_vertical
        self._show_presets = show_presets
        self._setup_ui()

    def _setup_ui(self):
        self.btn_swatch = QPushButton(self)
        self.btn_swatch.setFixedSize(32, 32)
        self.btn_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        if self._tooltip:
            self.btn_swatch.setToolTip(self._tooltip)
        self.btn_swatch.clicked.connect(self._open_color_dialog)

        self.txt_color = QLineEdit(self._current_color, self)
        self.txt_color.setMaxLength(7)
        self.txt_color.setMinimumWidth(76)
        self.txt_color.setFixedHeight(32)
        self.txt_color.textChanged.connect(self._on_text_changed)

        if self._is_vertical:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(*Size.Margin.NONE)
            layout.setSpacing(Size.SPACING_XS)

            row_top = QHBoxLayout()
            row_top.setContentsMargins(*Size.Margin.NONE)
            row_top.setSpacing(Size.SPACING_SM)
            row_top.addWidget(self.btn_swatch)
            row_top.addWidget(self.txt_color, stretch=1)
            layout.addLayout(row_top)

            if self._show_presets and self._presets:
                presets_layout = QHBoxLayout()
                presets_layout.setContentsMargins(*Size.Margin.NONE)
                presets_layout.setSpacing(Size.SPACING_XS)
                for hex_code in self._presets:
                    btn_p = QPushButton(self)
                    btn_p.setFixedSize(22, 22)
                    btn_p.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_p.setStyleSheet(get_swatch_qss(hex_code, border_width=1, radius=Size.Radius.SM))
                    btn_p.clicked.connect(lambda _, c=hex_code: self.set_color(c))
                    presets_layout.addWidget(btn_p)
                presets_layout.addStretch()
                layout.addLayout(presets_layout)
        else:
            layout = QHBoxLayout(self)
            layout.setContentsMargins(*Size.Margin.NONE)
            layout.setSpacing(Size.SPACING_SM)
            layout.addWidget(self.btn_swatch)
            layout.addWidget(self.txt_color, stretch=1)

            if self._show_presets and self._presets:
                presets_layout = QHBoxLayout()
                presets_layout.setSpacing(Size.SPACING_XS)
                for hex_code in self._presets:
                    btn_p = QPushButton(self)
                    btn_p.setFixedSize(22, 22)
                    btn_p.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_p.setStyleSheet(get_swatch_qss(hex_code, border_width=1, radius=Size.Radius.SM))
                    btn_p.clicked.connect(lambda _, c=hex_code: self.set_color(c))
                    presets_layout.addWidget(btn_p)
                layout.addLayout(presets_layout)

        self._update_swatch_style(self._current_color)

    def _open_color_dialog(self):
        title = self._tooltip
        color = QColorDialog.getColor(QColor(self._current_color), self, title)
        if color.isValid():
            self.set_color(color.name())

    def _on_text_changed(self, text: str):
        if QColor.isValidColorName(text):
            self._current_color = text
            self._update_swatch_style(text)
            self.color_changed.emit(text)

    def _update_swatch_style(self, hex_code: str):
        self.btn_swatch.setStyleSheet(get_swatch_qss(hex_code, border_width=1, radius=Size.Radius.SM))

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
