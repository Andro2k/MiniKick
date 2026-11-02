# frontend\window\startup.py

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from collections.abc import Callable, Iterable

from PySide6.QtCore import QTimer

from backend.connections import LiveChatConnection


class StartupSequencer:
    WHATS_NEW_DELAY_MS = 750
    PREWARM_DELAY_MS = 300
    DATABASE_MAINTENANCE_DELAY_MS = 10_000
    INITIAL_HYDRATION_DELAY_MS = 50
    NEXT_HYDRATION_DELAY_MS = 16

    def __init__(
        self,
        logger: logging.Logger,
        is_active: Callable[[], bool],
        whats_new_check: Callable[[], None],
        prewarm_views: Callable[[int], None],
        start_database_maintenance: Callable[[], None],
        schedule: Callable[[int, Callable[[], None]], None] = QTimer.singleShot,
    ) -> None:
        self._logger = logger
        self._is_active = is_active
        self._whats_new_check = whats_new_check
        self._prewarm_views = prewarm_views
        self._start_database_maintenance = start_database_maintenance
        self._schedule = schedule
        self._steps: deque[tuple[str, Callable[[], None]]] = deque()

    def start(self, steps: Iterable[tuple[str, Callable[[], None]]]) -> None:
        self._steps = deque(steps)
        self._schedule(self.INITIAL_HYDRATION_DELAY_MS, self._run_next)

    def _run_next(self) -> None:
        if not self._is_active() or not self._steps:
            return

        step_name, step = self._steps.popleft()
        step_started = time.perf_counter()
        try:
            step()
        except Exception:
            self._logger.exception("[Startup] Hydration phase '%s' failed.", step_name)
        else:
            self._logger.info(
                "[Perf/Startup] Hydration phase '%s' completed in %.2f ms",
                step_name,
                (time.perf_counter() - step_started) * 1000,
            )

        if self._steps:
            self._schedule(self.NEXT_HYDRATION_DELAY_MS, self._run_next)
        else:
            self._schedule_followups()

    def _schedule_followups(self) -> None:
        self._schedule(self.WHATS_NEW_DELAY_MS, self._whats_new_check)
        self._prewarm_views(self.PREWARM_DELAY_MS)
        self._schedule(
            self.DATABASE_MAINTENANCE_DELAY_MS,
            self._start_database_maintenance,
        )


class MainWindowStartup:
    def __init__(self, window, view_prewarmer) -> None:
        self._window = window
        self._sequencer = StartupSequencer(
            logger=window.logger,
            is_active=lambda: not window._is_shutting_down,
            whats_new_check=window.whats_new.check_dialog,
            prewarm_views=view_prewarmer.start,
            start_database_maintenance=self.start_database_maintenance,
        )

    def load_settings_into_ui(self, *, refresh_chat_backend: bool = False) -> None:
        w = self._window
        w.logger.debug(
            "[AutoStart] Loading controller initial state (Rewards, Widgets, Chat, Spam, Timers, Music)..."
        )
        steps = (
            ("rewards", w.rewards_controller.load_initial_data),
            ("widgets", w.widgets_controller.load_initial_data),
            ("chat settings", self._load_chat_settings),
            ("command cache", w.command_service.reload_cache),
            ("spam, timers, and music", self._load_remaining_controller_data),
            (
                "chat and overlay settings",
                lambda: self._load_chat_controller_data(refresh_backend=refresh_chat_backend),
            ),
            ("integrations and profile", self._finish_settings_hydration),
        )
        self._sequencer.start(steps)

    def on_backup_restored(self) -> None:
        self.load_settings_into_ui(refresh_chat_backend=True)

    def _load_chat_settings(self) -> None:
        w = self._window
        settings = w.chat_service.get_settings()
        w.tray_manager.set_tts_state(settings.get("enabled", True))
        w.tray_manager.set_tts_use_command_state(settings.get("use_command", False))
        w.tray_manager.set_tts_voice_type_state(settings.get("provider", "piper") == "web")

    def _load_remaining_controller_data(self) -> None:
        w = self._window
        w.spam_controller.load_initial_data()
        w.timers_controller.load_initial_data()
        w.music_controller.load_initial_data()

    def _load_chat_controller_data(self, *, refresh_backend: bool = False) -> None:
        w = self._window
        w.chat_controller.load_initial_data(refresh_backend=refresh_backend)
        w.overlay_server.trigger_chat_config_update(
            w.chat_controller.get_active_overlay_config()
        )

    def _finish_settings_hydration(self) -> None:
        w = self._window
        w._apply_dynamic_theme(w.settings_service.get_font_size())
        w.platform_connections.update_integrations_status_ui()
        w.platform_connections.refresh_sidebar_profile()
        w.platform_connections.evaluate_all_scopes()
        self._autostart_authenticated_platforms()
        self._schedule_live_chat_autostarts()

    def _autostart_authenticated_platforms(self) -> None:
        w = self._window
        if w.kick_auth_manager.is_authenticated():
            try:
                w.logger.info("[AutoStart] Starting Kick integration...")
                w.platform_connections.handle_auth_process(startup=True)
            except Exception as error:
                w.logger.error("[AutoStart] Error auto-starting Kick integration: %s", error)

        twitch_tokens = w.container.twitch_token_storage.load()
        if twitch_tokens and twitch_tokens.get("access_token"):
            QTimer.singleShot(1200, self._autostart_twitch)

    def _schedule_live_chat_autostarts(self) -> None:
        w = self._window
        for chat, delay_ms in ((w.youtube, 2400), (w.tiktok, 3600)):
            target = chat.saved_target()
            if target:
                QTimer.singleShot(
                    delay_ms,
                    lambda c=chat, t=target: self._autostart_live_chat(c, t),
                )

    def _autostart_twitch(self) -> None:
        w = self._window
        if w._is_shutting_down:
            return
        try:
            w.logger.info("[AutoStart] Starting Twitch integration...")
            w._startup_silent_connections.add("twitch")
            w.twitch.resume_session()
        except Exception as error:
            w.logger.error("[AutoStart] Error auto-starting Twitch integration: %s", error)

    def _autostart_live_chat(self, chat: LiveChatConnection, target: str) -> None:
        w = self._window
        if w._is_shutting_down:
            return
        if chat.is_offline_saved():
            w.logger.info(
                "[AutoStart] Skipping %s integration because the saved stream is offline; connect manually to retry.",
                chat.log_tag,
            )
            return
        try:
            w.logger.info(
                "[AutoStart] Starting %s integration (target='%s')...",
                chat.log_tag,
                target,
            )
            w._startup_silent_connections.add(chat.platform_id)
            chat.connect_channel(target, manual=False)
        except Exception as error:
            w.logger.error(
                "[AutoStart] Error auto-starting %s integration: %s",
                chat.log_tag,
                error,
            )

    def start_database_maintenance(self) -> None:
        w = self._window
        if w._is_shutting_down:
            return
        threading.Thread(
            target=w.container.db_maintenance.run,
            name="DatabaseMaintenance",
            daemon=True,
        ).start()
