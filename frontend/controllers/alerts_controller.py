# frontend\controllers\alerts_controller.py

from PySide6.QtCore import QObject, Slot
from frontend.dialogs import AlertConfigWizard

class AlertsController(QObject):
    def __init__(self, view, service):
        super().__init__()
        self.view = view
        self.service = service
        self.current_rewards_list = [self.view.i18n.get("alerts.dialogs.wizard.step1.no_rewards")]
        self._active_dialog = None
        self._connect_signals()

    def _connect_signals(self):
        self.view.add_requested.connect(self._handle_add)
        self.view.edit_requested.connect(self._handle_edit)
        self.view.delete_requested.connect(self._handle_delete)
        self.view.preview_requested.connect(self._handle_preview)

    def load_initial_data(self):
        mappings = self.service.get_mappings()
        self.view.populate_table(mappings)

    @Slot(list)
    def update_rewards_list(self, rewards: list):
        self.current_rewards_list = rewards if rewards else [self.view.i18n.get("alerts.dialogs.wizard.step1.no_rewards")]
        if self._active_dialog:
            self._active_dialog.update_rewards(self._get_available_rewards())

    def _get_available_rewards(self, ignore_reward=None):
        mappings = self.service.get_mappings()
        used_rewards = mappings.keys()
        available = [r for r in self.current_rewards_list if r not in used_rewards or r == ignore_reward]
        return available if available else [self.view.i18n.get("alerts.dialogs.wizard.step1.no_available")]

    @Slot()
    def _handle_add(self):
        available_rewards = self._get_available_rewards()
        self._active_dialog = AlertConfigWizard(
            self.view.i18n, 
            parent=self.view, 
            rewards_list=available_rewards
        )
        
        if self._active_dialog.exec():
            reward, config = self._active_dialog.get_config_data()
            
            loading_str = self.view.i18n.get("alerts.dialogs.wizard.step1.loading")
            no_rewards_str = self.view.i18n.get("alerts.dialogs.wizard.step1.no_rewards")
            no_avail_str = self.view.i18n.get("alerts.dialogs.wizard.step1.no_available")
            
            if reward and reward not in [loading_str, no_rewards_str, no_avail_str] and config["filepath"]:
                mappings = self.service.get_mappings()
                mappings[reward] = config
                self.service.save_mappings(mappings)
                self.view.populate_table(mappings)
                if hasattr(self.view.window(), 'toast'):
                    self.view.window().toast.show_toast(
                        title=self.view.i18n.get("alerts.status.created"),
                        message=(self.view.i18n.get("alerts.status.created_msg")).replace("{reward}", reward),
                        state="success"
                    )
                
        self._active_dialog = None

    @Slot(str)
    def _handle_edit(self, reward_name: str):
        mappings = self.service.get_mappings()
        if reward_name not in mappings:
            return
            
        available_rewards = self._get_available_rewards(ignore_reward=reward_name)
        self._active_dialog = AlertConfigWizard(
            self.view.i18n, 
            parent=self.view, 
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
                if hasattr(self.view.window(), 'toast'):
                    self.view.window().toast.show_toast(
                        title=self.view.i18n.get("alerts.status.updated"),
                        message=(self.view.i18n.get("alerts.status.updated_msg")).replace("{reward}", new_reward),
                        state="success"
                    )
                
        self._active_dialog = None

    @Slot(str)
    def _handle_delete(self, reward_name: str):
        mappings = self.service.get_mappings()
        if reward_name in mappings:
            del mappings[reward_name]
            self.service.save_mappings(mappings)
            self.view.populate_table(mappings)
            if hasattr(self.view.window(), 'toast'):
                self.view.window().toast.show_toast(
                    title=self.view.i18n.get("alerts.status.deleted"),
                    message=(self.view.i18n.get("alerts.status.deleted_msg")).replace("{reward}", reward_name),
                    state="warning"
                )

    @Slot(str)
    def _handle_preview(self, reward_name: str):
        mappings = self.service.get_mappings()
        if reward_name in mappings:
            self.service.trigger_preview(reward_name, mappings[reward_name])