# frontend\window\messages.py

from __future__ import annotations

from datetime import datetime
from typing import Callable

from backend.services import ChatMessageDTO


class ChatMessageRouter:
    def __init__(
        self,
        process_message: Callable[[ChatMessageDTO], None],
        record_message: Callable[[str], None],
        profile_provider: Callable[[str], tuple[str, str]],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._process_message = process_message
        self._record_message = record_message
        self._profile_provider = profile_provider
        self._clock = clock or datetime.now

    def route(
        self,
        user_or_dto,
        msg: str | None = None,
        badges: list | None = None,
        color: str = "",
        msg_id: str = "",
        sender_id: int = 0,
        avatar_url: str = "",
    ) -> None:
        if isinstance(user_or_dto, ChatMessageDTO):
            dto = user_or_dto
            if not dto.timestamp:
                dto.timestamp = self._clock().strftime("%H:%M")
            platform = dto.platform or "kick"
        else:
            dto = ChatMessageDTO(
                user_or_dto,
                msg,
                badges or [],
                color,
                msg_id,
                sender_id,
                timestamp=self._clock().strftime("%H:%M"),
                avatar_url=avatar_url,
            )
            platform = "kick"

        if not dto.avatar_url:
            username, profile_avatar = self._profile_provider(platform)
            if username and str(dto.user).lower() == username.lower():
                dto.avatar_url = profile_avatar

        self._record_message(platform)
        self._process_message(dto)
