# frontend\widgets\category_search.py

from PySide6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, 
                               QListWidget, QListWidgetItem, QLabel, QWidget, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QEvent, QSize
from frontend.common.icons import get_icon_colored
from frontend.common.theme import COLOR_NEUTRAL_400

class CategoryItemWidget(QWidget):
    def __init__(self, platform: str, name: str, cat_id=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        plat_upper = platform.upper()
        self.badge = QLabel(plat_upper)
        self.badge.setFixedHeight(20)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if plat_upper == "KICK":
            self.badge.setProperty("role", "badge_kick")
        elif plat_upper == "TWITCH":
            self.badge.setProperty("role", "badge_twitch")
        else:
            self.badge.setProperty("role", "caption")

        layout.addWidget(self.badge)

        self.lbl_name = QLabel(name)
        self.lbl_name.setProperty("role", "body")
        self.lbl_name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.lbl_name)

class CategorySuggestionsPopup(QFrame):
    category_selected = Signal(object)

    def __init__(self, target_input: QWidget, parent=None):
        super().__init__(parent)
        self.target_input = target_input
        self.setProperty("role", "category_dropdown")
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self.list_widget = QListWidget(self)
        self.list_widget.setProperty("role", "category_list")
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        self.target_input.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and self.isVisible():
            key = event.key()
            if key == Qt.Key.Key_Escape:
                self.hide()
                return True
            elif key == Qt.Key.Key_Down:
                cur = self.list_widget.currentRow()
                if cur < self.list_widget.count() - 1:
                    self.list_widget.setCurrentRow(cur + 1)
                else:
                    self.list_widget.setCurrentRow(0)
                return True
            elif key == Qt.Key.Key_Up:
                cur = self.list_widget.currentRow()
                if cur > 0:
                    self.list_widget.setCurrentRow(cur - 1)
                else:
                    self.list_widget.setCurrentRow(self.list_widget.count() - 1)
                return True
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                item = self.list_widget.currentItem()
                if item:
                    self._on_item_clicked(item)
                    return True
        elif event.type() == QEvent.Type.FocusOut:
            QTimer.singleShot(150, self._check_hide_on_focus_lost)
        return super().eventFilter(obj, event)

    def _check_hide_on_focus_lost(self):
        if not self.target_input.hasFocus() and not self.hasFocus() and not self.list_widget.hasFocus():
            self.hide()

    def show_results(self, platform: str, results: list[dict]):
        self.list_widget.clear()
        if not results or not self.target_input.isVisible():
            self.hide()
            return

        for item_data in results[:50]:
            name = item_data.get("name", "")
            cat_id = item_data.get("id", "")
            plat = item_data.get("platform", platform)

            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(QSize(0, 36))
            payload = {
                "platform": plat,
                "id": cat_id,
                "name": name,
                "thumbnail": item_data.get("thumbnail", "")
            }
            list_item.setData(Qt.ItemDataRole.UserRole, payload)

            custom_widget = CategoryItemWidget(plat, name, cat_id, parent=self.list_widget)
            self.list_widget.setItemWidget(list_item, custom_widget)

        global_pos = self.target_input.mapToGlobal(QPoint(0, self.target_input.height() + 4))
        self.move(global_pos)
        self.setFixedWidth(max(self.target_input.width(), 260))

        visible_count = min(len(results), 6)
        total_height = visible_count * 38 + 12
        self.setFixedHeight(total_height)
        self.show()
        self.raise_()

    def _on_item_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        self.hide()
        if data:
            self.category_selected.emit(data)

class CategorySearchComboBox(QFrame):
    category_selected = Signal(object)
    search_requested = Signal(str, str)
    textChanged = Signal(str)
    returnPressed = Signal()

    def __init__(self, placeholder: str = "", default_platform: str = "both", parent=None):
        super().__init__(parent)
        self.default_platform = default_platform
        self._selected_category_data = None
        self.setProperty("role", "search_bar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._icon_search = get_icon_colored("search.svg", COLOR_NEUTRAL_400, 16)
        self._icon_clear = get_icon_colored("x.svg", COLOR_NEUTRAL_400, 16)

        self.txt_input = QLineEdit(self)
        self.txt_input.setPlaceholderText(placeholder)
        self.txt_input.setFrame(False)
        self.txt_input.textChanged.connect(self._on_text_changed)
        self.txt_input.returnPressed.connect(self.returnPressed.emit)

        self.btn_action = QPushButton(self)
        self.btn_action.setIcon(self._icon_search)
        self.btn_action.setIconSize(QSize(16, 16))
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.clicked.connect(self._on_action_clicked)

        layout.addWidget(self.txt_input, stretch=1)
        layout.addWidget(self.btn_action)

        self.popup = CategorySuggestionsPopup(self.txt_input, parent=self)
        self.popup.category_selected.connect(self._on_category_picked)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self._emit_search)

    def _on_text_changed(self, text: str):
        if text.strip():
            self.btn_action.setIcon(self._icon_clear)
            if len(text.strip()) >= 2:
                self.search_timer.start()
            else:
                self.search_timer.stop()
                self.popup.hide()
        else:
            self.btn_action.setIcon(self._icon_search)
            self.search_timer.stop()
            self.popup.hide()
            self._selected_category_data = None

        self.textChanged.emit(text)

    def _on_action_clicked(self):
        if self.txt_input.text().strip():
            self.clear()
            self.txt_input.setFocus()
        else:
            self._emit_search()

    def _emit_search(self):
        query = self.txt_input.text().strip()
        if query:
            self.search_requested.emit(query, self.default_platform)

    def _on_category_picked(self, data: dict):
        self.search_timer.stop()
        self._selected_category_data = data
        name = data.get("name", "")

        self.txt_input.blockSignals(True)
        self.txt_input.setText(name)
        self.txt_input.blockSignals(False)
        self.btn_action.setIcon(self._icon_clear)
        self.txt_input.setFocus()

        self.category_selected.emit(data)

    def set_results(self, platform: str, results: list[dict]):
        if len(self.txt_input.text().strip()) >= 2:
            self.popup.show_results(platform, results)

    def get_selected_category(self) -> dict | None:
        return self._selected_category_data

    def set_selected_category(self, name: str, cat_id=None, platform: str = ""):
        self._selected_category_data = {
            "name": name,
            "id": cat_id,
            "platform": platform or self.default_platform
        }
        self.txt_input.blockSignals(True)
        self.txt_input.setText(name)
        self.txt_input.blockSignals(False)
        self.btn_action.setIcon(self._icon_clear if name else self._icon_search)

    def set_platform(self, platform: str):
        self.default_platform = platform

    def text(self) -> str:
        return self.txt_input.text()

    def setText(self, text: str):
        self.txt_input.setText(text)
        self.btn_action.setIcon(self._icon_clear if text else self._icon_search)

    def setPlaceholderText(self, text: str):
        self.txt_input.setPlaceholderText(text)

    def clear(self):
        self._selected_category_data = None
        self.txt_input.clear()
        self.btn_action.setIcon(self._icon_search)
        self.popup.hide()

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.txt_input.setEnabled(enabled)
        self.btn_action.setEnabled(enabled)

    def setFocus(self):
        self.txt_input.setFocus()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.popup.hide()
