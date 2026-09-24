# frontend\widgets\filter_header.py

from PySide6.QtWidgets import QHeaderView, QMenu, QStyleOptionHeader, QStyle
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize
from PySide6.QtGui import QPainter, QAction, QColor, QFont
from frontend.common import COLOR_GREEN, COLOR_NEUTRAL_500, COLOR_NEUTRAL_400, COLOR_WHITE, get_icon_colored

class FilterHeaderView(QHeaderView):
    filter_changed = Signal(object)
    sort_requested = Signal(int, str)

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._column_filters: dict[int, dict] = {}
        self._icon_filtered = get_icon_colored("filter-filled.svg", COLOR_GREEN, 16)
        self._icon_unfiltered = get_icon_colored("filter-filled.svg", COLOR_NEUTRAL_500, 16)
        self.setSectionsClickable(True)
        self.setSectionsMovable(False)
        self.sectionClicked.connect(self._on_section_clicked)

    def set_column_filter(
        self,
        col_idx: int,
        title: str,
        options: list[dict] | None = None,
        all_label: str = "",
        sort_asc_label: str = "",
        sort_desc_label: str = "",
        default_active: list[str] | None = None
    ):
        opts = options or []
        all_ids = {opt["id"] for opt in opts}
        active_ids = set(default_active) if default_active is not None else set(all_ids)

        self._column_filters[col_idx] = {
            "title": title,
            "options": opts,
            "all_label": all_label,
            "sort_asc_label": sort_asc_label,
            "sort_desc_label": sort_desc_label,
            "active": active_ids
        }
        self.viewport().update()

    def get_active_filters(self) -> dict[int, set[str]]:
        return {col: config["active"] for col, config in self._column_filters.items()}

    def reset_filters(self):
        changed = False
        for col, config in self._column_filters.items():
            opts = config.get("options", [])
            all_ids = {opt["id"] for opt in opts}
            if config["active"] != all_ids:
                config["active"] = set(all_ids)
                changed = True
        if changed:
            self.viewport().update()
            self.filter_changed.emit(self.get_active_filters())

    def has_active_filters(self) -> bool:
        for col, config in self._column_filters.items():
            opts = config.get("options", [])
            all_ids = {opt["id"] for opt in opts}
            if opts and len(config["active"]) < len(all_ids):
                return True
        return False

    def sectionSizeFromContents(self, logicalIndex: int) -> QSize:
        base_size = super().sectionSizeFromContents(logicalIndex)
        if logicalIndex in self._column_filters:
            return QSize(base_size.width() + 30, base_size.height())
        return base_size

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int):
        if logicalIndex not in self._column_filters:
            super().paintSection(painter, rect, logicalIndex)
            return

        config = self._column_filters[logicalIndex]
        total_opts = len(config["options"])
        active_opts = len(config["active"])
        is_filtered = (active_opts < total_opts) and (total_opts > 0)

        title = config.get("title")
        if not title and self.model():
            header_val = self.model().headerData(logicalIndex, self.orientation(), Qt.ItemDataRole.DisplayRole)
            title = str(header_val) if header_val is not None else ""
        if not title:
            title = ""

        opt = QStyleOptionHeader()
        self.initStyleOption(opt)
        opt.section = logicalIndex
        opt.rect = rect
        opt.text = ""
        self.style().drawControl(QStyle.ControlElement.CE_Header, opt, painter, self)

        icon_size = 14
        pad_left = 10
        gap = 6

        icon_rect = QRect(
            rect.left() + pad_left,
            rect.center().y() - icon_size // 2,
            icon_size,
            icon_size
        )
        icon = self._icon_filtered if is_filtered else self._icon_unfiltered
        icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)

        text_rect = QRect(
            rect.left() + pad_left + icon_size + gap,
            rect.top(),
            max(0, rect.width() - (pad_left + icon_size + gap + 8)),
            rect.height()
        )

        is_hover_or_pressed = bool(opt.state & (QStyle.StateFlag.State_MouseOver | QStyle.StateFlag.State_Sunken))
        text_color = QColor(COLOR_WHITE) if is_hover_or_pressed else QColor(COLOR_NEUTRAL_400)

        painter.save()
        painter.setPen(text_color)
        font = self.font()
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        elided = painter.fontMetrics().elidedText(title, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided)
        painter.restore()

    def _on_section_clicked(self, logicalIndex: int):
        if logicalIndex not in self._column_filters:
            return

        config = self._column_filters[logicalIndex]
        menu = QMenu(self)

        action_sort_asc = None
        action_sort_desc = None
        has_sort = bool(config.get("sort_asc_label") or config.get("sort_desc_label"))

        if config.get("sort_asc_label"):
            action_sort_asc = menu.addAction(get_icon_colored("chevron-up-filled.svg", COLOR_NEUTRAL_400, 14), config["sort_asc_label"])
        if config.get("sort_desc_label"):
            action_sort_desc = menu.addAction(get_icon_colored("chevron-down-filled.svg", COLOR_NEUTRAL_400, 14), config["sort_desc_label"])

        action_all = None
        action_map: dict[QAction, str] = {}
        all_ids = set()
        is_all_active = True

        if config.get("options"):
            if has_sort:
                menu.addSeparator()

            all_ids = {opt["id"] for opt in config["options"]}
            is_all_active = config["active"] == all_ids

            if config.get("all_label"):
                action_all = menu.addAction(config["all_label"])
                action_all.setCheckable(True)
                action_all.setChecked(is_all_active)
                menu.addSeparator()

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
        elif action_all and selected_action == action_all:
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
