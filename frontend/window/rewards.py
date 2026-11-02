from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable

from frontend.recent_redemptions import RecentRedemptionCache


@dataclass(frozen=True)
class RewardRedemption:
    user: str
    reward_name: str
    platform: str


@dataclass(frozen=True)
class RewardRedemptionOutcome:
    configured: bool
    media_valid: bool | None = None
    filepath: str = ""


class RewardRedemptionHandler:
    def __init__(
        self,
        rewards_service,
        recent_redemptions: RecentRedemptionCache,
        logger: logging.Logger,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._rewards_service = rewards_service
        self._recent_redemptions = recent_redemptions
        self._logger = logger
        self._clock = clock or time.time

    def begin(
        self,
        user: str,
        reward_name: str,
        platform: str,
    ) -> RewardRedemption | None:
        dedup_key = (
            f"{platform}:{user.lower()}:{reward_name.lower()}:"
            f"{int(self._clock() / 8)}"
        )
        if self._recent_redemptions.contains_or_add(dedup_key):
            self._logger.debug("[Reward] Ignoring duplicate redemption: %s", dedup_key)
            return None

        self._logger.info(
            "[Reward] Redemption processed: user='%s', reward='%s' (Platform: %s)",
            user,
            reward_name,
            platform.capitalize(),
        )
        return RewardRedemption(user, reward_name, platform)

    def process(self, redemption: RewardRedemption) -> RewardRedemptionOutcome:
        config = self._rewards_service.get_reward_config(
            redemption.reward_name,
            platform=redemption.platform,
        )
        if not config:
            return RewardRedemptionOutcome(configured=False)

        filepath = (
            config.get("filepath", "")
            if isinstance(config, dict)
            else config if isinstance(config, str) else ""
        )
        if not self._rewards_service.trigger_preview(redemption.reward_name, config):
            return RewardRedemptionOutcome(
                configured=True,
                media_valid=False,
                filepath=str(filepath),
            )

        self._rewards_service.log_redemption(
            redemption.reward_name,
            redemption.user,
            platform=redemption.platform,
        )
        return RewardRedemptionOutcome(
            configured=True,
            media_valid=True,
            filepath=str(filepath),
        )
