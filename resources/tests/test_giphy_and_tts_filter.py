# resources\tests\test_giphy_and_tts_filter.py

from unittest.mock import MagicMock
from backend.services.chat.chat_pipeline import ChatMessageDTO
from backend.providers.chat.twitch_ws_provider import TwitchSocketManager
from backend.handlers.spam_handler import ChatFilterHandler
from backend.services.chat.giphy_service import GiphyService


class DummyI18n:
    def get(self, key: str, default: str = "") -> str:
        table = {
            "chat.status.web_link": "un enlace web",
            "common.anonymous": "Anónimo",
        }
        return table.get(key, default or key)

def test_twitch_irc_gifs_tag_parsing():
    callback = MagicMock()
    i18n = DummyI18n()
    manager = TwitchSocketManager(token="oauth:dummy", nick="tester", i18n=i18n)
    manager._callback = callback

    raw_irc_line = (
        "@badge-info=;badges=broadcaster/1;color=#00FF7F;display-name=TheAndro2K;emotes=;"
        "first-msg=0;flags=;gifs=0-42|joSNxeswxuc74Juo8X|https://media4.giphy.com/media/joSNxeswxuc74Juo8X/giphy.gif?cid=test;"
        "id=1234-abcd;mod=0;room-id=98765;subscriber=1;tmi-sent-ts=1700000000000;turbo=0;"
        "user-id=98765;user-type= :theandro2k!theandro2k@theandro2k.tmi.twitch.tv "
        "PRIVMSG #theandro2k :[Wacky Races Lol GIF by Boomerang Official]\r\n"
    )

    manager._parse_privmsg(raw_irc_line)

    callback.assert_called_once()
    args = callback.call_args[0]
    assert args[0] == "TheAndro2K"
    assert args[1] == "[Wacky Races Lol GIF by Boomerang Official]"
    assert args[7] == "https://media4.giphy.com/media/joSNxeswxuc74Juo8X/giphy.gif?cid=test"

def test_clean_message_for_tts_twitch_gif_suppression():
    i18n = DummyI18n()
    handler = ChatFilterHandler(i18n=i18n, service=None)

    msg = "[Wacky Races Lol GIF by Boomerang Official]"
    cleaned = handler.clean_message_for_tts(msg)
    assert cleaned == ""

    msg_with_text = "hola a todos [Wacky Races Lol GIF by Boomerang Official] que tal"
    cleaned_text = handler.clean_message_for_tts(msg_with_text)
    assert cleaned_text == "hola a todos que tal"

    gif_url = "https://media4.giphy.com/media/joSNxeswxuc74Juo8X/giphy.gif"
    msg_url = f"mira este meme {gif_url}"
    cleaned_url = handler.clean_message_for_tts(msg_url, gif_url=gif_url)
    assert cleaned_url == "mira este meme"

    cleaned_only_url = handler.clean_message_for_tts(gif_url, gif_url=gif_url)
    assert cleaned_only_url == ""

    giphy_page = "https://giphy.com/gifs/autumn-fall-peanuts-Zb2lUCnGMXzjO"
    assert handler.clean_message_for_tts(giphy_page, gif_url="https://media.giphy.com/media/Zb2lUCnGMXzjO/giphy.gif") == ""

    giphy_media_full = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3/Zb2lUCnGMXzjO/giphy.gif"
    assert handler.clean_message_for_tts(giphy_media_full, gif_url="https://media.giphy.com/media/Zb2lUCnGMXzjO/giphy.gif") == ""

def test_giphy_service_resolution():
    service = GiphyService()

    direct_url = "https://media.giphy.com/media/test12345/giphy.gif"
    assert service.resolve_gif(direct_url) == direct_url

    page_url = "https://giphy.com/gifs/boomerang-toons-wacky-races-joSNxeswxuc74Juo8X"
    assert service.resolve_gif(page_url) == "https://media.giphy.com/media/joSNxeswxuc74Juo8X/giphy.gif"

    short_page_url = "https://giphy.com/gifs/joSNxeswxuc74Juo8X"
    assert service.resolve_gif(short_page_url) == "https://media.giphy.com/media/joSNxeswxuc74Juo8X/giphy.gif"

    webp_url = "https://media.tenor.com/images/12345/tenor.webp"
    assert service.resolve_gif(webp_url) == webp_url

    assert service.resolve_gif("") is None
    assert service.resolve_gif("   ") is None

