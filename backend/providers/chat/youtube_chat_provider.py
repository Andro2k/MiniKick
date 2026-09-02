# backend\providers\chat\youtube_chat_provider.py

import logging
import re
import time
from typing import Callable, Any
import requests
from backend.services.system.translation_service import TranslationService
from backend.utils.json_utils import fast_loads

logger = logging.getLogger("minikick.providers.chat.youtube")

class YouTubeChatProvider:
    DEFAULT_YOUTUBE_COLOR = "#FF0000"

    @staticmethod
    def resolve_live_video_id(target: str) -> str | None:
        if not target:
            return None
        target = target.strip()

        if len(target) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', target):
            return target

        match = re.search(r'(?:v=|\/live\/|\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})', target)
        if match and not target.startswith("@") and "/@" not in target:
            return match.group(1)

        channel_url = target
        if not channel_url.startswith("http"):
            channel_url = f"https://www.youtube.com/{target.lstrip('/')}/live"
        elif not channel_url.endswith("/live"):
            channel_url = f"{channel_url.rstrip('/')}/live"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
            r = requests.get(channel_url, headers=headers, timeout=6)
            canonical = re.search(r'<link rel="canonical" href="([^"]+)"', r.text)
            canonical_url = canonical.group(1) if canonical else ""

            canonical_match = re.search(r'(?:watch\?v=|/live/)([a-zA-Z0-9_-]{11})', canonical_url)
            if canonical_match:
                return canonical_match.group(1)

            player_match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?});(?:var|\s*</script>)', r.text)
            if player_match:
                try:
                    p_data = fast_loads(player_match.group(1))
                    v_details = p_data.get("videoDetails", {})
                    if (v_details.get("isLive") or v_details.get("isLiveContent")) and v_details.get("videoId"):
                        return v_details.get("videoId")
                except Exception:
                    pass
        except Exception as e:
            logger.warning("[YouTubeChatProvider] Failed to resolve live video ID for %s: %s", target, e)

        return None

    def __init__(self, i18n=None) -> None:
        self.i18n = i18n or TranslationService()
        self._chat: Any | None = None
        self._is_running = False
        self._video_id: str = ""
        self._target_channel: str = ""
        self._seen_msg_ids: set = set()

    def start_chat(
        self,
        target: str,
        on_message: Callable[[str, str, list, str, str, int, dict], None],
        on_connected: Callable[[dict], None] | None = None,
        on_disconnected: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None
    ) -> None:
        self._is_running = True
        self._target_channel = target

        video_id = self.resolve_live_video_id(target)
        if not video_id:
            err_msg = self.i18n.get("logs.youtube.video_not_found").replace("{target}", target)
            if on_error:
                on_error(err_msg)
            return

        self._video_id = video_id
        logger.info("[YouTubeChatProvider] Connecting to YouTube live video: %s (Target: %s)", video_id, target)

        try:
            import pytchat
            self._chat = pytchat.create(video_id=video_id, interruptable=False)
            
            is_replay_func = getattr(self._chat, "is_replay", None)
            is_replay = is_replay_func() if callable(is_replay_func) else False

            if not self._chat.is_alive() or is_replay:
                err_msg = self.i18n.get("logs.youtube.stream_unavailable")
                if on_error:
                    on_error(err_msg)
                return

            if on_connected:
                on_connected({"platform": "youtube", "video_id": video_id, "channel": target})

            msg_seq = 0
            while self._is_running and self._chat.is_alive():
                sync_items = self._chat.get().sync_items()
                for c in sync_items:
                    if not self._is_running:
                        break

                    msg_seq += 1
                    user = getattr(c.author, "name", "User")
                    message = getattr(c, "message", "")
                    
                    badges = []
                    if getattr(c.author, "isChatOwner", False):
                        badges.append("broadcaster")
                    if getattr(c.author, "isChatModerator", False):
                        badges.append("moderator")
                    if getattr(c.author, "isChatSponsor", False):
                        badges.append("subscriber")
                    if getattr(c.author, "isVerified", False):
                        badges.append("verified")

                    amount_str = getattr(c, "amountString", "")
                    message_ex = getattr(c, "messageEx", [])
                    emotes = []
                    seen_emote_names = set()
                    if isinstance(message_ex, list):
                        for item in message_ex:
                            if isinstance(item, dict) and "url" in item:
                                txt = item.get("txt")
                                if not txt and item.get("id"):
                                    txt = f":{item.get('id')}:"
                                url = item.get("url", "")
                                if url.startswith("//"):
                                    url = f"https:{url}"
                                if txt and url and txt not in seen_emote_names:
                                    seen_emote_names.add(txt)
                                    emotes.append({
                                        "name": txt,
                                        "url": url,
                                        "id": str(item.get("id", ""))
                                    })

                    extra_data = {
                        "is_superchat": bool(amount_str),
                        "amount": amount_str,
                        "datetime": getattr(c, "datetime", ""),
                        "channel_id": getattr(c.author, "channelId", ""),
                        "emotes": emotes
                    }

                    color = "#FF0000" if "broadcaster" in badges else "#16a34a" if "moderator" in badges else "#2563eb" if "subscriber" in badges else self.DEFAULT_YOUTUBE_COLOR

                    raw_id = getattr(c, "id", None)
                    msg_id = raw_id if raw_id else f"yt_{int(time.time()*1000)}_{msg_seq}"
                    
                    if msg_id in self._seen_msg_ids:
                        continue
                    self._seen_msg_ids.add(msg_id)
                    if len(self._seen_msg_ids) > 5000:
                        self._seen_msg_ids.pop()

                    sender_id = hash(getattr(c.author, "channelId", user)) % 10000000

                    if on_message:
                        on_message(user, message, badges, color, msg_id, sender_id, extra_data)

                time.sleep(0.3)

            if on_disconnected and self._is_running:
                on_disconnected()

        except Exception as e:
            logger.error("[YouTubeChatProvider] Exception during live chat polling: %s", e)
            if on_error and self._is_running:
                on_error(str(e))
        finally:
            self.stop_chat()

    def stop_chat(self) -> None:
        self._is_running = False
        if self._chat:
            try:
                self._chat.terminate()
            except Exception:
                pass
            self._chat = None
