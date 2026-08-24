# backend\services\chat\spam_service.py

import logging
import re
from collections import deque

class SpamService:
    _LINK_REGEX = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
    _KICK_EMOTE_REGEX = re.compile(r'\[emote:\d+:[^\]]+\]', re.IGNORECASE)
    _ALLOWED_LATIN_PATTERN = re.compile(r'[a-zA-Z0-9\s\u00C0-\u024F\.\,\!\?\-\_\:\;\(\)\[\]\'\"\/\\\@\#\$\%\&\*\+\=\<\>]')

    def __init__(self, storage, api_client=None, max_history_size: int = 1000, i18n=None):
        self.storage = storage
        self.api_client = api_client
        self.twitch_api = None
        self.twitch_worker = None
        self.twitch_broadcaster_id = ""
        self.i18n = i18n
        self.broadcaster_id = 0
        self.filters = {}
        self.user_history = {}
        self.user_insertion_order = deque()
        self.max_history_size = max_history_size
        self.reload_filters()

    def reload_filters(self):
        self.filters = self.storage.load_all()

    def save_filter(self, filter_id: str, config: dict):
        self.storage.save_filter(filter_id, config)
        self.reload_filters()

    def _get_clean_text(self, message: str, emotes_tag: str = "", strip_urls: bool = False) -> str:
        clean_msg = self._KICK_EMOTE_REGEX.sub('', message)
        if emotes_tag:
            from backend.providers.chat.twitch_websocket import TwitchSocketManager
            clean_msg = TwitchSocketManager.strip_twitch_emotes(clean_msg, emotes_tag)
        if strip_urls:
            clean_msg = self._LINK_REGEX.sub('', clean_msg)
        return clean_msg

    def is_spam(self, user: str, message: str, badges: list, msg_id: str, sender_id: int, emotes_tag: str = "", platform: str = "kick") -> bool:
        if not message:
            return False

        if "bot" in badges or "broadcaster" in badges:
            return False

        is_mod = "moderator" in badges
        is_sub = "subscriber" in badges or "vip" in badges

        from backend.providers.chat.twitch_websocket import TwitchSocketManager
        twitch_emotes = TwitchSocketManager.count_twitch_emotes(emotes_tag)

        for f_id, config in self.filters.items():
            if not config.get("is_active"):
                continue
            if platform == "kick" and not config.get("apply_kick", True):
                continue
            if platform == "twitch" and not config.get("apply_twitch", True):
                continue

            exclude_group = config.get("exclude_group", "none")
            if exclude_group == "moderator" and is_mod:
                continue
            if exclude_group == "subscriber" and (is_sub or is_mod):
                continue
            
            max_amount = config.get("max_amount", 0)
            is_violation = False

            if f_id == "caps_protection":
                clean_msg = self._get_clean_text(message, emotes_tag=emotes_tag, strip_urls=True)
                caps_count = sum(1 for c in clean_msg if c.isupper())
                if len(clean_msg.strip()) > 5 and caps_count > max_amount:
                    is_violation = True

            elif f_id == "emote_protection":
                kick_emotes = message.count("[emote:")
                total_emotes = kick_emotes + twitch_emotes
                if total_emotes > max_amount:
                    is_violation = True
                    
            elif f_id == "symbol_protection":
                clean_msg = self._get_clean_text(message, emotes_tag=emotes_tag)
                strange_chars = self._ALLOWED_LATIN_PATTERN.sub('', clean_msg)
                symbols_only = re.findall(r'[^a-zA-Z0-9\s\u00C0-\u024F]', clean_msg)
                threshold = max_amount if max_amount > 0 else 15
                if len(strange_chars) > threshold or len(symbols_only) > (threshold * 2):
                    is_violation = True

            elif f_id == "paragraph_protection":
                clean_msg = self._get_clean_text(message, emotes_tag=emotes_tag)
                threshold = max_amount if max_amount > 0 else 300
                if len(clean_msg) > threshold or clean_msg.count('\n') >= 5:
                    is_violation = True

            elif f_id == "link_protection":
                found_links = self._LINK_REGEX.findall(message)
                if found_links:
                    allowlist_str = config.get("allowlist", "")
                    allowed_domains = [d.strip().lower() for d in allowlist_str.split(",") if d.strip()]
                    
                    is_violation = False
                    for link in found_links:
                        link_lower = link.lower()
                        if not any(domain in link_lower for domain in allowed_domains):
                            is_violation = True
                            break

            elif f_id == "repetition_protection":
                clean_msg = self._get_clean_text(message, emotes_tag=emotes_tag, strip_urls=True)
                words = clean_msg.lower().split()
                if words:
                    word_counts = {}
                    for w in words:
                        word_counts[w] = word_counts.get(w, 0) + 1
                    
                    if any(count > max_amount for count in word_counts.values()):
                        is_violation = True
                    else:
                        self._track_user_message(user, clean_msg.lower())
                        if self.user_history[user]["count"] > max_amount:
                            is_violation = True
            if is_violation:
                self._apply_penalty(user, sender_id, msg_id, config, f_id, message, platform=platform)
                return True

        return False

    def _track_user_message(self, user: str, msg_lower: str):
        if user not in self.user_history:
            if len(self.user_history) >= self.max_history_size:
                oldest_user = self.user_insertion_order.popleft()
                self.user_history.pop(oldest_user, None)
                
            self.user_history[user] = {"message": msg_lower, "count": 1}
            self.user_insertion_order.append(user)
        else:
            if self.user_history[user]["message"] == msg_lower:
                self.user_history[user]["count"] += 1
            else:
                self.user_history[user] = {"message": msg_lower, "count": 1}

    def _apply_penalty(self, user: str, sender_id: int, msg_id: str, config: dict, filter_id: str, message: str, platform: str = "kick"):
        penalty_type = config.get("penalty", "timeout")
        duration_mins = config.get("duration", 5)

        if hasattr(self.storage, "db_manager") and self.storage.db_manager:
            self.storage.db_manager.log_spam_violation(
                username=user,
                sender_id=sender_id,
                filter_id=filter_id,
                message_content=message,
                penalty_type=penalty_type,
                duration=duration_mins,
                platform=platform
            )

        if platform == "kick":
            if not self.api_client:
                return

            try:
                if penalty_type == "delete":
                    self.api_client.delete_chat_message(msg_id)
                elif penalty_type == "timeout" and self.broadcaster_id:
                    self.api_client.timeout_user(self.broadcaster_id, sender_id, duration_mins)
                elif penalty_type == "ban" and self.broadcaster_id:
                    self.api_client.ban_user(self.broadcaster_id, sender_id)
                elif penalty_type == "warn_delete":
                    self.api_client.delete_chat_message(msg_id)
                    if self.i18n:
                        warn_msg = self.i18n.get("spam.status.warn_msg").replace("{user}", user)
                        self.api_client.post_chat_message(warn_msg, msg_type="bot")
            except Exception as e:
                logging.error("[SpamService] Error attempting to penalize Kick user %s: %s", user, e)

        elif platform == "twitch":
            try:
                duration_sec = duration_mins * 60
                b_id = str(self.twitch_broadcaster_id) if hasattr(self, 'twitch_broadcaster_id') and self.twitch_broadcaster_id else ""
                
                if penalty_type == "delete":
                    if self.twitch_api and b_id:
                        self.twitch_api.delete_chat_message(b_id, b_id, msg_id)
                    elif self.twitch_worker:
                        self.twitch_worker.send_bot_message(f"/delete {msg_id}")
                elif penalty_type == "timeout":
                    if self.twitch_api and b_id:
                        self.twitch_api.timeout_user(b_id, b_id, str(sender_id), duration_sec)
                    elif self.twitch_worker:
                        self.twitch_worker.send_bot_message(f"/timeout {user} {duration_sec}")
                elif penalty_type == "ban":
                    if self.twitch_api and b_id:
                        self.twitch_api.ban_user(b_id, b_id, str(sender_id))
                    elif self.twitch_worker:
                        self.twitch_worker.send_bot_message(f"/ban {user}")
                elif penalty_type == "warn_delete":
                    if self.twitch_api and b_id:
                        self.twitch_api.delete_chat_message(b_id, b_id, msg_id)
                    elif self.twitch_worker:
                        self.twitch_worker.send_bot_message(f"/delete {msg_id}")
                    if self.i18n and self.twitch_worker:
                        warn_msg = self.i18n.get("spam.status.warn_msg").replace("{user}", user)
                        self.twitch_worker.send_bot_message(warn_msg)
            except Exception as e:
                logging.error("[SpamService] Error attempting to penalize Twitch user %s: %s", user, e)