def test_chat_message_dto_gif_url():
    dto = ChatMessageDTO(
        user="Tester",
        content="[GIF]",
        badges=["moderator"],
        color="#00FF7F",
        msg_id="1234",
        sender_id=1,
        gif_url="https://media.giphy.com/media/xyz/giphy.gif"
    )
    assert dto.gif_url == "https://media.giphy.com/media/xyz/giphy.gif"

def test_auto_embed_gif_resolution_logic():
    service = GiphyService()
    
    text = "https://media.giphy.com/media/xyz/giphy.gif"
    assert service.resolve_gif(text) == "https://media.giphy.com/media/xyz/giphy.gif"

    res = service.resolve_gif("cat")
    assert res is not None and res.startswith("http")

def test_giphy_service_has_active_key():
    service = GiphyService()
    assert service.has_active_key("") is True
    assert service.has_active_key("override_key_123") is True

class MockSettingsStorage:
    def __init__(self):
        self.data = {}
    def load_bool(self, key, default=False):
        return self.data.get(key, default)
    def save_bool(self, key, val):
        self.data[key] = val
    def load_string(self, key, default=""):
        return self.data.get(key, default)
    def save_string(self, key, val):
        self.data[key] = val
    def load_int(self, key, default=0):
        return self.data.get(key, default)
    def save_int(self, key, val):
        self.data[key] = val

class MockCommandStorage:
    def __init__(self):
        self.commands = []
    def load_all(self):
        return [dict(c) for c in self.commands]
    def save_command(self, trigger, response, is_active, cooldown, aliases, is_regex, permission, *args):
        for c in self.commands:
            if c["trigger"].strip().lower() == trigger.strip().lower():
                c.update({
                    "response": response, "is_active": is_active,
                    "cooldown": cooldown, "aliases": aliases,
                    "is_regex": is_regex, "permission": permission
                })
                return
        self.commands.append({
            "trigger": trigger, "response": response, "is_active": is_active,
            "cooldown": cooldown, "aliases": aliases, "is_regex": is_regex,
            "permission": permission
        })
    def delete_command(self, trigger):
        self.commands = [c for c in self.commands if c["trigger"].strip().lower() != trigger.strip().lower()]
    def get_command_by_trigger(self, trigger):
        for c in self.commands:
            if c["trigger"].strip().lower() == trigger.strip().lower():
                return dict(c)
        return None

def test_chat_service_overlay_show_gifs_persistence():
    from backend.services.chat.chat_service import ChatService
    storage = MockSettingsStorage()
    chat_svc = ChatService(tts_manager=MagicMock(), settings_storage=storage)
    
    chat_svc.save_settings({"chat_overlay_show_gifs": False})
    overlay_settings = chat_svc.get_overlay_settings()
    assert overlay_settings.get("show_gifs") is False

    chat_svc.save_settings({"chat_overlay_show_gifs": True})
    overlay_settings = chat_svc.get_overlay_settings()
    assert overlay_settings.get("show_gifs") is True

def test_chat_controller_gif_command_sync(qapp):
    from backend.controllers.chat_controller import ChatController, _DEFAULT_MOD_COMMANDS
    from backend.services.chat.commands_service import CommandService
    from backend.services.chat.chat_service import ChatService

    mock_view = MagicMock()
    mock_view.overlay_show_gifs = True
    mock_view.overlay_theme = "glass"
    mock_view.overlay_size = 14
    mock_view.overlay_fade = 15
    mock_view.overlay_show_bots = False
    mock_view.overlay_show_time = False
    mock_view.overlay_big_emotes = True
    mock_view.overlay_anim_in = "fade"
    mock_view.get_role_voices.return_value = {}
    mock_view.use_command_enabled = False
    mock_view.tts_command = "!tts"
    mock_view.is_web_provider = False
    mock_view.tts_volume = 100
    mock_view.tts_speed = 100
    mock_view.mod_mute_command_enabled = True
    mock_view.mod_block_command_enabled = True

    cmd_storage = MockCommandStorage()
    cmd_svc = CommandService(commands_storage=cmd_storage)
    settings_storage = MockSettingsStorage()
    chat_svc = ChatService(tts_manager=MagicMock(), settings_storage=settings_storage)
    i18n = DummyI18n()

    controller = ChatController(
        view=mock_view,
        service=chat_svc,
        command_service=cmd_svc,
        spam_service=MagicMock(),
        i18n=i18n
    )

    commands = cmd_svc.get_all_commands()
    gif_cmd = next((c for c in commands if c.get("response") == "[PLUGIN_CHAT_GIF]"), None)
    if gif_cmd:
        cmd_svc.delete_command(gif_cmd["trigger"])
    
    assert next((c for c in cmd_svc.get_all_commands() if c.get("response") == "[PLUGIN_CHAT_GIF]"), None) is None

    cmd_svc.set_command_active_by_tag("[PLUGIN_CHAT_GIF]", True, _DEFAULT_MOD_COMMANDS["[PLUGIN_CHAT_GIF]"])
    recreated = next((c for c in cmd_svc.get_all_commands() if c.get("response") == "[PLUGIN_CHAT_GIF]"), None)
    assert recreated is not None
    assert recreated["trigger"] == "!gif"
    assert recreated["is_active"] is True

    cmd_svc.set_command_active_by_tag("[PLUGIN_CHAT_GIF]", False, _DEFAULT_MOD_COMMANDS["[PLUGIN_CHAT_GIF]"])
    deactivated = next((c for c in cmd_svc.get_all_commands() if c.get("response") == "[PLUGIN_CHAT_GIF]"), None)
    assert deactivated is not None
    assert deactivated["is_active"] is False

    controller._sync_tts_command_from_db()
    assert mock_view.overlay_show_gifs is False

