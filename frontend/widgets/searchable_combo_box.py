# frontend\widgets\searchable_combo_box.py

import time
from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QLabel, QApplication, QWidget
)
from frontend.common import (
    get_pixmap_colored, COLOR_NEUTRAL_400,
    MARGIN_XS, SPACING_XS, SPACING_2XS
)
from .no_wheel import NoWheelComboBox

class _SearchLineEdit(QLineEdit):
    def __init__(self, popup: "SearchableComboPopup", parent=None):
        super().__init__(parent)
        self._popup = popup

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Down:
            self._popup.navigate_list(1)
            event.accept()
            return
        elif key == Qt.Key.Key_Up:
            self._popup.navigate_list(-1)
            event.accept()
            return
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._popup.select_current_item()
            event.accept()
            return
        elif key == Qt.Key.Key_Escape:
            self._popup.combo.hidePopup()
            event.accept()
            return
        super().keyPressEvent(event)

class SearchableComboPopup(QFrame):
    def __init__(self, combo: "SearchableComboBox", placeholder: str = "", empty_text: str = "", parent: QWidget = None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.combo = combo
        self.empty_text = empty_text
        self.setProperty("role", "searchable_combo_popup")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(*MARGIN_XS)
        layout.setSpacing(SPACING_2XS)

        search_container = QFrame(self)
        search_container.setProperty("role", "searchable_combo_search_bar")
        search_container.setFixedHeight(30)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(8, 0, 8, 0)
        search_layout.setSpacing(SPACING_XS)

        self.lbl_search_icon = QLabel(search_container)
        self.lbl_search_icon.setPixmap(get_pixmap_colored("search.svg", COLOR_NEUTRAL_400, size=14))
        self.lbl_search_icon.setFixedSize(14, 14)
        search_layout.addWidget(self.lbl_search_icon, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.search_input = _SearchLineEdit(self, search_container)
        self.search_input.setProperty("role", "searchable_combo_input")
        self.search_input.setPlaceholderText(placeholder)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_input)

        layout.addWidget(search_container)

        self.list_widget = QListWidget(self)
        self.list_widget.setProperty("role", "searchable_combo_list")
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.setSpacing(2)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        self.lbl_empty = QLabel(self.empty_text or "...", self)
        self.lbl_empty.setProperty("role", "searchable_combo_empty")
        self.lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_empty.setVisible(False)
        layout.addWidget(self.lbl_empty)

    def sync_items(self):
        self.list_widget.clear()
        selected_idx = self.combo.currentIndex()
        item_to_select = None

        for i in range(self.combo.count()):
            text = self.combo.itemText(i)
            icon = self.combo.itemIcon(i)
            item = QListWidgetItem(icon, text) if not icon.isNull() else QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole + 1, i)
            item.setSizeHint(QSize(0, 32))
            self.list_widget.addItem(item)
            if i == selected_idx:
                item_to_select = item

        if item_to_select:
            self.list_widget.setCurrentItem(item_to_select)
            self.list_widget.scrollToItem(item_to_select)
        elif self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

        self._adjust_dimensions(self.list_widget.count())

    def _adjust_dimensions(self, visible_count: int):
        if visible_count == 0:
            self.lbl_empty.setVisible(True)
            self.list_widget.setVisible(False)
            self.adjustSize()
            return

        self.lbl_empty.setVisible(False)
        self.list_widget.setVisible(True)

        row_height = 34
        max_height = 238
        min_height = 36
        target_height = min(max_height, max(min_height, visible_count * row_height + 4))

        if visible_count * row_height + 4 > max_height:
            self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_widget.setFixedHeight(target_height)
        self.adjustSize()

    def _on_search_text_changed(self, text: str):
        query = text.strip().lower()
        visible_count = 0
        first_visible = None

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            matches = not query or (query in item.text().lower())
            item.setHidden(not matches)
            if matches:
                visible_count += 1
                if first_visible is None:
                    first_visible = item

        if first_visible:
            self.list_widget.setCurrentItem(first_visible)

        self._adjust_dimensions(visible_count)

    def navigate_list(self, step: int):
        count = self.list_widget.count()
        if count == 0:
            return

        cur_row = self.list_widget.currentRow()
        idx = cur_row + step
        while 0 <= idx < count:
            item = self.list_widget.item(idx)
            if not item.isHidden():
                self.list_widget.setCurrentRow(idx)
                self.list_widget.scrollToItem(item)
                break
            idx += step

    def select_current_item(self):
        cur = self.list_widget.currentItem()
        if cur and not cur.isHidden():
            self._on_item_clicked(cur)

    def _on_item_clicked(self, item: QListWidgetItem):
        orig_index = item.data(Qt.ItemDataRole.UserRole + 1)
        if orig_index is not None and 0 <= orig_index < self.combo.count():
            self.combo.setCurrentIndex(orig_index)
        self.combo.hidePopup()

    def show_at(self, combo: "SearchableComboBox"):
        target_width = max(combo.width(), 240)
        self.setFixedWidth(target_width)
        self.adjustSize()

        popup_height = self.sizeHint().height()
        global_pos = combo.mapToGlobal(QPoint(0, combo.height() + 2))

        screen = combo.screen() or QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()
            if global_pos.y() + popup_height > screen_rect.bottom():
                global_pos = combo.mapToGlobal(QPoint(0, -popup_height - 2))

        self.move(global_pos)
        self.show()
        self.search_input.clear()
        self.search_input.setFocus()

    def hideEvent(self, event):
        self.combo._on_popup_closed()
        super().hideEvent(event)

class SearchableComboBox(NoWheelComboBox):
    def __init__(self, parent: QWidget = None, placeholder: str = "", empty_text: str = ""):
        super().__init__(parent)
        self._placeholder = placeholder
        self._empty_text = empty_text
        self._popup = SearchableComboPopup(self, placeholder=placeholder, empty_text=empty_text, parent=self)
        self._last_popup_close_time = 0.0

    def setPlaceholderText(self, placeholder: str):
        self._placeholder = placeholder
        self._popup.search_input.setPlaceholderText(placeholder)

    def setEmptyText(self, empty_text: str):
        self._empty_text = empty_text
        self._popup.empty_text = empty_text
        self._popup.lbl_empty.setText(empty_text)

    def showPopup(self):
        if self.count() == 0:
            return

        self.setProperty("state", "active")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

        self._popup.sync_items()
        self._popup.show_at(self)

    def hidePopup(self):
        if self._popup.isVisible():
            self._popup.hide()

    def _on_popup_closed(self):
        self._last_popup_close_time = time.time()
        self.setProperty("state", "normal")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def mousePressEvent(self, event):
        if time.time() - self._last_popup_close_time < 0.25:
            return
        super().mousePressEvent(event)
