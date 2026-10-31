# resources\tests\test_action_line_edit.py

from PySide6.QtCore import QEvent
from PySide6.QtGui import QFocusEvent
from PySide6.QtWidgets import QApplication

from frontend.widgets import ActionLineEdit, CategorySearchComboBox, ClearableLineEdit, UnifiedSearchBar


def _recorder(signal) -> list:
    calls: list = []
    signal.connect(lambda *args: calls.append(args))
    return calls


def _shows_delete_icon(edit: ActionLineEdit) -> bool:
    return edit.btn_action.icon().cacheKey() == edit._icon_delete.cacheKey()


def test_all_inputs_share_the_same_base(qapp):
    assert issubclass(UnifiedSearchBar, ActionLineEdit)
    assert issubclass(ClearableLineEdit, ActionLineEdit)
    assert issubclass(CategorySearchComboBox, ActionLineEdit)


def test_search_mode_toggles_search_and_delete_icon(qapp):
    bar = UnifiedSearchBar(placeholder="Buscar")
    changes = _recorder(bar.textChanged)

    assert not bar.btn_action.isHidden() and bar.btn_action.isEnabled()
    assert not _shows_delete_icon(bar)

    bar.txt_input.setText("abc")
    assert _shows_delete_icon(bar)
    assert changes == [("abc",)]

    bar.txt_input.setText("   ")
    assert not _shows_delete_icon(bar)


def test_search_mode_click_clears_text_or_requests_search(qapp):
    bar = UnifiedSearchBar()
    searches, cleared = _recorder(bar.searchClicked), _recorder(bar.textCleared)

    bar.btn_action.click()
    assert searches == [("",)] and cleared == []

    bar.setText("zelda")
    bar.btn_action.click()
    assert bar.text() == "" and cleared == [()] and len(searches) == 1


def test_clear_mode_button_only_exists_while_there_is_text(qapp):
    edit = ClearableLineEdit(placeholder="Ruta")
    cleared = _recorder(edit.textCleared)

    assert edit.btn_action.isHidden() and not edit.btn_action.isEnabled()
    assert edit.btn_clear is edit.btn_action

    edit.setText("a.mp4")
    assert not edit.btn_action.isHidden() and edit.btn_action.isEnabled()

    edit.btn_clear.click()
    assert edit.text() == "" and edit.btn_action.isHidden() and cleared == [()]


def test_clear_mode_read_only_and_enabled_state_drive_the_button(qapp):
    edit = ClearableLineEdit()
    edit.setText("valor")

    edit.setReadOnly(True)
    assert edit.isReadOnly() and edit.btn_action.isHidden()
    edit.setReadOnly(False)
    assert not edit.btn_action.isHidden()

    edit.setEnabled(False)
    assert not edit.btn_action.isEnabled()
    edit.setEnabled(True)
    assert edit.btn_action.isEnabled() and edit.txt_input.isEnabled()


def test_proxy_methods_forward_to_the_inner_line_edit(qapp):
    edit = ClearableLineEdit(placeholder="Inicial")
    assert edit.placeholderText() == "Inicial"

    edit.setPlaceholderText("Nuevo")
    edit.setToolTip("Ayuda")
    edit.setMinimumWidth(240)

    assert edit.txt_input.placeholderText() == "Nuevo"
    assert edit.txt_input.toolTip() == "Ayuda" and edit.toolTip() == "Ayuda"
    assert edit.minimumWidth() == 240 and edit.txt_input.minimumWidth() == 240


def test_return_pressed_is_relayed(qapp):
    edit = UnifiedSearchBar()
    pressed = _recorder(edit.returnPressed)
    edit.txt_input.returnPressed.emit()
    assert pressed == [()]


def test_focus_events_toggle_the_focused_state(qapp):
    edit = UnifiedSearchBar()

    QApplication.sendEvent(edit.txt_input, QFocusEvent(QEvent.Type.FocusIn))
    assert edit.property("state") == "focused"
    QApplication.sendEvent(edit.txt_input, QFocusEvent(QEvent.Type.FocusOut))
    assert edit.property("state") == ""


def test_category_search_debounces_and_requests_only_with_two_characters(qapp):
    box = CategorySearchComboBox(default_platform="kick")
    requests = _recorder(box.search_requested)

    box.txt_input.setText("f")
    assert not box.search_timer.isActive()

    box.txt_input.setText("fo")
    assert box.search_timer.isActive()

    box.search_timer.timeout.emit()
    assert requests == [("fo", "kick")]

    box.txt_input.setText("")
    assert not box.search_timer.isActive()


def test_category_selection_sets_text_without_retriggering_search(qapp):
    box = CategorySearchComboBox()
    changes, picked = _recorder(box.textChanged), _recorder(box.category_selected)

    box._on_category_picked({"name": "Fortnite", "id": 7, "platform": "kick"})
    assert box.text() == "Fortnite" and _shows_delete_icon(box)
    assert changes == [] and not box.search_timer.isActive()
    assert picked == [({"name": "Fortnite", "id": 7, "platform": "kick"},)]

    box.set_selected_category("Valorant", 3, "twitch")
    assert box.text() == "Valorant" and changes == []
    assert box._selected_category_data == {"name": "Valorant", "id": 3, "platform": "twitch"}


def test_category_clear_resets_selection_and_hides_popup(qapp):
    box = CategorySearchComboBox()
    box.show()
    box.set_selected_category("Fortnite", 1, "kick")
    box.txt_input.setText("fo")
    box.set_results("kick", [{"name": "Fortnite", "id": 1}])
    assert box.popup.isVisible()

    box.btn_action.click()

    assert box.text() == "" and box._selected_category_data is None
    assert not box.popup.isVisible()
    box.close()


def test_category_popup_only_opens_for_queries_of_two_characters(qapp):
    box = CategorySearchComboBox()
    box.show()
    box.txt_input.blockSignals(True)
    box.txt_input.setText("f")
    box.txt_input.blockSignals(False)

    box.set_results("kick", [{"name": "Fortnite", "id": 1}])
    assert not box.popup.isVisible()

    box.txt_input.setText("fo")
    box.set_results("kick", [{"name": "Fortnite", "id": 1}])
    assert box.popup.isVisible()

    box.hide()
    assert not box.popup.isVisible()
