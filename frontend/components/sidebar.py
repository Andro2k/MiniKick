from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QSizePolicy, QWidget, QButtonGroup)
from PySide6.QtCore import Qt, QPropertyAnimation, QParallelAnimationGroup, QSize, Signal, QEasingCurve
from frontend.utils import get_icon, get_icon_colored
from frontend.theme import COLOR_TEXT_SECONDARY, COLOR_ACCENT

class Sidebar(QFrame):
    view_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.is_expanded = True
        self.expanded_width = 250
        self.collapsed_width = 65
        self.setFixedWidth(self.expanded_width)
        
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.buttonClicked.connect(self._on_tab_clicked)
        
        self.nav_buttons = []
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 20, 10, 20)
        self.main_layout.setSpacing(8)
        
        # --- HEADER ---
        self.header_container = QWidget()
        self.header_layout = QHBoxLayout(self.header_container)
        self.header_layout.setContentsMargins(0, 0, 0, 0) 
        self.header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        
        self.logo_btn = QPushButton()
        self.logo_btn.setIcon(get_icon("logo.svg")) 
        self.logo_btn.setIconSize(QSize(30, 30))
        self.logo_btn.setStyleSheet("border: none; background: transparent;")
        
        self.title_label = QLabel("MiniKick")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding-left: 6px;")
        
        self.expanded_spacer = QWidget()
        self.expanded_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        self.btn_toggle = QPushButton()
        self.btn_toggle.setIcon(get_icon_colored("chevron-left.svg", COLOR_TEXT_SECONDARY)) 
        self.btn_toggle.setFixedSize(30, 30)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        
        self.header_layout.addWidget(self.logo_btn)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addWidget(self.expanded_spacer) 
        self.header_layout.addWidget(self.btn_toggle)
        self.main_layout.addWidget(self.header_container)
        self.main_layout.addSpacing(24)
        
        # --- NAVEGACIÓN SUPERIOR ---
        self.nav_layout = QVBoxLayout()
        self.nav_layout.setSpacing(4)
        self.main_layout.addLayout(self.nav_layout)
        
        self.main_layout.addStretch()

    def add_tab(self, name, icon_name, is_active=False):
        btn = QPushButton(name)
        btn.setObjectName("NavButton")
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn.setProperty("original_text", name)
        btn.setProperty("view_name", name)
        btn.setProperty("icon_name", icon_name)
        
        icon_color = COLOR_ACCENT if is_active else COLOR_TEXT_SECONDARY
        btn.setIcon(get_icon_colored(icon_name, icon_color, 22))
        
        # Estilo inicial expandido
        btn.setStyleSheet("text-align: left; padding-left: 12px;")
        
        if is_active:
            btn.setChecked(True)
            
        self.button_group.addButton(btn)
        self.nav_buttons.append(btn)
        self.nav_layout.addWidget(btn)

    def toggle_sidebar(self):
        self.is_expanded = not self.is_expanded
        target_width = self.expanded_width if self.is_expanded else self.collapsed_width
        
        self.btn_toggle.setIcon(get_icon_colored("chevron-left.svg" if self.is_expanded else "chevron-right.svg", COLOR_TEXT_SECONDARY))
        
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
            
            if show:
                btn.setStyleSheet("text-align: left; padding-left: 12px;")
            else:
                # El padding 0px garantiza el centrado absoluto al contraer
                btn.setStyleSheet("text-align: center; padding: 10px;")
                
            btn.setProperty("collapsed", not show)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

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

    def _on_tab_clicked(self, btn):
        for b in self.button_group.buttons():
            color = COLOR_ACCENT if b.isChecked() else COLOR_TEXT_SECONDARY
            b.setIcon(get_icon_colored(b.property("icon_name"), color, 22))
        self.view_selected.emit(btn.property("view_name"))