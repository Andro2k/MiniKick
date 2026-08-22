# backend\services\__init__.py

_LAZY_IMPORTS = {
    "AuthManager": (".auth.oauth_service", "AuthManager"),
    "TwitchAuthManager": (".auth.oauth_service", "TwitchAuthManager"),
    "OAuthCallbackServer": (".auth.oauth_service", "OAuthCallbackServer"),
    "ChatService": (".chat.chat_service", "ChatService"),
    "CommandService": (".chat.command_service", "CommandService"),
    "ChatMessageDTO": (".chat.pipeline", "ChatMessageDTO"),
    "MessagePipeline": (".chat.pipeline", "MessagePipeline"),
    "SpamService": (".chat.spam_service", "SpamService"),
    "TimerService": (".chat.timer_service", "TimerService"),
    "TTSManager": (".chat.tts_service", "TTSManager"),
    "OverlayServerManager": (".overlay", "OverlayServerManager"),
    "RewardsService": (".rewards.rewards_service", "RewardsService"),
    "AvatarService": (".system.dashboard_service", "AvatarService"),
    "BackupService": (".system.backup_service", "BackupService"),
    "SocketInstanceProvider": (".system.instance_services", "SocketInstanceProvider"),
    "LogService": (".system.log_service", "LogService"),
    "NetworkService": (".system.network_service", "NetworkService"),
    "SettingsService": (".system.settings_service", "SettingsService"),
    "TranslationService": (".system.translation_service", "TranslationService"),
    "GithubUpdateProvider": (".system.updater_service", "GithubUpdateProvider"),
    "WindowsInstaller": (".system.updater_service", "WindowsInstaller"),
    "UpdateManager": (".system.updater_service", "UpdateManager"),
    "WidgetService": (".system.widget_service", "WidgetService"),
    "ScheduleService": (".schedule.schedule_service", "ScheduleService")
}

def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module_rel, attr = _LAZY_IMPORTS[name]
        import importlib
        mod = importlib.import_module(module_rel, package=__name__)
        val = getattr(mod, attr)
        globals()[name] = val
        return val
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = list(_LAZY_IMPORTS.keys())
