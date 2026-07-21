# frontend\dialogs\base_dialogs.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
                               QStackedWidget, QProgressBar, QWidget)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QColor, QMouseEvent
from frontend.common.theme import COLOR_RED, PATH_ICON_HELP

class ModernFramelessShell(QDialog):
    _icon_close = None

    def __init__(self, width: int = 420, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._old_drag_pos = None

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.container = QFrame()
        self.container.setProperty("role", "dialog")
        self.container.setFixedWidth(width)
        self.container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(30)
        self.glow.setOffset(0, 0)
        self.glow.setColor(QColor(0, 0, 0, 0))
        self.container.setGraphicsEffect(self.glow)

        self.main_layout.addWidget(self.container)

        from frontend.common.utils import get_icon_colored
        from frontend.common.theme import COLOR_NEUTRAL_400

        self.btn_close_shell = QPushButton(self.container)
        self.btn_close_shell.setProperty("role", "btn_ghost")
        self.btn_close_shell.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close_shell.setFixedSize(26, 26)
        if ModernFramelessShell._icon_close is None:
            ModernFramelessShell._icon_close = get_icon_colored("x.svg", COLOR_NEUTRAL_400, 14)
        self.btn_close_shell.setIcon(ModernFramelessShell._icon_close)
        self.btn_close_shell.setIconSize(QSize(14, 14))
        self.btn_close_shell.clicked.connect(self.reject)
        self.btn_close_shell.move(width - 34, 8)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'btn_close_shell'):
            self.btn_close_shell.move(self.container.width() - 34, 8)

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
        role = "danger_icon" if bg_color == COLOR_RED else "accent_icon"
        icon_container.setProperty("role", role)
        
        icon_inner_layout = QVBoxLayout(icon_container)
        icon_inner_layout.setContentsMargins(0, 0, 0, 0)
        icon_inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_lbl = QLabel()
        dpr = self.devicePixelRatio()
        icon_lbl.setPixmap(QIcon(icon_path).pixmap(QSize(48, 48), dpr))
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
    def __init__(self, title_steps: list[str], subtitle_steps: list[str], i18n, width: int = 520, parent=None):
        super().__init__(width=width, parent=parent)
        self.title_steps = title_steps
        self.subtitle_steps = subtitle_steps
        self.i18n = i18n
        self.current_step = 0
        self.total_steps = len(title_steps)
        
        self.panel_layout = QVBoxLayout(self.container)
        self.panel_layout.setContentsMargins(16, 16, 16, 16)
        self.panel_layout.setSpacing(14)
        
        self.lbl_step_num = QLabel()
        self.lbl_step_num.setProperty("role", "caption")
        self.panel_layout.addWidget(self.lbl_step_num)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setRange(0, self.total_steps)
        self.progress_bar.setValue(0)
        self.progress_bar.setProperty("role", "wizard_progress")
        self.panel_layout.addWidget(self.progress_bar)
        self.panel_layout.addSpacing(2)
        
        self.lbl_title = QLabel()
        self.lbl_title.setProperty("role", "h2")
        self.lbl_title.setWordWrap(True)
        self.panel_layout.addWidget(self.lbl_title)
        
        self.lbl_subtitle = QLabel()
        self.lbl_subtitle.setProperty("role", "body")
        self.lbl_subtitle.setWordWrap(True)
        self.panel_layout.addWidget(self.lbl_subtitle)
        
        self.main_content = QStackedWidget()
        self.panel_layout.addWidget(self.main_content)
        
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addStretch()
        
        self.btn_back = QPushButton()
        self.btn_back.setProperty("role", "action_outlined")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self._go_back)
        
        self.btn_next = QPushButton()
        self.btn_next.setProperty("role", "action_accent")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.clicked.connect(self._go_next)
        
        self.btn_layout.addWidget(self.btn_back)
        self.btn_layout.addWidget(self.btn_next)
        self.panel_layout.addLayout(self.btn_layout)

    def add_page(self, widget: QWidget):
        self.main_content.addWidget(widget)
        
    def start_wizard(self):
        self._update_step_ui()
        
    def _update_step_ui(self):
        step_tmpl = self.i18n.get("dialogs.wizard.step_indicator")
        self.lbl_step_num.setText(step_tmpl.replace("{current}", str(self.current_step + 1)).replace("{total}", str(self.total_steps)))
        self.progress_bar.setValue(self.current_step + 1)
        self.lbl_title.setText(self.title_steps[self.current_step])
        self.lbl_subtitle.setText(self.subtitle_steps[self.current_step])
        self.main_content.setCurrentIndex(self.current_step)
        
        if self.current_step == 0:
            self.btn_back.setText(self.i18n.get("common.buttons.cancel"))
        else:
            self.btn_back.setText(self.i18n.get("common.buttons.back"))
            
        if self.current_step == self.total_steps - 1:
            self.btn_next.setText(self.i18n.get("common.buttons.save"))
        else:
            self.btn_next.setText(self.i18n.get("common.buttons.next"))

    def _go_back(self):
        if self.current_step == 0:
            self.reject()
        else:
            self.current_step -= 1
            self._update_step_ui()
            
    def _go_next(self):
        if not self.validate_step(self.current_step):
            return
        if self.current_step == self.total_steps - 1:
            self.accept()
        else:
            self.current_step += 1
            self._update_step_ui()

    def validate_step(self, step_index: int) -> bool:
        return True

class ModernConfirmDialog(ModernModal):
    def __init__(self, i18n, parent=None, title_text="", body_text=""):
        super().__init__(title=title_text, icon_path=PATH_ICON_HELP, icon_bg_color=COLOR_RED, width=420, parent=parent)
        self.set_dialog_state("danger", QColor(239, 68, 68, 60))
        
        body_label = QLabel(body_text)
        body_label.setProperty("role", "body")
        body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_label.setWordWrap(True)
        body_label.setMinimumHeight(60) 
        
        self.content_layout.addWidget(body_label)
        
        btn_cancel = self._create_btn(i18n.get("common.buttons.cancel"), "action_outlined", self.reject)
        btn_confirm = self._create_btn(i18n.get("common.buttons.continue"), "action_danger_border", self.accept)

        self.add_action_buttons(btn_cancel, btn_confirm, stretch_center=False)

    def _create_btn(self, text, role, callback):
        btn = QPushButton(text)
        btn.setProperty("role", role)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumWidth(110)
        btn.clicked.connect(callback)
        return btn
