# backend/controllers/timer_controller.py

from PySide6.QtCore import QObject, Slot, Signal

class TimerController(QObject):
    metrics_update_requested = Signal()

    def __init__(self, view, service, toast_manager=None):
        super().__init__()
        self.view = view
        self.service = service
        self.toast = toast_manager
        self._connect_signals()

    def _connect_signals(self):
        self.view.add_requested.connect(self._handle_add)
        self.view.edit_requested.connect(self._handle_edit)
        self.view.delete_requested.connect(self._handle_delete)
        self.view.status_toggled.connect(self._handle_status_change)
        self.view.search_text_changed.connect(self._handle_search)

    def load_initial_data(self):
        timers = self.service.get_all_timers()
        self.view.populate_table(timers)

    @Slot()
    def _handle_add(self):
        data = self.view.show_add_dialog()
        if data:
            data.pop("timer_id")
            if data["name"] and data["messages"]:
                self.service.save_timer(**data)
                self.load_initial_data()
                self.metrics_update_requested.emit()
                if self.toast:
                    self.toast.show_toast(
                        title=self.view.i18n.get("timer.status.created"),
                        message=(self.view.i18n.get("timer.status.created_msg")).replace("{name}", data['name']),
                        state="success"
                    )

    @Slot(int)
    def _handle_edit(self, timer_id: int):
        timers = self.service.get_all_timers()
        existing = next((t for t in timers if t["id"] == timer_id), None)
        if not existing:
            return
        
        data = self.view.show_edit_dialog(existing)
        if data:
            if data["name"] and data["messages"]:
                self.service.save_timer(**data)
                self.load_initial_data()
                self.metrics_update_requested.emit()
                if self.toast:
                    self.toast.show_toast(
                        title=self.view.i18n.get("timer.status.updated"),
                        message=(self.view.i18n.get("timer.status.updated_msg")).replace("{name}", data['name']),
                        state="success"
                    )

    @Slot(int)
    def _handle_delete(self, timer_id: int):
        timers = self.service.get_all_timers()
        existing = next((t for t in timers if t["id"] == timer_id), None)
        if not existing:
            return
        name = existing["name"]
        self.service.delete_timer(timer_id)
        self.load_initial_data()
        self.metrics_update_requested.emit()
        if self.toast:
            self.toast.show_toast(
                title=self.view.i18n.get("timer.status.deleted"),
                message=(self.view.i18n.get("timer.status.deleted_msg")).replace("{name}", name),
                state="warning"
            )

    @Slot(int, bool)
    def _handle_status_change(self, timer_id: int, is_active: bool):
        timers = self.service.get_all_timers()
        existing = next((t for t in timers if t["id"] == timer_id), None)
        
        if existing:
            self.service.save_timer(
                name=existing["name"],
                messages=existing["messages"],
                is_active=is_active,
                interval_online=existing["interval_online"],
                interval_offline=existing["interval_offline"],
                chat_lines=existing["chat_lines"],
                keywords=existing["keywords"],
                categories=existing["categories"],
                timer_id=timer_id
            )
            self.metrics_update_requested.emit()
            if self.toast:
                ## Cambiar el texto por i18n, nada de texto en el codigo.
                title_key = "timer.status.enabled" if is_active else "timer.status.disabled"
                fallback_title = "Temporizador Activado" if is_active else "Temporizador Desactivado"
                state_color = "success" if is_active else "info"
                
                status_txt = self.view.i18n.get("common.status.active") if is_active else self.view.i18n.get("common.status.inactive")
                message = (self.view.i18n.get("timer.status.toggled_msg")).replace("{name}", existing['name']).replace("{status}", status_txt.lower())

                self.toast.show_toast(
                    title=self.view.i18n.get(title_key) or fallback_title,
                    message=message,
                    state=state_color
                )

    @Slot(str)
    def _handle_search(self, text: str):
        if not text.strip():
            self.load_initial_data()
            return
            
        filtered_timers = self.service.search_timers(text)
        self.view.populate_table(filtered_timers)
