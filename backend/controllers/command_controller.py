# backend\controllers\command_controller.py

import logging
from PySide6.QtCore import QObject, Slot

logger = logging.getLogger("minikick.controllers.commands")

class CommandController(QObject):
    def __init__(self, view, service, toast_manager=None, connected_platforms_provider=None, i18n=None):
        super().__init__()
        self.view = view
        self.service = service
        self.toast = toast_manager
        self.connected_platforms_provider = connected_platforms_provider
        self.i18n = i18n
        self._needs_reload = False
        self._view_connected = False
        self._is_internal_toggle = False

        if self.service and hasattr(self.service, "commands_changed"):
            self.service.commands_changed.connect(self._on_commands_changed)

        if self.view is not None:
            self._connect_signals()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            self.load_initial_data(force=True)

    def _get_i18n(self):
        if self.i18n:
            return self.i18n
        if self.view and hasattr(self.view, "i18n") and self.view.i18n:
            return self.view.i18n
        from backend.services.system.translation_service import TranslationService
        return TranslationService()

    def _connect_signals(self):
        if not self.view or self._view_connected:
            return
        self._view_connected = True
        self.view.add_requested.connect(self._handle_add)
        self.view.edit_requested.connect(self._handle_edit)
        self.view.delete_requested.connect(self._handle_delete)
        self.view.status_toggled.connect(self._handle_status_change)
        self.view.search_text_changed.connect(self._handle_search)
        if hasattr(self.view, "view_shown"):
            self.view.view_shown.connect(self._on_view_shown)

    def _on_view_shown(self):
        if self._needs_reload:
            self.load_initial_data(force=True)

    def _on_commands_changed(self):
        if self._is_internal_toggle:
            return
        self.load_initial_data(force=False)

    def load_initial_data(self, force: bool = False):
        if self.view is not None:
            if callable(self.connected_platforms_provider) and hasattr(self.view, "set_connected_platforms"):
                self.view.connected_platforms = self.connected_platforms_provider()
            if force or self.view.isVisible():
                self._needs_reload = False
                commands = self.service.get_all_commands()
                self.view.populate_table(commands)
            else:
                self._needs_reload = True

    @Slot()
    def _handle_add(self):
        logger.info("[User Action] Opened Add Command dialog")
        connected_plats = self.connected_platforms_provider() if callable(self.connected_platforms_provider) else None
        data = self.view.show_add_dialog(connected_platforms=connected_plats)
        if data:
            data.pop("original_trigger", None)
            if data.get("trigger") and data.get("response"):
                logger.info("[User Action] Created new command: trigger='%s', response='%s', cooldown=%s, perm='%s'",
                            data.get("trigger"), data.get("response"), data.get("cooldown"), data.get("permission"))
                self.service.save_command(**data)
                self._show_toast("command.status.created", "command.status.created_msg", data['trigger'], "success")

    @Slot(str)
    def _handle_edit(self, trigger: str):
        existing = self.service.get_command_by_trigger(trigger)
        if not existing:
            return
        logger.info("[User Action] Opened Edit Command dialog: trigger='%s'", trigger)
        connected_plats = self.connected_platforms_provider() if callable(self.connected_platforms_provider) else None
        data = self.view.show_edit_dialog(existing, connected_platforms=connected_plats)
        if data:
            original_trigger = data.pop("original_trigger", None)
            if data.get("response") and data.get("trigger"):
                if original_trigger and original_trigger != data["trigger"]:
                    logger.info("[User Action] Renamed command trigger from '%s' to '%s'", original_trigger, data["trigger"])
                    self.service.delete_command(original_trigger)
                    
                logger.info("[User Action] Updated command: trigger='%s', response='%s', cooldown=%s, perm='%s'",
                            data.get("trigger"), data.get("response"), data.get("cooldown"), data.get("permission"))
                self.service.save_command(**data)
                self._show_toast("command.status.updated", "command.status.updated_msg", data['trigger'], "success")

    @Slot(str)
    def _handle_delete(self, trigger: str):
        logger.info("[User Action] Deleted command: trigger='%s'", trigger)
        self.service.delete_command(trigger)
        self._show_toast("command.status.deleted", "command.status.deleted_msg", trigger, "warning")

    @Slot(str, bool)
    def _handle_status_change(self, trigger: str, is_active: bool):
        existing = self.service.get_command_by_trigger(trigger)
        if not existing:
            return
        if existing.get("is_active") == is_active:
            return

        logger.info("[User Action] Toggled command status: trigger='%s', is_active=%s", trigger, is_active)
        i18n = self._get_i18n()
        if self.toast:
            title_key = "command.status.enabled" if is_active else "command.status.disabled"
            state_color = "success" if is_active else "info"
            self.toast.show_toast(
                title=i18n.get(title_key),
                message=i18n.get("command.status.toggled_msg").replace("{trigger}", trigger),
                state=state_color,
                tag=f"cmd_toggle_{trigger}"
            )

        self._is_internal_toggle = True
        try:
            self.service.save_command(
                trigger=existing["trigger"],
                response=existing["response"],
                is_active=is_active,
                cooldown=existing["cooldown"],
                aliases=existing["aliases"],
                is_regex=existing["is_regex"],
                permission=existing.get("permission", "everyone"),
                apply_kick=existing.get("apply_kick", True),
                apply_twitch=existing.get("apply_twitch", True),
                apply_youtube=existing.get("apply_youtube", True),
                apply_tiktok=existing.get("apply_tiktok", True)
            )
        finally:
            self._is_internal_toggle = False

    @Slot(str)
    def _handle_search(self, text: str):
        logger.debug("[User Action] Filtered commands by search term: '%s'", text)
        if not text.strip():
            self.load_initial_data()
            return
            
        filtered_commands = self.service.search_commands(text)
        self.view.populate_table(filtered_commands)

    def _show_toast(self, title_key: str, msg_key: str, val: str, state: str):
        if self.toast:
            i18n = self._get_i18n()
            self.toast.show_toast(
                title=i18n.get(title_key),
                message=i18n.get(msg_key).replace("{trigger}", val),
                state=state
            )
