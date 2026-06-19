# frontend/controllers/spam_controller.py

from PySide6.QtCore import QObject, Slot

class SpamController(QObject):
    def __init__(self, view, service):
        super().__init__()
        self.view = view
        self.service = service
        self._connect_signals()

    def _connect_signals(self):
        self.view.filter_updated.connect(self._handle_filter_update)

    def load_initial_data(self):
        filters = self.service.filters
        self.view.populate_filters(filters)

    @Slot(str, dict)
    def _handle_filter_update(self, filter_id: str, config: dict):
        self.service.save_filter(filter_id, config)