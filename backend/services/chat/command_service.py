# backend/services/command_service.py

import re
import time

class CommandService:
    def __init__(self, commands_storage, api_client):
        self.storage = commands_storage
        self.api_client = api_client
        self.cooldown_timers = {}

    def get_all_commands(self) -> list[dict]:
        return self.storage.load_all()

    def save_command(self, trigger: str, response: str, is_active: bool, cooldown: int, aliases: str, is_regex: bool, permission: str):
        self.storage.save_command(trigger.strip(), response, is_active, cooldown, aliases, is_regex, permission)

    def delete_command(self, trigger: str):
        if trigger in self.cooldown_timers:
            del self.cooldown_timers[trigger]
        self.storage.delete_command(trigger)

    def _has_permission(self, required_perm: str, user_badges: list) -> bool:
        if required_perm == "everyone": 
            return True
        
        levels = {
            "everyone": 0,
            "subscriber": 1,
            "vip": 2,
            "moderator": 3,
            "broadcaster": 4
        }
        
        user_level = 0
        for badge in user_badges:
            badge_lower = badge.lower()
            if badge_lower in levels and levels[badge_lower] > user_level:
                user_level = levels[badge_lower]
                
        required_level = levels.get(required_perm, 0)
        return user_level >= required_level

    def process_incoming_message(self, user: str, message: str, badges: list) -> tuple[bool, str, dict, str]:
        if not message:
            return False, "", {}, ""

        commands = self.get_all_commands()
        
        for cmd in commands:
            if not cmd.get("is_active", True):
                continue

            permission = cmd.get("permission", "everyone")
            if not self._has_permission(permission, badges):
                continue

            trigger = cmd["trigger"]
            cooldown = cmd.get("cooldown", 5)

            last_executed = self.cooldown_timers.get(trigger, 0)
            if time.time() - last_executed < cooldown:
                continue

            is_match = False
            matched_prefix = ""

            if cmd.get("is_regex", False):
                regex_pattern = cmd.get("aliases", "")
                try:
                    match = re.search(regex_pattern, message, re.IGNORECASE)
                    if match:
                        is_match = True
                        matched_prefix = match.group(0)
                except re.error:
                    pass
            else:
                triggers_to_check = [trigger.lower()]
                raw_aliases = cmd.get("aliases", "")
                
                if raw_aliases:
                    for alias in raw_aliases.split(","):
                        if alias.strip():
                            triggers_to_check.append(alias.strip().lower())
                
                msg_parts = message.split()
                first_word = msg_parts[0].lower() if msg_parts else ""
                
                if first_word in triggers_to_check:
                    is_match = True
                    matched_prefix = msg_parts[0]

            if is_match:
                self.cooldown_timers[trigger] = time.time()
                final_response = cmd["response"].replace("{user}", user)
                if final_response.startswith("[PLUGIN_"):
                    return True, final_response, cmd, matched_prefix

                self.send_response(final_response)
                return True, "", cmd, matched_prefix

        return False, "", {}, ""

    def send_response(self, response_text: str):
        try:
            self.api_client.post_chat_message(content=response_text, msg_type="bot")
        except Exception as e:
            print(f"[CommandService] Error sending command to chat: {e}")