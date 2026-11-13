# backend\utils\chat_command_config.py

_MUTE_REMOVE_KEYWORDS = frozenset({"unmute", "desilenciar", "quitar", "remove", "del", "-"})
_MUTE_REMOVE_ALIASES = frozenset({"!unmutetts", "!desilenciartts", "!ttsunmute"})
_MUTE_ADD_KEYWORDS = frozenset({"add", "mute", "silenciar", "+"})

_BLOCK_REMOVE_KEYWORDS = frozenset({"unblock", "descensurar", "desbloquear", "quitar", "remove", "del", "-"})
_BLOCK_REMOVE_ALIASES = frozenset({"!unblockword", "!descensurartts", "!ttsunblock"})
_BLOCK_ADD_KEYWORDS = frozenset({"add", "block", "censurar", "bloquear", "+"})


def _build_command_response_map(commands: list[dict]) -> dict[str, dict]:
    return {cmd.get("response", ""): cmd for cmd in commands if "response" in cmd}


def _parse_mute_args(prefix: str, content: str) -> tuple[bool, str]:
    raw_args = content[len(prefix):].strip()
    tokens = raw_args.split() if raw_args else []
    prefix_lower = prefix.strip().lower()

    if prefix_lower in _MUTE_REMOVE_ALIASES:
        return True, (tokens[0].lstrip("@-+") if tokens else "")

    if not tokens:
        return False, ""

    first_token = tokens[0]
    first_token_lower = first_token.lower().lstrip("-+")

    if first_token.lower() in _MUTE_REMOVE_KEYWORDS or (first_token.startswith("-") and first_token_lower):
        if first_token.startswith("-") and first_token_lower:
            return True, first_token_lower.lstrip("@")
        return True, (tokens[1].lstrip("@") if len(tokens) > 1 else "")

    if first_token.lower() in _MUTE_ADD_KEYWORDS or (first_token.startswith("+") and first_token_lower):
        if first_token.startswith("+") and first_token_lower:
            return False, first_token_lower.lstrip("@")
        return False, (tokens[1].lstrip("@") if len(tokens) > 1 else "")

    return False, first_token.lstrip("@")


def _parse_block_args(prefix: str, content: str) -> tuple[bool, str]:
    raw_args = content[len(prefix):].strip()
    tokens = raw_args.split() if raw_args else []
    prefix_lower = prefix.strip().lower()

    if prefix_lower in _BLOCK_REMOVE_ALIASES:
        return True, raw_args.strip().lower()

    if not tokens:
        return False, ""

    first_token = tokens[0]
    first_token_lower = first_token.lower().lstrip("-+")

    if first_token.lower() in _BLOCK_REMOVE_KEYWORDS or (first_token.startswith("-") and first_token_lower):
        if first_token.startswith("-") and first_token_lower:
            return True, " ".join([first_token_lower] + tokens[1:]).strip().lower()
        return True, (" ".join(tokens[1:]).strip().lower() if len(tokens) > 1 else "")

    if first_token.lower() in _BLOCK_ADD_KEYWORDS or (first_token.startswith("+") and first_token_lower):
        if first_token.startswith("+") and first_token_lower:
            return False, " ".join([first_token_lower] + tokens[1:]).strip().lower()
        return False, (" ".join(tokens[1:]).strip().lower() if len(tokens) > 1 else "")

    return False, raw_args.strip().lower()


_DEFAULT_MOD_COMMANDS: dict[str, dict] = {
    "[PLUGIN_CHAT_TTS_MUTE]": {
        "trigger": "!ttsmute",
        "response": "[PLUGIN_CHAT_TTS_MUTE]",
        "cooldown": 2,
        "aliases": "!mutetts,!silenciartts,!unmutetts,!desilenciartts",
        "is_regex": False,
        "permission": "moderator",
        "apply_kick": True,
        "apply_twitch": True,
        "apply_youtube": True,
        "apply_tiktok": True,
    },
    "[PLUGIN_CHAT_TTS_BLOCK]": {
        "trigger": "!ttsblock",
        "response": "[PLUGIN_CHAT_TTS_BLOCK]",
        "cooldown": 2,
        "aliases": "!blockword,!censurartts,!unblockword,!descensurartts",
        "is_regex": False,
        "permission": "moderator",
        "apply_kick": True,
        "apply_twitch": True,
        "apply_youtube": True,
        "apply_tiktok": True,
    },
    "[PLUGIN_CHAT_TTS_SKIP]": {
        "trigger": "!skiptts",
        "response": "[PLUGIN_CHAT_TTS_SKIP]",
        "cooldown": 2,
        "aliases": "!stoptts,!ttsskip,!ttsstop,!silenciotts",
        "is_regex": False,
        "permission": "moderator",
        "apply_kick": True,
        "apply_twitch": True,
        "apply_youtube": True,
        "apply_tiktok": True,
    },
    "[PLUGIN_CHAT_GIF]": {
        "trigger": "!gif",
        "response": "[PLUGIN_CHAT_GIF]",
        "cooldown": 2,
        "aliases": "!giphy",
        "is_regex": False,
        "permission": "everyone",
        "apply_kick": True,
        "apply_twitch": True,
        "apply_youtube": True,
        "apply_tiktok": True,
    },
    "[PLUGIN_CHAT_COMMANDS]": {
        "trigger": "!commands",
        "response": "[PLUGIN_CHAT_COMMANDS]",
        "cooldown": 5,
        "aliases": "!comandos,!help,!ayuda",
        "is_regex": False,
        "permission": "everyone",
        "apply_kick": True,
        "apply_twitch": True,
        "apply_youtube": True,
        "apply_tiktok": True,
    },
}

_DEFAULT_TTS_COMMAND: dict = {
    "cooldown": 1,
    "aliases": "",
    "is_regex": False,
    "permission": "everyone",
}

_DEFAULT_SYSTTS_COMMAND: dict = {
    "trigger": "!systts",
    "cooldown": 3,
    "aliases": "!ttssys",
    "is_regex": False,
    "permission": "moderator",
}
