# backend\workers\__init__.py

from typing import TYPE_CHECKING

_EXPORTS = {
    "KickAuthWorker": ".kick_auth_worker",
    "TwitchAuthWorker": ".twitch_auth_worker",
    "BugReportWorker": ".bug_report_worker",
    "CrashReportWorker": ".crash_report_worker",
    "KickChatWorker": ".kick_chat_worker",
    "TwitchChatWorker": ".twitch_chat_worker",
    "YouTubeChatWorker": ".youtube_chat_worker",
    "TikTokChatWorker": ".tiktok_chat_worker",
    "YouTubeResolveWorker": ".music_worker",
    "YouTubeSearchWorker": ".music_worker",
    "TwitchRewardWorker": ".twitch_rewards_worker",
    "FetchRewardsWorker": ".rewards_worker",
    "CreateRewardWorker": ".rewards_worker",
    "UpdateRewardWorker": ".rewards_worker",
    "TimerWorker": ".timers_worker",
    "UpdateCheckWorker": ".updater_worker",
    "UpdateDownloadWorker": ".updater_worker",
    "ReleaseNotesWorker": ".updater_worker",
    "VoiceFetcherWorker": ".voice_worker",
    "ScheduleWorker": ".schedule_worker",
    "GlobalMediaWorker": ".global_media_worker",
}

__all__ = list(_EXPORTS.keys())

def __getattr__(name: str):
    if name in _EXPORTS:
        import importlib
        mod = importlib.import_module(_EXPORTS[name], package=__name__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

if TYPE_CHECKING:
    from .kick_auth_worker import KickAuthWorker
    from .twitch_auth_worker import TwitchAuthWorker
    from .bug_report_worker import BugReportWorker
    from .crash_report_worker import CrashReportWorker
    from .kick_chat_worker import KickChatWorker
    from .twitch_chat_worker import TwitchChatWorker
    from .youtube_chat_worker import YouTubeChatWorker
    from .tiktok_chat_worker import TikTokChatWorker
    from .music_worker import YouTubeResolveWorker, YouTubeSearchWorker
    from .twitch_rewards_worker import TwitchRewardWorker
    from .rewards_worker import FetchRewardsWorker, CreateRewardWorker, UpdateRewardWorker
    from .timers_worker import TimerWorker
    from .updater_worker import UpdateCheckWorker, UpdateDownloadWorker, ReleaseNotesWorker
    from .voice_worker import VoiceFetcherWorker
    from .schedule_worker import ScheduleWorker
    from .global_media_worker import GlobalMediaWorker

