# frontend\window\composition.py

from __future__ import annotations

from backend.connections import ConnectionHub, KickConnection, WorkerSlot
from backend.config import KICK_PUSHER
from backend.controllers import (
    AlertsController,
    ChatController,
    CommandsController,
    DashboardController,
    LogsController,
    MusicController,
    RewardsController,
    ScheduleController,
    SettingsController,
    SpamController,
    TimersController,
    WebhooksController,
    WidgetsController,
)
from backend.services import (
    AvatarService,
    ChatService,
    CommandService,
    LogService,
    RewardsService,
    SettingsService,
    SpamService,
    TimerService,
)
from backend.workers import GlobalMediaWorker
from frontend.common.qt_debounce import qt_debounce
from frontend.window.integrations_status import IntegrationsStatusPresenter
from frontend.window.media_keys import MediaKeysHandler
from frontend.window.messages import ChatMessageRouter
from frontend.window.platform_connections import PlatformConnectionHandlers
from frontend.window.overlay_events import OverlayEventPresenter
from frontend.window.rewards import RewardRedemptionHandler, RewardRedemptionPresenter
from frontend.window.schedule import SchedulePresenter


class MainWindowComposition:
    def __init__(self, window) -> None:
        self._window = window

    def create_services(self) -> None:
        w = self._window
        w.avatar_service = AvatarService(avatar_storage=w.container.avatar_storage)
        w.chat_service = ChatService(w.tts_manager, w.settings_storage, debounce=qt_debounce)
        w.settings_service = SettingsService(w.settings_storage, w.backup_service)
        w.rewards_service = RewardsService(w.rewards_storage, w.overlay_server)
        w.reward_redemption_handler = RewardRedemptionHandler(
            w.rewards_service,
            w._recent_reward_redemptions,
            w.logger,
        )

        w.command_service = CommandService(w.commands_storage, api_client=None)
        w.spam_service = SpamService(w.spam_storage, api_client=None, i18n=w.i18n)
        w.timer_service = TimerService(w.timers_storage, api_client=None)
        w.kick = KickConnection(
            auth_manager=w.kick_auth_manager,
            i18n=w.i18n,
            timer_service=w.timer_service,
            pusher=KICK_PUSHER,
            coordinator=w._worker_shutdown_coordinator,
            is_shutting_down=lambda: w._is_shutting_down,
            parent=w,
        )
        w._schedule_slot = WorkerSlot("Worker_Stream_Schedule", w._worker_shutdown_coordinator)
        w.log_service = LogService(log_storage=w.container.system_log_storage)
        w.schedule_service = w.container.schedule_service

    def create_controllers(self) -> None:
        w = self._window
        w.platform_connections = PlatformConnectionHandlers(w)
        w.reward_redemption_presenter = RewardRedemptionPresenter(
            w,
            w.reward_redemption_handler,
        )
        w.overlay_events = OverlayEventPresenter(w.overlay_server)
        w.dashboard_controller = DashboardController(
            view=w.view_dashboard,
            avatar_service=w.avatar_service,
            db_manager=w.container.db_manager,
            widget_service=w.container.widget_service,
            toast_manager=w.toast,
            i18n=w.i18n,
        )
        w.chat_controller = ChatController(
            view=None,
            service=w.chat_service,
            command_service=w.command_service,
            spam_service=w.spam_service,
            i18n=w.i18n,
            timer_service=w.timer_service,
            toast_manager=w.toast,
        )
        w.chat_message_router = ChatMessageRouter(
            process_message=w.chat_controller.process_message,
            record_message=w.session_metrics.record_message,
            profile_provider=w.platform_connections.get_message_profile,
        )
        w.widgets_controller = WidgetsController(
            view=None,
            widget_service=w.container.widget_service,
            command_service=w.command_service,
            overlay_server=w.overlay_server,
            i18n=w.i18n,
            toast_manager=w.toast,
            ignored_users_provider=w.chat_service.get_ignored_users,
        )
        w.dashboard_controller.widgets_controller = w.widgets_controller
        w.music_controller = MusicController(
            view=None,
            command_service=w.command_service,
            toast_manager=w.toast,
            i18n=w.i18n,
            settings_storage=w.container.settings_storage,
            music_storage=w.container.music_storage,
            music_provider=w.container.music_provider,
        )
        w.media_keys = MediaKeysHandler(
            w.music_controller,
            config=w.settings_storage,
            slot=WorkerSlot("Worker_Global_Media_Keys", w._worker_shutdown_coordinator),
            worker_factory=GlobalMediaWorker,
            is_shutting_down=lambda: w._is_shutting_down,
        )
        w.chat_service.set_speech_callbacks(
            on_started=lambda: w.music_controller.set_ducking(True),
            on_finished=lambda: w.music_controller.set_ducking(False),
        )
        w.rewards_controller = RewardsController(
            view=None,
            service=w.rewards_service,
            toast_manager=w.toast,
            kick_auth_manager=w.kick_auth_manager,
            twitch_auth_manager=w.container.twitch_auth_manager,
        )
        w.commands_controller = CommandsController(
            None,
            w.command_service,
            toast_manager=w.toast,
            connected_platforms_provider=w.platform_connections.get_connected_platforms,
        )
        w.spam_controller = SpamController(
            None,
            w.spam_service,
            toast_manager=w.toast,
            connected_platforms_provider=w.platform_connections.get_connected_platforms,
        )
        w.timers_controller = TimersController(
            None,
            w.timer_service,
            toast_manager=w.toast,
            schedule_service=w.schedule_service,
            connected_platforms_provider=w.platform_connections.get_connected_platforms,
        )
        w.webhooks_controller = WebhooksController(
            None,
            w.container.webhook_service,
            toast_manager=w.toast,
            i18n=w.i18n,
        )
        w.settings_controller = SettingsController(
            view=None,
            service=w.settings_service,
            toast_manager=w.toast,
            music_provider=w.container.music_provider,
            tts_manager=w.tts_manager,
            browser_service=w.container.browser_service,
        )
        w.logs_controller = LogsController(
            view=None,
            service=w.log_service,
            toast_manager=w.toast,
        )
        w.schedule_controller = ScheduleController(
            view=None,
            service=w.schedule_service,
            toast_manager=w.toast,
            i18n=w.i18n,
            connected_platforms_provider=w.platform_connections.get_connected_platforms,
        )
        w.schedule_presenter = SchedulePresenter(w)
        w.alerts_controller = AlertsController(
            view=None,
            service=w.container.alert_service,
            toast_manager=w.toast,
            i18n=w.i18n,
            browser_service=w.container.browser_service,
        )
        w.connection_hub = ConnectionHub(
            connections={
                "kick": w.kick,
                "twitch": w.twitch,
                "youtube": w.youtube,
                "tiktok": w.tiktok,
            },
            authenticated_providers={
                "kick": w.kick_auth_manager.is_authenticated,
                "twitch": w.container.twitch_auth_manager.is_authenticated,
            },
            parent=w,
        )
        w.integrations_status = IntegrationsStatusPresenter(
            hub=w.connection_hub,
            dashboard_controller=w.dashboard_controller,
            session_metrics=w.session_metrics,
            settings_view_provider=lambda: w.view_settings,
            platform_views_provider=lambda: (
                w.view_chat,
                w.view_commands,
                w.view_schedule,
                w.view_rewards,
                w.view_timers,
                w.view_alerts,
            ),
        )
