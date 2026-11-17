# frontend\navigation\sidebar_component.py
"""Barra lateral de navegación."""

from PySide6.QtWidgets import QBoxLayout, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy, QWidget, QButtonGroup, QScrollArea
from PySide6.QtCore import Qt, QPropertyAnimation, QSize, Signal, QEasingCurve, Property, QEvent
from PySide6.QtGui import QPainter, QPixmap, QColor
from frontend.common import get_icon, get_icon_colored, create_circular_pixmap, get_pixmap_colored, Palette, Size
from frontend.widgets import configure_icon_only_button

_BADGE_INSET = 2
_BADGE_RIGHT_MARGIN = 10
_LAYOUT_PENDING_SIZE = 10

class Sidebar(QFrame):
    _SECTIONS = ("main", "stream", "tools", "system")
    view_selected = Signal(str)
    section_viewed = Signal(str)
    update_requested = Signal()

    def __init__(self, i18n, app_version: str = "", parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.app_version = app_version
        self.has_update = False
        self._update_dismissed = False
        self._current_avatar_bytes = None
        self._has_profile_avatar = False
        self._default_avatar_pixmap = None
        self.anim = None
        self._has_version = bool(app_version)
        self.setProperty("role", "sidebar")
        self.is_expanded = True
        self.expanded_width = Size.SIDEBAR_EXPANDED
        self.collapsed_width = Size.SIDEBAR_COLLAPSED
        self.setFixedWidth(self.expanded_width)

        self._icon_collapse = get_icon_colored("chevrons-left.svg", Palette.NEUTRAL_050, Size.ICON_SMALL)
        self._icon_expand = get_icon_colored("chevrons-right.svg", Palette.NEUTRAL_050, Size.ICON_SMALL)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.buttonClicked.connect(self._on_tab_clicked)

        self.nav_buttons = []
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(*Size.Margin.MRG_XSM)
        self.main_layout.setSpacing(Size.SPACING_SM)

        self.header_container = QWidget()
        self.header_layout = QHBoxLayout(self.header_container)
        self.header_layout.setContentsMargins(*Size.Margin.MRG_NON)
        self.header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.logo_btn = QPushButton()
        self.logo_btn.setIcon(get_icon("logo.svg"))
        configure_icon_only_button(self.logo_btn)
        self.logo_btn.setProperty("role", "btn_ghost")

        self.title_label = QLabel("MiniKick")
        self.title_label.setProperty("role", "text_h2")

        plain_version = self.app_version.lstrip("vV")
        self.lbl_version = QLabel(f"v{plain_version}", self.header_container)
        self.lbl_version.setProperty("role", "badge_kick")
        self.lbl_version.setToolTip(self.i18n.get("main.sidebar.version").replace("{version}", plain_version))
        self.lbl_version.setVisible(self._has_version)

        self.expanded_spacer = QWidget()
        self.expanded_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.btn_toggle = QPushButton()
        self.btn_toggle.setProperty("role", "btn_ghost")
        self.btn_toggle.setIcon(get_icon_colored("chevrons-left.svg", size=Size.ICON_SMALL))
        configure_icon_only_button(self.btn_toggle)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_sidebar)

        self.toggle_badge = QLabel("N", self.btn_toggle)
        self.toggle_badge.setProperty("role", "badge_new")
        self.toggle_badge.setProperty("state", "collapsed")
        self.toggle_badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.toggle_badge.setFixedSize(Size.BADGE_DOT, Size.BADGE_DOT)
        self.toggle_badge.move(Size.ICON_BASIC - Size.BADGE_DOT + _BADGE_INSET, _BADGE_INSET)
        self.toggle_badge.setVisible(False)

        self.header_layout.addWidget(self.logo_btn)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addWidget(self.lbl_version)
        self.header_layout.addWidget(self.expanded_spacer)
        self.header_layout.addWidget(self.btn_toggle)
        self.main_layout.addWidget(self.header_container)
        self.main_layout.addSpacing(Size.SPACING_SM)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(*Size.Margin.MRG_NON)
        scroll_layout.setSpacing(Size.SPACING_SM)

        self.section_headers: dict[str, QLabel] = {}
        self.section_layouts: dict[str, QVBoxLayout] = {}
        last_section = self._SECTIONS[-1]
        for section in self._SECTIONS:
            if section == last_section:
                scroll_layout.addStretch(1)
            title = self.i18n.get(f"main.sidebar.section.{section}")
            header = QLabel(title.upper() if title else "")
            header.setProperty("role", "text_caption")
            scroll_layout.addWidget(header)

            nav_layout = QVBoxLayout()
            nav_layout.setContentsMargins(*Size.Margin.MRG_NON)
            nav_layout.setSpacing(Size.SPACING_XS)
            scroll_layout.addLayout(nav_layout)
            if section != last_section:
                scroll_layout.addSpacing(Size.SPACING_MD)
            self.section_headers[section] = header
            self.section_layouts[section] = nav_layout

        self.scroll_area.setWidget(scroll_content)
        self.main_layout.addWidget(self.scroll_area, stretch=1)
        self.main_layout.addSpacing(Size.SPACING_SM)

        self._setup_update_card()
        self.main_layout.addWidget(self.update_card)

        self.btn_collapsed_update = QPushButton()
        self.btn_collapsed_update.setProperty("role", "action_outlined")
        self.btn_collapsed_update.setIcon(get_icon_colored("cloud-download.svg"))
        configure_icon_only_button(self.btn_collapsed_update)
        self.btn_collapsed_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_collapsed_update.clicked.connect(self._on_update_action_clicked)
        self.btn_collapsed_update.setVisible(False)
        self.main_layout.addWidget(self.btn_collapsed_update, alignment=Qt.AlignmentFlag.AlignCenter)

        self._setup_profile_card()
        self.main_layout.addWidget(self.profile_card)

    def _setup_update_card(self):
        self.update_card = QFrame()
        self.update_card.setProperty("role", "update_banner_card")

        card_layout = QVBoxLayout(self.update_card)
        card_layout.setContentsMargins(*Size.Margin.MRG_MED)
        card_layout.setSpacing(Size.SPACING_MD)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(*Size.Margin.MRG_NON)
        top_row.setSpacing(Size.SPACING_SM)

        self.lbl_update_title = QLabel(self.i18n.get("main.sidebar.update_card.title"))
        self.lbl_update_title.setProperty("role", "text_h2")
        self.lbl_update_title.setWordWrap(True)
        top_row.addWidget(self.lbl_update_title, stretch=1, alignment=Qt.AlignmentFlag.AlignTop)

        self.btn_dismiss_update = QPushButton()
        self.btn_dismiss_update.setProperty("role", "btn_dismiss")
        self.btn_dismiss_update.setIcon(get_icon_colored("x.svg"))
        configure_icon_only_button(self.btn_dismiss_update)
        self.btn_dismiss_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dismiss_update.setToolTip(self.i18n.get("main.sidebar.update_card.tooltip_dismiss"))
        self.btn_dismiss_update.clicked.connect(self._dismiss_update_card)
        top_row.addWidget(self.btn_dismiss_update, alignment=Qt.AlignmentFlag.AlignTop)

        card_layout.addLayout(top_row)

        self.lbl_update_desc = QLabel(self.i18n.get("main.sidebar.update_card.desc").replace("{version}", ""))
        self.lbl_update_desc.setProperty("role", "text_caption")
        self.lbl_update_desc.setWordWrap(True)
        card_layout.addWidget(self.lbl_update_desc)

        self.btn_update_action = QPushButton(self.i18n.get("main.sidebar.update_card.btn"))
        self.btn_update_action.setProperty("role", "action_outlined")
        self.btn_update_action.setIcon(get_icon_colored("cloud-download.svg"))
        self.btn_update_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update_action.clicked.connect(self._on_update_action_clicked)
        card_layout.addWidget(self.btn_update_action)

        self.update_card.setVisible(False)

    def _setup_profile_card(self):
        self.profile_card = QFrame()
        self.profile_card.setProperty("role", "profile_card")

        self.profile_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.profile_card)
        self.profile_layout.setContentsMargins(*Size.Margin.MRG_MED)
        self.profile_layout.setSpacing(Size.SPACING_SM)
        self.profile_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.profile_avatar = QLabel()
        self.profile_avatar.setFixedSize(Size.AVATAR_SM, Size.AVATAR_SM)
        self.profile_avatar.setScaledContents(True)
        self.reset_profile_avatar()

        self.profile_text_widget = QWidget()
        self.profile_text_layout = QVBoxLayout(self.profile_text_widget)
        self.profile_text_layout.setContentsMargins(*Size.Margin.MRG_NON)
        self.profile_text_layout.setSpacing(Size.SPACING_XS)

        self.profile_name_lbl = QLabel()
        self.profile_name_lbl.setProperty("role", "text_section_header")

        self.profile_role_lbl = QLabel()
        self.profile_role_lbl.setProperty("role", "text_caption")

        self.profile_text_layout.addWidget(self.profile_name_lbl)
        self.profile_text_layout.addWidget(self.profile_role_lbl)

        self.profile_layout.addWidget(self.profile_avatar)
        self.profile_layout.addWidget(self.profile_text_widget, stretch=1)

        self.reset_profile_info()

    def update_profile_info(self, username: str, status_or_role: str):
        self.profile_name_lbl.setText(username)
        self.profile_role_lbl.setText(status_or_role)

    def update_profile_avatar(self, image_data: bytes):
        if self._current_avatar_bytes == image_data and self._has_profile_avatar:
            return
        self._current_avatar_bytes = image_data
        dpr = self.devicePixelRatio()
        target_physical = int(Size.AVATAR_SM * dpr)
        pixmap = create_circular_pixmap(image_data, target_size=target_physical)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                target_physical, target_physical,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            scaled_pixmap.setDevicePixelRatio(dpr)
            self.profile_avatar.setPixmap(scaled_pixmap)
            self._has_profile_avatar = True
        else:
            self._has_profile_avatar = False
            self.reset_profile_avatar()

    def reset_profile_avatar(self):
        if self._default_avatar_pixmap is not None and not self._default_avatar_pixmap.isNull():
            self.profile_avatar.setPixmap(self._default_avatar_pixmap)
            return

        dpr = self.devicePixelRatio()
        logical_size = Size.AVATAR_SM
        physical_size = int(logical_size * dpr)

        icon_pixmap = get_pixmap_colored("user.svg", size=Size.ICON_SMALL, dpr=dpr)

        circle_pixmap = QPixmap(physical_size, physical_size)
        circle_pixmap.fill(Qt.GlobalColor.transparent)
        circle_pixmap.setDevicePixelRatio(dpr)

        painter = QPainter(circle_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor(Palette.NEUTRAL_900))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, logical_size, logical_size)

        icon_inset = (logical_size - Size.ICON_SMALL) // 2
        painter.drawPixmap(icon_inset, icon_inset, icon_pixmap)
        painter.end()

        self._default_avatar_pixmap = circle_pixmap
        self.profile_avatar.setPixmap(circle_pixmap)

    def reset_profile_info(self):
        offline_name = self.i18n.get("main.sidebar.profile.offline_name")
        offline_status = self.i18n.get("common.status.offline")
        self.profile_name_lbl.setText(offline_name)
        self.profile_role_lbl.setText(offline_status)
        self.reset_profile_avatar()

    def set_update_available(self, available: bool = True, version: str = ""):
        self.has_update = available
        if version:
            self.lbl_update_desc.setText(self.i18n.get("main.sidebar.update_card.desc").replace("{version}", version))
            collapsed_tooltip = self.i18n.get("main.sidebar.update_card.tooltip_collapsed").replace("{version}", version)
            self.btn_collapsed_update.setToolTip(collapsed_tooltip)
        self._update_notification_visibility()

    def _dismiss_update_card(self):
        self._update_dismissed = True
        self._update_notification_visibility()

    def _on_update_action_clicked(self):
        self.update_requested.emit()

    def _update_notification_visibility(self):
        if self.has_update and not self._update_dismissed:
            if self.is_expanded:
                self.update_card.setVisible(True)
                self.btn_collapsed_update.setVisible(False)
            else:
                self.update_card.setVisible(False)
                self.btn_collapsed_update.setVisible(True)
        else:
            self.update_card.setVisible(False)
            self.btn_collapsed_update.setVisible(False)

    def add_tab(self, name, icon_name, is_active=False, position="main"):
        key_name = name.lower().replace(" ", "_")
        display_name = self.i18n.get(f"main.sidebar.tabs.{key_name}")
        btn = QPushButton(display_name)
        btn.setProperty("role", "nav_button")
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("original_text", display_name)
        btn.setProperty("view_name", name)
        btn.setProperty("icon_name", icon_name)

        btn.setIcon(get_icon_colored(icon_name, Palette.NEUTRAL_050, Size.ICON_SMALL))
        btn.setFixedHeight(Size.NAV_BUTTON_HEIGHT)
        btn.setToolTip("" if self.is_expanded else display_name)

        if is_active:
            btn.setChecked(True)

        badge = QLabel("N", btn)
        badge.setProperty("role", "badge_new")
        badge.setProperty("state", "normal")
        badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        badge.setToolTip(self.i18n.get("whats_new.badge.tooltip"))
        badge.setVisible(False)
        btn.badge_label = badge
        btn.installEventFilter(self)

        self.button_group.addButton(btn)
        self.nav_buttons.append(btn)

        if position == "profile":
            btn.setText("")
            btn.setToolTip(display_name)
            btn.setProperty("profile_action", True)
            btn.setProperty("collapsed", True)
            configure_icon_only_button(btn)
            self.profile_layout.addWidget(btn)
            return
        self.section_layouts.get(position, self.section_layouts[self._SECTIONS[0]]).addWidget(btn)

    def set_tab_badge(self, tab_name: str, show: bool = True):
        for btn in self.nav_buttons:
            if btn.property("view_name") == tab_name:
                if hasattr(btn, "badge_label"):
                    btn.badge_label.setVisible(show)
                    self._position_badge(btn)
                break
        self._update_toggle_badge()

    def select_tab(self, view_name: str) -> None:
        """Navega a una vista como si se hubiera pulsado su botón."""
        for btn in self.nav_buttons:
            if btn.property("view_name") == view_name:
                btn.click()
                return

    def clear_tab_badge(self, tab_name: str):
        self.set_tab_badge(tab_name, False)

    @staticmethod
    def _set_badge_state(badge: QLabel, state: str, size: int) -> None:
        if badge.property("state") != state:
            badge.setProperty("state", state)
            badge.style().unpolish(badge)
            badge.style().polish(badge)
        badge.setFixedSize(size, size)

    def _position_badge(self, btn):
        if not hasattr(btn, "badge_label") or not btn.badge_label.isVisible():
            return
        if not self.is_expanded or btn.property("profile_action"):
            self._set_badge_state(btn.badge_label, "collapsed", Size.BADGE_DOT)
            btn_w = btn.width() if btn.width() > _LAYOUT_PENDING_SIZE else self.collapsed_width
            btn.badge_label.move(btn_w - (Size.BADGE_DOT + _BADGE_INSET), _BADGE_INSET)
        else:
            self._set_badge_state(btn.badge_label, "normal", Size.BADGE_MIN)
            btn_w = btn.width() if btn.width() > self.collapsed_width else (self.expanded_width - Size.SPACING_XL)
            btn_h = btn.height() if btn.height() > _LAYOUT_PENDING_SIZE else Size.NAV_BUTTON_HEIGHT
            btn.badge_label.move(btn_w - (Size.BADGE_MIN + _BADGE_RIGHT_MARGIN), (btn_h - Size.BADGE_MIN) // 2)
        btn.badge_label.raise_()

    def _update_toggle_badge(self):
        has_any_unseen = any(
            hasattr(b, "badge_label") and b.badge_label.isVisible()
            for b in self.nav_buttons
        )
        self.toggle_badge.setVisible(has_any_unseen and not self.is_expanded)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Resize and watched in self.nav_buttons:
            self._position_badge(watched)
        return super().eventFilter(watched, event)

    def showEvent(self, event):
        super().showEvent(event)
        for btn in self.nav_buttons:
            self._position_badge(btn)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for btn in self.nav_buttons:
            self._position_badge(btn)
        self._update_toggle_badge()

    def _get_sidebar_width(self) -> int:
        return self.width()

    def _set_sidebar_width(self, w: int) -> None:
        self.setFixedWidth(w)

    sidebar_width = Property(int, _get_sidebar_width, _set_sidebar_width)

    def toggle_sidebar(self):
        self.is_expanded = not self.is_expanded
        target_width = self.expanded_width if self.is_expanded else self.collapsed_width

        icon = self._icon_collapse if self.is_expanded else self._icon_expand
        self.btn_toggle.setIcon(icon)

        if self.anim is not None and self.anim.state() == QPropertyAnimation.State.Running:
            self.anim.stop()

        self.anim = QPropertyAnimation(self, b"sidebar_width")
        self.anim.setDuration(220)
        self.anim.setStartValue(self.width())
        self.anim.setEndValue(target_width)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.finished.connect(self._on_animation_finished)

        if not self.is_expanded:
            self.logo_btn.hide()
            self.title_label.hide()
            self.lbl_version.hide()
            self.expanded_spacer.hide()
            self.header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._update_texts_and_styles(show=False)

        self.anim.start()

    def _update_texts_and_styles(self, show: bool):
        for btn in self.nav_buttons:
            if btn.property("profile_action"):
                self._position_badge(btn)
                continue
            btn.setText(btn.property("original_text") if show else "")
            btn.setToolTip("" if show else btn.property("original_text"))
            btn.setProperty("collapsed", not show)
            if show:
                btn.setProperty("icon_only", False)
                btn.setMinimumWidth(0)
                btn.setMaximumWidth(16777215)
                btn.setFixedHeight(Size.NAV_BUTTON_HEIGHT)
            else:
                configure_icon_only_button(btn)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            self._position_badge(btn)

        alignment = Qt.AlignmentFlag.AlignTop if show else Qt.AlignmentFlag.AlignHCenter
        for section in self._SECTIONS:
            self.section_layouts[section].setAlignment(alignment)
            self.section_headers[section].setVisible(show)
        self._update_notification_visibility()
        self._update_toggle_badge()

        self.profile_text_widget.setVisible(show)
        self.profile_layout.setDirection(
            QBoxLayout.Direction.LeftToRight if show else QBoxLayout.Direction.TopToBottom
        )
        if show:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.profile_layout.setContentsMargins(*Size.Margin.MRG_XSM)
            self.profile_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        else:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.profile_layout.setContentsMargins(*Size.Margin.MRG_XSM)
            self.profile_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _on_animation_finished(self):
        if self.is_expanded:
            self.header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.logo_btn.show()
            self.title_label.show()
            self.lbl_version.setVisible(self._has_version)
            self.expanded_spacer.show()
            self._update_texts_and_styles(show=True)
        else:
            for btn in self.nav_buttons:
                self._position_badge(btn)
            self._update_toggle_badge()

    def _on_tab_clicked(self, btn):
        view_name = btn.property("view_name")
        if hasattr(btn, "badge_label") and btn.badge_label.isVisible():
            btn.badge_label.setVisible(False)
            self._update_toggle_badge()
            self.section_viewed.emit(view_name)
        self.view_selected.emit(view_name)
