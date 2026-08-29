# backend\controllers\rewards_controller.py

import logging
from PySide6.QtCore import QObject, Slot
from backend.providers.chat.kick_client import KickAPIClient
from backend.workers import CreateRewardWorker, UpdateRewardWorker

logger = logging.getLogger("minikick.controllers.rewards")

class RewardsController(QObject):
    def __init__(self, view, service, toast_manager=None, auth_manager=None):
        super().__init__()
        self.view = view
        self.service = service
        self.toast = toast_manager
        self.auth_manager = auth_manager
        self.create_reward_worker = None
        self.update_reward_worker = None
        self.rewards_details_map = {}
        self.current_rewards_list = [self.view.i18n.get("rewards.dialogs.wizard.step1.no_rewards")] if self.view else ["No Rewards"]
        if self.view is not None:
            self._connect_signals()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            self.load_initial_data()

    def _connect_signals(self):
        self.view.add_requested.connect(self._handle_add)
        self.view.edit_requested.connect(self._handle_edit)
        self.view.delete_requested.connect(self._handle_delete)
        self.view.preview_requested.connect(self._handle_preview)

    def load_initial_data(self):
        if self.view is not None:
            mappings = self.service.get_mappings()
            self.view.populate_table(mappings)

    @Slot(object)
    @Slot(object, object)
    def update_rewards_list(self, rewards: list, rewards_map: dict = None):
        if self.view is not None:
            self.current_rewards_list = rewards if rewards else [self.view.i18n.get("rewards.dialogs.wizard.step1.no_rewards")]
            if isinstance(rewards_map, dict):
                self.rewards_details_map.update(rewards_map)
                
                mappings = self.service.get_mappings()
                updated = False
                for title, details in rewards_map.items():
                    if title in mappings and isinstance(mappings[title], dict):
                        conf = mappings[title]
                        if "id" in details and conf.get("id") != details["id"]:
                            conf["id"] = details["id"]
                            updated = True
                        if "cost" in details and conf.get("cost") != details["cost"]:
                            conf["cost"] = details["cost"]
                            updated = True
                        if "description" in details and conf.get("description") != details["description"]:
                            conf["description"] = details["description"]
                            updated = True
                        if "background_color" in details and conf.get("background_color") != details["background_color"]:
                            conf["background_color"] = details["background_color"]
                            updated = True
                        if "is_user_input_required" in details and conf.get("is_user_input_required") != details["is_user_input_required"]:
                            conf["is_user_input_required"] = details["is_user_input_required"]
                            updated = True
                if updated:
                    self.service.save_mappings(mappings)

            self.view.update_active_dialog_rewards(self._get_available_rewards())

    def _get_available_rewards(self, ignore_reward=None):
        mappings = self.service.get_mappings()
        used_rewards = mappings.keys()
        available = [r for r in self.current_rewards_list if r not in used_rewards or r == ignore_reward]
        return available if available else [self.view.i18n.get("rewards.dialogs.wizard.step1.no_available")]

    @Slot()
    def _handle_add(self):
        logger.info("[User Action] Opened Add Reward dialog")
        available_rewards = self._get_available_rewards()
        res = self.view.show_add_dialog(available_rewards, self.rewards_details_map)
        if not res:
            return

        reward, config = res
        if not config.get("filepath"):
            return

        logger.info("[User Action] Added custom reward trigger: name='%s', is_new=%s", reward, config.get("is_new_reward"))
        if config.get("is_new_reward") and config.get("new_reward_data"):
            if not self.auth_manager or not self.auth_manager.get_tokens():
                if self.toast:
                    self.toast.show_toast(
                        title=self.view.i18n.get("common.status.error"),
                        message=self.view.i18n.get("main.logs.api_offline"),
                        state="danger"
                    )
                return

            if self.toast:
                self.toast.show_toast(
                    title=self.view.i18n.get("rewards.status.created"),
                    message=self.view.i18n.get("rewards.status.creating_api"),
                    state="info"
                )

            api_client = KickAPIClient(auth_provider=self.auth_manager)
            self.create_reward_worker = CreateRewardWorker(
                api_client=api_client,
                payload=config["new_reward_data"],
                parent=self
            )
            self.create_reward_worker.reward_created.connect(
                lambda res_dict: self._on_reward_created_api(res_dict, config)
            )
            self.create_reward_worker.error_occurred.connect(self._on_reward_creation_error)
            self.create_reward_worker.finished.connect(self.create_reward_worker.deleteLater)
            self.create_reward_worker.start()
        else:
            self._save_reward_mapping(reward, config)

    def _on_reward_created_api(self, api_response: dict, config: dict):
        created_title = api_response.get("title", "")
        created_id = api_response.get("id", "")

        config["id"] = created_id
        config["cost"] = api_response.get("cost", config.get("new_reward_data", {}).get("cost", 100))
        config["description"] = api_response.get("description", config.get("new_reward_data", {}).get("description", ""))
        config["background_color"] = api_response.get("background_color", config.get("new_reward_data", {}).get("background_color", "#53FC18"))
        config["is_user_input_required"] = api_response.get("is_user_input_required", config.get("new_reward_data", {}).get("is_user_input_required", False))

        self.current_rewards_list.append(created_title)
        self.rewards_details_map[created_title] = {
            "id": created_id,
            "cost": config["cost"],
            "description": config["description"],
            "background_color": config["background_color"],
            "is_user_input_required": config["is_user_input_required"]
        }

        self._save_reward_mapping(created_title, config)
        
        if self.toast:
            self.toast.show_toast(
                title=self.view.i18n.get("rewards.status.created"),
                message=self.view.i18n.get("rewards.status.created_api_success").replace("{reward}", created_title),
                state="success"
            )

        if self.view and hasattr(self.view, "refresh_rewards_requested"):
            self.view.refresh_rewards_requested.emit()

    def _on_reward_creation_error(self, err_msg: str):
        logger.error("[RewardsController] Error creating reward on API: %s", err_msg)
        if self.toast:
            self.toast.show_toast(
                title=self.view.i18n.get("common.status.error"),
                message=self.view.i18n.get("rewards.status.created_api_error").replace("{error}", err_msg),
                state="danger"
            )

    def _save_reward_mapping(self, reward_name: str, config: dict):
        from backend.services.rewards.thumbnail_service import generate_media_thumbnail
        config["thumbnail_bytes"] = generate_media_thumbnail(config["filepath"])
        mappings = self.service.get_mappings()
        mappings[reward_name] = config
        self.service.save_mappings(mappings)
        if self.view:
            self.view.populate_table(mappings)
            if self.toast and not config.get("is_new_reward"):
                self.toast.show_toast(
                    title=self.view.i18n.get("rewards.status.created"),
                    message=(self.view.i18n.get("rewards.status.created_msg")).replace("{reward}", reward_name),
                    state="success"
                )

    @Slot(str)
    def _handle_edit(self, reward_name: str):
        mappings = self.service.get_mappings()
        if reward_name not in mappings:
            return
            
        logger.info("[User Action] Opened Edit Reward dialog: name='%s'", reward_name)
        available_rewards = self._get_available_rewards(ignore_reward=reward_name)
        res = self.view.show_edit_dialog(available_rewards, mappings[reward_name], reward_name, self.rewards_details_map)
        if res:
            new_reward, updated_config = res
            if updated_config.get("filepath"):
                reward_id = (
                    updated_config.get("id") or 
                    mappings.get(reward_name, {}).get("id") or 
                    self.rewards_details_map.get(reward_name, {}).get("id")
                )
                if reward_id:
                    updated_config["id"] = reward_id

                if reward_id and self.auth_manager and self.auth_manager.get_tokens():
                    if self.toast:
                        self.toast.show_toast(
                            title=self.view.i18n.get("rewards.status.updated"),
                            message=self.view.i18n.get("rewards.status.updating_api"),
                            state="info"
                        )

                    payload = {
                        "title": new_reward,
                        "cost": updated_config.get("cost", 100),
                        "description": updated_config.get("description", ""),
                        "background_color": updated_config.get("background_color", "#53FC18"),
                        "is_user_input_required": updated_config.get("is_user_input_required", False)
                    }

                    api_client = KickAPIClient(auth_provider=self.auth_manager)
                    self.update_reward_worker = UpdateRewardWorker(
                        api_client=api_client,
                        reward_id=reward_id,
                        payload=payload,
                        parent=self
                    )
                    self.update_reward_worker.reward_updated.connect(
                        lambda res_dict, o=reward_name, n=new_reward, c=updated_config: self._on_reward_updated_api(res_dict, o, n, c)
                    )
                    self.update_reward_worker.error_occurred.connect(self._on_reward_update_error)
                    self.update_reward_worker.finished.connect(self.update_reward_worker.deleteLater)
                    self.update_reward_worker.start()
                else:
                    self._save_edited_mapping(reward_name, new_reward, updated_config)

    def _on_reward_updated_api(self, api_response: dict, old_reward: str, new_reward: str, updated_config: dict):
        updated_title = api_response.get("title", new_reward)
        updated_id = api_response.get("id", updated_config.get("id"))

        updated_config["id"] = updated_id
        updated_config["cost"] = api_response.get("cost", updated_config.get("cost", 100))
        updated_config["description"] = api_response.get("description", updated_config.get("description", ""))
        updated_config["background_color"] = api_response.get("background_color", updated_config.get("background_color", "#53FC18"))
        updated_config["is_user_input_required"] = api_response.get("is_user_input_required", updated_config.get("is_user_input_required", False))

        if old_reward in self.current_rewards_list:
            self.current_rewards_list.remove(old_reward)
        self.current_rewards_list.append(updated_title)

        if old_reward in self.rewards_details_map:
            del self.rewards_details_map[old_reward]
        self.rewards_details_map[updated_title] = {
            "id": updated_id,
            "cost": updated_config["cost"],
            "description": updated_config["description"],
            "background_color": updated_config["background_color"],
            "is_user_input_required": updated_config["is_user_input_required"]
        }

        self._save_edited_mapping(old_reward, updated_title, updated_config)

        if self.toast:
            self.toast.show_toast(
                title=self.view.i18n.get("rewards.status.updated"),
                message=self.view.i18n.get("rewards.status.updated_api_success").replace("{reward}", updated_title),
                state="success"
            )

        if self.view and hasattr(self.view, "refresh_rewards_requested"):
            self.view.refresh_rewards_requested.emit()

    def _on_reward_update_error(self, err_msg: str):
        logger.error("[RewardsController] Error updating reward on API: %s", err_msg)
        if self.toast:
            self.toast.show_toast(
                title=self.view.i18n.get("common.status.error"),
                message=self.view.i18n.get("rewards.status.updated_api_error").replace("{error}", err_msg),
                state="danger"
            )

    def _save_edited_mapping(self, old_reward: str, new_reward: str, updated_config: dict):
        logger.info("[User Action] Saved edited reward trigger mapping: old='%s', new='%s'", old_reward, new_reward)
        from backend.services.rewards.thumbnail_service import generate_media_thumbnail
        mappings = self.service.get_mappings()
        old_filepath = mappings.get(old_reward, {}).get("filepath", "") if old_reward in mappings else ""
        if updated_config["filepath"] != old_filepath or "thumbnail_bytes" not in mappings.get(old_reward, {}):
            updated_config["thumbnail_bytes"] = generate_media_thumbnail(updated_config["filepath"])
        else:
            updated_config["thumbnail_bytes"] = mappings.get(old_reward, {}).get("thumbnail_bytes")

        if old_reward in mappings and old_reward != new_reward:
            del mappings[old_reward]

        mappings[new_reward] = updated_config
        self.service.save_mappings(mappings)
        if self.view:
            self.view.populate_table(mappings)
            if self.toast and not updated_config.get("id"):
                self.toast.show_toast(
                    title=self.view.i18n.get("rewards.status.updated"),
                    message=(self.view.i18n.get("rewards.status.updated_msg")).replace("{reward}", new_reward),
                    state="success"
                )

    @Slot(str)
    def _handle_delete(self, reward_name: str):
        logger.info("[User Action] Deleted reward trigger mapping: name='%s'", reward_name)
        mappings = self.service.get_mappings()
        if reward_name in mappings:
            del mappings[reward_name]
            self.service.save_mappings(mappings)
            self.view.populate_table(mappings)
            if self.toast:
                self.toast.show_toast(
                    title=self.view.i18n.get("rewards.status.deleted"),
                    message=(self.view.i18n.get("rewards.status.deleted_msg")).replace("{reward}", reward_name),
                    state="warning"
                )

    @Slot(str)
    def _handle_preview(self, reward_name: str):
        logger.info("[User Action] Preview triggered for reward: name='%s'", reward_name)
        mappings = self.service.get_mappings()
        if reward_name in mappings:
            config = mappings[reward_name]
            if not self.service.is_file_valid(config):
                if self.toast and self.view:
                    self.toast.show_toast(
                        title=self.view.i18n.get("common.status.error"),
                        message=self.view.i18n.get("rewards.status.file_not_found_action"),
                        state="danger"
                    )
                return
            self.service.trigger_preview(reward_name, config)
