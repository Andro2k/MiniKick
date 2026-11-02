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


def test_default_view_uses_the_wide_centered_column(qapp):
    view = BaseView(_I18n(), "t", "s")
    _show(qapp, view, 2000)
    width, left, right = _margins(view)
    assert width == Size.CONTENT_WIDE_MAX_WIDTH
    assert abs(left - right) <= 1 and left > 0


def test_column_uses_the_full_width_until_it_reaches_the_cap(qapp):
    view = BaseView(_I18n(), "t", "s")
    for width in (700, 1100, Size.CONTENT_WIDE_MAX_WIDTH - 40):
        _show(qapp, view, width)
        column_width, left, right = _margins(view)
        assert (left, right) == (0, 0)
        assert column_width == view.scroll_content.width() < Size.CONTENT_WIDE_MAX_WIDTH


def test_view_can_opt_out_of_the_width_cap(qapp):
    view = BaseView(_I18n(), "t", "s", max_content_width=None)
    assert view.content_column is view.scroll_content
    assert view.main_layout.parentWidget() is view.scroll_content
    _show(qapp, view, 2000)
    assert view.scroll_content.width() >= 1900


def test_setting_row_roles_are_configurable_and_backward_compatible(qapp):
    default_row = SettingRow(title_text="T", desc_text="D", right_widget=QWidget())
    assert default_row.lbl_desc.property("role") == "body"

    row = SettingRow(title_text="T", desc_text="D", right_widget=QWidget(), title_role="setting_title", desc_role="caption")
    roles = {lbl.text(): lbl.property("role") for lbl in row.findChildren(QLabel)}
    assert roles == {"T": "setting_title", "D": "caption"}


def test_global_qss_defines_setting_title_role():
    assert 'role="setting_title"' in get_global_qss(13)
