# frontend\widgets\clickable_frame.py

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame


class ClickableFrame(QFrame):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._emit_clicked()
        super().mousePressEvent(event)

    def _emit_clicked(self):
        self.clicked.emit()
