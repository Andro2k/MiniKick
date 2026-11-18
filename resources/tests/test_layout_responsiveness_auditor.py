# resources\tests\test_layout_responsiveness_auditor.py
"""Pruebas de la detección de scroll horizontal interno del auditor de responsividad."""

from PySide6.QtWidgets import QHeaderView, QScrollArea, QTableWidget, QVBoxLayout, QWidget

from resources.tools import frontend_layout_responsiveness_auditor as auditor


def _view_with(child: QWidget) -> QWidget:
    view = QWidget()
    layout = QVBoxLayout(view)
    layout.addWidget(child)
    return view


def _table(columns: int, column_width: int) -> QTableWidget:
    table = QTableWidget(0, columns)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    for column in range(columns):
        table.setColumnWidth(column, column_width)
    return table


def test_el_ancho_minimo_soportado_es_la_ventana_minima_con_sidebar_expandido():
    assert auditor.MIN_SUPPORTED_WIDTH == 670


def test_detecta_una_tabla_que_no_cabe_en_el_ancho_de_la_vista(qapp):
    view = _view_with(_table(columns=4, column_width=300))
    view.resize(500, 400)
    view.show()
    qapp.processEvents()

    assert auditor.find_inner_horizontal_scroll(view) == ["QTableWidget"]
    view.close()


def test_no_marca_una_tabla_que_cabe(qapp):
    view = _view_with(_table(columns=2, column_width=100))
    view.resize(500, 400)
    view.show()
    qapp.processEvents()

    assert auditor.find_inner_horizontal_scroll(view) == []
    view.close()


def test_no_marca_un_scroll_horizontal_que_no_es_de_tabla_ni_lista(qapp):
    area = QScrollArea()
    area.setWidget(QWidget())
    area.widget().setFixedWidth(1200)
    view = _view_with(area)
    view.resize(500, 400)
    view.show()
    qapp.processEvents()

    assert auditor.find_inner_horizontal_scroll(view) == []
    view.close()


def test_la_inspeccion_falla_a_partir_del_ancho_minimo_y_no_por_debajo(qapp):
    view = _view_with(_table(columns=4, column_width=300))

    passed, steps = auditor.inspect_view_responsiveness("demo", view, [670, 600])
    by_width = {step["width"]: step for step in steps}

    assert passed is False
    assert by_width[670]["inner_scroll"] == ["QTableWidget"]
    assert by_width[600]["inner_scroll"] == []
