# backend\services\chat\command_service.py

import logging
import re
import time

from PySide6.QtCore import QObject, Signal

class CommandService(QObject):
    commands_changed = Signal()
    response_generated = Signal(str, str)
    _PERMISSIONS = {
        "everyone": 0, "subscriber": 1,
        "vip": 2, "moderator": 3, "broadcaster": 4
    }

    def __init__(self, commands_storage, api_client=None):
        super().__init__()
        self.storage = commands_storage
        self.api_client = api_client
        self.twitch_worker = None
        self.cooldown_timers: dict[str, float] = {}
        self._dispatch_table: dict[str, dict] = {}
        self._regex_commands: list[dict] = []
        self._all_commands_cache: list[dict] = []
        
        from PySide6.QtCore import QTimer
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._flush_saves)
        self._pending_saves = {}
        
        self.reload_cache()

    def reload_cache(self):
        self._all_commands_cache = self.storage.load_all()
        self._rebuild_dispatch_table_from_cache()

    def _rebuild_dispatch_table_from_cache(self):
        self._dispatch_table.clear()
        self._regex_commands.clear()
        
        for cmd in self._all_commands_cache:
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

    def _flush_saves(self):
        for trigger_lower, cmd in list(self._pending_saves.items()):
            self.storage.save_command(
                cmd["trigger"], cmd["response"], cmd["is_active"],
                cmd["cooldown"], cmd["aliases"], cmd["is_regex"], cmd["permission"]
            )
        self._pending_saves.clear()

    def get_all_commands(self) -> list[dict]:
        return list(self._all_commands_cache)

    def get_command_by_trigger(self, trigger: str) -> dict | None:
        clean = trigger.strip().lower()
        if clean in self._dispatch_table:
            return self._dispatch_table[clean]
        for cmd in self._all_commands_cache:
            if cmd["trigger"].strip().lower() == clean:
                return cmd
        return self.storage.get_command_by_trigger(trigger)

    def search_commands(self, query: str) -> list[dict]:
        clean_q = query.strip().lower()
        if not clean_q:
            return self.get_all_commands()
        return [
            cmd for cmd in self._all_commands_cache
            if clean_q in cmd["trigger"].lower() or clean_q in cmd.get("aliases", "").lower() or clean_q in cmd.get("response", "").lower()
        ]

    def save_command(self, trigger: str, response: str, is_active: bool, cooldown: int, aliases: str, is_regex: bool, permission: str):
        trigger_clean = trigger.strip()
        cmd_dict = {
            "trigger": trigger_clean,
            "response": response,
            "is_active": is_active,
            "cooldown": cooldown,
            "aliases": aliases,
            "is_regex": is_regex,
            "permission": permission
        }
        
        existing_idx = -1
        for i, cmd in enumerate(self._all_commands_cache):
            if cmd["trigger"].strip().lower() == trigger_clean.lower():
                existing_idx = i
                break
                
        if existing_idx != -1:
            self._all_commands_cache[existing_idx] = cmd_dict
        else:
            self._all_commands_cache.append(cmd_dict)
            
        self._rebuild_dispatch_table_from_cache()
        
        self._pending_saves[trigger_clean.lower()] = cmd_dict
        self._save_timer.start()

    def delete_command(self, trigger: str):
        clean_trigger = trigger.strip()
        self.cooldown_timers.pop(clean_trigger, None)
        self._pending_saves.pop(clean_trigger.lower(), None)
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

    def process_incoming_message(self, user: str, message: str, badges: list, platform: str = "kick") -> tuple[bool, str, dict, str]:
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
            return self._try_execute(cmd, user, touser, badges, raw_first_word, platform=platform)

        for regex_cmd in self._regex_commands:
            compiled = regex_cmd.get("_compiled_regex")
            if compiled:
                match = compiled.search(message)
                if match:
                    remaining = message[match.end():].strip()
                    reg_touser = remaining.split()[0] if remaining else user
                    if reg_touser.startswith("@"):
                        reg_touser = reg_touser[1:]
                    return self._try_execute(regex_cmd, user, reg_touser, badges, match.group(0), platform=platform)

        return False, "", {}, ""

    def _try_execute(self, cmd: dict, user: str, touser: str, badges: list, matched_prefix: str, platform: str = "kick") -> tuple[bool, str, dict, str]:
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

        if final_response.startswith("[PLUGIN_") or final_response.startswith("__PLUGIN:"):
            clean_tag = final_response
            if clean_tag.startswith("__PLUGIN:") and clean_tag.endswith("__"):
                clean_tag = clean_tag[len("__PLUGIN:"): -2]
            return True, clean_tag, cmd, matched_prefix

        self.send_response(final_response, platform=platform)
        return True, "", cmd, matched_prefix

    def send_response(self, response_text: str, platform: str = "kick"):
        if not response_text:
            return

        if platform == "twitch":
            tw_worker = getattr(self, "twitch_worker", None)
            if tw_worker and hasattr(tw_worker, "send_bot_message"):
                try:
                    tw_worker.send_bot_message(response_text)
                except Exception as e:
                    logging.error("[CommandService] Error enviando mensaje a Twitch: %s", e)
        else:
            if self.api_client:
                try:
                    self.api_client.post_chat_message(content=response_text, msg_type="bot")
                except Exception as e:
                    logging.error("[CommandService] Error enviando respuesta a Kick: %s", e)

        self.response_generated.emit(response_text, platform)
