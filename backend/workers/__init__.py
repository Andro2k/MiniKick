# backend\workers\__init__.py

_LAZY_WORKERS = {
    "AuthWorker": (".auth_worker", "AuthWorker"),
    "TwitchAuthWorker": (".twitch_auth_worker", "TwitchAuthWorker"),
    "BugReportWorker": (".bug_report_worker", "BugReportWorker"),
    "CrashReportWorker": (".crash_report_worker", "CrashReportWorker"),
    "ChatWorker": (".chat_worker", "ChatWorker"),
    "TwitchChatWorker": (".twitch_chat_worker", "TwitchChatWorker"),
    "YouTubeChatWorker": (".youtube_chat_worker", "YouTubeChatWorker"),
    "YouTubeResolveWorker": (".music_worker", "YouTubeResolveWorker"),
    "YouTubeSearchWorker": (".music_worker", "YouTubeSearchWorker"),
    "NetworkWorker": (".network_worker", "NetworkWorker"),
    "RewardWorker": (".rewards_worker", "RewardWorker"),
    "FetchRewardsWorker": (".rewards_worker", "FetchRewardsWorker"),
    "CreateRewardWorker": (".rewards_worker", "CreateRewardWorker"),
    "UpdateRewardWorker": (".rewards_worker", "UpdateRewardWorker"),
    "TimerWorker": (".timers_worker", "TimerWorker"),
    "UpdateCheckWorker": (".update_worker", "UpdateCheckWorker"),
    "UpdateDownloadWorker": (".update_worker", "UpdateDownloadWorker"),
    "ReleaseNotesWorker": (".update_worker", "ReleaseNotesWorker"),
    "VoiceFetcherWorker": (".voice_worker", "VoiceFetcherWorker"),
    "ScheduleWorker": (".schedule_worker", "ScheduleWorker"),
}

def __getattr__(name: str):
    if name in _LAZY_WORKERS:
        module_rel, attr = _LAZY_WORKERS[name]
        import importlib
        mod = importlib.import_module(module_rel, package=__name__)
        val = getattr(mod, attr)
        globals()[name] = val
        return val
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = list(_LAZY_WORKERS.keys())
