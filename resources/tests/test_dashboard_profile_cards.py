from frontend.components.dashboard import PlatformDistributionRing
from frontend.views.dashboard_view import DashboardView
from frontend.widgets import StatCard


class _TestI18n:
    @staticmethod
    def get(key):
        return key


def test_channel_stats_render_as_cards_outside_profile_panel(qapp):
    dashboard = DashboardView(_TestI18n())

    assert dashboard.channel_badges_container.parentWidget() is dashboard.content_column
    assert len(dashboard.channel_badge_cards) == 4
    assert set(dashboard.channel_badges) == {"followers", "created", "category", "identifier"}
    assert all(isinstance(card, StatCard) for card in dashboard.channel_badge_cards)
    assert all(
        card.parentWidget() is dashboard.channel_badges_container
        for card in dashboard.channel_badge_cards
    )
    assert not hasattr(dashboard, "avatar_size_controls")
    assert not hasattr(dashboard, "btn_avatar_smaller")
    assert not hasattr(dashboard, "btn_avatar_larger")
    dashboard.deleteLater()


def test_removed_profile_stats_are_not_read_or_rendered(qapp):
    class _ProfileData(dict):
        accessed_keys = []

        def get(self, key, default=None):
            self.accessed_keys.append(key)
            return super().get(key, default)

    dashboard = DashboardView(_TestI18n())
    profile = _ProfileData(username="streamer", followers=10)

    dashboard.render_channel_profile("twitch", profile, ["twitch"])

    assert "next_schedule" not in profile.accessed_keys
    assert "broadcaster_type" not in profile.accessed_keys
    dashboard.deleteLater()


def test_identifier_card_title_preserves_translation_case(qapp):
    dashboard = DashboardView(_TestI18n())

    dashboard.render_channel_profile("kick", {"username": "streamer"}, ["kick"])

    assert dashboard.channel_badges["identifier"]["title"].text() == "dashboard.stats.room_id"
    dashboard.deleteLater()


def test_channel_avatar_size_uses_code_default(qapp):
    ring = PlatformDistributionRing()

    assert ring.DEFAULT_AVATAR_SIZE == 124
    assert ring._avatar_size == ring.DEFAULT_AVATAR_SIZE
    ring.deleteLater()
