# resources\tests\test_widgets_view_layout.py

from PySide6.QtWidgets import QLabel

from backend.services.system import TranslationService
from frontend.common import Size
from frontend.views.widgets_view import WidgetsView
from frontend.widgets import ExpandableCard


def _view(qapp, width: int) -> WidgetsView:
    view = WidgetsView(TranslationService(default_lang="es"))
    view.resize(width, 900)
    view.show()
    qapp.processEvents()
    qapp.processEvents()
    return view


def test_widgets_view_is_a_single_centered_column(qapp):
    view = _view(qapp, 1600)
    cards = list(view.cards.values())
    assert len(cards) == 9

    geometries = [card.geometry() for card in cards]
    assert len({g.x() for g in geometries}) == 1 and len({g.width() for g in geometries}) == 1
    assert [g.y() for g in geometries] == sorted(g.y() for g in geometries)

    column = view.content_column.geometry()
    assert column.width() == Size.CONTENT_MAX_WIDTH
    assert abs(column.left() - (view.scroll_content.width() - column.right() - 1)) <= 1


def test_widgets_view_shrinks_without_breaking_cards(qapp):
    view = _view(qapp, 700)
    column_width = view.content_column.width()
    assert Size.CONTENT_MIN_WIDTH <= column_width < Size.CONTENT_MAX_WIDTH
    assert all(card.width() <= column_width for card in view.cards.values())


def test_widget_cards_have_no_icon_and_use_clean_roles(qapp):
    view = _view(qapp, 1200)
    for w_id, card in view.cards.items():
        assert card.lbl_icon is None, f"{w_id} aún muestra un ícono"
        assert card.lbl_title.property("role") == "setting_title"
        assert card.lbl_desc.property("role") == "caption"


def test_widget_cards_still_expand_load_data_and_emit_changes(qapp):
    view = _view(qapp, 1200)
    saved = []
    view.widget_saved.connect(lambda *args: saved.append(args))

    card = view.cards["death"]
    assert not card.is_expanded()
    card.toggle_expand()
    assert card.is_expanded() and not card.body_widget.isHidden()

    view.populate_widgets({"death": {"is_active": True, "config": {"count": 7}}})
    assert card.spn_deaths.value() == 7 and card.switch.isChecked()

    card.switch.setChecked(False)
    assert saved and saved[-1][0] == "death" and saved[-1][1] is False


def test_expandable_card_defaults_are_backward_compatible(qapp):
    card = ExpandableCard("Título", "Descripción", "star-filled.svg")
    assert card.lbl_icon is not None
    assert card.lbl_title.property("role") == "h3"
    assert card.lbl_desc.property("role") == "body"
    assert card.header_widget.layout().contentsMargins().left() == Size.Margin.MRG_MED[0]


def test_expandable_card_accepts_custom_roles_and_margins(qapp):
    card = ExpandableCard("T", "D", title_role="setting_title", desc_role="caption", header_margins=Size.Margin.MRG_LRG)
    assert card.lbl_icon is None
    assert {lbl.property("role") for lbl in card.header_widget.findChildren(QLabel)} == {"setting_title", "caption"}
    assert card.header_widget.layout().contentsMargins().left() == Size.Margin.MRG_LRG[0]
