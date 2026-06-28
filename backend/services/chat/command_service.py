# backend\services\chat\command_service.py

import re
import time

class CommandService:
    _PERMISSIONS = {
        "everyone": 0,"subscriber": 1,
        "vip": 2,"moderator": 3,"broadcaster": 4
    }

    def __init__(self, commands_storage, api_client=None):
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
                self._regex_commands.append(cmd)
            else:
                trigger = cmd["trigger"].strip().lower()
                self._dispatch_table[trigger] = cmd
                
                aliases = cmd.get("aliases", "")
                if aliases:
                    for alias in aliases.split(","):
                        clean_alias = alias.strip().lower()
                        if clean_alias:
                            self._dispatch_table[clean_alias] = cmd

    def get_all_commands(self) -> list[dict]:
        return self.storage.load_all()

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

        cmd = self._dispatch_table.get(first_word)
        if cmd:
            return self._try_execute(cmd, user, badges, raw_first_word)

        for regex_cmd in self._regex_commands:
            pattern = regex_cmd.get("aliases", "")
            try:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    return self._try_execute(regex_cmd, user, badges, match.group(0))
            except re.error:
                continue

        return False, "", {}, ""

    def _try_execute(self, cmd: dict, user: str, badges: list, matched_prefix: str) -> tuple[bool, str, dict, str]:
        if not self._has_permission(cmd.get("permission", "everyone"), badges):
            return False, "", {}, ""

        trigger = cmd["trigger"]
        cooldown = cmd.get("cooldown", 5)
        now = time.time()

        if now - self.cooldown_timers.get(trigger, 0) < cooldown:
            return False, "", {}, ""

        self.cooldown_timers[trigger] = now
        final_response = cmd["response"].replace("{user}", user)

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
            print(f"[CommandService] Error sending command to chat: {e}")