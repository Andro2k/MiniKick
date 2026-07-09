# frontend/widgets/flow_layout.py

from PySide6.QtWidgets import QLayout
from PySide6.QtCore import Qt, QSize, QRect

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, hspacing=8, vspacing=8):
        super().__init__(parent)
        self._item_list = []
        self._hspacing = hspacing
        self._vspacing = vspacing
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QSize(left + right, top + bottom)
        return size

    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(left, top, -right, -bottom)
        
        h_space = self._hspacing
        v_space = self._vspacing
        
        lines = []
        current_line = []
        x = effective_rect.x()
        
        for item in self._item_list:
            item_w = item.sizeHint().width()
            if x + item_w > effective_rect.right() and len(current_line) > 0:
                lines.append(current_line)
                current_line = [item]
                x = effective_rect.x() + item_w + h_space
            else:
                current_line.append(item)
                x += item_w + h_space
                
        if current_line:
            lines.append(current_line)
            
        y = effective_rect.y()
        max_n = max(len(line) for line in lines) if lines else 1
        
        for line in lines:
            n = len(line)
            w = (effective_rect.width() - (max_n - 1) * h_space) / max_n
            
            line_height = 0
            for item in line:
                h = item.sizeHint().height()
                wid = item.widget()
                if wid and wid.maximumHeight() < h:
                    h = wid.maximumHeight()
                line_height = max(line_height, h)

            x = effective_rect.x()
            for item in line:
                h = line_height
                wid = item.widget()
                item_w = w
                if wid:
                    if wid.maximumWidth() < item_w:
                        item_w = wid.maximumWidth()
                    if wid.maximumHeight() < h:
                        h = wid.maximumHeight()
                        
                if not test_only:
                    item.setGeometry(QRect(int(x), int(y), int(item_w), int(h)))
                    
                x += w + h_space
                
            y += line_height + v_space
            
        if lines:
            return y - v_space - effective_rect.y() + top + bottom
        return top + bottom
