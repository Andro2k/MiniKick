# backend\controllers\rewards_controller.py

import logging
from PySide6.QtCore import QObject, Slot
from backend.providers.chat.kick_client import KickAPIClient
from backend.providers.chat.twitch_client import TwitchAPIClient
from backend.config.api_keys import TWITCH_CLIENT_ID
from backend.workers import CreateRewardWorker, UpdateRewardWorker

logger = logging.getLogger("minikick.controllers.rewards")

class RewardsController(QObject):
    def __init__(self, view, service, toast_manager=None, auth_manager=None, twitch_auth_manager=None, twitch_api_client=None, twitch_broadcaster_id=""):
        super().__init__()
        self.view = view
        self.service = service
        self.toast = toast_manager
        self.auth_manager = auth_manager
        self.twitch_auth_manager = twitch_auth_manager
        self.twitch_api_client = twitch_api_client
        self.twitch_broadcaster_id = twitch_broadcaster_id
        self.create_reward_worker = None
        self.update_reward_worker = None
        self.rewards_details_map = {}
        self.current_rewards_list = [self.view.i18n.get("rewards.dialogs.wizard.step1.no_rewards")] if self.view else ["No Rewards"]
        if self.view is not None:
            self._connect_signals()

    def set_twitch_context(self, twitch_auth_manager, twitch_api_client: TwitchAPIClient | None, broadcaster_id: str = ""):
        self.twitch_auth_manager = twitch_auth_manager
        self.twitch_api_client = twitch_api_client
        self.twitch_broadcaster_id = broadcaster_id

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
            placeholder_strings = {
                self.view.i18n.get("rewards.dialogs.wizard.step1.no_rewards"),
                self.view.i18n.get("rewards.dialogs.wizard.step1.no_available"),
                self.view.i18n.get("rewards.dialogs.wizard.step1.loading"),
                "No Rewards", "No rewards available"
            }

            if isinstance(rewards_map, dict):
                target_platform = "kick"
                for item in rewards_map.values():
                    if isinstance(item, dict) and "platform" in item:
                        target_platform = item["platform"]
                        break

                keys_to_remove = [
                    k for k, v in self.rewards_details_map.items()
                    if isinstance(v, dict) and v.get("platform", "kick") == target_platform
                ]
                for k in keys_to_remove:
                    del self.rewards_details_map[k]

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
                        if "platform" in details and conf.get("platform") != details["platform"]:
                            conf["platform"] = details["platform"]
                            updated = True
                if updated:
                    self.service.save_mappings(mappings)

            self.current_rewards_list = [
                title for title in self.rewards_details_map.keys()
                if title and title not in placeholder_strings
            ]
            if rewards:
                for r in rewards:
                    if r and r not in placeholder_strings and r not in self.current_rewards_list:
                        self.current_rewards_list.append(r)

            self.view.update_active_dialog_rewards(self._get_available_rewards(), self.rewards_details_map)

    def _get_available_rewards(self, ignore_reward=None):
        mappings = self.service.get_mappings()
        used_rewards = set(mappings.keys())
        
        all_rewards = []
        placeholder_strings = {
            self.view.i18n.get("rewards.dialogs.wizard.step1.no_rewards"),
            self.view.i18n.get("rewards.dialogs.wizard.step1.no_available"),
            self.view.i18n.get("rewards.dialogs.wizard.step1.loading"),
            "No Rewards", "No rewards available"
        } if self.view else set()

        combined = list(self.rewards_details_map.keys()) + self.current_rewards_list
        for r in combined:
            if r and r not in placeholder_strings and r not in all_rewards:
                all_rewards.append(r)

        available = [r for r in all_rewards if r not in used_rewards or r == ignore_reward]
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

        target_platform = config.get("platform", "kick")
        logger.info("[User Action] Added custom reward trigger: name='%s', platform=%s, is_new=%s", reward, target_platform, config.get("is_new_reward"))

        if config.get("is_new_reward") and config.get("new_reward_data"):
            if target_platform == "twitch":
                if not self.twitch_auth_manager or not self.twitch_auth_manager.is_authenticated():
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
                        message=self.view.i18n.get("rewards.status.creating_api").replace("{platform}", "Twitch"),
                        state="info"
                    )

                api_client = self.twitch_api_client or TwitchAPIClient(self.twitch_auth_manager, TWITCH_CLIENT_ID, i18n=self.view.i18n)
                self.create_reward_worker = CreateRewardWorker(
                    api_client=api_client,
                    payload=config["new_reward_data"],
                    broadcaster_id=self.twitch_broadcaster_id,
                    platform="twitch"
                )
                self.create_reward_worker.reward_created.connect(
                    lambda res_dict: self._on_reward_created_api(res_dict, config)
                )
                self.create_reward_worker.error_occurred.connect(self._on_reward_creation_error)
                self.create_reward_worker.finished.connect(self.create_reward_worker.deleteLater)
                self.create_reward_worker.start()

            else:
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
                        message=self.view.i18n.get("rewards.status.creating_api").replace("{platform}", "Kick"),
                        state="info"
                    )

                api_client = KickAPIClient(auth_provider=self.auth_manager)
                self.create_reward_worker = CreateRewardWorker(
                    api_client=api_client,
                    payload=config["new_reward_data"],
                    platform="kick"
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
        platform = api_response.get("platform", config.get("platform", "kick"))

        config["id"] = created_id
        config["platform"] = platform
        config["cost"] = api_response.get("cost", config.get("new_reward_data", {}).get("cost", 100))
        config["description"] = api_response.get("description", config.get("new_reward_data", {}).get("description", ""))
        config["background_color"] = api_response.get("background_color", config.get("new_reward_data", {}).get("background_color", "#00e701"))
        config["is_user_input_required"] = api_response.get("is_user_input_required", config.get("new_reward_data", {}).get("is_user_input_required", False))

        self.current_rewards_list.append(created_title)
        self.rewards_details_map[created_title] = {
            "id": created_id,
            "platform": platform,
            "cost": config["cost"],
            "description": config["description"],
            "background_color": config["background_color"],
            "is_user_input_required": config["is_user_input_required"]
        }

        self._save_reward_mapping(created_title, config)
        
        plat_label = "Twitch" if platform == "twitch" else "Kick"
        if self.toast:
            self.toast.show_toast(
                title=self.view.i18n.get("rewards.status.created"),
                message=self.view.i18n.get("rewards.status.created_api_success").replace("{reward}", created_title).replace("{platform}", plat_label),
                state="success"
            )

        if self.view and hasattr(self.view, "refresh_rewards_requested"):
            self.view.refresh_rewards_requested.emit()

    def _on_reward_creation_error(self, err_msg: str):
        logger.error("[RewardsController] Error creating reward on API: %s", err_msg)
        if self.toast:
            self.toast.show_toast(
                title=self.view.i18n.get("common.status.error"),
                message=self.view.i18n.get("rewards.status.created_api_error").replace("{error}", err_msg).replace("{platform}", "API"),
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

                target_platform = updated_config.get("platform", mappings.get(reward_name, {}).get("platform", "kick"))
                updated_config["platform"] = target_platform

                if target_platform == "twitch" and reward_id and self.twitch_auth_manager and self.twitch_auth_manager.is_authenticated():
                    if self.toast:
                        self.toast.show_toast(
                            title=self.view.i18n.get("rewards.status.updated"),
                            message=self.view.i18n.get("rewards.status.updating_api").replace("{platform}", "Twitch"),
                            state="info"
                        )

                    payload = {
                        "title": new_reward,
                        "cost": updated_config.get("cost", 100),
                        "description": updated_config.get("description", ""),
                        "background_color": updated_config.get("background_color", "#9146FF"),
                        "is_user_input_required": updated_config.get("is_user_input_required", False)
                    }

                    api_client = self.twitch_api_client or TwitchAPIClient(self.twitch_auth_manager, TWITCH_CLIENT_ID, i18n=self.view.i18n)
                    self.update_reward_worker = UpdateRewardWorker(
                        api_client=api_client,
                        reward_id=reward_id,
                        payload=payload,
                        broadcaster_id=self.twitch_broadcaster_id,
                        platform="twitch"
                    )
                    self.update_reward_worker.reward_updated.connect(
                        lambda res_dict, o=reward_name, n=new_reward, c=updated_config: self._on_reward_updated_api(res_dict, o, n, c)
                    )
                    self.update_reward_worker.error_occurred.connect(
                        lambda err_msg, o=reward_name, n=new_reward, c=updated_config, p=target_platform: self._on_reward_update_error(err_msg, o, n, c, p)
                    )
                    self.update_reward_worker.finished.connect(self.update_reward_worker.deleteLater)
                    self.update_reward_worker.start()

                elif target_platform == "kick" and reward_id and self.auth_manager and self.auth_manager.get_tokens():
                    if self.toast:
                        self.toast.show_toast(
                            title=self.view.i18n.get("rewards.status.updated"),
                            message=self.view.i18n.get("rewards.status.updating_api").replace("{platform}", "Kick"),
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
                        platform="kick"
                    )
                    self.update_reward_worker.reward_updated.connect(
                        lambda res_dict, o=reward_name, n=new_reward, c=updated_config: self._on_reward_updated_api(res_dict, o, n, c)
                    )
                    self.update_reward_worker.error_occurred.connect(
                        lambda err_msg, o=reward_name, n=new_reward, c=updated_config, p=target_platform: self._on_reward_update_error(err_msg, o, n, c, p)
                    )
                    self.update_reward_worker.finished.connect(self.update_reward_worker.deleteLater)
                    self.update_reward_worker.start()
                else:
                    self._save_edited_mapping(reward_name, new_reward, updated_config)

    def _on_reward_updated_api(self, api_response: dict, old_reward: str, new_reward: str, updated_config: dict):
        updated_title = api_response.get("title", new_reward)
        updated_id = api_response.get("id", updated_config.get("id"))
        platform = api_response.get("platform", updated_config.get("platform", "kick"))

        updated_config["id"] = updated_id
        updated_config["platform"] = platform
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
            "platform": platform,
            "cost": updated_config["cost"],
            "description": updated_config["description"],
            "background_color": updated_config["background_color"],
            "is_user_input_required": updated_config["is_user_input_required"]
        }

        self._save_edited_mapping(old_reward, updated_title, updated_config)

        plat_label = "Twitch" if platform == "twitch" else "Kick"
        if self.toast:
            self.toast.show_toast(
                title=self.view.i18n.get("rewards.status.updated"),
                message=self.view.i18n.get("rewards.status.updated_api_success").replace("{reward}", updated_title).replace("{platform}", plat_label),
                state="success"
            )

        if self.view and hasattr(self.view, "refresh_rewards_requested"):
            self.view.refresh_rewards_requested.emit()

    def _on_reward_update_error(self, err_msg: str, old_reward: str = "", new_reward: str = "", updated_config: dict = None, platform: str = "kick"):
        logger.error("[RewardsController] Error updating reward on API: %s", err_msg)
        if old_reward and updated_config:
            target_name = new_reward or old_reward
            self._save_edited_mapping(old_reward, target_name, updated_config)

        if self.toast:
            is_twitch_unmanageable = "403" in err_msg or "Client-Id" in err_msg or "partner or affiliate" in err_msg
            if platform == "twitch" and is_twitch_unmanageable:
                self.toast.show_toast(
                    title=self.view.i18n.get("rewards.status.updated"),
                    message=self.view.i18n.get("rewards.status.updated_local_only_twitch_unmanageable"),
                    state="warning"
                )
            else:
                plat_label = "Twitch" if platform == "twitch" else "Kick"
                self.toast.show_toast(
                    title=self.view.i18n.get("rewards.status.updated"),
                    message=self.view.i18n.get("rewards.status.updated_local_saved_api_failed").replace("{error}", err_msg).replace("{platform}", plat_label),
                    state="warning"
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
