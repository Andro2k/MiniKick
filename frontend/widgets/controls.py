# frontend\widgets\controls.py

import re
from PySide6.QtWidgets import (QPushButton, QAbstractButton, QSizePolicy, 
                               QTextEdit, QListWidget, QSpinBox)
from PySide6.QtCore import QRectF, Qt, QSize
from PySide6.QtGui import (QColor, QPainter, QPainterPath, QPen, QLinearGradient, 
                           QSyntaxHighlighter, QTextCharFormat, QFont, QKeyEvent, QIcon)
from frontend.common import (
    get_icon_colored, COLOR_GREEN, COLOR_RED, COLOR_NEUTRAL_400, COLOR_WHITE, COLOR_BLACK
)

_REGEX_VAR_END = re.compile(r"\{[a-zA-Z_]+\}$")
_REGEX_VAR_START = re.compile(r"^\{[a-zA-Z_]+\}")

class ModernButton(QPushButton):
    def __init__(self, text: str = "", role: str = "action_accent", icon_name: str = "", 
                 icon_color: str | None = None, icon_size: int = 16, parent=None):
        super().__init__(text, parent)
        self._role = role
        self.setProperty("role", role)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon_name:
            self.set_icon(icon_name, color=icon_color, size=icon_size)

    @staticmethod
    def _resolve_role_color(role: str) -> str:
        role_map = {
            "action_accent": COLOR_WHITE,
            "action_kick": COLOR_WHITE,
            "action_twitch": COLOR_WHITE,
            "action_youtube": COLOR_WHITE,
            "action_tiktok": COLOR_BLACK,
            "action_outlined": COLOR_WHITE,
            "action_neutral_border": COLOR_WHITE,
            "action_danger_border": COLOR_RED,
            "action_accent_border": COLOR_GREEN,
            "btn_ghost": COLOR_NEUTRAL_400,
            "nav_button": COLOR_NEUTRAL_400,
            "filter_chip": COLOR_NEUTRAL_400,
        }
        return role_map.get(role, COLOR_WHITE)

    def set_icon(self, icon_name: str, color: str | None = None, size: int = 16):
        if not icon_name:
            self.setIcon(QIcon())
            return
        if color is None:
            current_role = self.property("role") or self._role
            color = self._resolve_role_color(current_role)
        self.setIcon(get_icon_colored(icon_name, color, size))
        self.setIconSize(QSize(size, size))

class ModernSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.toggled.connect(self.update)
        self._padding = 3.0

    def sizeHint(self) -> QSize:
        return QSize(44, 22)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.update()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.update()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.toggle()
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        has_focus = self.hasFocus()
        is_checked = self.isChecked()
        is_enabled = self.isEnabled()
        
        w = float(self.width())
        h = float(self.height())
        pen_width = 1.2
        rect = QRectF(pen_width / 2.0, pen_width / 2.0, w - pen_width, h - pen_width)
        radius = rect.height() / 2.0

        track_grad = QLinearGradient(0, 0, 0, h)
        if not is_enabled:
            track_grad.setColorAt(0.0, QColor("#18171C"))
            track_grad.setColorAt(1.0, QColor("#121115"))
            border_color = QColor("#27262D")
        elif is_checked:
            track_grad.setColorAt(0.0, QColor("#1E8E4D"))
            track_grad.setColorAt(1.0, QColor("#15733C"))
            border_color = QColor("#2ECD70") if has_focus else QColor("#1A7A42")
        else:
            track_grad.setColorAt(0.0, QColor("#201E25"))
            track_grad.setColorAt(1.0, QColor("#2A2830"))
            border_color = QColor("#5E5C66") if has_focus else QColor("#38363E")

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.fillPath(path, track_grad)

        pen = QPen(border_color, pen_width)
        painter.setPen(pen)
        painter.drawPath(path)

        handle_size = h - (self._padding * 2.0)
        handle_x = (w - handle_size - self._padding) if is_checked else self._padding
        handle_y = self._padding
        handle_rect = QRectF(handle_x, handle_y, handle_size, handle_size)

        if is_enabled:
            shadow_rect = QRectF(handle_x, handle_y + 1.0, handle_size, handle_size)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 60))
            painter.drawEllipse(shadow_rect)

        thumb_grad = QLinearGradient(handle_x, handle_y, handle_x, handle_y + handle_size)
        if not is_enabled:
            thumb_grad.setColorAt(0.0, QColor("#6E6C78"))
            thumb_grad.setColorAt(1.0, QColor("#504E58"))
        elif is_checked:
            thumb_grad.setColorAt(0.0, QColor("#FFFFFF"))
            thumb_grad.setColorAt(1.0, QColor("#E4E3EA"))
        else:
            thumb_grad.setColorAt(0.0, QColor("#D4D2DC"))
            thumb_grad.setColorAt(1.0, QColor("#9D9AA8"))

        painter.setBrush(thumb_grad)
        painter.setPen(QPen(QColor(0, 0, 0, 30), 0.8))
        painter.drawEllipse(handle_rect)

        painter.end()

