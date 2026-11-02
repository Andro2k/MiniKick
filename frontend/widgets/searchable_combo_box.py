# frontend\widgets\searchable_combo_box.py

import time
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QListWidgetItem, QLabel, QWidget
from frontend.common import get_pixmap_colored, Size
from .floating_list_popup import BaseFloatingListPopup
from .no_wheel import NoWheelComboBox
from .style_utils import set_state

class SearchableComboPopup(BaseFloatingListPopup):
    def __init__(self, combo: "SearchableComboBox", placeholder: str = "", empty_text: str = "", parent: QWidget = None):
        super().__init__(
            combo,
            frame_role="searchable_combo_popup",
            list_role="searchable_combo_list",
            window_flags=Qt.WindowType.Popup,
            parent=parent
        )
        self.combo = combo
        self.empty_text = empty_text

        self.content_layout.setContentsMargins(*Size.Margin.MRG_XXS)
        self.content_layout.setSpacing(Size.SPACING_XS)

        search_container = QFrame(self.bg_frame)
        search_container.setProperty("role", "searchable_combo_search_bar")
        search_container.setFixedHeight(32)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(*Size.Margin.MRG_HSM)
        search_layout.setSpacing(Size.SPACING_XS)

        self.lbl_search_icon = QLabel(search_container)
        self.lbl_search_icon.setPixmap(get_pixmap_colored("search-filled.svg"))
        search_layout.addWidget(self.lbl_search_icon, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.search_input = QLineEdit(search_container)
        self.search_input.setProperty("role", "searchable_combo_input")
        self.search_input.setPlaceholderText(placeholder)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.attach_key_navigation(self.search_input)
        search_layout.addWidget(self.search_input)
        self.content_layout.insertWidget(0, search_container)

        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setSpacing(Size.SPACING_XS)

        self.lbl_empty = QLabel(self.empty_text or "...", self.bg_frame)
        self.lbl_empty.setProperty("role", "searchable_combo_empty")
        self.lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_empty.setVisible(False)
        self.content_layout.addWidget(self.lbl_empty)

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
            self.update()
            return

        self.lbl_empty.setVisible(False)
        self.list_widget.setVisible(True)

        row_height = 36
        max_height = 236
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

    def _on_item_clicked(self, item: QListWidgetItem):
        orig_index = item.data(Qt.ItemDataRole.UserRole + 1)
        if orig_index is not None and 0 <= orig_index < self.combo.count():
            self.combo.setCurrentIndex(orig_index)
        self.combo.hidePopup()

    def show_for_combo(self):
        self.show_below_anchor()
        self.search_input.clear()
        self.search_input.setFocus()

    def hideEvent(self, event):
        self.combo._on_popup_closed()
        super().hideEvent(event)

class SearchableComboBox(NoWheelComboBox):
    def __init__(self, parent: QWidget = None, placeholder: str = "", empty_text: str = ""):
        super().__init__(parent)
        self._popup = SearchableComboPopup(self, placeholder=placeholder, empty_text=empty_text, parent=self)
        self._last_popup_close_time = 0.0

    def setPlaceholderText(self, placeholder: str):
        self._popup.search_input.setPlaceholderText(placeholder)

    def showPopup(self):
        if self.count() == 0:
            return

        set_state(self, "active")
        self.update()

        self._popup.sync_items()
        self._popup.show_for_combo()

    def hidePopup(self):
        if self._popup.isVisible():
            self._popup.hide()

    def _on_popup_closed(self):
        self._last_popup_close_time = time.time()
        set_state(self, "normal")
        self.update()

    def mousePressEvent(self, event):
        if time.time() - self._last_popup_close_time < 0.25:
            return
        super().mousePressEvent(event)
