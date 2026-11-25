# resources\tests\test_rewards_diagnostic_logs.py
"""Pruebas de los logs de diagnóstico de canjes de puntos de canal."""

from unittest.mock import MagicMock, patch

from backend.providers.chat.kick_ws_provider import KickWebSocketManager
from frontend.window.rewards_handler import RewardRedemptionHandler


def _kick_manager() -> KickWebSocketManager:
    mgr = KickWebSocketManager(cluster="us2", keys=("test_key",))
    mgr._on_reward = MagicMock()
    return mgr


def test_kick_reward_event_with_title_and_user_is_forwarded():
    mgr = _kick_manager()
    mgr._handle_reward_redeemed({"reward_title": "Gnomo", "username": "ana"}, MagicMock())
    mgr._on_reward.assert_called_once_with("ana", "Gnomo", "")


def test_kick_reward_event_missing_title_is_dropped_with_warning():
    mgr = _kick_manager()
    with patch("backend.providers.chat.kick_ws_provider.logger") as log:
        mgr._handle_reward_redeemed({"username": "ana", "foo": 1}, MagicMock())
    mgr._on_reward.assert_not_called()
    assert log.warning.call_count == 1
    assert "foo" in str(log.warning.call_args)


def test_duplicate_redemption_is_logged_at_info():
    cache = MagicMock()
    cache.contains_or_add.return_value = True
    logger = MagicMock()
    handler = RewardRedemptionHandler(MagicMock(), cache, logger, clock=lambda: 100.0)
    assert handler.begin("ana", "Gnomo", "kick") is None
    assert logger.info.call_count == 1
    logger.debug.assert_not_called()
