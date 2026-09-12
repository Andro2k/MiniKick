# frontend\widgets\inspector_widgets.py

from __future__ import annotations
import os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt, Signal

from frontend.common import (
    get_pixmap_colored, COLOR_NEUTRAL_400,
    SPACING_XS, SPACING_SM, MARGIN_NONE
)
from .controls_widget import ModernButton
from .no_wheel import NoWheelSpinBox, NoWheelSlider
from .color_picker import ModernColorPicker


class InspectorPropertyRow(QWidget):
    def __init__(
        self,
        label: str,
        content_widget: QWidget,
        icon_name: Optional[str] = None,
        tooltip: Optional[str] = None,
        stretch_content: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(36)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(SPACING_SM)

        if icon_name:
            self.lbl_icon = QLabel(self)
            self.lbl_icon.setPixmap(get_pixmap_colored(icon_name, COLOR_NEUTRAL_400, size=14))
            self.lbl_icon.setFixedSize(16, 16)
            self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.lbl_icon)

        self.lbl_title = QLabel(label, self)
        self.lbl_title.setProperty("role", "caption")
        self.lbl_title.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.lbl_title)

        if tooltip:
            self.setToolTip(tooltip)
            self.lbl_title.setToolTip(tooltip)

        self.content_widget = content_widget
        if stretch_content:
            layout.addWidget(self.content_widget, 1)
        else:
            layout.addStretch(1)
            layout.addWidget(self.content_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

class InspectorDualSpinBox(QWidget):
    def __init__(
        self,
        label1: str,
        label2: str,
        range1: tuple[int, int] = (0, 1000),
        range2: tuple[int, int] = (0, 1000),
        default1: int = 0,
        default2: int = 0,
        suffix: str = " px",
        special_text2: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*MARGIN_NONE)
        layout.setSpacing(SPACING_SM)

        self.lbl1 = QLabel(label1, self)
        self.lbl1.setProperty("role", "caption")
        self.lbl1.setProperty("state", "bold")

        self.spin1 = NoWheelSpinBox(self)
        self.spin1.setRange(*range1)
        self.spin1.setValue(default1)
        self.spin1.setSuffix(suffix)
        self.spin1.setMinimumWidth(96)

        self.lbl2 = QLabel(label2, self)
        self.lbl2.setProperty("role", "caption")
        self.lbl2.setProperty("state", "bold")

        self.spin2 = NoWheelSpinBox(self)
        self.spin2.setRange(*range2)
        self.spin2.setValue(default2)
        self.spin2.setSuffix(suffix)
        if special_text2:
            self.spin2.setSpecialValueText(special_text2)
        self.spin2.setMinimumWidth(96)

        layout.addWidget(self.lbl1)
        layout.addWidget(self.spin1)
        layout.addSpacing(SPACING_XS)
        layout.addWidget(self.lbl2)
        layout.addWidget(self.spin2)

class InspectorColorRow(QWidget):
    color_changed = Signal(str)
    opacity_changed = Signal(int)

    def __init__(
        self,
        initial_color: str = "#121317",
        initial_opacity: int = 88,
        tooltip: str = "",
        presets: Optional[list[str]] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*MARGIN_NONE)
        layout.setSpacing(SPACING_SM)

        preset_colors = presets or ["#121317", "#0E1118", "#1A1B23", "#000000", "#1E293B", "#FFFFFF"]
        self.picker = ModernColorPicker(
            initial_color=initial_color,
            tooltip=tooltip,
            presets=preset_colors,
            is_vertical=False,
            parent=self
        )
        self.picker.color_changed.connect(self._on_picker_changed)

        self.slider_opacity = NoWheelSlider(Qt.Orientation.Horizontal, parent=self)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(initial_opacity)
        self.slider_opacity.setFixedWidth(70)
        self.slider_opacity.valueChanged.connect(self._on_opacity_changed)

        self.lbl_opacity = QLabel(f"{initial_opacity}%", parent=self)
        self.lbl_opacity.setProperty("role", "caption")

        layout.addWidget(self.picker)
        layout.addWidget(self.slider_opacity)
        layout.addWidget(self.lbl_opacity)

    def _on_picker_changed(self, color_hex: str):
        self.color_changed.emit(color_hex)

    def _on_opacity_changed(self, val: int):
        self.lbl_opacity.setText(f"{val}%")
        self.opacity_changed.emit(val)

    def set_color(self, hex_color: str):
        self.picker.set_color(hex_color)

    def set_opacity(self, opacity: int):
        self.slider_opacity.setValue(opacity)
        self.lbl_opacity.setText(f"{opacity}%")

    def color(self) -> str:
        return self.picker.color()

    def opacity(self) -> int:
        return self.slider_opacity.value()

class InspectorFilePicker(QWidget):
    file_changed = Signal(str)

    def __init__(
        self,
        filter_str: str,
        browse_text: str = "Examinar...",
        clear_text: str = "Limpiar",
        empty_text: str = "Ningún archivo",
        dialog_title: str = "Seleccionar Archivo",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent=parent)
        self.filter_str = filter_str
        self.dialog_title = dialog_title
        self.empty_text = empty_text
        self._current_path = ""

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*MARGIN_NONE)
        layout.setSpacing(SPACING_XS)

        self.lbl_filename = QLabel(empty_text, self)
        self.lbl_filename.setProperty("role", "code")
        self.lbl_filename.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.btn_browse = ModernButton(
            text=browse_text,
            role="action_secondary",
            icon_name="folder-open-duotone.svg",
            icon_size=12,
            parent=self
        )
        self.btn_browse.setFixedHeight(28)
        self.btn_browse.clicked.connect(self._on_browse_clicked)

        self.btn_clear = ModernButton(
            text="",
            role="action_outlined",
            icon_name="trash.svg",
            icon_size=12,
            parent=self
        )
        self.btn_clear.setToolTip(clear_text)
        self.btn_clear.setFixedSize(28, 28)
        self.btn_clear.clicked.connect(self._on_clear_clicked)
        self.btn_clear.setVisible(False)

        layout.addWidget(self.lbl_filename, 1)
        layout.addWidget(self.btn_browse, 0)
        layout.addWidget(self.btn_clear, 0)

    def _on_browse_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.dialog_title,
            "",
            self.filter_str
        )
        if file_path:
            self.set_file_path(file_path)
            self.file_changed.emit(file_path)

    def _on_clear_clicked(self):
        self.set_file_path("")
        self.file_changed.emit("")

    def set_file_path(self, path: str):
        self._current_path = path or ""
        if self._current_path:
            filename = os.path.basename(self._current_path)
            self.lbl_filename.setText(filename)
            self.lbl_filename.setToolTip(self._current_path)
            self.lbl_filename.setProperty("state", "white")
            self.btn_clear.setVisible(True)
        else:
            self.lbl_filename.setText(self.empty_text)
            self.lbl_filename.setToolTip("")
            self.lbl_filename.setProperty("state", "normal")
            self.btn_clear.setVisible(False)

        if self.lbl_filename.style():
            self.lbl_filename.style().unpolish(self.lbl_filename)
            self.lbl_filename.style().polish(self.lbl_filename)

    def file_path(self) -> str:
        return self._current_path
