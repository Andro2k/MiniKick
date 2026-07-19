# backend\controllers\command_controller.py

from PySide6.QtCore import QObject, Slot

class CommandController(QObject):
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
        self.service.commands_changed.connect(self.load_initial_data)

    def load_initial_data(self):
        commands = self.service.get_all_commands()
        self.view.populate_table(commands)

    @Slot()
    def _handle_add(self):
        data = self.view.show_add_dialog()
        if data:
            data.pop("original_trigger", None)
            if data.get("trigger") and data.get("response"):
                self.service.save_command(**data)
                self.load_initial_data()
                self._show_toast("command.status.created", "command.status.created_msg", data['trigger'], "success")

    @Slot(str)
    def _handle_edit(self, trigger: str):
        existing = self.service.get_command_by_trigger(trigger)
        if not existing:
            return
        
        data = self.view.show_edit_dialog(existing)
        if data:
            original_trigger = data.pop("original_trigger", None)
            if data.get("response") and data.get("trigger"):
                if original_trigger and original_trigger != data["trigger"]:
                    self.service.delete_command(original_trigger)
                    
                self.service.save_command(**data)
                self.load_initial_data()
                self._show_toast("command.status.updated", "command.status.updated_msg", data['trigger'], "success")

    @Slot(str)
    def _handle_delete(self, trigger: str):
        self.service.delete_command(trigger)
        self.load_initial_data()
        self._show_toast("command.status.deleted", "command.status.deleted_msg", trigger, "warning")

    @Slot(str, bool)
    def _handle_status_change(self, trigger: str, is_active: bool):
        existing = self.service.get_command_by_trigger(trigger)
        if existing:
            self.service.save_command(
                trigger=existing["trigger"],
                response=existing["response"],
                is_active=is_active,
                cooldown=existing["cooldown"],
                aliases=existing["aliases"],
                is_regex=existing["is_regex"],
                permission=existing.get("permission", "everyone")
            )
            if self.toast:
                title_key = "command.status.enabled" if is_active else "command.status.disabled"
                state_color = "success" if is_active else "info"
                self.toast.show_toast(
                    title=self.view.i18n.get(title_key),
                    message=(self.view.i18n.get("command.status.toggled_msg")).replace("{trigger}", trigger),
                    state=state_color
                )

    @Slot(str)
    def _handle_search(self, text: str):
        if not text.strip():
            self.load_initial_data()
            return
            
        filtered_commands = self.service.search_commands(text)
        self.view.populate_table(filtered_commands)

    def _show_toast(self, title_key: str, msg_key: str, val: str, state: str):
        if self.toast:
            self.toast.show_toast(
                title=self.view.i18n.get(title_key),
                message=(self.view.i18n.get(msg_key)).replace("{trigger}", val),
                state=state
            )
