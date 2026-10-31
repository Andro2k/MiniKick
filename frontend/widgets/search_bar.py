# frontend\widgets\search_bar.py

from .action_line_edit import ActionLineEdit

class UnifiedSearchBar(ActionLineEdit):
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(placeholder, search_when_empty=True, parent=parent)