def test_extract_gif_url_and_non_gif_rejection():
    service = GiphyService()

    assert service.extract_gif_url("https://www.tiktok.com/@theandro2k") is None
    assert service.extract_gif_url("🖤Aquí está el enlace de TikTok!: https://www.tiktok.com/@theandro2k 👍") is None
    assert service.extract_gif_url("https://youtube.com/watch?v=123") is None
    assert service.extract_gif_url("Visita https://google.com para más info") is None

    assert service.extract_gif_url("https://media.giphy.com/media/xyz/giphy.gif") == "https://media.giphy.com/media/xyz/giphy.gif"
    assert service.extract_gif_url("Mira https://example.com/dance.gif genial") == "https://example.com/dance.gif"
    assert service.extract_gif_url("https://example.com/sticker.webp") == "https://example.com/sticker.webp"

    assert service.extract_gif_url("https://giphy.com/gifs/cat-dance-abc123xyz") == "https://media.giphy.com/media/abc123xyz/giphy.gif"
    assert service.extract_gif_url("https://media.giphy.com/media/v1.Y2lkPT/abc123xyz/giphy.gif") == "https://media.giphy.com/media/abc123xyz/giphy.gif"

def test_resolve_gif_blocks_long_queries_and_arbitrary_urls():
    service = GiphyService()

    assert service.resolve_gif("https://www.tiktok.com/@theandro2k") is None
    assert service.resolve_gif("🖤Aquí está el enlace de TikTok!: https://www.tiktok.com/@theandro2k 👍 ¡Sígueme para contenido único y entretenido! 🚀🎉") is None

    long_query = "word " * 30
    assert service.resolve_gif(long_query) is None

    res = service.resolve_gif("dance")
    assert res is not None and res.startswith("http")

def test_widgets_controller_ignores_minikick_and_bots_in_top_chatters():
    from backend.controllers.widgets_controller import WidgetsController
    from unittest.mock import MagicMock

    mock_widget_svc = MagicMock()
    mock_widget_svc.get_widget.return_value = {"is_active": True, "config": {"top_count": 5}}

    controller = WidgetsController(
        view=None,
        widget_service=mock_widget_svc,
        command_service=MagicMock(),
        overlay_server=None,
        i18n=MagicMock()
    )

    controller._record_chatter_message("@MiniKick", "Mensaje de timer", badges=["bot"])
    controller._record_chatter_message("MiniKick", "Respuesta del bot", badges=[])
    controller._record_chatter_message("@minikick", "Otro mensaje", badges=[])
    assert len(controller._chatters_counts) == 0

    controller._record_chatter_message("StreamElements", "Leaderboard update", badges=["bot"])
    controller._record_chatter_message("Nightbot", "Song requested", badges=[])
    controller._record_chatter_message("SomeRandomUser", "Beep boop", badges=["bot"])
    assert len(controller._chatters_counts) == 0

    controller._record_chatter_message("TheAndro2K", "Hola a todos!")
    controller._record_chatter_message("@TheAndro2K", "Como van?")
    assert len(controller._chatters_counts) == 1
    assert "theandro2k" in controller._chatters_counts
    assert controller._chatters_counts["theandro2k"]["count"] == 2
    assert controller._chatters_counts["theandro2k"]["user"] == "TheAndro2K"
