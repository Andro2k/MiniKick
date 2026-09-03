# frontend\navigation\toast_component.py

from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, Signal, QObject, QEvent, QSize
from frontend.common.theme import COLOR_GREEN, COLOR_RED, COLOR_BLUE, COLOR_NEUTRAL_200, COLOR_NEUTRAL_400, COLOR_AMBER
from frontend.common import get_icon_colored, get_pixmap_colored

class ModernToast(QFrame):
    expired = Signal(object)
    _pixmap_cache = {}

    def __init__(self, title: str, message: str, state: str = "success", duration_ms: int = 3500, tag: str = "", parent=None):
        super().__init__(parent)
        self.title_text = title
        self.message_text = message
        self.state_str = state
        self.tag = tag

        self.setFixedWidth(330)
        self.setMinimumHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)

        self.setProperty("role", "toast")
        self.setProperty("state", state)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        self.icon_lbl = QLabel(self)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._update_icon(state)
        layout.addWidget(self.icon_lbl)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.lbl_title = QLabel(title, self)
        self.lbl_title.setProperty("role", "h3")
        text_layout.addWidget(self.lbl_title)

        self.lbl_msg = QLabel(message or "", self)
        self.lbl_msg.setProperty("role", "body")
        self.lbl_msg.setWordWrap(True)
        self.lbl_msg.setVisible(bool(message))
        text_layout.addWidget(self.lbl_msg)

        layout.addLayout(text_layout, stretch=1)

        if "close" not in ModernToast._pixmap_cache:
            ModernToast._pixmap_cache["close"] = get_icon_colored("x.svg", COLOR_NEUTRAL_400, 14)

        btn_close = QPushButton(self)
        btn_close.setProperty("role", "btn_ghost")
        btn_close.setIcon(ModernToast._pixmap_cache["close"])
        btn_close.setIconSize(QSize(14, 14))
        btn_close.setFixedSize(20, 20)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.dismiss)
        
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignTop)

        self._is_dismissing = False
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.finished.connect(self._on_anim_finished)

        self.timer = QTimer(self)
        self.timer.setInterval(duration_ms)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.dismiss)
        self.timer.start()

    def _update_icon(self, state: str):
        if state not in ModernToast._pixmap_cache:
            icon_map = {
                "success": ("circle-check.svg", COLOR_GREEN),
                "danger": ("alert-circle.svg", COLOR_RED),
                "warning": ("alert-triangle.svg", COLOR_AMBER),
                "info": ("info-circle.svg", COLOR_BLUE)
            }
            icon_name, icon_color = icon_map.get(state, ("info-circle.svg", COLOR_NEUTRAL_200))
            ModernToast._pixmap_cache[state] = get_pixmap_colored(icon_name, icon_color, 20)
        self.icon_lbl.setPixmap(ModernToast._pixmap_cache[state])

    def update_content(self, title: str, message: str, state: str = "success", duration_ms: int = 3500):
        self.title_text = title
        self.message_text = message
        self.state_str = state
        self.lbl_title.setText(title)
        self.lbl_msg.setText(message or "")
        self.lbl_msg.setVisible(bool(message))
        self._update_icon(state)
        
        if self.property("state") != state:
            self.setProperty("state", state)
            self.style().unpolish(self)
            self.style().polish(self)

        if self._is_dismissing:
            self._is_dismissing = False
            self.anim.stop()

        self.timer.stop()
        self.timer.setInterval(duration_ms)
        self.timer.start()
        self.adjustSize()

    def _on_anim_finished(self):
        if self._is_dismissing:
            self.expired.emit(self)

    def move_to_target(self, target_pos: QPoint):
        if not self.isVisible() or self.pos() == QPoint(0, 0):
            self.move(QPoint(target_pos.x() + self.width() + 20, target_pos.y()))
        if self.pos() == target_pos:
            return
        self.anim.stop()
        self.anim.setDuration(180)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(target_pos)
        self.anim.start()

    def dismiss(self):
        if self._is_dismissing:
            return
        self._is_dismissing = True
        self.timer.stop()
        self.anim.stop()
        self.anim.setDuration(140)
        self.anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(QPoint(self.pos().x() + self.width() + 20, self.pos().y()))
        self.anim.start()


class ToastManager(QObject):
    MAX_VISIBLE = 3

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self._stack = []
        self.main_window.installEventFilter(self)

    def show_toast(self, title: str, message: str, state: str = "success", duration: int = 3500, tag: str = ""):
        if self._stack:
            last_toast = self._stack[-1]
            if getattr(last_toast, "title_text", None) == title and getattr(last_toast, "message_text", None) == message and getattr(last_toast, "state_str", None) == state:
                last_toast.timer.stop()
                last_toast.timer.start()
                return

            last_tag = getattr(last_toast, "tag", "")
            if tag and last_tag and tag == last_tag:
                last_toast.update_content(title, message, state, duration)
                self._calculate_positions()
                return

        while len(self._stack) >= self.MAX_VISIBLE:
            oldest_toast = self._stack.pop(0)
            oldest_toast.hide()
            oldest_toast.deleteLater()

        toast = ModernToast(title, message, state, duration, tag=tag, parent=self.main_window)
        self._stack.append(toast)
        toast.expired.connect(self._on_toast_expired)
        toast.show()
        toast.adjustSize()
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
        spacing = 10
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
