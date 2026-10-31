# frontend\widgets\category_search.py

from PySide6.QtCore import Qt, Signal, QTimer, QEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidgetItem, QSizePolicy, QWidget
from frontend.common import get_pixmap_colored, Size
from .action_line_edit import ActionLineEdit
from .floating_list_popup import BaseFloatingListPopup
from .stream_platform_widgets import platform_brand_pixmap

class CategoryItemWidget(QWidget):
    def __init__(self, platform: str, name: str, _cat_id=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*Size.Margin.MRG_XSM)
        layout.setSpacing(Size.SPACING_MD)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        pixmap = platform_brand_pixmap(platform)
        if pixmap is None:
            pixmap = get_pixmap_colored("gamepad-filled.svg")

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setPixmap(pixmap)
        layout.addWidget(self.icon_label)

        self.lbl_name = QLabel(name)
        self.lbl_name.setProperty("role", "body")
        self.lbl_name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.lbl_name)

class CategorySuggestionsPopup(BaseFloatingListPopup):
    category_selected = Signal(object)

    _MIN_WIDTH = 260
    _ANCHOR_GAP = 4
    _WRAP_NAVIGATION = True
    _ROW_HEIGHT = 50
    _MAX_VISIBLE_ROWS = 6
    _MAX_RESULTS = 50

    def __init__(self, target_input: QWidget, parent=None):
        super().__init__(
            target_input,
            frame_role="category_dropdown",
            list_role="category_list",
            window_flags=Qt.WindowType.ToolTip | Qt.WindowType.WindowStaysOnTopHint,
            parent=parent
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.attach_key_navigation(target_input)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusOut:
            QTimer.singleShot(150, self._check_hide_on_focus_lost)
        return super().eventFilter(obj, event)

    def _check_hide_on_focus_lost(self):
        if not self.anchor.hasFocus() and not self.hasFocus() and not self.list_widget.hasFocus():
            self.hide()

    def show_results(self, platform: str, results: list[dict]):
        self.list_widget.clear()
        if not results or not self.anchor.isVisible():
            self.hide()
            return

        for item_data in results[:self._MAX_RESULTS]:
            name = item_data.get("name", "")
            cat_id = item_data.get("id", "")
            plat = item_data.get("platform", platform)

            list_item = QListWidgetItem(self.list_widget)
            list_item.setData(Qt.ItemDataRole.UserRole, {
                "platform": plat,
                "id": cat_id,
                "name": name,
                "thumbnail": item_data.get("thumbnail", "")
            })

            custom_widget = CategoryItemWidget(plat, name, cat_id, parent=self.list_widget)
            list_item.setSizeHint(custom_widget.sizeHint())
            self.list_widget.setItemWidget(list_item, custom_widget)

        self.setFixedHeight(min(len(results), self._MAX_VISIBLE_ROWS) * self._ROW_HEIGHT)
        self.show_below_anchor()

    def _on_item_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        self.hide()
        if data:
            self.category_selected.emit(data)

class CategorySearchComboBox(ActionLineEdit):
    category_selected = Signal(object)
    search_requested = Signal(str, str)

    def __init__(self, placeholder: str = "", default_platform: str = "both", parent=None):
        super().__init__(placeholder, search_when_empty=True, parent=parent)
        self.default_platform = default_platform
        self._selected_category_data = None

        self.popup = CategorySuggestionsPopup(self.txt_input, parent=self)
        self.popup.category_selected.connect(self._on_category_picked)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self._emit_search)

    def _on_text_changed(self, text: str):
        query = text.strip()
        if len(query) >= 2:
            self.search_timer.start()
        else:
            self.search_timer.stop()
            self.popup.hide()
            if not query:
                self._selected_category_data = None
        super()._on_text_changed(text)

    def _emit_search(self):
        query = self.txt_input.text().strip()
        if query:
            self.search_requested.emit(query, self.default_platform)

    def _set_text_silently(self, text: str):
        self.txt_input.blockSignals(True)
        self.txt_input.setText(text)
        self.txt_input.blockSignals(False)
        self._sync_action_button()

    def _on_category_picked(self, data: dict):
        self.search_timer.stop()
        self._selected_category_data = data
        self._set_text_silently(data.get("name", ""))
        self.txt_input.setFocus()
        self.category_selected.emit(data)

    def set_results(self, platform: str, results: list[dict]):
        if len(self.txt_input.text().strip()) >= 2:
            self.popup.show_results(platform, results)

    def set_selected_category(self, name: str, cat_id=None, platform: str = ""):
        self._selected_category_data = {
            "name": name,
            "id": cat_id,
            "platform": platform or self.default_platform
        }
        self._set_text_silently(name)

    def clear(self):
        self._selected_category_data = None
        self.popup.hide()
        super().clear()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.popup.hide()
