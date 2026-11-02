import logging
from unittest.mock import MagicMock

from frontend.recent_redemptions import RecentRedemptionCache
from frontend.window.rewards import (
    RewardRedemptionHandler,
    RewardRedemptionOutcome,
    RewardRedemptionPresenter,
)


def _handler(service, clock=None):
    return RewardRedemptionHandler(
        rewards_service=service,
        recent_redemptions=RecentRedemptionCache(),
        logger=logging.getLogger("test.reward_redemption"),
        clock=clock or (lambda: 80.0),
    )


def test_reward_redemption_runs_preview_and_records_valid_file():
    service = MagicMock()
    service.get_reward_config.return_value = {"filepath": "reward.gif"}
    service.trigger_preview.return_value = True
    handler = _handler(service)

    redemption = handler.begin("viewer", "Hydrate", "kick")
    assert redemption is not None
    outcome = handler.process(redemption)

    assert outcome.configured is True
    assert outcome.media_valid is True
    assert outcome.filepath == "reward.gif"
    service.trigger_preview.assert_called_once_with("Hydrate", {"filepath": "reward.gif"})
    service.log_redemption.assert_called_once_with("Hydrate", "viewer", platform="kick")


def test_reward_redemption_reports_invalid_file_without_logging_it():
    service = MagicMock()
    service.get_reward_config.return_value = "missing.gif"
    service.trigger_preview.return_value = False

    handler = _handler(service)
    redemption = handler.begin("viewer", "Hydrate", "twitch")
    assert redemption is not None
    outcome = handler.process(redemption)

    assert outcome.configured is True
    assert outcome.media_valid is False
    assert outcome.filepath == "missing.gif"
    service.log_redemption.assert_not_called()


def test_duplicate_reward_redemption_skips_service_side_effects():
    service = MagicMock()
    handler = _handler(service)

    first = handler.begin("Viewer", "Hydrate", "kick")
    duplicate = handler.begin("viewer", "hydrate", "kick")

    assert first is not None
    assert duplicate is None
    service.get_reward_config.assert_not_called()
    service.trigger_preview.assert_not_called()


def test_unconfigured_reward_reports_no_file_action():
    service = MagicMock()
    service.get_reward_config.return_value = None

    handler = _handler(service)
    redemption = handler.begin("viewer", "Hydrate", "kick")
    assert redemption is not None
    outcome = handler.process(redemption)

    assert outcome.configured is False
    assert outcome.media_valid is None
    service.trigger_preview.assert_not_called()
    service.log_redemption.assert_not_called()


def test_reward_presenter_escapes_reward_name_and_processes_chat_message():
    window = MagicMock()
    window.i18n.get.side_effect = lambda key: {
        "main.toasts.reward_msg": "{user} redeemed {reward_name}",
        "main.toasts.reward_title": "Reward",
        "main.chat.reward_redeemed": "Redeemed {reward_name}",
        "main.chat.points_tag": "Points",
    }.get(key, key)
    window.chat_service.get_settings.return_value = {"enabled": True}
    handler = MagicMock()
    redemption = object()
    handler.begin.return_value = redemption
    handler.process.return_value = RewardRedemptionOutcome(configured=False)
    presenter = RewardRedemptionPresenter(window, handler)

    presenter.on_redeemed("viewer", "<script>", "hello", platform="twitch")

    window.view_chat.append_message.assert_called_once()
    assert "&lt;script&gt;" in window.view_chat.append_message.call_args.args[1]
    window.chat_controller.process_message.assert_called_once()
    handler.process.assert_called_once_with(redemption)
