# frontend\widgets\controls.py

import re
from PySide6.QtWidgets import QPushButton, QAbstractButton, QSizePolicy, QTextEdit, QListWidget, QSpinBox, QVBoxLayout, QWidget
from PySide6.QtCore import QRectF, Qt, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QLinearGradient, QSyntaxHighlighter, QTextCharFormat, QFont, QKeyEvent, QIcon
from frontend.common import get_icon_colored, get_qcolor_with_alpha, Palette, Semantic, BrandColors, SwitchTheme, Size, ROW_ACTION_COLORS
from .style_utils import repolish

_REGEX_VAR_END = re.compile(r"\{[a-zA-Z_]+\}$")
_REGEX_VAR_START = re.compile(r"^\{[a-zA-Z_]+\}")

def configure_icon_only_button(button: QPushButton, size: int | QSize = Size.ICON_BASIC) -> None:
    button.setProperty("icon_only", True)
    if isinstance(size, QSize):
        button.setFixedSize(size)
    else:
        button.setFixedSize(size, size)
    repolish(button)


class ModernButton(QPushButton):
    def __init__(self, text: str = "", role: str = "action_outlined", icon_name: str = "",
                 icon_color: str | None = None, parent=None):
        super().__init__(text, parent)
        self._role = role
        self.setProperty("role", role)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon_name:
            self.set_icon(icon_name, color=icon_color)

    def setIcon(self, icon: QIcon):
        super().setIcon(icon)
        if icon.isNull() or self.text():
            self.setProperty("icon_only", False)
            return
        configure_icon_only_button(self)

    @staticmethod
    def _resolve_role_color(role: str) -> str:
        role_map = {
            "action_outlined": Palette.NEUTRAL_050,
            "action_kick": Palette.NEUTRAL_050,
            "action_twitch": Palette.NEUTRAL_050,
            "action_youtube": Palette.NEUTRAL_050,
            "action_tiktok": Palette.NEUTRAL_999,
            "action_danger_solid": Palette.NEUTRAL_050,
            "action_accent_solid": Palette.NEUTRAL_050,
            "btn_ghost": Palette.NEUTRAL_400,
            "nav_button": Palette.NEUTRAL_400,
            **ROW_ACTION_COLORS,
        }
        return role_map.get(role, Palette.NEUTRAL_050)

    def set_icon(self, icon_name: str, color: str | None = None):
        if not icon_name:
            self.setIcon(QIcon())
            return
            
        if isinstance(color, int):
            color = None
            
        if color is None:
            current_role = self.property("role") or self._role
            color = self._resolve_role_color(current_role)
            
        self.setIcon(get_icon_colored(icon_name, color_str=color))

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
        return QSize(48, 24)

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

    def paintEvent(self, _event):
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
            track_grad.setColorAt(0.0, QColor(Palette.NEUTRAL_900))
            track_grad.setColorAt(1.0, QColor(Palette.NEUTRAL_950))
            border_color = QColor(Palette.NEUTRAL_750)
        elif is_checked:
            track_grad.setColorAt(0.0, QColor(SwitchTheme.SWITCH_TRACK_ON_00))
            track_grad.setColorAt(1.0, QColor(SwitchTheme.SWITCH_TRACK_ON_01))
            border_color = QColor(BrandColors.GREEN) if has_focus else QColor(BrandColors.KICK_BORDER)
        else:
            track_grad.setColorAt(0.0, QColor(SwitchTheme.SWITCH_TRACK_DIS_0))
            track_grad.setColorAt(1.0, QColor(SwitchTheme.SWITCH_TRACK_DIS_1))
            border_color = QColor(BrandColors.GREEN) if has_focus else QColor(Semantic.BORDER_TOP_SHINE)

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
            painter.setBrush(get_qcolor_with_alpha(Palette.NEUTRAL_999, 60))
            painter.drawEllipse(shadow_rect)

        thumb_grad = QLinearGradient(handle_x, handle_y, handle_x, handle_y + handle_size)
        if not is_enabled:
            thumb_grad.setColorAt(0.0, QColor(SwitchTheme.SWITCH_THUMB_OFF_0))
            thumb_grad.setColorAt(1.0, QColor(SwitchTheme.SWITCH_THUMB_OFF_1))
        elif is_checked:
            thumb_grad.setColorAt(0.0, QColor(Palette.NEUTRAL_000))
            thumb_grad.setColorAt(1.0, QColor(SwitchTheme.SWITCH_THUMB_ON_01))
        else:
            thumb_grad.setColorAt(0.0, QColor(SwitchTheme.SWITCH_THUMB_DIS_0))
            thumb_grad.setColorAt(1.0, QColor(SwitchTheme.SWITCH_THUMB_DIS_1))

        painter.setBrush(thumb_grad)
        painter.setPen(QPen(get_qcolor_with_alpha(Palette.NEUTRAL_999, 30), 0.8))
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
    def __init__(self, parent=None, pattern=r"\{[a-zA-Z_]+\}", color=None, bg_color=None):
        super().__init__(parent)
        self.pattern = pattern
        self._regex = re.compile(pattern)
        self.color = color if color is not None else QColor(BrandColors.PURPLE_LIGHT)
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
    def __init__(self, autocomplete_data=None, highlight_pattern=r"\{[a-zA-Z_]+\}", highlight_color=BrandColors.PURPLE_LIGHT, highlight_bg=None, parent=None):
        super().__init__(parent)

        if autocomplete_data is None:
            self.autocomplete_data = {
                "{": ["{user}", "{touser}", "{random}"]
            }
        else:
            self.autocomplete_data = autocomplete_data

        self.trigger_chars = list(self.autocomplete_data.keys())

        bg_qcolor = QColor(highlight_bg) if highlight_bg else None
        self.highlighter = VariableHighlighter(self.document(), highlight_pattern, QColor(highlight_color), bg_qcolor)

        self.popup_window = QWidget(self, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.popup_window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        layout = QVBoxLayout(self.popup_window)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.popup = QListWidget(self.popup_window)
        self.popup.setProperty("role", "variable_autocomplete_popup")
        self.popup.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.popup.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.popup.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.popup.itemActivated.connect(self._insert_selected)
        self.popup.itemClicked.connect(self._insert_selected)
        
        layout.addWidget(self.popup)

    def keyPressEvent(self, event: QKeyEvent):
        if self.popup_window.isVisible():
            if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                self._insert_selected()
                return
            elif event.key() == Qt.Key.Key_Escape:
                self.popup_window.hide()
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
        items = self.autocomplete_data.get(trigger, [])
        if not items:
            return

        self.popup.clear()
        self.popup.addItems(items)
        self.popup.setCurrentRow(0)

        cursor_rect = self.cursorRect()
        global_pos = self.mapToGlobal(cursor_rect.bottomLeft())
        max_len = max(len(item) for item in items)
        popup_width = max(130, max_len * 8 + 32)

        self.popup_window.setGeometry(global_pos.x(), global_pos.y() + 4, popup_width, min(160, len(items) * 30 + 12))
        self.popup_window.show()

    def _insert_selected(self):
        selected_item = self.popup.currentItem()
        if selected_item:
            var_text = selected_item.text().split()[0]
            cursor = self.textCursor()
            cursor.deletePreviousChar()
            cursor.insertText(var_text)
            self.setTextCursor(cursor)
        self.popup_window.hide()

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