class CompactSpinBox(QSpinBox):
    def __init__(self, min_val: int = 0, max_val: int = 100, init_val: int = 0, 
                 step: int = 1, suffix: str = "", prefix: str = "", 
                 special_value_text: str = "", fixed_width: int = 145, parent=None):
        super().__init__(parent)
        self.setRange(min_val, max_val)
        self.setSingleStep(step)
        self.setValue(init_val)
        if suffix:
            formatted_suffix = suffix if suffix.startswith(" ") else f" {suffix}"
            self.setSuffix(formatted_suffix)
        if prefix:
            self.setPrefix(prefix)
        if special_value_text:
            self.setSpecialValueText(special_value_text)
        if fixed_width:
            self.setFixedWidth(fixed_width)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
        else:
            super().wheelEvent(event)

class VariableHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, pattern=r"\{[a-zA-Z_]+\}", color=QColor("#C084FC"), bg_color=None):
        super().__init__(parent)
        self.pattern = pattern
        self._regex = re.compile(pattern)
        self.color = color
        self.bg_color = bg_color
        
    def highlightBlock(self, text):
        fmt = QTextCharFormat()
        fmt.setForeground(self.color)
        fmt.setFontWeight(QFont.Weight.Bold)
        if self.bg_color:
            fmt.setBackground(self.bg_color)
            
        for match in self._regex.finditer(text):
            start, end = match.span()
            self.setFormat(start, end - start, fmt)

class VariableTextEdit(QTextEdit):
    def __init__(self, autocomplete_data=None, highlight_pattern=r"\{[a-zA-Z_]+\}", highlight_color="#C084FC", highlight_bg=None, parent=None):
        super().__init__(parent)
        
        if autocomplete_data is None:
            self.autocomplete_data = {
                "{": ["{user}", "{touser}", "{random}"]
            }
        else:
            self.autocomplete_data = autocomplete_data
            
        self.trigger_chars = list(self.autocomplete_data.keys())
        self.current_trigger = None
        
        bg_qcolor = QColor(highlight_bg) if highlight_bg else None
        self.highlighter = VariableHighlighter(self.document(), highlight_pattern, QColor(highlight_color), bg_qcolor)
        
        self.popup = QListWidget(self)
        self.popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.popup.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.popup.itemActivated.connect(self._insert_selected)
        self.popup.itemClicked.connect(self._insert_selected)
        
    def keyPressEvent(self, event: QKeyEvent):
        if self.popup.isVisible():
            if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                self._insert_selected()
                return
            elif event.key() == Qt.Key.Key_Escape:
                self.popup.hide()
                return
            elif event.key() == Qt.Key.Key_Up:
                row = (self.popup.currentRow() - 1) % self.popup.count()
                self.popup.setCurrentRow(row)
                return
            elif event.key() == Qt.Key.Key_Down:
                row = (self.popup.currentRow() + 1) % self.popup.count()
                self.popup.setCurrentRow(row)
                return
                
        if event.key() == Qt.Key.Key_Backspace:
            if self._handle_backspace():
                return
        elif event.key() == Qt.Key.Key_Delete:
            if self._handle_delete():
                return
                
        super().keyPressEvent(event)
        
        if event.text() in self.trigger_chars:
            self._show_popup(event.text())
            
    def _show_popup(self, trigger: str):
        self.current_trigger = trigger
        items = self.autocomplete_data.get(trigger, [])
        if not items:
            return
            
        self.popup.clear()
        self.popup.addItems(items)
        self.popup.setCurrentRow(0)
        
        cursor_rect = self.cursorRect()
        global_pos = self.mapToGlobal(cursor_rect.bottomLeft())
        max_len = max(len(item) for item in items)
        popup_width = max(120, max_len * 7 + 24)
        
        self.popup.setGeometry(global_pos.x(), global_pos.y() + 4, popup_width, min(150, len(items) * 28 + 10))
        self.popup.show()
        
    def _insert_selected(self):
        selected_item = self.popup.currentItem()
        if selected_item:
            var_text = selected_item.text().split()[0]
            cursor = self.textCursor()
            cursor.deletePreviousChar()
            cursor.insertText(var_text)
            self.setTextCursor(cursor)
        self.popup.hide()

    def _handle_backspace(self) -> bool:
        cursor = self.textCursor()
        pos = cursor.position()
        text_before = self.toPlainText()[:pos]
        match = _REGEX_VAR_END.search(text_before)
        if match:
            tag_len = match.end() - match.start()
            cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.KeepAnchor, tag_len)
            cursor.removeSelectedText()
            return True
        return False

    def _handle_delete(self) -> bool:
        cursor = self.textCursor()
        pos = cursor.position()
        text_after = self.toPlainText()[pos:]
        match = _REGEX_VAR_START.match(text_after)
        if match:
            tag_len = match.end() - match.start()
            cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, tag_len)
            cursor.removeSelectedText()
            return True
        return False

    def insertFromMimeData(self, source):
        self.insertPlainText(source.text())
