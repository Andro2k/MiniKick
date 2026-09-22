# frontend\widgets\no_wheel.py

from PySide6.QtWidgets import QComboBox, QSlider, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox
from PySide6.QtCore import Qt

class NoWheelSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
        else:
            super().wheelEvent(event)

class NoWheelDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
        else:
            super().wheelEvent(event)

class NoWheelComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)

    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
        else:
            super().wheelEvent(event)

class NoWheelSlider(QSlider):
    def __init__(self, orientation=None, parent=None):
        if orientation is not None and not isinstance(orientation, QSlider):
            super().__init__(orientation, parent)
        else:
            super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
        else:
            super().wheelEvent(event)

class NoWheelDateEdit(QDateEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._calendar_configured = False

    def _configure_calendar_widget(self):
        if self._calendar_configured:
            return
        cal = super().calendarWidget()
        if cal:
            from PySide6.QtWidgets import QCalendarWidget
            from PySide6.QtGui import QTextCharFormat, QColor
            from frontend.common import COLOR_NEUTRAL_400

            cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
            cal.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
            neutral_fmt = QTextCharFormat()
            neutral_fmt.setForeground(QColor(COLOR_NEUTRAL_400))
            cal.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, neutral_fmt)
            cal.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, neutral_fmt)
            cal.setHeaderTextFormat(neutral_fmt)

            from PySide6.QtWidgets import QTableView
            from frontend.common import create_dark_palette
            dark_pal = create_dark_palette()
            cal.setPalette(dark_pal)
            popup = cal.parent()
            if popup:
                popup.setPalette(dark_pal)
            table = cal.findChild(QTableView, "qt_calendar_calendarview")
            if table:
                table.setPalette(dark_pal)
                if table.viewport():
                    table.viewport().setPalette(dark_pal)

            self._calendar_configured = True

    def calendarWidget(self):
        self._configure_calendar_widget()
        return super().calendarWidget()

    def mousePressEvent(self, event):
        if self.calendarPopup():
            self._configure_calendar_widget()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if self.calendarPopup() and event.key() in (Qt.Key.Key_Select, Qt.Key.Key_Space, Qt.Key.Key_Down):
            self._configure_calendar_widget()
        super().keyPressEvent(event)

    def wheelEvent(self, event):
        event.ignore()

class NoWheelTimeEdit(QTimeEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event):
        event.ignore()
