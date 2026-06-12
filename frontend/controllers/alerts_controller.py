# frontend/controllers/alerts_controller.py

from PySide6.QtCore import QObject, Slot
from frontend.components.dialogs import AlertConfigWizard

class AlertsController(QObject):
    def __init__(self, view, service):
        super().__init__()
        self.view = view
        self.service = service
        self.current_rewards_list = ["No hay recompensas"]
        self._connect_signals()

    def _connect_signals(self):
        self.view.add_requested.connect(self._handle_add)
        self.view.edit_requested.connect(self._handle_edit)
        self.view.delete_requested.connect(self._handle_delete)
        self.view.preview_requested.connect(self._handle_preview)

    def load_initial_data(self):
        """Carga los datos por primera vez e hidrata la vista."""
        mappings = self.service.get_mappings()
        self.view.populate_table(mappings)

    @Slot(list)
    def update_rewards_list(self, rewards: list):
        """Recibe la lista fresca de recompensas y actualiza la vista."""
        self.current_rewards_list = rewards if rewards else ["No hay recompensas"]
        self.view.update_rewards_combo(self.current_rewards_list)

    @Slot()
    def _handle_add(self):
        dialog = AlertConfigWizard(self.view, rewards_list=self.current_rewards_list)
        
        if dialog.exec():
            reward, config = dialog.get_config_data()
            if reward and reward not in ["Cargando recompensas...", "No hay recompensas"] and config["filepath"]:
                mappings = self.service.get_mappings()
                mappings[reward] = config
                self.service.save_mappings(mappings)
                self.view.populate_table(mappings)

    @Slot(str)
    def _handle_edit(self, reward_name: str):
        mappings = self.service.get_mappings()
        if reward_name not in mappings:
            return
            
        dialog = AlertConfigWizard(
            self.view, 
            rewards_list=self.current_rewards_list, 
            existing_config=mappings[reward_name], 
            existing_reward=reward_name
        )
        
        if dialog.exec():
            _, updated_config = dialog.get_config_data()
            if updated_config["filepath"]:
                mappings[reward_name] = updated_config
                self.service.save_mappings(mappings)
                self.view.populate_table(mappings)

    @Slot(str)
    def _handle_delete(self, reward_name: str):
        mappings = self.service.get_mappings()
        if reward_name in mappings:
            del mappings[reward_name]
            self.service.save_mappings(mappings)
            self.view.populate_table(mappings)

    @Slot(str)
    def _handle_preview(self, reward_name: str):
        mappings = self.service.get_mappings()
        if reward_name in mappings:
            self.service.trigger_preview(reward_name, mappings[reward_name])