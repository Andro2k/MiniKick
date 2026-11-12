# resources\tests\test_webhook_formatters.py

from backend.services.webhooks.webhook_formatters import DiscordEmbedFormatter, GenericJsonFormatter
from backend.utils import fast_loads
from resources.tests._webhook_helpers import make_event


def test_generic_envelope_is_versioned_and_complete():
    event = make_event("subscription", "kick", {"username": "viewer123", "months": 3})
    payload = fast_loads(GenericJsonFormatter().format(event))
    assert payload == {
        "schema_version": 1,
        "id": "evt-1",
        "type": "subscription",
        "platform": "kick",
        "timestamp": 1_731_289_200_000,
        "data": {"username": "viewer123", "months": 3},
    }


def test_discord_embed_colors_by_event_family():
    formatter = DiscordEmbedFormatter()
    colors = {
        event_type: fast_loads(formatter.format(make_event(event_type)))["embeds"][0]["color"]
        for event_type in ("subscription", "raid", "command", "music")
    }
    assert colors == {"subscription": 0x2ECC71, "raid": 0xF1C40F, "command": 0x3498DB, "music": 0x9B59B6}


def test_discord_embed_blocks_mass_mentions_and_truncates_chat():
    event = make_event("chat", "twitch", {"username": "troll", "message": "@everyone " + "x" * 5000})
    payload = fast_loads(DiscordEmbedFormatter().format(event))
    assert payload["allowed_mentions"] == {"parse": []}
    assert len(payload["embeds"][0]["description"]) <= 2000


def test_discord_embed_describes_rewards_by_title_and_music_by_artist_field():
    reward = make_event("reward", "twitch", {"username": "viewer123", "title": "Hydrate!", "message": "please"})
    song = make_event("music", "app", {"title": "Song", "artist": "Band"})
    reward_embed = fast_loads(DiscordEmbedFormatter().format(reward))["embeds"][0]
    song_embed = fast_loads(DiscordEmbedFormatter().format(song))["embeds"][0]
    assert reward_embed["description"] == "**viewer123**: Hydrate!"
    assert {"name": "Artist", "value": "Band", "inline": True} in song_embed["fields"]


def test_discord_embed_fields_and_optional_description():
    event = make_event("sub_gift", "twitch", {"amount": 5, "tier": "1"})
    embed = fast_loads(DiscordEmbedFormatter().format(event))["embeds"][0]
    assert "description" not in embed
    assert {f["name"]: f["value"] for f in embed["fields"]} == {"Platform": "Twitch", "Amount": "5", "Tier": "1"}
    assert embed["timestamp"].startswith("2024-11-")


def test_every_event_type_and_the_test_ping_have_an_embed_style():
    from backend.interfaces.i_webhooks import EVENT_TYPES
    from backend.services.webhooks.webhook_formatters import _DEFAULT_STYLE, _EMBED_STYLES
    assert all(event_type in _EMBED_STYLES for event_type in (*EVENT_TYPES, "test"))
    assert _EMBED_STYLES["test"] != _DEFAULT_STYLE


def test_discord_goal_embed_shows_progress_and_status():
    event = make_event("goal", "kick", {"goal_type": "followers", "current": 237, "target": 300, "status": "active", "message": "Followers: 237 / 300"})
    embed = fast_loads(DiscordEmbedFormatter().format(event))["embeds"][0]
    assert embed["title"] == "Goal progress"
    assert embed["description"] == "Followers: 237 / 300"
    assert {"name": "Status", "value": "active", "inline": True} in embed["fields"]
