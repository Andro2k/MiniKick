# backend\providers\chat\tiktok_chat_provider.py

import asyncio
import logging
import time
from collections import deque
from typing import Callable, Any
from backend.services.system.translation_service import TranslationService

logger = logging.getLogger("minikick.providers.chat.tiktok")

class TikTokChatProvider:
    DEFAULT_TIKTOK_COLOR = "#00F2FE"
    _MAX_SEEN_IDS = 1000

    def __init__(self, i18n=None) -> None:
        self.i18n = TranslationService()
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

        self._client = TikTokLiveClient(unique_id=f"@{clean_user}")
        self._connected_at = 0.0
        msg_seq = 0

        @self._client.on(ConnectEvent)
        def _on_connect(event: ConnectEvent):
            self._connected_at = time.time()
            room_id = getattr(self._client, "room_id", "")
            logger.info("[TikTokChatProvider] Conectado a TikTok Live @%s (Room ID: %s)", clean_user, room_id)
            if on_connected:
                on_connected({
                    "platform": "tiktok",
                    "unique_id": clean_user,
                    "room_id": str(room_id)
                })

        @self._client.on(CommentEvent)
        def _on_comment(event: CommentEvent):
            nonlocal msg_seq
            if not self._is_running:
                return

            common = getattr(event, "common", None)
            create_time_raw = getattr(common, "create_time", 0)
            if create_time_raw:
                create_time_sec = (create_time_raw / 1000.0) if create_time_raw > 1e11 else float(create_time_raw)
                if self._connected_at > 0 and create_time_sec < (self._connected_at - 1.0):
                    msg_id_val = getattr(common, "msg_id", None)
                    if msg_id_val:
                        self._mark_seen(str(msg_id_val))
                    return

            user_obj = getattr(event, "user", None)
            username = getattr(user_obj, "unique_id", "") or "User"
            display_name = getattr(user_obj, "nickname", "") or getattr(user_obj, "nick_name", "") or username
            comment_text = getattr(event, "comment", "")

            msg_id_val = getattr(common, "msg_id", None)
            msg_dedup_id = str(msg_id_val) if msg_id_val else f"{username}_{comment_text}_{int(time.time())}"
            if self._mark_seen(msg_dedup_id):
                return

            msg_seq += 1
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

            raw_data = {
                "platform": "tiktok",
                "msg_id": msg_id_val or msg_seq,
                "timestamp": timestamp,
                "comment": comment_text,
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
                    "fans_club_level": getattr(getattr(user_obj, "fans_club_info", None), "level", 0),
                    "badges": badges
                },
                "meta": {
                    "room_id": str(getattr(self._client, "room_id", "")),
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
                    logger.warning("[TikTokChatProvider] Error en callback on_message: %s", cb_err)

        @self._client.on(DisconnectEvent)
        def _on_disconnect(event: DisconnectEvent):
            logger.info("[TikTokChatProvider] Desconectado de TikTok Live @%s", clean_user)
            if on_disconnected:
                on_disconnected()

        try:
            self._client.run(fetch_live_check=True)
        except UserNotFoundError:
            err = self.i18n.get("logs.tiktok.user_not_found").replace("{unique_id}", clean_user)
            logger.warning("[TikTokChatProvider] %s", err)
            if on_error:
                on_error(err)
        except UserOfflineError:
            err = self.i18n.get("logs.tiktok.stream_offline").replace("{unique_id}", clean_user)
            logger.warning("[TikTokChatProvider] %s", err)
            if on_error:
                on_error(err)
        except AgeRestrictedError:
            err = self.i18n.get("logs.tiktok.age_restricted").replace("{unique_id}", clean_user)
            logger.warning("[TikTokChatProvider] %s", err)
            if on_error:
                on_error(err)
        except KeyboardInterrupt:
            logger.info("[TikTokChatProvider] Interrupción de teclado.")
        except TikTokLiveError as tle:
            err = f"Error de TikTokLive: {tle}"
            logger.error("[TikTokChatProvider] %s", err)
            if on_error:
                on_error(err)
        except Exception as ex:
            if self._is_running:
                logger.error("[TikTokChatProvider] Excepción general de conexión: %s", ex)
                if on_error:
                    on_error(str(ex))
        finally:
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
