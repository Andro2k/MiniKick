# backend\handlers\command_help_formatter.py

_CATEGORIES = ("chat", "music", "widgets", "moderation")
_MODERATION_TAGS = frozenset({"[PLUGIN_CHAT_TTS_MUTE]", "[PLUGIN_CHAT_TTS_BLOCK]", "[PLUGIN_CHAT_TTS_SKIP]"})
_MODERATION_PERMISSIONS = frozenset({"moderator", "broadcaster"})
_SECTION_ALIASES = {
    "chat": "chat", "general": "chat",
    "musica": "music", "music": "music", "cancion": "music",
    "widgets": "widgets", "widget": "widgets",
    "mod": "moderation", "moderacion": "moderation", "moderator": "moderation",
}
_ALL_MODE_WORDS = frozenset({"all", "todos", "status", "estado", "full"})
_SECTION_I18N_KEYS = {cat: f"chat.commands_help.sec_{cat}" for cat in _CATEGORIES}

DEFAULT_MAX_CHARS = 380


def chunk_messages(header: str, sections: list[str], max_chars: int = DEFAULT_MAX_CHARS) -> list[str]:
    if not sections:
        return []

    full_candidate = f"{header} " + " | ".join(sections)
    if len(full_candidate) <= max_chars:
        return [full_candidate]

    chunks: list[str] = []
    current = header
    for sec in sections:
        candidate = f"{current} | {sec}" if current != header else f"{header} {sec}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current != header:
            chunks.append(current)
        if len(f"{header} {sec}") <= max_chars:
            current = f"{header} {sec}"
            continue

        current = header
        sub_accum = ""
        for item in sec.split(", "):
            sub_cand = f"{sub_accum}, {item}" if sub_accum else item
            if len(f"{header} {sub_cand}") <= max_chars:
                sub_accum = sub_cand
            else:
                if sub_accum:
                    chunks.append(f"{header} {sub_accum}")
                sub_accum = item
        if sub_accum:
            current = f"{header} {sub_accum}"

    if current and current != header:
        chunks.append(current)
    return chunks


class CommandHelpFormatter:
    def __init__(self, i18n, max_chars: int = DEFAULT_MAX_CHARS):
        self.i18n = i18n
        self.max_chars = max_chars

    def format(self, commands: list[dict], raw_args: str, is_mod: bool) -> list[str]:
        if not commands:
            return [self.i18n.get("chat.commands_help.empty_general")]

        categories = self._categorize(commands)
        labels = {cat: self.i18n.get(key) for cat, key in _SECTION_I18N_KEYS.items()}

        target_cat = _SECTION_ALIASES.get(raw_args)
        if target_cat:
            if target_cat == "moderation" and not is_mod:
                return []
            return self._category_messages(target_cat, categories[target_cat], labels[target_cat])

        return self._overview_messages(categories, labels, is_mod, raw_args in _ALL_MODE_WORDS)

    @staticmethod
    def _categorize(commands: list[dict]) -> dict[str, dict[str, list[str]]]:
        categories = {cat: {"active": [], "inactive": []} for cat in _CATEGORIES}
        for cmd in commands:
            trigger = cmd.get("trigger", "").strip()
            if not trigger:
                continue
            response = cmd.get("response", "")
            permission = cmd.get("permission", "everyone").lower()

            if response.startswith("[PLUGIN_MUSIC_"):
                cat = "music"
            elif response.startswith("[PLUGIN_WIDGET_"):
                cat = "widgets"
            elif response in _MODERATION_TAGS or permission in _MODERATION_PERMISSIONS:
                cat = "moderation"
            else:
                cat = "chat"

            state = "active" if bool(cmd.get("is_active", True)) else "inactive"
            categories[cat][state].append(trigger)

        for buckets in categories.values():
            buckets["active"].sort()
            buckets["inactive"].sort()
        return categories

    def _category_messages(self, buckets: dict[str, list[str]], label: str) -> list[str]:
        active, inactive = buckets["active"], buckets["inactive"]
        if not active and not inactive:
            return [self.i18n.get("chat.commands_help.empty_category").replace("{category}", label)]

        parts = []
        if active:
            parts.append(f"{self.i18n.get('chat.commands_help.active_tag')}: {', '.join(active)}")
        if inactive:
            parts.append(f"{self.i18n.get('chat.commands_help.inactive_tag')}: {', '.join(inactive)}")
        return chunk_messages(f"{label}:", parts, self.max_chars)

    def _overview_messages(self, categories: dict, labels: dict, is_mod: bool, is_all_mode: bool) -> list[str]:
        header_key = "chat.commands_help.status_header" if is_all_mode else "chat.commands_help.active_header"
        visible = ["chat", "music", "widgets"] + (["moderation"] if is_mod else [])

        sections = []
        for cat in visible:
            active, inactive = categories[cat]["active"], categories[cat]["inactive"]
            if is_all_mode:
                if not active and not inactive:
                    continue
                inner = []
                if active:
                    inner.append(f"✅ {', '.join(active)}")
                if inactive:
                    inner.append(f"❌ {', '.join(inactive)}")
                sections.append(f"{labels[cat]}: [{' | '.join(inner)}]")
            elif active:
                sections.append(f"{labels[cat]}: {', '.join(active)}")

        if not sections:
            return [self.i18n.get("chat.commands_help.empty_general")]
        return chunk_messages(self.i18n.get(header_key), sections, self.max_chars)
