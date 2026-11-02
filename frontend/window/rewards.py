# frontend\window\rewards.py

from __future__ import annotations

import html
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from backend.services import ChatMessageDTO
from frontend.common import BrandColors
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


class RewardRedemptionPresenter:
    def __init__(self, window, handler: RewardRedemptionHandler) -> None:
        self._window = window
        self._handler = handler

    def on_redeemed(
        self,
        user: str,
        reward_name: str,
        message: str,
        platform: str = "kick",
    ) -> None:
        w = self._window
        redemption = self._handler.begin(user, reward_name, platform)
        if redemption is None:
            return

        toast_template = w.i18n.get("main.toasts.reward_msg")
        w.toast.show_toast(
            title=w.i18n.get("main.toasts.reward_title"),
            message=toast_template.replace("{user}", user).replace("{reward_name}", reward_name),
            state="success",
        )

        current_time = datetime.now().strftime("%H:%M")
        safe_reward_name = html.escape(reward_name)
        reward_template = w.i18n.get("main.chat.reward_redeemed")
        system_message = (
            f'<span style="color: {BrandColors.GREEN};">'
            f'{reward_template.replace("{reward_name}", safe_reward_name)}</span>'
        )
        tag = w.i18n.get("main.chat.points_tag")
        if w.view_chat is not None:
            w.view_chat.append_message(
                f"[{tag}] {user}",
                system_message,
                BrandColors.GREEN,
                timestamp=current_time,
                is_html=True,
                platform=platform,
            )

        outcome = self._handler.process(redemption)
        if outcome.configured and not outcome.media_valid:
            missing_log = (
                w.i18n.get("main.logs.reward_file_missing")
                .replace("{reward_name}", reward_name)
                .replace("{filepath}", outcome.filepath)
            )
            w.logger.warning(missing_log)
            w.toast.show_toast(
                title=w.i18n.get("common.status.warning"),
                message=w.i18n.get("rewards.status.redeem_file_missing").replace(
                    "{reward}", reward_name
                ),
                state="danger",
            )
        elif not outcome.configured:
            no_rewards_template = w.i18n.get("main.logs.reward_no_rewards")
            w.logger.debug(
                "[Reward] %s",
                no_rewards_template.replace("{reward_name}", reward_name),
            )

        settings = w.chat_service.get_settings()
        if settings.get("enabled", False) and message:
            dto = ChatMessageDTO(
                user,
                message,
                [],
                "",
                "",
                0,
                timestamp=current_time,
                platform=platform,
            )
            w.chat_controller.process_message(dto)
