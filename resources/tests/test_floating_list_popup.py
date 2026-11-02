# resources\tests\test_floating_list_popup.py

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QGuiApplication, QKeyEvent
from PySide6.QtWidgets import QApplication, QLineEdit, QListWidgetItem

from frontend.widgets import BaseFloatingListPopup, CategorySuggestionsPopup, SearchableComboBox


class _Popup(BaseFloatingListPopup):
    def __init__(self, anchor, items=("uno", "dos", "tres"), wrap=False):
        super().__init__(anchor, "test_popup", "test_list", Qt.WindowType.Popup)
        self._WRAP_NAVIGATION = wrap
        self.activated: list[str] = []
        for text in items:
            self.list_widget.addItem(QListWidgetItem(text))
        self.list_widget.setCurrentRow(0)

    def _on_item_clicked(self, item):
        self.activated.append(item.text())
        self.hide()


def _anchor(qapp, x: int = 50, y: int = 50) -> QLineEdit:
    anchor = QLineEdit()
    anchor.resize(300, 30)
    anchor.move(x, y)
    anchor.show()
    qapp.processEvents()
    return anchor


def _press(widget, key) -> None:
    QApplication.sendEvent(widget, QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier))


def test_base_popup_builds_frameless_translucent_window_with_styled_frame(qapp):
    popup = _Popup(QLineEdit())

    assert popup.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert popup.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert popup.bg_frame.property("role") == "test_popup"
    assert popup.list_widget.property("role") == "test_list"
    assert popup.list_widget.parentWidget() is popup.bg_frame


def test_base_popup_requires_subclasses_to_handle_item_clicks(qapp):
    popup = BaseFloatingListPopup(QLineEdit(), "r", "l", Qt.WindowType.Popup)
    with pytest.raises(NotImplementedError):
        popup._on_item_clicked(QListWidgetItem("x"))


def test_navigation_clamps_at_the_ends_by_default(qapp):
    popup = _Popup(QLineEdit())

    popup.navigate(-1)
    assert popup.list_widget.currentRow() == 0
    popup.navigate(1)
    popup.navigate(1)
    popup.navigate(1)
    assert popup.list_widget.currentRow() == 2


def test_navigation_can_wrap_around(qapp):
    popup = _Popup(QLineEdit(), wrap=True)

    popup.navigate(-1)
    assert popup.list_widget.currentRow() == 2
    popup.navigate(1)
    assert popup.list_widget.currentRow() == 0


def test_wrapping_navigation_from_no_selection_goes_to_the_edges(qapp):
    popup = _Popup(QLineEdit(), wrap=True)

    popup.list_widget.setCurrentRow(-1)
    popup.navigate(-1)
    assert popup.list_widget.currentRow() == 2

    popup.list_widget.setCurrentRow(-1)
    popup.navigate(1)
    assert popup.list_widget.currentRow() == 0


def test_navigation_skips_hidden_items(qapp):
    popup = _Popup(QLineEdit(), items=("a", "b", "c", "d"))
    popup.list_widget.item(1).setHidden(True)
    popup.list_widget.item(2).setHidden(True)

    popup.navigate(1)
    assert popup.list_widget.currentRow() == 3

    popup.list_widget.item(3).setHidden(True)
    popup.list_widget.setCurrentRow(0)
    popup.navigate(1)
    assert popup.list_widget.currentRow() == 0


def test_keyboard_through_the_attached_input(qapp):
    anchor = _anchor(qapp)
    popup = _Popup(anchor)
    popup.attach_key_navigation(anchor)
    popup.show_below_anchor()

    _press(anchor, Qt.Key.Key_Down)
    assert popup.list_widget.currentRow() == 1

    _press(anchor, Qt.Key.Key_Return)
    assert popup.activated == ["dos"] and not popup.isVisible()

    popup.show()
    _press(anchor, Qt.Key.Key_Escape)
    assert not popup.isVisible()
    anchor.close()


def test_keys_are_ignored_while_the_popup_is_hidden(qapp):
    anchor = _anchor(qapp)
    popup = _Popup(anchor)
    popup.attach_key_navigation(anchor)

    _press(anchor, Qt.Key.Key_Down)
    assert popup.list_widget.currentRow() == 0
    anchor.close()


