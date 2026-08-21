# backend\services\schedule\schedule_service.py

import time
import logging
from concurrent.futures import ThreadPoolExecutor
from backend.database.schedule_storage import SQLiteScheduleStorage
from backend.providers.chat.kick_client import KickAPIClient
from backend.providers.chat.twitch_client import TwitchAPIClient

logger = logging.getLogger("minikick.schedule_service")

class ScheduleService:
    def __init__(self, schedule_storage: SQLiteScheduleStorage,
                 kick_client: KickAPIClient | None = None,
                 twitch_client: TwitchAPIClient | None = None,
                 twitch_broadcaster_id: str = "",
                 i18n=None):
        self.schedule_storage = schedule_storage
        self.kick_client = kick_client
        self.twitch_client = twitch_client
        self.twitch_broadcaster_id = twitch_broadcaster_id
        self.i18n = i18n
        self._category_cache: dict[tuple[str, str], tuple[float, list[dict]]] = {}
        self._cache_ttl = 120.0

    def set_kick_client(self, kick_client: KickAPIClient | None) -> None:
        self.kick_client = kick_client

    def set_twitch_client(self, twitch_client: TwitchAPIClient | None, broadcaster_id: str = "") -> None:
        self.twitch_client = twitch_client
        if broadcaster_id:
            self.twitch_broadcaster_id = broadcaster_id

    def get_current_info(self) -> dict:
        results = {"kick": {}, "twitch": {}}
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_kick = executor.submit(self._fetch_kick_info)
            future_twitch = executor.submit(self._fetch_twitch_info)
            
            try:
                results["kick"] = future_kick.result(timeout=10)
            except Exception as e:
                logger.warning("[ScheduleService] Error fetching Kick channel info: %s", e)
                results["kick"] = {"error": str(e)}

            try:
                results["twitch"] = future_twitch.result(timeout=10)
            except Exception as e:
                logger.warning("[ScheduleService] Error fetching Twitch channel info: %s", e)
                results["twitch"] = {"error": str(e)}

        return results

    def _fetch_kick_info(self) -> dict:
        if not self.kick_client:
            return {}
        try:
            return self.kick_client.get_channel_metadata()
        except Exception as e:
            return {"error": str(e)}

    def _fetch_twitch_info(self) -> dict:
        if not self.twitch_client or not self.twitch_broadcaster_id:
            return {}
        if hasattr(self.twitch_client, "is_authenticated") and not self.twitch_client.is_authenticated():
            return {}
        try:
            return self.twitch_client.get_channel_metadata(self.twitch_broadcaster_id)
        except Exception as e:
            return {"error": str(e)}

    def search_categories(self, query: str, platform: str = "both") -> dict:
        query_clean = query.strip().lower()
        if not query_clean:
            return {"kick": [], "twitch": []}

        now = time.time()
        results = {"kick": [], "twitch": []}

        platforms_to_search = []
        if platform in ("both", "all"):
            platforms_to_search = ["kick"]
            if self.twitch_client and getattr(self.twitch_client, "is_authenticated", lambda: True)():
                platforms_to_search.append("twitch")
        elif platform == "kick":
            platforms_to_search = ["kick"]
        elif platform == "twitch":
            if self.twitch_client and getattr(self.twitch_client, "is_authenticated", lambda: True)():
                platforms_to_search = ["twitch"]

        search_tasks = {}
        with ThreadPoolExecutor(max_workers=2) as executor:
            for p in platforms_to_search:
                cache_key = (p, query_clean)
                if cache_key in self._category_cache:
                    cached_time, cached_items = self._category_cache[cache_key]
                    if now - cached_time < self._cache_ttl:
                        results[p] = cached_items
                        continue

                if p == "kick":
                    client = self.kick_client
                    if not client:
                        from backend.providers.chat.kick_client import KickAPIClient
                        client = KickAPIClient(None)
                    search_tasks["kick"] = executor.submit(client.search_categories, query)
                elif p == "twitch" and self.twitch_client:
                    search_tasks["twitch"] = executor.submit(self.twitch_client.search_categories, query)

            for p, future in search_tasks.items():
                try:
                    items = future.result(timeout=8)
                    ranked_items = self._rank_category_items(items, query_clean)
                    results[p] = ranked_items
                    self._category_cache[(p, query_clean)] = (now, ranked_items)
                except Exception as e:
                    logger.warning("[ScheduleService] Error searching categories on %s: %s", p, e)
                    results[p] = []

        return results

    @staticmethod
    def _rank_category_items(items: list[dict], query_clean: str) -> list[dict]:
        if not items or not query_clean:
            return items or []
        
        seen = set()
        deduped = []
        for item in items:
            name = item.get("name", "").strip()
            if not name:
                continue
            cat_id = str(item.get("id", name))
            if cat_id in seen:
                continue
            seen.add(cat_id)
            deduped.append(item)

        def _sort_key(item: dict) -> tuple[int, int, str]:
            name_lower = item.get("name", "").strip().lower()
            if name_lower == query_clean:
                score = 0
            elif name_lower.startswith(query_clean):
                score = 1
            elif query_clean in name_lower:
                score = 2
            else:
                score = 3
            return (score, len(name_lower), name_lower)

        return sorted(deduped, key=_sort_key)

    def update_stream_info(self, title: str | None,
                           kick_category_id: int | None = None,
                           twitch_category_id: str | None = None,
                           platform: str = "both",
                           category_query: str = "") -> dict:
        outcome = {
            "kick": {"success": False, "error": None},
            "twitch": {"success": False, "error": None}
        }

        clean_title = str(title).strip() if title is not None and str(title).strip() else None

        clean_kick_cat = None
        if kick_category_id is not None:
            try:
                cid = int(kick_category_id)
                if cid > 0:
                    clean_kick_cat = cid
            except (ValueError, TypeError):
                pass

        clean_twitch_cat = str(twitch_category_id).strip() if twitch_category_id is not None and str(twitch_category_id).strip() else None

        if platform in ("both", "all", "kick") and self.kick_client and not clean_kick_cat and category_query:
            try:
                search_res = self.kick_client.search_categories(category_query)
                if search_res:
                    clean_kick_cat = search_res[0].get("id")
            except Exception as e:
                logger.warning("[ScheduleService] Auto-resolve Kick category error: %s", e)

        if platform in ("both", "all", "twitch") and self.twitch_client and not clean_twitch_cat and category_query:
            if getattr(self.twitch_client, "is_authenticated", lambda: True)():
                try:
                    search_res = self.twitch_client.search_categories(category_query)
                    if search_res:
                        clean_twitch_cat = search_res[0].get("id")
                except Exception as e:
                    logger.warning("[ScheduleService] Auto-resolve Twitch category error: %s", e)

        tasks = {}
        with ThreadPoolExecutor(max_workers=2) as executor:
            if platform in ("both", "all", "kick") and self.kick_client:
                tasks["kick"] = executor.submit(
                    self.kick_client.update_channel_metadata,
                    category_id=clean_kick_cat,
                    stream_title=clean_title
                )

            if platform in ("both", "all", "twitch") and self.twitch_client and self.twitch_broadcaster_id:
                if getattr(self.twitch_client, "is_authenticated", lambda: True)():
                    tasks["twitch"] = executor.submit(
                        self.twitch_client.update_channel_metadata,
                        broadcaster_id=self.twitch_broadcaster_id,
                        title=clean_title,
                        game_id=clean_twitch_cat
                    )

            for p, future in tasks.items():
                try:
                    ok = future.result(timeout=15)
                    outcome[p]["success"] = bool(ok)
                    if not ok:
                        err_key = "stream_info.errors.update_failed"
                        outcome[p]["error"] = self.i18n.get(err_key) if self.i18n else "Update failed"
                except Exception as e:
                    logger.error("[ScheduleService] Exception updating %s: %s", p, e)
                    outcome[p]["success"] = False
                    outcome[p]["error"] = str(e)

        return outcome

    def get_all_schedules(self) -> list[dict]:
        return self.schedule_storage.load_all()

    def save_schedule(self, name: str, date_str: str, time_str: str, target_platform: str,
                      title: str, kick_category_id: int | None, kick_category_name: str,
                      twitch_category_id: str | None, twitch_category_name: str,
                      is_active: bool = True, schedule_id: int | None = None) -> int:
        return self.schedule_storage.save(
            name=name,
            date_str=date_str,
            time_str=time_str,
            target_platform=target_platform,
            title=title,
            kick_category_id=kick_category_id,
            kick_category_name=kick_category_name,
            twitch_category_id=twitch_category_id,
            twitch_category_name=twitch_category_name,
            is_active=is_active,
            schedule_id=schedule_id
        )

    def delete_schedule(self, schedule_id: int) -> bool:
        return self.schedule_storage.delete(schedule_id)

    def toggle_schedule(self, schedule_id: int, is_active: bool) -> bool:
        return self.schedule_storage.toggle_active(schedule_id, is_active)

    def apply_schedule(self, schedule: dict) -> dict:
        target_platform = schedule.get("target_platform", "all")
        title = schedule.get("title", "")
        kick_cat_id = schedule.get("kick_category_id")
        twitch_cat_id = schedule.get("twitch_category_id")

        logger.info("[ScheduleService] Executing automated schedule: '%s' (Platform: %s)",
                    schedule.get("name"), target_platform)

        res = self.update_stream_info(
            title=title,
            kick_category_id=kick_cat_id,
            twitch_category_id=twitch_cat_id,
            platform=target_platform
        )
        return res
