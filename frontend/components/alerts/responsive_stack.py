# frontend\components\alerts\responsive_stack.py

from PySide6.QtWidgets import QStackedWidget, QSizePolicy

class ResponsiveStackedWidget(QStackedWidget):
    def addWidget(self, w):
        idx = super().addWidget(w)
        if self.count() > 1 and w != self.currentWidget():
            w.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        return idx

    def setCurrentWidget(self, w):
        super().setCurrentWidget(w)
        for i in range(self.count()):
            child = self.widget(i)
            if child == w:
                child.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            else:
                child.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

    def setCurrentIndex(self, index: int):
        super().setCurrentIndex(index)
        for i in range(self.count()):
            child = self.widget(i)
            if i == index:
                child.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            else:
                child.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

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
