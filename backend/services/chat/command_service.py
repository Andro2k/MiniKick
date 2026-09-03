# backend\services\chat\command_service.py

import logging
import re
import time

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger("minikick.services.chat.commands")

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
                        logger.error("[CommandService] Error compiling regex pattern '%s' for trigger '%s': %s", pattern, cmd['trigger'], e)
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
                cmd["cooldown"], cmd["aliases"], cmd["is_regex"], cmd["permission"],
                cmd.get("apply_kick", True), cmd.get("apply_twitch", True), cmd.get("apply_youtube", True), cmd.get("apply_tiktok", True)
            )
        self._pending_saves.clear()

    def get_all_commands(self) -> list[dict]:
        return [dict(c) for c in self._all_commands_cache]

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

    def save_command(self, trigger: str, response: str, is_active: bool, cooldown: int, aliases: str, is_regex: bool, permission: str, apply_kick: bool = None, apply_twitch: bool = None, apply_youtube: bool = None, apply_tiktok: bool = None):
        trigger_clean = trigger.strip()
        existing = self.get_command_by_trigger(trigger_clean)
        
        final_kick = apply_kick if apply_kick is not None else (existing.get("apply_kick", True) if existing else True)
        final_twitch = apply_twitch if apply_twitch is not None else (existing.get("apply_twitch", True) if existing else True)
        final_youtube = apply_youtube if apply_youtube is not None else (existing.get("apply_youtube", True) if existing else True)
        final_tiktok = apply_tiktok if apply_tiktok is not None else (existing.get("apply_tiktok", True) if existing else True)

        cmd_dict = {
            "trigger": trigger_clean,
            "response": response,
            "is_active": is_active,
            "cooldown": cooldown,
            "aliases": aliases,
            "is_regex": is_regex,
            "permission": permission,
            "apply_kick": final_kick,
            "apply_twitch": final_twitch,
            "apply_youtube": final_youtube,
            "apply_tiktok": final_tiktok
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
        if not message or not message.strip():
            return False, "", {}, ""

        parts = message.strip().split(maxsplit=1)
        if not parts:
            return False, "", {}, ""

        first_word = parts[0].lower()
        raw_first_word = parts[0]

        args = parts[1] if len(parts) > 1 else ""
        args_words = args.strip().split()
        touser = args_words[0] if args_words else user
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
                    rem_words = remaining.split()
                    reg_touser = rem_words[0] if rem_words else user
                    if reg_touser.startswith("@"):
                        reg_touser = reg_touser[1:]
                    return self._try_execute(regex_cmd, user, reg_touser, badges, match.group(0), platform=platform)

        return False, "", {}, ""

    def _try_execute(self, cmd: dict, user: str, touser: str, badges: list, matched_prefix: str, platform: str = "kick") -> tuple[bool, str, dict, str]:
        if platform == "kick" and not cmd.get("apply_kick", True):
            return False, "", {}, ""
        if platform == "twitch" and not cmd.get("apply_twitch", True):
            return False, "", {}, ""
        if platform == "youtube" and not cmd.get("apply_youtube", True):
            return False, "", {}, ""
        if platform == "tiktok" and not cmd.get("apply_tiktok", True):
            return False, "", {}, ""

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
            self.storage.log_command_execution(trigger, user, platform=platform)
        except Exception as e:
            logger.error("[CommandService] Error logging command execution: %s", e)

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
            if tw_worker and hasattr(tw_worker, "send_bot_message") and (not hasattr(tw_worker, "isRunning") or tw_worker.isRunning()):
                try:
                    tw_worker.send_bot_message(response_text)
                except Exception as e:
                    logger.error("[CommandService] Error sending message to Twitch: %s", e)
            else:
                logger.debug("[CommandService] Twitch worker not active, skipping Twitch chat message dispatch.")
        elif platform == "kick":
            if self.api_client and (not hasattr(self.api_client, "is_authenticated") or self.api_client.is_authenticated()):
                try:
                    self.api_client.post_chat_message(content=response_text, msg_type="bot")
                except Exception as e:
                    logger.error("[CommandService] Error sending response to Kick: %s", e)
            else:
                logger.debug("[CommandService] Kick not authenticated, skipping Kick chat message dispatch.")
        elif platform in ("youtube", "tiktok"):
            logger.info("[CommandService] Command response for %s chat (Read-Only mode, message not posted): %s", platform, response_text)
            return

        self.response_generated.emit(response_text, platform)

    def post_chat_message(self, message: str, apply_kick: bool = True, apply_twitch: bool = True):
        if not message:
            return
        if apply_kick:
            self.send_response(message, platform="kick")
        if apply_twitch:
            self.send_response(message, platform="twitch")
