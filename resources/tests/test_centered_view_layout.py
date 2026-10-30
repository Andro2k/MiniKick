# resources\tests\test_centered_view_layout.py

from PySide6.QtWidgets import QLabel, QWidget

from frontend.common import Size, get_global_qss
from frontend.views.base_view import BaseView
from frontend.widgets import SettingRow


class _I18n:
    def get(self, key):
        return key


def _show(qapp, view: BaseView, width: int) -> None:
    view.resize(width, 600)
    view.show()
    qapp.processEvents()
    qapp.processEvents()


def _margins(view: BaseView) -> tuple[int, int, int]:
    geo = view.content_column.geometry()
    return geo.width(), geo.left(), view.scroll_content.width() - geo.right() - 1


def test_centered_view_caps_width_and_centers(qapp):
    view = BaseView(_I18n(), "t", "s", max_content_width=Size.CONTENT_MAX_WIDTH, min_content_width=Size.CONTENT_MIN_WIDTH)
    _show(qapp, view, 1600)
    width, left, right = _margins(view)
    assert width == Size.CONTENT_MAX_WIDTH
    assert abs(left - right) <= 1 and left > 0


def test_centered_view_shrinks_fluidly_down_to_min_width(qapp):
    view = BaseView(_I18n(), "t", "s", max_content_width=Size.CONTENT_MAX_WIDTH, min_content_width=Size.CONTENT_MIN_WIDTH)
    _show(qapp, view, 700)
    width, left, right = _margins(view)
    assert Size.CONTENT_MIN_WIDTH <= width < Size.CONTENT_MAX_WIDTH
    assert abs(left - right) <= 1

    _show(qapp, view, 300)
    assert view.content_column.width() == Size.CONTENT_MIN_WIDTH


def test_default_view_keeps_full_width_layout(qapp):
    view = BaseView(_I18n(), "t", "s")
    assert view.content_column is view.scroll_content
    assert view.main_layout.parentWidget() is view.scroll_content
    _show(qapp, view, 1600)
    assert view.scroll_content.width() >= 1500


def test_setting_row_roles_are_configurable_and_backward_compatible(qapp):
    default_row = SettingRow(title_text="T", desc_text="D", right_widget=QWidget())
    assert default_row.lbl_desc.property("role") == "body"

    row = SettingRow(title_text="T", desc_text="D", right_widget=QWidget(), title_role="setting_title", desc_role="caption")
    roles = {lbl.text(): lbl.property("role") for lbl in row.findChildren(QLabel)}
    assert roles == {"T": "setting_title", "D": "caption"}


def test_global_qss_defines_setting_title_role():
    assert 'role="setting_title"' in get_global_qss(13)
