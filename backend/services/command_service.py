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

    def save_command(self, trigger: str, response: str, is_active: bool, cooldown: int, aliases: str, is_regex: bool):
        self.storage.save_command(trigger.strip(), response, is_active, cooldown, aliases, is_regex)

    def delete_command(self, trigger: str):
        if trigger in self.cooldown_timers:
            del self.cooldown_timers[trigger]
        self.storage.delete_command(trigger)

    def process_incoming_message(self, user: str, message: str):
        """Comprueba si el mensaje encaja con algún comando activo y ejecuta respuesta."""
        if not message:
            return

        commands = self.get_all_commands()
        
        for cmd in commands:
            if not cmd.get("is_active", True):
                continue

            trigger = cmd["trigger"]
            cooldown = cmd.get("cooldown", 5)

            last_executed = self.cooldown_timers.get(trigger, 0)
            if time.time() - last_executed < cooldown:
                continue

            is_match = False

            if cmd.get("is_regex", False):
                try:
                    if re.search(trigger, message, re.IGNORECASE):
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
        """Envía la respuesta configurada a través del cliente oficial de Kick."""
        try:
            self.api_client.post_chat_message(content=response_text, msg_type="bot")
        except Exception as e:
            print(f"[CommandService] Error al enviar comando al chat: {e}")