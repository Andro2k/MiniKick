# backend\services\chat\command_service.py

import logging
import re
import time

from PySide6.QtCore import QObject, Signal

class CommandService(QObject):
    commands_changed = Signal()
    _PERMISSIONS = {
        "everyone": 0,"subscriber": 1,
        "vip": 2,"moderator": 3,"broadcaster": 4
    }

    def __init__(self, commands_storage, api_client=None):
        super().__init__()
        self.storage = commands_storage
        self.api_client = api_client
        self.cooldown_timers: dict[str, float] = {}
        self._dispatch_table: dict[str, dict] = {}
        self._regex_commands: list[dict] = []
        self.reload_cache()

    def reload_cache(self):
        self._dispatch_table.clear()
        self._regex_commands.clear()
        
        for cmd in self.storage.load_all():
            if not cmd.get("is_active", True):
                continue
            
            if cmd.get("is_regex", False):
                pattern = cmd.get("aliases", "").strip()
                if pattern:
                    try:
                        cmd["_compiled_regex"] = re.compile(pattern, re.IGNORECASE)
                        self._regex_commands.append(cmd)
                    except re.error as e:
                        logging.error("[CommandService] Error compiling regex pattern '%s' for trigger '%s': %s", pattern, cmd['trigger'], e)
            else:
                trigger = cmd["trigger"].strip().lower()
                self._dispatch_table[trigger] = cmd
                
                aliases = cmd.get("aliases", "")
                if aliases:
                    for alias in aliases.split(","):
                        clean_alias = alias.strip().lower()
                        if clean_alias:
                            self._dispatch_table[clean_alias] = cmd
        self.commands_changed.emit()

    def get_all_commands(self) -> list[dict]:
        return self.storage.load_all()

    def get_command_by_trigger(self, trigger: str) -> dict | None:
        return self.storage.get_command_by_trigger(trigger)

    def search_commands(self, query: str) -> list[dict]:
        return self.storage.search_commands(query)

    def save_command(self, trigger: str, response: str, is_active: bool, cooldown: int, aliases: str, is_regex: bool, permission: str):
        self.storage.save_command(trigger.strip(), response, is_active, cooldown, aliases, is_regex, permission)
        self.reload_cache()

    def delete_command(self, trigger: str):
        clean_trigger = trigger.strip()
        self.cooldown_timers.pop(clean_trigger, None)
        self.storage.delete_command(clean_trigger)
        self.reload_cache()

    def _has_permission(self, required_perm: str, user_badges: list) -> bool:
        req_level = self._PERMISSIONS.get(required_perm, 0)
        if req_level == 0:
            return True

        user_level = 0
        for badge in user_badges:
            val = self._PERMISSIONS.get(badge.lower(), 0)
            if val > user_level:
                user_level = val

        return user_level >= req_level

    def process_incoming_message(self, user: str, message: str, badges: list) -> tuple[bool, str, dict, str]:
        if not message:
            return False, "", {}, ""

        parts = message.split(maxsplit=1)
        first_word = parts[0].lower()
        raw_first_word = parts[0]

        args = parts[1] if len(parts) > 1 else ""
        touser = args.strip().split()[0] if args.strip() else user
        if touser.startswith("@"):
            touser = touser[1:]

        cmd = self._dispatch_table.get(first_word)
        if cmd:
            return self._try_execute(cmd, user, touser, badges, raw_first_word)

        for regex_cmd in self._regex_commands:
            compiled = regex_cmd.get("_compiled_regex")
            if compiled:
                match = compiled.search(message)
                if match:
                    remaining = message[match.end():].strip()
                    reg_touser = remaining.split()[0] if remaining else user
                    if reg_touser.startswith("@"):
                        reg_touser = reg_touser[1:]
                    return self._try_execute(regex_cmd, user, reg_touser, badges, match.group(0))

        return False, "", {}, ""

    def _try_execute(self, cmd: dict, user: str, touser: str, badges: list, matched_prefix: str) -> tuple[bool, str, dict, str]:
        if not self._has_permission(cmd.get("permission", "everyone"), badges):
            return False, "", {}, ""

        trigger = cmd["trigger"]
        cooldown = cmd.get("cooldown", 5)
        now = time.time()

        if now - self.cooldown_timers.get(trigger, 0) < cooldown:
            return False, "", {}, ""

        self.cooldown_timers[trigger] = now
        
        import random
        final_response = cmd["response"].replace("{user}", user).replace("{touser}", touser).replace("{random}", str(random.randint(1, 100)))

        try:
            self.storage.log_command_execution(trigger, user)
        except Exception as e:
            logging.error("[CommandService] Error logging command execution: %s", e)

        if final_response.startswith("[PLUGIN_"):
            return True, final_response, cmd, matched_prefix

        self.send_response(final_response)
        return True, "", cmd, matched_prefix

    def send_response(self, response_text: str):
        if not self.api_client:
            return
        try:
            self.api_client.post_chat_message(content=response_text, msg_type="bot")
        except Exception as e:
            logging.error("[CommandService] Error sending command to chat: %s", e)
