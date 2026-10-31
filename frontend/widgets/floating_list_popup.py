# frontend\widgets\floating_list_popup.py

from PySide6.QtCore import Qt, QEvent, QPoint
from PySide6.QtWidgets import QApplication, QFrame, QListWidget, QListWidgetItem, QVBoxLayout, QWidget
from frontend.common import Size

class BaseFloatingListPopup(QFrame):
    _MIN_WIDTH = 260
    _ANCHOR_GAP = 4
    _WRAP_NAVIGATION = False

    def __init__(self, anchor: QWidget, frame_role: str, list_role: str, window_flags: Qt.WindowType, parent: QWidget | None = None):
        super().__init__(parent, window_flags | Qt.WindowType.FramelessWindowHint)
        self.anchor = anchor
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(*Size.Margin.MRG_NON)
        outer_layout.setSpacing(Size.SPACING_NN)
        outer_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)

        self.bg_frame = QFrame(self)
        self.bg_frame.setProperty("role", frame_role)
        outer_layout.addWidget(self.bg_frame)

        self.content_layout = QVBoxLayout(self.bg_frame)
        self.content_layout.setContentsMargins(*Size.Margin.MRG_NON)
        self.content_layout.setSpacing(Size.SPACING_NN)

        self.list_widget = QListWidget(self.bg_frame)
        self.list_widget.setProperty("role", list_role)
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.content_layout.addWidget(self.list_widget)

    def _on_item_clicked(self, _item: QListWidgetItem) -> None:
        raise NotImplementedError

    def attach_key_navigation(self, line_edit: QWidget) -> None:
        line_edit.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and self.isVisible() and self._handle_key(event.key()):
            return True
        return super().eventFilter(obj, event)

    def _handle_key(self, key: int) -> bool:
        if key == Qt.Key.Key_Escape:
            self.hide()
        elif key == Qt.Key.Key_Down:
            self.navigate(1)
        elif key == Qt.Key.Key_Up:
            self.navigate(-1)
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            item = self.list_widget.currentItem()
            if item is None or item.isHidden():
                return False
            self._on_item_clicked(item)
        else:
            return False
        return True

    def navigate(self, step: int) -> None:
        count = self.list_widget.count()
        row = self.list_widget.currentRow()
        if row < 0:
            row = 0 if step < 0 else -1

        for _ in range(count):
            row += step
            if self._WRAP_NAVIGATION:
                row %= count
            elif not 0 <= row < count:
                return

            item = self.list_widget.item(row)
            if not item.isHidden():
                self.list_widget.setCurrentRow(row)
                self.list_widget.scrollToItem(item)
                return

    def show_below_anchor(self) -> None:
        self.setFixedWidth(max(self.anchor.width(), self._MIN_WIDTH))
        self.adjustSize()

        pos = self.anchor.mapToGlobal(QPoint(0, self.anchor.height() + self._ANCHOR_GAP))
        screen = self.anchor.screen() or QApplication.primaryScreen()
        if screen and pos.y() + self.height() > screen.availableGeometry().bottom():
            pos = self.anchor.mapToGlobal(QPoint(0, -self.height() - self._ANCHOR_GAP))

        self.move(pos)
        self.show()
        self.raise_()
