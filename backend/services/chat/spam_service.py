# backend\services\chat\spam_service.py

import logging
import re

class SpamService:
    _LINK_REGEX = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
    _SYMBOL_REGEX = re.compile(r'[^a-zA-Z0-9\s]')
    def __init__(self, storage, api_client=None):
        self.storage = storage
        self.api_client = api_client
        self.broadcaster_id = 0
        self.filters = {}
        self.user_history = {}
        self.reload_filters()

    def reload_filters(self):
        self.filters = self.storage.load_all()

    def save_filter(self, filter_id: str, config: dict):
        self.storage.save_filter(filter_id, config)
        self.reload_filters()

    def is_spam(self, user: str, message: str, badges: list, msg_id: str, sender_id: int) -> bool:
        if not message:
            return False

        if "bot" in badges or "broadcaster" in badges:
            return False

        is_mod = "moderator" in badges
        is_sub = "subscriber" in badges or "vip" in badges

        for f_id, config in self.filters.items():
            if not config.get("is_active"):
                continue
            exclude_group = config.get("exclude_group", "none")
            if exclude_group == "moderator" and is_mod:
                continue
            if exclude_group == "subscriber" and (is_sub or is_mod):
                continue
            
            max_amount = config.get("max_amount", 0)
            is_violation = False

            if f_id == "caps_protection":
                caps_count = sum(1 for c in message if c.isupper())
                if len(message) > 5 and caps_count > max_amount:
                    is_violation = True

            elif f_id == "emote_protection":
                emote_count = message.count("[emote:")
                if emote_count > max_amount:
                    is_violation = True
                    
            elif f_id == "symbol_protection":
                symbol_count = len(self._SYMBOL_REGEX.findall(message))
                if symbol_count > max_amount:
                    is_violation = True

            elif f_id == "paragraph_protection":
                if len(message) > max_amount:
                    is_violation = True

            elif f_id == "link_protection":
                if self._LINK_REGEX.search(message):
                    is_violation = True

            elif f_id == "repetition_protection":
                words = message.lower().split()
                word_counts = {}
                for w in words:
                    word_counts[w] = word_counts.get(w, 0) + 1
                
                if any(count > max_amount for count in word_counts.values()):
                    is_violation = True
                else:
                    if user not in self.user_history:
                        self.user_history[user] = {"message": message.lower(), "count": 1}
                    else:
                        if self.user_history[user]["message"] == message.lower():
                            self.user_history[user]["count"] += 1
                        else:
                            self.user_history[user] = {"message": message.lower(), "count": 1}

                    if self.user_history[user]["count"] > max_amount:
                        is_violation = True
            if is_violation:
                self._apply_penalty(user, sender_id, msg_id, config)
                return True

        return False

    def _apply_penalty(self, user: str, sender_id: int, msg_id: str, config: dict):
        if not self.api_client:
            return

        penalty_type = config.get("penalty", "timeout")
        duration_secs = config.get("duration", 300)

        try:
            if penalty_type == "delete":
                self.api_client.delete_chat_message(msg_id)
                
            elif penalty_type == "timeout" and self.broadcaster_id:
                self.api_client.timeout_user(self.broadcaster_id, sender_id, duration_secs)
                
        except Exception as e:
            logging.error("[SpamService] Error attempting to penalize %s: %s", user, e)