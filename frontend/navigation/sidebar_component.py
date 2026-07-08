# frontend\navigation\sidebar_component.py

from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QSizePolicy, QWidget, QButtonGroup)
from PySide6.QtCore import Qt, QPropertyAnimation, QParallelAnimationGroup, QSize, Signal, QEasingCurve
from PySide6.QtGui import QPainter, QPixmap, QColor
from frontend.common.utils import get_icon, get_icon_colored, create_circular_pixmap
from frontend.common.theme import COLOR_NEUTRAL_950, COLOR_NEUTRAL_400, COLOR_GREEN, COLOR_NEUTRAL_800
from backend.config.version import APP_VERSION

class Sidebar(QFrame):
    view_selected = Signal(str)

    def __init__(self, i18n, app_version: str = APP_VERSION):
        super().__init__()
        self.i18n = i18n
        self.app_version = app_version
        self.has_update = False  
        self.setProperty("role", "sidebar")
        self.is_expanded = True
        self.expanded_width = 230
        self.collapsed_width = 60
        self.setFixedWidth(self.expanded_width)
        
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.buttonClicked.connect(self._on_tab_clicked)
        self.button_group.buttonToggled.connect(self._update_icons)
        
        self.nav_buttons = []
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(8)

        self.header_container = QWidget()
        self.header_layout = QHBoxLayout(self.header_container)
        self.header_layout.setContentsMargins(0, 0, 0, 0) 
        self.header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        
        self.logo_btn = QPushButton()
        self.logo_btn.setIcon(get_icon("logo.svg")) 
        self.logo_btn.setIconSize(QSize(30, 30))
        self.logo_btn.setProperty("role", "btn_ghost")
        
        self.title_label = QLabel("MiniKick")
        self.title_label.setProperty("role", "h3")
        
        self.expanded_spacer = QWidget()
        self.expanded_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        self.btn_toggle = QPushButton()
        self.btn_toggle.setProperty("role", "btn_ghost")
        self.btn_toggle.setIcon(get_icon_colored("chevron-left-pipe.svg", COLOR_NEUTRAL_400)) 
        self.btn_toggle.setFixedSize(36, 36)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        
        self.header_layout.addWidget(self.logo_btn)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addWidget(self.expanded_spacer) 
        self.header_layout.addWidget(self.btn_toggle)
        self.main_layout.addWidget(self.header_container)
        self.main_layout.addSpacing(16)
        
        navigate_text = self.i18n.get("main.sidebar.section.navigate")
        self.lbl_navigate_header = QLabel(navigate_text)
        self.lbl_navigate_header.setProperty("role", "body")
        self.main_layout.addWidget(self.lbl_navigate_header)
        
        self.top_nav_layout = QVBoxLayout()
        self.top_nav_layout.setContentsMargins(0, 0, 0, 0)
        self.top_nav_layout.setSpacing(4)
        self.main_layout.addLayout(self.top_nav_layout)
        self.main_layout.addStretch()

        more_text = self.i18n.get("main.sidebar.section.more")
        self.lbl_more_header = QLabel(more_text)
        self.lbl_more_header.setProperty("role", "body")
        self.main_layout.addWidget(self.lbl_more_header)

        self.bottom_nav_layout = QVBoxLayout()
        self.bottom_nav_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_nav_layout.setSpacing(4)
        self.main_layout.addLayout(self.bottom_nav_layout)
        self.main_layout.addSpacing(8)
        
        self._setup_profile_card()
        self.main_layout.addWidget(self.profile_card)
        self.main_layout.addSpacing(8)
        
        self.btn_update_rewards = QPushButton(self.i18n.get("main.sidebar.new_version"))
        self.btn_update_rewards.setProperty("role", "action_accent")
        self.btn_update_rewards.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update_rewards.setIcon(get_icon_colored("cloud-download.svg", COLOR_NEUTRAL_950, 14))
        
        self.btn_update_rewards.setVisible(False)
        self.btn_update_rewards.clicked.connect(self._on_update_rewards_clicked)
        self.main_layout.addWidget(self.btn_update_rewards)

        version_text = self.i18n.get("main.sidebar.version").replace("{version}", self.app_version)
        self.lbl_version = QLabel(version_text)
        self.lbl_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_version.setProperty("role", "caption")
        self.main_layout.addWidget(self.lbl_version)

    def _setup_profile_card(self):
        self.profile_card = QFrame()
        self.profile_card.setProperty("role", "profile_card")
        
        self.profile_layout = QHBoxLayout(self.profile_card)
        self.profile_layout.setContentsMargins(8, 8, 8, 8)
        self.profile_layout.setSpacing(6)
        self.profile_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.profile_avatar = QLabel()
        self.profile_avatar.setFixedSize(36, 36)
        self.profile_avatar.setScaledContents(True)
        self.reset_profile_avatar()
        
        self.profile_text_widget = QWidget()
        self.profile_text_layout = QVBoxLayout(self.profile_text_widget)
        self.profile_text_layout.setContentsMargins(0, 0, 0, 0)
        self.profile_text_layout.setSpacing(2)
        
        self.profile_name_lbl = QLabel()
        self.profile_name_lbl.setObjectName("body")
        
        self.profile_role_lbl = QLabel()
        self.profile_role_lbl.setObjectName("caption")
        
        self.profile_text_layout.addWidget(self.profile_name_lbl)
        self.profile_text_layout.addWidget(self.profile_role_lbl)
        
        self.profile_layout.addWidget(self.profile_avatar)
        self.profile_layout.addWidget(self.profile_text_widget, stretch=1)
        
        self.profile_card.setCursor(Qt.CursorShape.PointingHandCursor)
        self.profile_card.mousePressEvent = self._on_profile_card_clicked
        self.reset_profile_info()

    def _on_profile_card_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.view_selected.emit("Dashboard")
            for btn in self.nav_buttons:
                if btn.property("view_name") == "Dashboard":
                    btn.setChecked(True)
                    self._update_icons()
                    break

    def update_profile_info(self, username: str, status_or_role: str):
        self.profile_name_lbl.setText(username)
        self.profile_role_lbl.setText(status_or_role)

    def update_profile_avatar(self, image_data: bytes):
        pixmap = create_circular_pixmap(image_data)
        if not pixmap.isNull():
            self.profile_avatar.setPixmap(pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.reset_profile_avatar()

    def reset_profile_avatar(self):
        icon_pixmap = get_icon_colored("user.svg", COLOR_NEUTRAL_400, 36).pixmap(36, 36)
        
        circle_pixmap = QPixmap(36, 36)
        circle_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(circle_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setBrush(QColor(COLOR_NEUTRAL_800))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 36, 36)
        
        painter.drawPixmap(6, 6, 24, 24, icon_pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        painter.end()
        
        self.profile_avatar.setPixmap(circle_pixmap)

    def reset_profile_info(self):
        offline_name = self.i18n.get("main.sidebar.profile.offline_name")
        offline_status = self.i18n.get("common.status.offline")
        self.profile_name_lbl.setText(offline_name)
        self.profile_role_lbl.setText(offline_status)
        self.reset_profile_avatar()

    def set_update_available(self, available: bool = True):
        self.has_update = available
        if self.is_expanded:
            self.btn_update_rewards.setVisible(available)

    def _on_update_rewards_clicked(self):
        for btn in self.nav_buttons:
            if btn.property("view_name") == "Settings":
                btn.setChecked(True)
                self._on_tab_clicked(btn)
                break

    def add_tab(self, name, icon_name, is_active=False, position="top"):
        key_name = name.lower().replace(" ", "_")
        display_name = self.i18n.get(f"main.sidebar.tabs.{key_name}")
        btn = QPushButton(display_name)
        btn.setProperty("role", "nav_button")
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)       
        btn.setProperty("original_text", display_name)
        btn.setProperty("view_name", name)
        btn.setProperty("icon_name", icon_name)        
        icon_color = COLOR_GREEN if is_active else COLOR_NEUTRAL_400
        btn.setIcon(get_icon_colored(icon_name, icon_color, 28))
        btn.setToolTip("" if self.is_expanded else display_name)
        
        if is_active:
            btn.setChecked(True)
            
        self.button_group.addButton(btn)
        self.nav_buttons.append(btn)

        if position == "bottom":
            self.bottom_nav_layout.addWidget(btn)
        else:
            self.top_nav_layout.addWidget(btn)

    def toggle_sidebar(self):
        self.is_expanded = not self.is_expanded
        target_width = self.expanded_width if self.is_expanded else self.collapsed_width
        
        self.btn_toggle.setIcon(get_icon_colored("chevron-left-pipe.svg" if self.is_expanded else "chevron-right-pipe.svg", COLOR_NEUTRAL_400))
        
        self.anim_group = QParallelAnimationGroup()
        for prop in [b"minimumWidth", b"maximumWidth"]:
            anim = QPropertyAnimation(self, prop)
            anim.setDuration(250)
            anim.setStartValue(self.width())
            anim.setEndValue(target_width)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.anim_group.addAnimation(anim)
        
        if not self.is_expanded:
            self.logo_btn.hide()
            self.title_label.hide()
            self.expanded_spacer.hide()
            self.header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._update_texts_and_styles(show=False)
        else:
            self.anim_group.finished.connect(self._on_expand_finished)
            
        self.anim_group.start()

    def _update_texts_and_styles(self, show: bool):
        for btn in self.nav_buttons:
            btn.setText(btn.property("original_text") if show else "")
            btn.setToolTip("" if show else btn.property("original_text"))
            btn.setProperty("collapsed", not show)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        self.lbl_navigate_header.setVisible(show)
        self.lbl_more_header.setVisible(show)
        self.lbl_version.setVisible(show)
        if self.has_update:
            self.btn_update_rewards.setVisible(show)
            
        self.profile_text_widget.setVisible(show)
        if show:
            self.profile_layout.setContentsMargins(8, 8, 8, 8)
            self.profile_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        else:
            self.profile_layout.setContentsMargins(0, 8, 0, 8)
            self.profile_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _on_expand_finished(self):
        if self.is_expanded:
            self.header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.logo_btn.show()
            self.title_label.show()
            self.expanded_spacer.show()
            self._update_texts_and_styles(show=True)
            try:
                self.anim_group.finished.disconnect(self._on_expand_finished)
            except RuntimeError:
                pass

    def _update_icons(self, btn=None, checked=None):
        for b in self.button_group.buttons():
            color = COLOR_GREEN if b.isChecked() else COLOR_NEUTRAL_400
            b.setIcon(get_icon_colored(b.property("icon_name"), color, 28))

    def _on_tab_clicked(self, btn):
        self.view_selected.emit(btn.property("view_name"))