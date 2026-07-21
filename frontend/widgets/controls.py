# frontend\widgets\controls.py

import re
from PySide6.QtWidgets import (QPushButton, QAbstractButton, QSizePolicy, QWidget, 
                               QHBoxLayout, QLabel, QTextEdit, QListWidget)
from PySide6.QtCore import QRectF, Qt, QSize
from PySide6.QtGui import (QColor, QPainter, QPainterPath, QPen, QSyntaxHighlighter, 
                           QTextCharFormat, QFont, QKeyEvent)
from frontend.common.theme import COLOR_GREEN, COLOR_NEUTRAL_850, COLOR_NEUTRAL_800, COLOR_WHITE
from frontend.common.utils import NoWheelSlider

class ModernButton(QPushButton):
    def __init__(self, text: str, role: str = "action_accent", parent=None):
        super().__init__(text, parent)
        self.setProperty("role", role)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class ModernSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.toggled.connect(self.update)
        
        self._bg_color_checked = QColor(COLOR_GREEN)
        self._bg_color_unchecked = QColor(COLOR_NEUTRAL_850)
        self._border_color_checked = QColor(COLOR_GREEN)
        self._border_color_unchecked = QColor(COLOR_NEUTRAL_800)
        self._handle_color = QColor(COLOR_WHITE)

    def sizeHint(self) -> QSize:
        return QSize(44, 22)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen_width = 1.5 if not self.isChecked() else 1.0
        rect = QRectF(pen_width / 2, pen_width / 2, self.width() - pen_width, self.height() - pen_width)
        radius = rect.height() / 1.8

        bg_color = self._bg_color_checked if self.isChecked() else self._bg_color_unchecked
        border_color = self._border_color_checked if self.isChecked() else self._border_color_unchecked

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.fillPath(path, bg_color)

        pen = QPen(border_color, pen_width)
        painter.setPen(pen)
        painter.drawPath(path)

        padding = 3
        handle_size = self.height() - (padding * 2)
        handle_x = self.width() - handle_size - padding if self.isChecked() else padding
        
        handle_rect = QRectF(handle_x, padding, handle_size, handle_size)
        handle_radius = handle_size / 2.0

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._handle_color)
        painter.drawRoundedRect(handle_rect, handle_radius, handle_radius)
        
        painter.end()

class CompactSlider(QWidget):
    def __init__(self, min_val: int, max_val: int, init_val: int, suffix: str = "", parent=None):
        super().__init__(parent)
        self.suffix = suffix
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        self.slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(init_val)
        self.slider.setFixedWidth(140)
        
        self.label = QLabel(self._format_value(init_val))
        self.label.setFixedWidth(40)
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.slider.valueChanged.connect(self._on_value_changed)
        
        layout.addWidget(self.slider)
        layout.addWidget(self.label)
        
    def _format_value(self, val: int) -> str:
        if self.suffix == "s" and val == 0:
            return "Nunca"
        return f"{val}{self.suffix}"
        
    def _on_value_changed(self, val: int):
        self.label.setText(self._format_value(val))
        
    def value(self) -> int:
        return self.slider.value()
        
    def setValue(self, val: int):
        self.slider.setValue(val)
        self.label.setText(self._format_value(val))


class VariableHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, pattern=r"\{[a-zA-Z_]+\}", color=QColor("#C084FC"), bg_color=None):
        super().__init__(parent)
        self.pattern = pattern
        self.color = color
        self.bg_color = bg_color
        
    def highlightBlock(self, text):
        fmt = QTextCharFormat()
        fmt.setForeground(self.color)
        fmt.setFontWeight(QFont.Weight.Bold)
        if self.bg_color:
            fmt.setBackground(self.bg_color)
            
        for match in re.finditer(self.pattern, text):
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
        
        self.popup = QListWidget()
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
        match = re.search(r"\{[a-zA-Z_]+\}$", text_before)
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
        match = re.match(r"^\{[a-zA-Z_]+\}", text_after)
        if match:
            tag_len = match.end() - match.start()
            cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, tag_len)
            cursor.removeSelectedText()
            return True
        return False

    def insertFromMimeData(self, source):
        self.insertPlainText(source.text())
