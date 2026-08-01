# backend/handlers/chat_filter_handler.py

import re
import logging

logger = logging.getLogger("minikick.handlers.chat_filter")

class ChatFilterHandler:
    _URL_REGEX = re.compile(r"https?://\S+|www\.\S+")
    _EMOTE_REGEX = re.compile(r"\[emote:[^\]]+\]")
    _SPACES_REGEX = re.compile(r"\s+")
    _DEFAULT_BOTS = frozenset({"botrix", "nightbot", "streamelements", "moobot", "@minikick"})

    def __init__(self, i18n, service):
        self.i18n = i18n
        self.service = service
        self.muted_bots: set[str] = set()
        self.banned_words: set[str] = set()
        self._banned_words_regex: re.Pattern | None = None

    def initialize_from_settings(self, settings: dict, view) -> None:
        bots_str = settings.get("ignored_users", "")
        self.muted_bots = {b.strip().lower() for b in bots_str.split(",") if b.strip()}
        
        view.clear_bots_list()
        for bot in self.muted_bots:
            view.add_bot_tag(bot)

        words_str = settings.get("banned_words", "")
        self.banned_words = {w.strip().lower() for w in words_str.split(",") if w.strip()}
        self._recompile_banned_words_regex()
        
        view.clear_words_list()
        for word in self.banned_words:
            view.add_word_tag(word)

    def _recompile_banned_words_regex(self) -> None:
        if not self.banned_words:
            self._banned_words_regex = None
        else:
            sorted_words = sorted(self.banned_words, key=len, reverse=True)
            pattern = r'\b(?:' + '|'.join(re.escape(w) for w in sorted_words) + r')\b'
            self._banned_words_regex = re.compile(pattern, re.IGNORECASE)

    def is_message_banned(self, msg: str) -> bool:
        if not self._banned_words_regex:
            return False
        return bool(self._banned_words_regex.search(msg))

    def is_bot(self, username: str, badges: list | None = None) -> bool:
        u_lower = username.lower()
        if u_lower in self._DEFAULT_BOTS or u_lower in self.muted_bots:
            return True
        return bool(badges and "bot" in badges)

    def clean_message_for_tts(self, text: str) -> str:
        web_link_label = self.i18n.get("chat.status.web_link") if self.i18n else "enlace web"
        cleaned = self._URL_REGEX.sub(web_link_label, text)
        cleaned = self._EMOTE_REGEX.sub("", cleaned)
        return self._SPACES_REGEX.sub(" ", cleaned).strip()

    def add_bot(self, bot_name: str, view) -> bool:
        clean_name = bot_name.strip().lower()
        if clean_name and clean_name not in self.muted_bots:
            self.muted_bots.add(clean_name)
            view.add_bot_tag(clean_name)
            self._save_bot_list()
            return True
        return False

    def remove_bot(self, bot_name: str) -> bool:
        clean_name = bot_name.lower()
        if clean_name in self.muted_bots:
            self.muted_bots.remove(clean_name)
            self._save_bot_list()
            return True
        return False

    def _save_bot_list(self) -> None:
        settings = self.service.get_settings()
        settings["ignored_users"] = ",".join(self.muted_bots)
        self.service.save_settings(settings)

    def add_word(self, word: str, view) -> bool:
        clean_word = word.strip().lower()
        if clean_word and clean_word not in self.banned_words:
            self.banned_words.add(clean_word)
            self._recompile_banned_words_regex()
            view.add_word_tag(clean_word)
            self._save_word_list()
            return True
        return False

    def remove_word(self, word: str) -> bool:
        clean_word = word.lower()
        if clean_word in self.banned_words:
            self.banned_words.remove(clean_word)
            self._recompile_banned_words_regex()
            self._save_word_list()
            return True
        return False

    def _save_word_list(self) -> None:
        settings = self.service.get_settings()
        settings["banned_words"] = ",".join(self.banned_words)
        self.service.save_settings(settings)
