# frontend\widgets\filter_header.py

from PySide6.QtWidgets import QHeaderView, QMenu
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QPainter, QAction
from frontend.common.theme import COLOR_GREEN, COLOR_NEUTRAL_500
from frontend.common.utils import get_icon_colored

class FilterHeaderView(QHeaderView):
    filter_changed = Signal(dict)
    sort_requested = Signal(int, str)

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._column_filters: dict[int, dict] = {}
        self._icon_filtered = get_icon_colored("adjustments.svg", COLOR_GREEN, 16)
        self._icon_unfiltered = get_icon_colored("adjustments.svg", COLOR_NEUTRAL_500, 16)
        self.setSectionsClickable(True)
        self.setSectionsMovable(False)
        self.sectionClicked.connect(self._on_section_clicked)

    def set_column_filter(
        self,
        col_idx: int,
        title: str,
        options: list[dict],
        all_label: str = "Mostrar Todos",
        sort_asc_label: str = "Orden Ascendente (A-Z)",
        sort_desc_label: str = "Orden Descendente (Z-A)",
        default_active: list[str] | None = None
    ):
        all_ids = {opt["id"] for opt in options}
        active_ids = set(default_active) if default_active is not None else set(all_ids)

        self._column_filters[col_idx] = {
            "title": title,
            "options": options,
            "all_label": all_label,
            "sort_asc_label": sort_asc_label,
            "sort_desc_label": sort_desc_label,
            "active": active_ids
        }
        self.viewport().update()

    def get_active_filters(self) -> dict[int, set[str]]:
        return {col: config["active"] for col, config in self._column_filters.items()}

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int):
        super().paintSection(painter, rect, logicalIndex)

        if logicalIndex in self._column_filters:
            config = self._column_filters[logicalIndex]
            total_opts = len(config["options"])
            active_opts = len(config["active"])
            is_filtered = (active_opts < total_opts) and (total_opts > 0)

            icon_size = 16
            margin = 4
            icon_rect = QRect(
                rect.right() - icon_size - margin,
                rect.center().y() - icon_size // 2,
                icon_size,
                icon_size
            )

            icon = self._icon_filtered if is_filtered else self._icon_unfiltered
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)


    def _on_section_clicked(self, logicalIndex: int):
        if logicalIndex not in self._column_filters:
            return

        config = self._column_filters[logicalIndex]
        menu = QMenu(self)

        header_action = menu.addAction(config["title"])
        header_action.setEnabled(False)
        menu.addSeparator()

        action_sort_asc = menu.addAction(get_icon_colored("chevron-up.svg", COLOR_GREEN, 14), config["sort_asc_label"])
        action_sort_desc = menu.addAction(get_icon_colored("chevron-down.svg", COLOR_GREEN, 14), config["sort_desc_label"])
        menu.addSeparator()

        all_ids = {opt["id"] for opt in config["options"]}
        is_all_active = config["active"] == all_ids

        action_all = menu.addAction(config["all_label"])
        action_all.setCheckable(True)
        action_all.setChecked(is_all_active)
        menu.addSeparator()

        action_map: dict[QAction, str] = {}
        for opt in config["options"]:
            action = menu.addAction(opt["label"])
            action.setCheckable(True)
            action.setChecked(opt["id"] in config["active"])
            action_map[action] = opt["id"]

        section_x = self.sectionViewportPosition(logicalIndex)
        global_pos = self.mapToGlobal(QPoint(section_x, self.height()))

        exec_func = getattr(menu, "exec_", getattr(menu, "exec", None))
        selected_action = exec_func(global_pos)

        if selected_action is None:
            return
        if selected_action == action_sort_asc:
            self.sort_requested.emit(logicalIndex, "asc")
            return
        elif selected_action == action_sort_desc:
            self.sort_requested.emit(logicalIndex, "desc")
            return
        elif selected_action == action_all:
            config["active"] = set(all_ids)
        elif selected_action in action_map:
            opt_id = action_map[selected_action]
            if is_all_active:
                config["active"] = {opt_id}
            else:
                if opt_id in config["active"]:
                    config["active"].remove(opt_id)
                    if len(config["active"]) == 0:
                        config["active"] = set(all_ids)
                else:
                    config["active"].add(opt_id)

        self.viewport().update()
        self.filter_changed.emit(self.get_active_filters())
