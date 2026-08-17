# frontend\widgets\segmented_control.py

from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QButtonGroup, QSizePolicy
from PySide6.QtCore import Qt, Signal, QSize
from frontend.common.utils import get_icon_colored
from frontend.common.theme import COLOR_WHITE, COLOR_NEUTRAL_400

class ModernSegmentedControl(QFrame):
    value_changed = Signal(str)

    def __init__(self, parent=None, button_size: QSize = QSize(32, 28), icon_size: QSize = QSize(16, 16)):
        super().__init__(parent)
        self.setProperty("role", "segmented_control")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._button_size = button_size
        self._icon_size = icon_size
        self._buttons: dict[str, QPushButton] = {}
        self._icons: dict[str, str] = {}
        self._current_value = ""

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setSpacing(2)

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

    def add_option(self, option_id: str, icon_name: str, tooltip: str = "") -> QPushButton:
        btn = QPushButton(self)
        btn.setProperty("role", "segmented_item")
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(self._button_size)
        btn.setIconSize(self._icon_size)
        if tooltip:
            btn.setToolTip(tooltip)

        self._buttons[option_id] = btn
        self._icons[option_id] = icon_name
        self._btn_group.addButton(btn)

        btn.setIcon(get_icon_colored(icon_name, COLOR_NEUTRAL_400, self._icon_size.width()))
        btn.toggled.connect(lambda checked, oid=option_id: self._on_button_toggled(oid, checked))

        self._layout.addWidget(btn)

        if not self._current_value:
            self.set_current_value(option_id)

        return btn

    def set_options(self, options: list[tuple[str, str, str]]):
        prev_val = self._current_value
        self.clear()
        for opt in options:
            if len(opt) == 3:
                oid, icon, tip = opt
            else:
                oid, icon = opt[0], opt[1]
                tip = ""
            self.add_option(oid, icon, tip)

        if prev_val and prev_val in self._buttons:
            self.set_current_value(prev_val)
        elif options:
            self.set_current_value(options[0][0])

    def clear(self):
        for btn in list(self._buttons.values()):
            self._btn_group.removeButton(btn)
            self._layout.removeWidget(btn)
            btn.deleteLater()
        self._buttons.clear()
        self._icons.clear()
        self._current_value = ""

    def _on_button_toggled(self, option_id: str, checked: bool):
        btn = self._buttons.get(option_id)
        icon_name = self._icons.get(option_id, "")
        if btn and icon_name:
            color = COLOR_WHITE if checked else COLOR_NEUTRAL_400
            btn.setIcon(get_icon_colored(icon_name, color, self._icon_size.width()))

        if checked:
            if self._current_value != option_id:
                self._current_value = option_id
                self.value_changed.emit(option_id)

    def current_value(self) -> str:
        return self._current_value

    def set_current_value(self, option_id: str):
        if option_id in self._buttons:
            self._buttons[option_id].setChecked(True)
            self._current_value = option_id
            for oid, btn in self._buttons.items():
                icon = self._icons.get(oid, "")
                if icon:
                    color = COLOR_WHITE if oid == option_id else COLOR_NEUTRAL_400
                    btn.setIcon(get_icon_colored(icon, color, self._icon_size.width()))
