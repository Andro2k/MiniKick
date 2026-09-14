# backend\providers\chat\tiktok_chat_provider.py

import os
import asyncio
import logging
import re
import time
from collections import deque
from typing import Callable, Any
from backend.services.system import TranslationService
from backend.config import SIGN_API_KEY

try:
    from websockets.exceptions import InvalidStatusCode
except ImportError:
    InvalidStatusCode = None

logger = logging.getLogger("minikick.providers.chat.tiktok")

class TikTokChatProvider:
    DEFAULT_TIKTOK_COLOR = "#00F2FE"
    _MAX_SEEN_IDS = 1000
    _WS_MAX_RETRIES = 2
    _WS_RETRY_DELAY = 5.0

    def __init__(self, i18n=None, sign_api_key: str | None = None) -> None:
        self.i18n = i18n or TranslationService()
        self.sign_api_key = (
            sign_api_key
            or os.environ.get("SIGN_API_KEY")
            or SIGN_API_KEY
            or ""
        ).strip()
        self._client: Any | None = None
        self._is_running = False
        self._target_unique_id: str = ""
        self._seen_msg_ids: set[str] = set()
        self._seen_ids_order: deque[str] = deque()

    def _mark_seen(self, item_id: str) -> bool:
        if not item_id:
            return False
        if item_id in self._seen_msg_ids:
            return True
        self._seen_msg_ids.add(item_id)
        self._seen_ids_order.append(item_id)
        if len(self._seen_ids_order) > self._MAX_SEEN_IDS:
            oldest = self._seen_ids_order.popleft()
            self._seen_msg_ids.discard(oldest)
        return False

    @staticmethod
    def _extract_avatar_url(user_obj) -> str:
        if not user_obj:
            return ""
        for attr in ("avatar_thumb", "avatar_medium", "avatar_large"):
            val = getattr(user_obj, attr, None)
            if isinstance(val, str) and val.startswith("http"):
                return val
            if hasattr(val, "url_list") and getattr(val, "url_list", None):
                urls = getattr(val, "url_list")
                if urls and isinstance(urls, list) and isinstance(urls[0], str):
                    return urls[0]
        return ""

    def _build_client(
        self,
        TikTokLiveClient: Any,
        ConnectEvent: Any,
        CommentEvent: Any,
        DisconnectEvent: Any,
        clean_user: str,
        msg_seq_holder: list,
        on_message: Callable[[str, str, list, str, str, int, dict], None],
        on_connected: Callable[[dict], None] | None,
        on_disconnected: Callable[[], None] | None,
    ) -> Any:
        web_kwargs: dict[str, Any] = {}
        if self.sign_api_key:
            web_kwargs["signer_kwargs"] = {"sign_api_key": self.sign_api_key}
            os.environ["SIGN_API_KEY"] = self.sign_api_key

        client = TikTokLiveClient(
            unique_id=f"@{clean_user}",
            web_kwargs=web_kwargs if web_kwargs else None
        )
        connected_at_holder: list[float] = [0.0]

        @client.on(ConnectEvent)
        def _on_connect(event: ConnectEvent):
            connected_at_holder[0] = time.time()
            room_id = getattr(client, "room_id", "")
            logger.info(
                "[TikTokChatProvider] Conectado a TikTok Live @%s (Room ID: %s)",
                clean_user, room_id
            )
            if on_connected:
                on_connected({
                    "platform": "tiktok",
                    "unique_id": clean_user,
                    "room_id": str(room_id)
                })

        @client.on(CommentEvent)
        def _on_comment(event: CommentEvent):
            if not self._is_running:
                return

            common = getattr(event, "common", None)
            create_time_raw = getattr(common, "create_time", 0)
            if create_time_raw:
                create_time_sec = (
                    (create_time_raw / 1000.0)
                    if create_time_raw > 1e11
                    else float(create_time_raw)
                )
                if connected_at_holder[0] > 0 and create_time_sec < (connected_at_holder[0] - 1.0):
                    msg_id_val = getattr(common, "msg_id", None)
                    if msg_id_val:
                        self._mark_seen(str(msg_id_val))
                    return

            user_obj = getattr(event, "user", None)
            username = getattr(user_obj, "unique_id", "") or "User"
            display_name = (
                getattr(user_obj, "nickname", "")
                or getattr(user_obj, "nick_name", "")
                or username
            )
            comment_text = getattr(event, "comment", "")

            msg_id_val = getattr(common, "msg_id", None)
            msg_dedup_id = (
                str(msg_id_val)
                if msg_id_val
                else f"{username}_{comment_text}_{int(time.time())}"
            )
            if self._mark_seen(msg_dedup_id):
                return

            msg_seq_holder[0] += 1
            msg_seq = msg_seq_holder[0]

            badges = []
            if username and clean_user and username.lower() == clean_user.lower():
                badges.append("broadcaster")
            if getattr(user_obj, "is_moderator", False):
                badges.append("moderator")
            if getattr(user_obj, "is_subscribe", False) or getattr(user_obj, "is_subscriber", False):
                badges.append("subscriber")
            if getattr(event, "user_is_super_fan", False):
                badges.append("super_fan")

            avatar_url = self._extract_avatar_url(user_obj)
            timestamp = time.strftime("%H:%M:%S")

            emotes_list = []
            raw_emotes = getattr(event, "emotes", None)
            bracket_tokens = (
                re.findall(r'\[[a-zA-Z0-9_\-]+\]', comment_text)
                if comment_text
                else []
            )

            if raw_emotes and isinstance(raw_emotes, (list, tuple)):
                for idx, em in enumerate(raw_emotes):
                    sub_em = getattr(em, "emote", None)
                    name = (
                        getattr(em, "place_in_comment", "")
                        or (getattr(sub_em, "place_in_comment", "") if sub_em else "")
                        or (getattr(sub_em, "emote_id", "") if sub_em else "")
                        or getattr(em, "emote_id", "")
                        or getattr(em, "name", "")
                    )
                    url = ""
                    img = getattr(em, "image", None) or (
                        getattr(sub_em, "image", None) if sub_em else None
                    )
                    if img:
                        if hasattr(img, "url_list") and img.url_list and isinstance(img.url_list, list):
                            url = img.url_list[0]
                        elif isinstance(img, str) and img.startswith("http"):
                            url = img
                    elif hasattr(em, "url") and isinstance(getattr(em, "url"), str):
                        url = getattr(em, "url")
                    elif sub_em and hasattr(sub_em, "url") and isinstance(getattr(sub_em, "url"), str):
                        url = getattr(sub_em, "url")

                    if not name and hasattr(em, "emote_id"):
                        name = str(getattr(em, "emote_id"))
                    if not name and sub_em and hasattr(sub_em, "emote_id"):
                        name = str(getattr(sub_em, "emote_id"))

                    token_name = bracket_tokens[idx].strip("[]") if idx < len(bracket_tokens) else ""

                    if url:
                        if token_name:
                            emotes_list.append({"name": str(token_name), "url": str(url)})
                        if name and name != token_name:
                            emotes_list.append({"name": str(name), "url": str(url)})

            raw_data = {
                "platform": "tiktok",
                "msg_id": msg_id_val or msg_seq,
                "timestamp": timestamp,
                "comment": comment_text,
                "emotes": emotes_list,
                "user": {
                    "unique_id": username,
                    "nickname": display_name,
                    "avatar_url": avatar_url,
                    "is_moderator": getattr(user_obj, "is_moderator", False),
                    "is_subscriber": getattr(user_obj, "is_subscribe", False),
                    "is_follower": getattr(user_obj, "is_follower", False),
                    "is_friend": getattr(user_obj, "is_friend", False),
                    "is_top_gifter": getattr(user_obj, "is_top_gifter", False),
                    "gifter_level": getattr(user_obj, "gifter_level", 0),
                    "member_level": getattr(user_obj, "member_level", 0),
                    "fans_club_level": getattr(
                        getattr(user_obj, "fans_club_info", None), "level", 0
                    ),
                    "badges": badges
                },
                "meta": {
                    "room_id": str(getattr(client, "room_id", "")),
                    "create_time": getattr(common, "create_time", 0)
                }
            }

            if on_message:
                try:
                    on_message(
                        display_name,
                        comment_text,
                        badges,
                        self.DEFAULT_TIKTOK_COLOR,
                        timestamp,
                        msg_seq,
                        raw_data
                    )
                except Exception as cb_err:
                    logger.warning(
                        "[TikTokChatProvider] Error en callback on_message: %s", cb_err
                    )

        @client.on(DisconnectEvent)
        def _on_disconnect(event: DisconnectEvent):
            logger.info(
                "[TikTokChatProvider] Desconectado de TikTok Live @%s", clean_user
            )
            if on_disconnected:
                on_disconnected()

        return client

    def start_chat(
        self,
        unique_id: str,
        on_message: Callable[[str, str, list, str, str, int, dict], None],
        on_connected: Callable[[dict], None] | None = None,
        on_disconnected: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None
    ) -> None:
        if not unique_id or not unique_id.strip():
            err_msg = self.i18n.get("logs.tiktok.empty_user")
            if on_error:
                on_error(err_msg)
            return

        clean_user = unique_id.strip().lstrip("@")
        self._target_unique_id = clean_user
        self._is_running = True
        self._seen_msg_ids.clear()
        self._seen_ids_order.clear()

        logger.info("[TikTokChatProvider] Iniciando conexión con TikTok Live de @%s", clean_user)

        try:
            from TikTokLive import TikTokLiveClient
            from TikTokLive.events import (
                CommentEvent, ConnectEvent, DisconnectEvent
            )
            from TikTokLive.client.errors import (
                UserNotFoundError, UserOfflineError, AgeRestrictedError, TikTokLiveError
            )
        except ImportError as e:
            err_msg = f"Dependencia TikTokLive no disponible: {e}"
            logger.error("[TikTokChatProvider] %s", err_msg)
            if on_error:
                on_error(err_msg)
            return

        msg_seq_holder: list[int] = [0]

        for attempt in range(self._WS_MAX_RETRIES + 1):
            if not self._is_running:
                break

            self._client = self._build_client(
                TikTokLiveClient=TikTokLiveClient,
                ConnectEvent=ConnectEvent,
                CommentEvent=CommentEvent,
                DisconnectEvent=DisconnectEvent,
                clean_user=clean_user,
                msg_seq_holder=msg_seq_holder,
                on_message=on_message,
                on_connected=on_connected,
                on_disconnected=on_disconnected,
            )

            try:
                self._client.run(fetch_live_check=True)
                break

            except UserNotFoundError:
                err = self.i18n.get("logs.tiktok.user_not_found").replace("{unique_id}", clean_user)
                logger.warning("[TikTokChatProvider] %s", err)
                if on_error:
                    on_error(err)
                break

            except UserOfflineError:
                err = self.i18n.get("logs.tiktok.stream_offline").replace("{unique_id}", clean_user)
                logger.warning("[TikTokChatProvider] %s", err)
                if on_error:
                    on_error(err)
                break

            except AgeRestrictedError:
                err = self.i18n.get("logs.tiktok.age_restricted").replace("{unique_id}", clean_user)
                logger.warning("[TikTokChatProvider] %s", err)
                if on_error:
                    on_error(err)
                break

            except KeyboardInterrupt:
                logger.info("[TikTokChatProvider] Interrupción de teclado.")
                break

            except TikTokLiveError as tle:
                logger.error("[TikTokChatProvider] Error de TikTokLive: %s", tle)
                if on_error:
                    on_error(str(tle))
                break

            except Exception as ex:
                is_ws_400 = (
                    InvalidStatusCode is not None
                    and isinstance(ex, InvalidStatusCode)
                    and getattr(ex, "status_code", None) == 400
                )

                if is_ws_400 and attempt < self._WS_MAX_RETRIES and self._is_running:
                    warn_msg = self.i18n.get("logs.tiktok.ws_rejected_400")
                    logger.warning(
                        "[TikTokChatProvider] HTTP 400 en intento %d/%d — %s",
                        attempt + 1, self._WS_MAX_RETRIES + 1, warn_msg
                    )
                    time.sleep(self._WS_RETRY_DELAY)
                    continue

                if is_ws_400:
                    err = self.i18n.get("logs.tiktok.ws_rejected_400_final")
                    logger.error(
                        "[TikTokChatProvider] WebSocket rechazado definitivamente (HTTP 400) tras %d intento(s).",
                        attempt + 1
                    )
                    if on_error:
                        on_error(err)
                    break

                if InvalidStatusCode is not None and isinstance(ex, InvalidStatusCode):
                    err = self.i18n.get("logs.tiktok.ws_rejected").replace(
                        "{code}", str(getattr(ex, "status_code", "?"))
                    )
                    logger.error(
                        "[TikTokChatProvider] WebSocket rechazado (HTTP %s): %s",
                        getattr(ex, "status_code", "?"), ex
                    )
                    if on_error:
                        on_error(err)
                    break

                if self._is_running:
                    logger.error(
                        "[TikTokChatProvider] Excepción general de conexión (%s): %s",
                        type(ex).__name__, ex, exc_info=True
                    )
                    if on_error:
                        on_error(str(ex))
                break

        self._is_running = False

    def stop_chat(self) -> None:
        self._is_running = False
        if self._client:
            try:
                loop = getattr(self._client, "_asyncio_loop", None)
                if loop and loop.is_running():
                    fut = asyncio.run_coroutine_threadsafe(self._client.disconnect(), loop)
                    try:
                        fut.result(timeout=1.5)
                    except Exception:
                        pass
                elif loop and not loop.is_closed():
                    try:
                        loop.run_until_complete(self._client.disconnect())
                    except Exception:
                        pass
            except Exception as e:
                logger.debug("[TikTokChatProvider] Error menor al desconectar cliente: %s", e)
        self._seen_msg_ids.clear()
        self._seen_ids_order.clear()
        logger.info("[TikTokChatProvider] Chat detenido para @%s", self._target_unique_id)
