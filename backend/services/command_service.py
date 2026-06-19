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
        """Verifica jerárquicamente si los badges del usuario cumplen con el nivel requerido."""
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

    def process_incoming_message(self, user: str, message: str, badges: list):
        """Comprueba si el mensaje encaja con algún comando activo y ejecuta respuesta, validando permisos."""
        if not message:
            return

        commands = self.get_all_commands()
        
        for cmd in commands:
            if not cmd.get("is_active", True):
                continue

            permission = cmd.get("permission", "everyone")
            if permission == "moderator" and not ("moderator" in badges or "broadcaster" in badges):
                continue
            if permission == "broadcaster" and "broadcaster" not in badges:
                continue

            trigger = cmd["trigger"]
            cooldown = cmd.get("cooldown", 5)

            last_executed = self.cooldown_timers.get(trigger, 0)
            if time.time() - last_executed < cooldown:
                continue

            is_match = False

            if cmd.get("is_regex", False):
                regex_pattern = cmd.get("aliases", "")
                try:
                    if re.search(regex_pattern, message, re.IGNORECASE):
                        is_match = True
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

            if is_match:
                self.cooldown_timers[trigger] = time.time()
                final_response = cmd["response"].replace("{user}", user)
                self.send_response(final_response)
                break

    def send_response(self, response_text: str):
        try:
            self.api_client.post_chat_message(content=response_text, msg_type="bot")
        except Exception as e:
            print(f"[CommandService] Error al enviar comando al chat: {e}")