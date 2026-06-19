# frontend/controllers/alerts_controller.py

from PySide6.QtCore import QObject, Slot
from frontend.components.dialogs import AlertConfigWizard

class AlertsController(QObject):
    def __init__(self, view, service):
        super().__init__()
        self.view = view
        self.service = service
        self.current_rewards_list = ["No hay recompensas"]
        self._active_dialog = None
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
        if self._active_dialog:
            self._active_dialog.update_rewards(self._get_available_rewards())

    def _get_available_rewards(self, ignore_reward=None):
        """Filtra la lista para ocultar las recompensas que ya tienen una alerta asignada."""
        mappings = self.service.get_mappings()
        used_rewards = mappings.keys()
        available = [r for r in self.current_rewards_list if r not in used_rewards or r == ignore_reward]
        return available if available else ["No hay recompensas disponibles"]

    @Slot()
    def _handle_add(self):
        available_rewards = self._get_available_rewards()
        self._active_dialog = AlertConfigWizard(self.view, rewards_list=available_rewards)
        
        if self._active_dialog.exec():
            reward, config = self._active_dialog.get_config_data()
            if reward and reward not in ["Cargando recompensas...", "No hay recompensas", "No hay recompensas disponibles"] and config["filepath"]:
                mappings = self.service.get_mappings()
                mappings[reward] = config
                self.service.save_mappings(mappings)
                self.view.populate_table(mappings)
                
        self._active_dialog = None

    @Slot(str)
    def _handle_edit(self, reward_name: str):
        mappings = self.service.get_mappings()
        if reward_name not in mappings:
            return
            
        available_rewards = self._get_available_rewards(ignore_reward=reward_name)
        self._active_dialog = AlertConfigWizard(
            self.view, 
            rewards_list=available_rewards, 
            existing_config=mappings[reward_name], 
            existing_reward=reward_name
        )
        
        if self._active_dialog.exec():
            new_reward, updated_config = self._active_dialog.get_config_data()
            if updated_config["filepath"]:
                if new_reward != reward_name:
                    del mappings[reward_name]
                    
                mappings[new_reward] = updated_config
                self.service.save_mappings(mappings)
                self.view.populate_table(mappings)
                
        self._active_dialog = None

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