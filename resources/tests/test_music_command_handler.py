# resources\tests\test_music_command_handler.py

from backend.handlers.music_handler import MusicCommandHandler


class _I18n:
    def get(self, key):
        return key


class _Provider:
    def __init__(self, queue=None, current=None):
        self.queue = queue or []
        self.current = current
        self.added = []

    def get_queue(self):
        return list(self.queue)

    def get_current_song(self):
        return self.current

    def add_to_queue(self, query, callback, requester, platform, max_duration_min):
        self.added.append((query, requester, platform, max_duration_min))
        return True, "queued"

    def skip_current(self):
        return True


class _Context:
    def __init__(self, provider=None, **limits):
        self.i18n = _I18n()
        self.music_provider = provider
        self.music_service_enabled = True
        self.max_queue_size = limits.get("max_queue_size", 30)
        self.user_cooldown = limits.get("user_cooldown", 30)
        self.max_user_songs = limits.get("max_user_songs", 2)
        self.max_song_duration = limits.get("max_song_duration", 10)
        self.current_volume = 55
        self.sent = []
        self.refreshes = 0
        self.volumes = []

    def send_chat_message(self, message, platform="kick"):
        self.sent.append(message)

    def refresh_now_playing(self):
        self.refreshes += 1

    def apply_chat_volume(self, volume):
        self.volumes.append(volume)


def _handler(provider=None, **limits):
    ctx = _Context(provider, **limits)
    return ctx, MusicCommandHandler(ctx)


def test_service_disabled_short_circuits_before_touching_provider():
    ctx, handler = _handler(_Provider())
    ctx.music_service_enabled = False
    handler.handle_command("[PLUGIN_MUSIC_SR]", "ana", "!sr x", "!sr")
    assert ctx.sent == ["music.stats.service_disabled_chat"]


def test_commands_require_linked_provider():
    ctx, handler = _handler(None)
    handler.handle_command("[PLUGIN_MUSIC_SKIP]", "ana", "!skip", "!skip")
    assert ctx.sent == ["music.chat.not_linked_youtube"]


def test_sr_without_query_sends_usage():
    ctx, handler = _handler(_Provider())
    handler.handle_command("[PLUGIN_MUSIC_SR]", "ana", "!sr", "!sr")
    assert ctx.sent == ["music.chat.sr_usage"]


def test_sr_success_registers_request_and_refreshes_without_private_access():
    provider = _Provider()
    ctx, handler = _handler(provider, max_song_duration=7)
    handler.handle_command("[PLUGIN_MUSIC_SR]", "Ana", "!sr tema", "!sr", platform="twitch")

    assert provider.added == [("tema", "Ana", "twitch", 7)]
    assert ctx.sent == ["queued"]
    assert ctx.refreshes >= 1


def test_sr_cooldown_is_kept_inside_the_handler():
    ctx, handler = _handler(_Provider(), user_cooldown=60)
    handler.handle_command("[PLUGIN_MUSIC_SR]", "ana", "!sr uno", "!sr")
    ctx.sent.clear()
    handler.handle_command("[PLUGIN_MUSIC_SR]", "ANA", "!sr dos", "!sr")
    assert ctx.sent == ["music.chat.cooldown_active"]
    assert not hasattr(ctx, "_user_last_request_time")


def test_sr_rejects_full_queue_and_user_limit():
    full = _Provider(queue=[{"requester": "x"}] * 3)
    ctx, handler = _handler(full, max_queue_size=3)
    handler.handle_command("[PLUGIN_MUSIC_SR]", "ana", "!sr a", "!sr")
    assert ctx.sent == ["music.chat.queue_full"]

    mine = _Provider(queue=[{"requester": "ana"}, {"requester": "Ana"}])
    ctx, handler = _handler(mine, max_user_songs=2, user_cooldown=0)
    handler.handle_command("[PLUGIN_MUSIC_SR]", "ana", "!sr a", "!sr")
    assert ctx.sent == ["music.chat.user_limit_reached"]


def test_volume_validates_range_and_delegates_application():
    ctx, handler = _handler(_Provider())
    handler.handle_command("[PLUGIN_MUSIC_VOLUME]", "ana", "!vol", "!vol")
    assert ctx.sent[-1] == "music.chat.vol_current"

    handler.handle_command("[PLUGIN_MUSIC_VOLUME]", "ana", "!vol 150", "!vol")
    assert ctx.sent[-1] == "music.chat.vol_usage" and ctx.volumes == []

    handler.handle_command("[PLUGIN_MUSIC_VOLUME]", "ana", "!vol 80", "!vol")
    assert ctx.volumes == [80] and ctx.sent[-1] == "music.chat.vol_success"


def test_skip_reports_result():
    ctx, handler = _handler(_Provider())
    handler.handle_command("[PLUGIN_MUSIC_SKIP]", "ana", "!skip", "!skip")
    assert ctx.sent == ["music.chat.skip_success"]
