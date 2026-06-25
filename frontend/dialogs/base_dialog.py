# frontend\dialogs\base_dialogs.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QSizePolicy, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QColor, QMouseEvent

from frontend.common.theme import COLOR_DANGER, PATH_ICON_HELP

class ModernFramelessShell(QDialog):
    def __init__(self, width: int = 420, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._old_drag_pos = None

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.container = QFrame()
        self.container.setProperty("role", "dialog")
        self.container.setProperty("state", "neutral")
        self.container.setFixedWidth(width)
        self.container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(30)
        self.glow.setOffset(0, 0)
        self.glow.setColor(QColor(0, 0, 0, 0))
        self.container.setGraphicsEffect(self.glow)

        self.main_layout.addWidget(self.container)

    def set_dialog_state(self, state: str, glow_color: QColor = None):
        self.container.setProperty("state", state)
        self.container.style().unpolish(self.container)
        self.container.style().polish(self.container)
        self.glow.setColor(glow_color if glow_color else QColor(0, 0, 0, 0))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._old_drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._old_drag_pos:
            delta = event.globalPosition().toPoint() - self._old_drag_pos
            self.move(self.pos() + delta)
            self._old_drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._old_drag_pos = None
        event.accept()

class ModernModal(ModernFramelessShell):
    def __init__(self, title: str = "", icon_path: str = "", icon_bg_color: str = "", width: int = 420, parent=None):
        super().__init__(width=width, parent=parent)
        
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        self.content_layout.setSpacing(12)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        if icon_path:
            self._setup_header(icon_path, icon_bg_color)
        
        if title:
            self.title_lbl = QLabel(title)
            self.title_lbl.setProperty("role", "h1")
            self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.title_lbl.setWordWrap(True)
            self.content_layout.addWidget(self.title_lbl)

    def _setup_header(self, icon_path: str, bg_color: str):
        icon_wrapper = QHBoxLayout()
        icon_wrapper.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_container = QFrame()
        icon_container.setFixedSize(52, 52)
        role = "danger_icon" if bg_color == COLOR_DANGER else "accent_icon"
        icon_container.setProperty("dialog_role", role)
        
        icon_inner_layout = QVBoxLayout(icon_container)
        icon_inner_layout.setContentsMargins(0, 0, 0, 0)
        icon_inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(QIcon(icon_path).pixmap(48, 48))
        icon_inner_layout.addWidget(icon_lbl)

        icon_wrapper.addWidget(icon_container)
        self.content_layout.addLayout(icon_wrapper)

    def add_action_buttons(self, btn_left: QPushButton, btn_right: QPushButton, stretch_center: bool = False):
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        if btn_left: btn_layout.addWidget(btn_left)
        if stretch_center: btn_layout.addStretch()
        if btn_right: btn_layout.addWidget(btn_right)
        
        self.content_layout.addSpacing(8)
        self.content_layout.addLayout(btn_layout)

class ModernWizardPanel(ModernFramelessShell):
    def __init__(self, title: str, subtitle: str = "", width: int = 520, parent=None):
        super().__init__(width=width, parent=parent)
        
        self.panel_layout = QVBoxLayout(self.container)
        self.panel_layout.setContentsMargins(20, 20, 20, 20)
        self.panel_layout.setSpacing(15)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        lbl_title = QLabel(title)
        lbl_title.setProperty("role", "h2")
        header_layout.addWidget(lbl_title)
        
        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setProperty("role", "caption")
            header_layout.addWidget(lbl_sub)
            
        self.panel_layout.addLayout(header_layout)
        self.main_content = QVBoxLayout()
        self.panel_layout.addLayout(self.main_content)

    def set_bottom_actions(self, btn_back_or_cancel: QPushButton, btn_next_or_save: QPushButton):
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_back_or_cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_next_or_save)
        
        self.panel_layout.addSpacing(10)
        self.panel_layout.addLayout(btn_layout)

class ModernConfirmDialog(ModernModal):
    def __init__(self, i18n, parent=None, title_text="", body_text=""):
        super().__init__(title=title_text, icon_path=PATH_ICON_HELP, icon_bg_color=COLOR_DANGER, width=420, parent=parent)
        self.set_dialog_state("danger", QColor(239, 68, 68, 60))
        
        body_label = QLabel(body_text)
        body_label.setProperty("role", "body")
        body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_label.setWordWrap(True)
        body_label.setMinimumHeight(60) 
        
        self.content_layout.addWidget(body_label)
        
        btn_cancel = self._create_btn(i18n.get("dialogs.confirm.btn_cancel"), "action_outlined", self.reject)
        btn_confirm = self._create_btn(i18n.get("dialogs.confirm.btn_continue"), "action_danger", self.accept)

        self.add_action_buttons(btn_cancel, btn_confirm, stretch_center=False)

    def _create_btn(self, text, role, callback):
        btn = QPushButton(text)
        btn.setProperty("role", role)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumWidth(110)
        btn.clicked.connect(callback)
        return btn