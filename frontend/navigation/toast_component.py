# frontend\navigation\toast_component.py

from PySide6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, 
                               QLabel, QPushButton, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, Signal, QObject, QEvent

from frontend.common.theme import COLOR_ACCENT, COLOR_DANGER, COLOR_INFO, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_WARNING
from frontend.common.utils import get_icon_colored

class ModernToast(QFrame):
    expired = Signal(object)

    def __init__(self, title: str, message: str, state: str = "success", duration_ms: int = 4000, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        self.setFixedWidth(330)
        self.setMinimumHeight(66)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)

        self.setProperty("role", "toast")
        self.setProperty("state", state)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 14, 12)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        icon_map = {
            "success": ("circle-check.svg", COLOR_ACCENT),
            "danger": ("alert-circle.svg", COLOR_DANGER),
            "warning": ("alert-triangle.svg", COLOR_WARNING),
            "info": ("info-circle.svg", COLOR_INFO)
        }
        icon_name, icon_color = icon_map.get(state, ("info-circle.svg", COLOR_TEXT_PRIMARY))

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon_colored(icon_name, icon_color, 22).pixmap(22, 22))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(icon_lbl)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl_title = QLabel(title)
        lbl_title.setProperty("role", "h3")
        text_layout.addWidget(lbl_title)

        if message:
            lbl_msg = QLabel(message)
            lbl_msg.setProperty("role", "body")
            lbl_msg.setWordWrap(True)
            text_layout.addWidget(lbl_msg)

        layout.addLayout(text_layout, stretch=1)

        btn_close = QPushButton()
        btn_close.setProperty("role", "btn_ghost")
        btn_close.setIcon(get_icon_colored("x.svg", COLOR_TEXT_SECONDARY, 14))
        btn_close.setFixedSize(20, 20)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.dismiss)
        
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignTop)

        self.anim = QPropertyAnimation(self, b"pos")

        self.timer = QTimer(self)
        self.timer.setInterval(duration_ms)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.dismiss)
        self.timer.start()

    def move_to_target(self, target_pos: QPoint):
        if self.pos() == QPoint(0, 0):
            self.move(QPoint(target_pos.x() + self.width() + 20, target_pos.y()))

        self.anim.stop()
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.OutExpo)
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(target_pos)
        self.anim.start()

    def dismiss(self):
        self.timer.stop()
        self.anim.stop()
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.Type.InExpo)
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(QPoint(self.pos().x() + self.width() + 20, self.pos().y()))
        self.anim.finished.connect(lambda: self.expired.emit(self))
        self.anim.start()


class ToastManager(QObject):
    MAX_VISIBLE = 4

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self._stack = []
        self.main_window.installEventFilter(self)

    def show_toast(self, title: str, message: str, state: str = "success", duration: int = 4000):
        if len(self._stack) >= self.MAX_VISIBLE:
            oldest_toast = self._stack.pop(0)
            oldest_toast.dismiss()

        toast = ModernToast(title, message, state, duration, parent=self.main_window)
        self._stack.append(toast)
        toast.expired.connect(self._on_toast_expired)  
        
        toast.setStyleSheet(self.main_window.styleSheet())
        toast.adjustSize()
        toast.show()
        toast.raise_()
        self._calculate_positions()

    def _on_toast_expired(self, toast_ref):
        if toast_ref in self._stack:
            self._stack.remove(toast_ref)
            toast_ref.deleteLater()
            self._calculate_positions()
        else:
            toast_ref.deleteLater()

    def _calculate_positions(self):
        margin_x = 24
        margin_y = 24
        spacing = 12

        current_bottom = self.main_window.height() - margin_y
        target_x = self.main_window.width() - 330 - margin_x

        for toast in reversed(self._stack):
            target_y = current_bottom - toast.height()
            toast.move_to_target(QPoint(target_x, target_y))
            current_bottom = target_y - spacing

    def eventFilter(self, obj, event):
        if obj == self.main_window and event.type() == QEvent.Type.Resize:
            self._calculate_positions()
        return False