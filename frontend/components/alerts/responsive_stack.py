# frontend\components\alerts\responsive_stack.py

from PySide6.QtWidgets import QStackedWidget

class ResponsiveStackedWidget(QStackedWidget):
    def minimumSizeHint(self):
        cur = self.currentWidget()
        if cur is not None:
            return cur.minimumSizeHint()
        return super().minimumSizeHint()

    def sizeHint(self):
        cur = self.currentWidget()
        if cur is not None:
            return cur.sizeHint()
        return super().sizeHint()
