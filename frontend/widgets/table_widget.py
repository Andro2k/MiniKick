# frontend\widgets\table.py

import os
from PySide6.QtWidgets import (
    QTableWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, 
    QStackedWidget, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal, QEvent
from .controls_widget import ModernButton, ModernSwitch
from .scalable_illustration import ScalableIllustration
from .filter_header import FilterHeaderView
from .search_bar import UnifiedSearchBar
from .block_widget import ModernDivider
from frontend.common import (
    get_icon_colored, get_assets_path,
    SPACING_NONE, SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG,
    MARGIN_NONE, MARGIN_MD, MARGIN_XL, MARGIN_H_SM
)

class ModernTable(QTableWidget):
    def __init__(self, headers: list[str], parent=None):
        super().__init__(0, len(headers), parent)
        self.setHorizontalHeaderLabels(headers)     
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(42)
        self.setShowGrid(False)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def enable_filter_header(self) -> FilterHeaderView:
        headers = [self.horizontalHeaderItem(i).text() if self.horizontalHeaderItem(i) else "" for i in range(self.columnCount())]
        filter_header = FilterHeaderView(Qt.Orientation.Horizontal, parent=self)
        self.setHorizontalHeader(filter_header)
        self.setHorizontalHeaderLabels(headers)
        return filter_header

def _is_valid_widget(widget) -> bool:
    if widget is None:
        return False
    try:
        from shiboken6 import isValid
        return isValid(widget)
    except Exception:
        try:
            widget.isVisible()
            return True
        except RuntimeError:
            return False

class ModernTableCard(QFrame):
    clear_filters_requested = Signal()

    def __init__(self, title_text: str = None, headers: list[str] = None, 
                 search_placeholder: str = None, add_button_text: str = None, 
                 add_button_icon: str = "plus-filled.svg", parent=None, i18n=None,
                 custom_table: QTableWidget = None):
        super().__init__(parent)
        self.i18n = i18n
        self.setProperty("role", "card")
        
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(*MARGIN_NONE)
        self.card_layout.setSpacing(SPACING_NONE)
        
        self.lbl_title = None
        self.txt_search = None
        self.btn_add = None
        self.divider = None
        self.header_widget = None
        self.header_main_layout = None
        self.header_top_widget = None
        self.header_top_layout = None
        self.header_layout = None
        self.header_controls_layout = None
        self.header_actions_widget = None
        self.header_actions_layout = None
        self.action_buttons: list[ModernButton] = []
        self.footer_widget = None
        self.footer_divider = None
        self.no_results_overlay = None
        
        if title_text or search_placeholder or add_button_text:
            self._ensure_header()
            
            if title_text:
                self.lbl_title = QLabel(title_text, self.header_top_widget)
                self.lbl_title.setProperty("role", "h3")
                self.header_top_layout.insertWidget(0, self.lbl_title)
                
            if search_placeholder:
                self.txt_search = UnifiedSearchBar(placeholder=search_placeholder, parent=self.header_top_widget)
                self.header_controls_layout.addWidget(self.txt_search)
                
            if add_button_text:
                self.btn_add = ModernButton(add_button_text, role="action_outlined", parent=self.header_top_widget)
                if add_button_icon:
                    self.btn_add.set_icon(add_button_icon, size=16)
                self.header_controls_layout.addWidget(self.btn_add)
            
        self.stack = QStackedWidget(self)
        
        self.table = custom_table if custom_table is not None else ModernTable(headers or [], parent=self)
        self.stack.addWidget(self.table)
        
        self.empty_widget = None
        self.lbl_illustration = None

        self._setup_no_results_overlay()
        
        self.card_layout.addWidget(self.stack, 1)

    def _is_valid(self, widget) -> bool:
        return _is_valid_widget(widget)

    def _setup_no_results_overlay(self):
        if not self._is_valid(self.table):
            return
        self.no_results_overlay = QWidget(self.table)
        self.no_results_overlay.setProperty("role", "table_no_results")
        self.no_results_layout = QVBoxLayout(self.no_results_overlay)
        self.no_results_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_results_layout.setSpacing(SPACING_MD)
        self.no_results_layout.setContentsMargins(*MARGIN_NONE)

        self.lbl_no_results = QLabel(self.no_results_overlay)
        self.lbl_no_results.setProperty("role", "body")
        self.lbl_no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_no_results.setWordWrap(True)

        self.btn_clear_filters = ModernButton("", role="action_outlined", parent=self.no_results_overlay)
        self.btn_clear_filters.set_icon("filter-filled.svg", size=14)
        self.btn_clear_filters.clicked.connect(self.clear_filters)

        self.no_results_layout.addStretch(1)
        self.no_results_layout.addWidget(self.lbl_no_results)
        self.no_results_layout.addWidget(self.btn_clear_filters, alignment=Qt.AlignmentFlag.AlignCenter)
        self.no_results_layout.addStretch(2)

        self.no_results_overlay.hide()
        try:
            self.table.viewport().installEventFilter(self)
        except Exception:
            pass

    def _ensure_header(self):
        if self.header_widget is not None:
            return
        self.header_widget = QWidget(self)
        self.header_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.header_main_layout = QVBoxLayout(self.header_widget)
        self.header_main_layout.setContentsMargins(*MARGIN_MD)
        self.header_main_layout.setSpacing(SPACING_SM)

        self.header_top_widget = QWidget(self.header_widget)
        self.header_top_layout = QHBoxLayout(self.header_top_widget)
        self.header_top_layout.setContentsMargins(*MARGIN_NONE)
        self.header_top_layout.setSpacing(SPACING_MD)
        self.header_layout = self.header_top_layout

        self.header_top_layout.addStretch()

        self.header_controls_layout = QHBoxLayout()
        self.header_controls_layout.setContentsMargins(*MARGIN_NONE)
        self.header_controls_layout.setSpacing(SPACING_SM)
        self.header_top_layout.addLayout(self.header_controls_layout)

        self.header_main_layout.addWidget(self.header_top_widget)

        self.header_actions_widget = QWidget(self.header_widget)
        self.header_actions_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.header_actions_layout = QGridLayout(self.header_actions_widget)
        self.header_actions_layout.setContentsMargins(*MARGIN_NONE)
        self.header_actions_layout.setSpacing(SPACING_SM)
        self.header_actions_widget.hide()
        self.header_main_layout.addWidget(self.header_actions_widget)

        self.card_layout.insertWidget(0, self.header_widget)
        if self.divider is None:
            self.divider = ModernDivider(self)
            self.card_layout.insertWidget(1, self.divider)

    def add_header_control(self, widget: QWidget, insert_before_search: bool = False):
        self._ensure_header()
        if insert_before_search and self.txt_search:
            idx = self.header_controls_layout.indexOf(self.txt_search)
            if idx >= 0:
                self.header_controls_layout.insertWidget(idx, widget)
                return
        self.header_controls_layout.addWidget(widget)

    def add_action_button(self, btn: ModernButton):
        self._ensure_header()
        if btn not in self.action_buttons:
            self.action_buttons.append(btn)
            btn.setParent(self.header_actions_widget)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setMinimumHeight(30)
            self.header_actions_widget.show()
            self.reflow_header_actions()

    def set_action_buttons(self, buttons: list[ModernButton]):
        self._ensure_header()
        self.action_buttons = list(buttons)
        for btn in self.action_buttons:
            btn.setParent(self.header_actions_widget)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setMinimumHeight(30)
        self.reflow_header_actions()

    def reflow_header_actions(self, available_width: int | None = None):
        if not hasattr(self, "header_actions_layout") or self.header_actions_layout is None:
            return
        if not hasattr(self, "action_buttons") or not self.action_buttons:
            return

        visible = [b for b in self.action_buttons if not b.isHidden()]
        if not visible:
            if hasattr(self, "header_actions_widget") and self.header_actions_widget:
                self.header_actions_widget.hide()
            return

        self.header_actions_widget.show()
        if available_width is None:
            available_width = self.width()

        content_width = max(available_width - 32, 280)
        btn_min_width = 115
        cols = max(1, min(len(visible), content_width // btn_min_width))

        while self.header_actions_layout.count() > 0:
            self.header_actions_layout.takeAt(0)

        for c in range(12):
            self.header_actions_layout.setColumnStretch(c, 0)

        for c in range(cols):
            self.header_actions_layout.setColumnStretch(c, 1)

        for i, btn in enumerate(visible):
            self.header_actions_layout.addWidget(btn, i // cols, i % cols)

        self.header_actions_layout.activate()
        self.header_actions_widget.updateGeometry()
        if hasattr(self, "header_main_layout") and self.header_main_layout:
            self.header_main_layout.activate()
        if hasattr(self, "header_widget") and self.header_widget:
            self.header_widget.updateGeometry()
        if hasattr(self, "card_layout") and self.card_layout:
            self.card_layout.activate()

    def set_footer_widget(self, widget: QWidget):
        if hasattr(self, "footer_widget") and self.footer_widget:
            self.card_layout.removeWidget(self.footer_widget)
        if hasattr(self, "footer_divider") and self.footer_divider:
            self.card_layout.removeWidget(self.footer_divider)

        self.footer_divider = ModernDivider(self)
        self.card_layout.addWidget(self.footer_divider)
        self.footer_widget = widget
        self.footer_widget.setParent(self)
        self.card_layout.addWidget(self.footer_widget)

    def setup_empty_state(self, title: str, desc: str, icon_name: str, button_text: str, on_button_clicked, button_icon: str = "plus-filled.svg"):
        self.empty_widget = QWidget(self)
        layout = QVBoxLayout(self.empty_widget)
        layout.setContentsMargins(*MARGIN_XL)
        layout.setSpacing(SPACING_LG)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        illustration_path = get_assets_path(os.path.join("icons", icon_name))
        self.lbl_illustration = ScalableIllustration(
            icon_path=illustration_path,
            aspect_ratio=1.0,
            min_size=120,
            max_size=280,
            size_offset=180,
            parent=self
        )
        
        lbl_title = QLabel(title)
        lbl_title.setProperty("role", "h2")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_desc = QLabel(desc)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setMaximumWidth(450)
        
        self.btn_empty_action = ModernButton(button_text, role="action_outlined")
        if button_icon:
            self.btn_empty_action.set_icon(button_icon, size=16)
        self.btn_empty_action.clicked.connect(on_button_clicked)
        
        layout.addStretch(1)
        layout.addWidget(self.lbl_illustration, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addSpacing(SPACING_MD)
        layout.addWidget(self.btn_empty_action, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(2)
        
        self.stack.addWidget(self.empty_widget)

    def eventFilter(self, watched, event):
        try:
            if self._is_valid(self.table) and watched == self.table.viewport() and event.type() == QEvent.Type.Resize:
                if self._is_valid(self.no_results_overlay) and self.no_results_overlay.isVisible():
                    self._update_no_results_geometry()
        except RuntimeError:
            pass
        return super().eventFilter(watched, event)

    def _update_no_results_geometry(self):
        try:
            if self._is_valid(self.table) and self._is_valid(self.no_results_overlay):
                vp = self.table.viewport()
                if self._is_valid(vp):
                    self.no_results_overlay.setGeometry(vp.geometry())
        except RuntimeError:
            pass

    def clear_filters(self):
        if self.txt_search:
            self.txt_search.clear()
        if hasattr(self.table, "horizontalHeader"):
            header = self.table.horizontalHeader()
            if hasattr(header, "reset_filters"):
                header.reset_filters()
        self.clear_filters_requested.emit()

    def set_no_results(self, show: bool, message: str = ""):
        if not self._is_valid(self.no_results_overlay):
            return
        try:
            if show:
                msg = message
                if not msg and self.i18n:
                    msg = self.i18n.get("common.no_results_filter")
                if not msg:
                    msg = "No se encontraron resultados que coincidan con los filtros aplicados."
                self.lbl_no_results.setText(msg)

                btn_txt = self.i18n.get("common.buttons.clear_filters") if self.i18n else "Limpiar filtros"
                self.btn_clear_filters.setText(btn_txt)

                self._update_no_results_geometry()
                self.no_results_overlay.show()
                self.no_results_overlay.raise_()
            else:
                self.no_results_overlay.hide()
        except RuntimeError:
            pass

    def set_empty(self, is_empty: bool):
        if is_empty and self.stack.count() > 1:
            self.stack.setCurrentIndex(1)
            try:
                if self._is_valid(self.no_results_overlay):
                    self.no_results_overlay.hide()
            except RuntimeError:
                pass
            if self.txt_search and not self.txt_search.text().strip():
                self.txt_search.setVisible(False)
            if hasattr(self, "footer_widget") and self._is_valid(self.footer_widget):
                self.footer_widget.setVisible(False)
            if hasattr(self, "footer_divider") and self._is_valid(self.footer_divider):
                self.footer_divider.setVisible(False)
        else:
            self.stack.setCurrentIndex(0)
            if self.txt_search:
                self.txt_search.setVisible(True)
            if hasattr(self, "footer_widget") and self._is_valid(self.footer_widget):
                self.footer_widget.setVisible(True)
            if hasattr(self, "footer_divider") and self._is_valid(self.footer_divider):
                self.footer_divider.setVisible(True)
        try:
            if is_empty and hasattr(self, "lbl_illustration") and self._is_valid(self.lbl_illustration):
                card_h = max(self.height(), 300)
                self.lbl_illustration.update_image(card_h)
        except RuntimeError:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            if hasattr(self, "header_actions_widget") and self._is_valid(self.header_actions_widget) and hasattr(self, "action_buttons") and self.action_buttons:
                self.reflow_header_actions(available_width=event.size().width())
        except RuntimeError:
            pass
        try:
            if self._is_valid(self.no_results_overlay) and self.no_results_overlay.isVisible():
                self._update_no_results_geometry()
        except RuntimeError:
            pass
        try:
            if hasattr(self, "lbl_illustration") and self._is_valid(self.lbl_illustration) and self.stack.currentIndex() == 1:
                card_h = max(self.height(), 300)
                self.lbl_illustration.update_image(card_h)
        except RuntimeError:
            pass

    def set_title_count(
        self,
        base_title: str,
        count: int,
        total_count: int | None = None,
        extra_suffix: str = "",
        filtered_format: str | None = None
    ):
        if not self.lbl_title:
            return

        if total_count is not None and count < total_count:
            fmt = filtered_format
            if not fmt and hasattr(self, "i18n") and self.i18n:
                fmt = self.i18n.get("common.filtered_count")
            if fmt and "{count}" in fmt and "{total}" in fmt:
                cnt_str = fmt.replace("{count}", str(count)).replace("{total}", str(total_count))
            else:
                cnt_str = f"({count} / {total_count})"
            self.lbl_title.setText(f"{base_title} {cnt_str}{extra_suffix}")
        else:
            self.lbl_title.setText(f"{base_title} ({count}){extra_suffix}")

    def enable_filter_header(self) -> FilterHeaderView:
        return self.table.enable_filter_header()

class TableActionCell(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(*MARGIN_NONE)
        self.layout.setSpacing(SPACING_SM)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
    def add_switch(self, checked: bool, callback) -> ModernSwitch:
        sw = ModernSwitch(self)
        sw.setChecked(checked)
        sw.toggled.connect(callback)
        self.layout.addWidget(sw)
        self.layout.addSpacing(SPACING_XS)
        return sw
        
    def add_button(self, icon_name: str, color: str, role: str, tooltip: str, callback) -> ModernButton:
        btn = ModernButton("", role=role, parent=self)
        btn.setFixedSize(24, 24)
        btn.setIcon(get_icon_colored(icon_name, color, size=16))
        btn.setIconSize(QSize(16, 16))
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        self.layout.addWidget(btn)
        return btn

class PlatformBadgeCell(QWidget):
    def __init__(self, platforms: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(*MARGIN_H_SM)
        self.layout.setSpacing(SPACING_SM)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if platforms is not None:
            self.set_platforms(platforms)

    def set_platforms(self, platforms: list[str]):
        while self.layout.count() > 0:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not platforms:
            lbl_empty = QLabel("-", self)
            lbl_empty.setProperty("role", "body")
            self.layout.addWidget(lbl_empty)
            return

        from frontend.common import COLOR_GREEN, COLOR_TWITCH, COLOR_YOUTUBE, COLOR_TIKTOK, get_pixmap_colored
        plat_configs = {
            "kick": ("brand-kick.svg", COLOR_GREEN, "Kick"),
            "twitch": ("brand-twitch.svg", COLOR_TWITCH, "Twitch"),
            "youtube": ("brand-youtube.svg", COLOR_YOUTUBE, "YouTube"),
            "tiktok": ("brand-tiktok.svg", COLOR_TIKTOK, "TikTok"),
        }

        for p in platforms:
            p_key = p.lower()
            if p_key in plat_configs:
                icon_file, color, name = plat_configs[p_key]
                lbl_icon = QLabel(self)
                lbl_icon.setPixmap(get_pixmap_colored(icon_file, color, 16))
                lbl_icon.setToolTip(name)
                self.layout.addWidget(lbl_icon)

        self.layout.addStretch()

