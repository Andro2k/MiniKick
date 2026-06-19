# frontend/controllers/command_controller.py

from PySide6.QtCore import QObject, Slot
from frontend.components.dialogs import CommandConfigWizard

class CommandController(QObject):
    def __init__(self, view, service):
        super().__init__()
        self.view = view
        self.service = service
        self._connect_signals()

    def _connect_signals(self):
        self.view.add_requested.connect(self._handle_add)
        self.view.edit_requested.connect(self._handle_edit)
        self.view.delete_requested.connect(self._handle_delete)
        
        self.view.status_toggled.connect(self._handle_status_change)
        self.view.search_text_changed.connect(self._handle_search)

    def load_initial_data(self):
        commands = self.service.get_all_commands()
        self.view.populate_table(commands)

    @Slot()
    def _handle_add(self):
        dialog = CommandConfigWizard(self.view)
        if dialog.exec():
            data = dialog.get_command_data()
            data.pop("original_trigger")
            if data["trigger"] and data["response"]:
                self.service.save_command(**data)
                self.load_initial_data()

    @Slot(str)
    def _handle_edit(self, trigger: str):
        commands = self.service.get_all_commands()
        existing = next((c for c in commands if c["trigger"] == trigger), None)
        if not existing:
            return
            
        dialog = CommandConfigWizard(self.view, existing_config=existing)
        if dialog.exec():
            data = dialog.get_command_data()
            original_trigger = data.pop("original_trigger")
            
            if data["response"] and data["trigger"]:
                if original_trigger and original_trigger != data["trigger"]:
                    self.service.delete_command(original_trigger)
                    
                self.service.save_command(**data)
                self.load_initial_data()

    @Slot(str)
    def _handle_delete(self, trigger: str):
        self.service.delete_command(trigger)
        self.load_initial_data()

    @Slot(str, bool)
    def _handle_status_change(self, trigger: str, is_active: bool):
        commands = self.service.get_all_commands()
        existing = next((c for c in commands if c["trigger"] == trigger), None)
        
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

    @Slot(str)
    def _handle_search(self, text: str):
        commands = self.service.get_all_commands()

        if not text.strip():
            self.view.populate_table(commands)
            return
            
        search_term = text.lower()
        filtered_commands = []

        for cmd in commands:
            if (search_term in cmd["trigger"].lower() or 
                search_term in cmd["response"].lower() or 
                search_term in cmd.get("aliases", "").lower()):
                filtered_commands.append(cmd)
                
        self.view.populate_table(filtered_commands)