def test_enter_without_a_selectable_item_is_not_consumed(qapp):
    popup = _Popup(QLineEdit(), items=("a",))
    popup.list_widget.item(0).setHidden(True)
    assert popup._handle_key(Qt.Key.Key_Return) is False
    assert popup._handle_key(Qt.Key.Key_A) is False


def test_popup_opens_below_the_anchor_with_a_minimum_width(qapp):
    anchor = _anchor(qapp, y=60)
    popup = _Popup(anchor)
    popup.show_below_anchor()

    anchor_bottom = anchor.mapToGlobal(anchor.rect().bottomLeft()).y()
    assert popup.isVisible()
    assert popup.y() >= anchor_bottom
    assert popup.width() == max(anchor.width(), popup._MIN_WIDTH)
    popup.hide()
    anchor.close()


def test_popup_flips_above_the_anchor_when_there_is_no_room_below(qapp):
    screen = QGuiApplication.primaryScreen().availableGeometry()
    anchor = _anchor(qapp, y=screen.bottom() - 60)
    popup = _Popup(anchor)
    popup.setFixedHeight(220)
    popup.show_below_anchor()

    anchor_top = anchor.mapToGlobal(anchor.rect().topLeft()).y()
    assert popup.y() + popup.height() <= anchor_top
    popup.hide()
    anchor.close()


def test_category_popup_configuration(qapp):
    popup = CategorySuggestionsPopup(QLineEdit())

    assert popup.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert popup.bg_frame.property("role") == "category_dropdown"
    assert popup.list_widget.property("role") == "category_list"
    assert popup._WRAP_NAVIGATION is True
    assert popup.windowFlags() & Qt.WindowType.ToolTip


def test_category_popup_lists_results_and_emits_the_picked_one(qapp):
    anchor = _anchor(qapp)
    popup = CategorySuggestionsPopup(anchor)
    picked = []
    popup.category_selected.connect(picked.append)

    popup.show_results("kick", [{"name": f"Juego {i}", "id": i, "thumbnail": ""} for i in range(10)])
    assert popup.isVisible() and popup.list_widget.count() == 10
    assert popup.height() == CategorySuggestionsPopup._MAX_VISIBLE_ROWS * CategorySuggestionsPopup._ROW_HEIGHT

    popup.show_results("kick", [{"name": "Solo", "id": 1}, {"name": "Dos", "id": 2}])
    assert popup.height() == 2 * CategorySuggestionsPopup._ROW_HEIGHT

    popup.attach_key_navigation(anchor)
    assert popup.list_widget.currentRow() == -1
    _press(anchor, Qt.Key.Key_Down)
    assert popup.list_widget.currentRow() == 0
    _press(anchor, Qt.Key.Key_Down)
    _press(anchor, Qt.Key.Key_Down)
    assert popup.list_widget.currentRow() == 0
    _press(anchor, Qt.Key.Key_Up)
    assert popup.list_widget.currentRow() == 1

    _press(anchor, Qt.Key.Key_Enter)
    assert picked and picked[0]["name"] == "Dos" and picked[0]["platform"] == "kick"
    assert not popup.isVisible()

    popup.show_results("kick", [])
    assert not popup.isVisible()
    anchor.close()


def test_searchable_combo_popup_is_translucent_and_styled(qapp):
    combo = SearchableComboBox()
    popup = combo._popup

    assert popup.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert popup.bg_frame.property("role") == "searchable_combo_popup"
    assert popup.list_widget.property("role") == "searchable_combo_list"
    assert popup._WRAP_NAVIGATION is False


def test_searchable_combo_filters_navigates_and_selects_with_the_keyboard(qapp):
    combo = SearchableComboBox()
    combo.addItems(["Alfa", "Beta", "Gamma", "Delta"])
    combo.show()
    combo.showPopup()
    popup = combo._popup
    assert popup.isVisible()

    popup.search_input.setText("a")
    visible = [popup.list_widget.item(i).text() for i in range(4) if not popup.list_widget.item(i).isHidden()]
    assert visible == ["Alfa", "Beta", "Gamma", "Delta"]

    popup.search_input.setText("gam")
    _press(popup.search_input, Qt.Key.Key_Return)
    assert combo.currentText() == "Gamma" and not popup.isVisible()

    combo.showPopup()
    _press(popup.search_input, Qt.Key.Key_Down)
    _press(popup.search_input, Qt.Key.Key_Escape)
    assert not popup.isVisible() and combo.currentText() == "Gamma"
    combo.close()
