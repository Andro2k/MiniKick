# resources\tests\test_table_columns_fit.py
"""Pruebas de que las tablas de Recompensas y Comandos caben en el ancho mínimo soportado."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QTableView

from backend.services.settings.translation_service import TranslationService
from frontend.common import Size
from frontend.views.commands_view import CommandView
from frontend.views.rewards_view import RewardsView

MIN_CONTENT_WIDTH = Size.WINDOW_MIN_WIDTH - Size.SIDEBAR_EXPANDED


def _i18n():
    return TranslationService(default_lang="es")


def _show(qapp, view, width):
    window = QMainWindow()
    window.setCentralWidget(view)
    window.resize(width, 800)
    window.show()
    for _ in range(4):
        qapp.processEvents()
    table = next(t for t in view.findChildren(QTableView) if t.isVisible())
    return window, table


def _hidden_titles(table):
    header = table.horizontalHeader()
    return [
        table.model().headerData(i, Qt.Orientation.Horizontal)
        for i in range(header.count())
        if header.isSectionHidden(i)
    ]


def _has_horizontal_scroll(table):
    bar = table.horizontalScrollBar()
    return bar.isVisible() and bar.maximum() > 0


def test_rewards_hides_position_when_the_table_does_not_fit(qapp):
    window, table = _show(qapp, RewardsView(_i18n()), MIN_CONTENT_WIDTH)

    assert table.isColumnHidden(RewardsView._POSITION_COLUMN)
    assert not _has_horizontal_scroll(table)
    window.close()


def test_rewards_shows_every_column_at_the_collapsed_sidebar_width(qapp):
    width = Size.WINDOW_MIN_WIDTH - Size.SIDEBAR_COLLAPSED
    window, table = _show(qapp, RewardsView(_i18n()), width)

    assert _hidden_titles(table) == []
    assert not _has_horizontal_scroll(table)
    window.close()


@pytest.mark.parametrize("width", [MIN_CONTENT_WIDTH, Size.WINDOW_MIN_WIDTH - Size.SIDEBAR_COLLAPSED])
def test_commands_table_has_no_horizontal_scroll(qapp, width):
    window, table = _show(qapp, CommandView(_i18n()), width)

    assert not _has_horizontal_scroll(table)
    window.close()
