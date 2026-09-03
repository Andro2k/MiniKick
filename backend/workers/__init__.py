# backend\workers\__init__.py

from .kick_auth_worker import KickAuthWorker
from .twitch_auth_worker import TwitchAuthWorker
from .bug_report_worker import BugReportWorker
from .crash_report_worker import CrashReportWorker
from .kick_chat_worker import KickChatWorker
from .twitch_chat_worker import TwitchChatWorker
from .youtube_chat_worker import YouTubeChatWorker
from .tiktok_chat_worker import TikTokChatWorker
from .music_worker import YouTubeResolveWorker, YouTubeSearchWorker
from .twitch_reward_worker import TwitchRewardWorker
from .rewards_worker import FetchRewardsWorker, CreateRewardWorker, UpdateRewardWorker
from .timers_worker import TimerWorker
from .update_worker import UpdateCheckWorker, UpdateDownloadWorker, ReleaseNotesWorker
from .voice_worker import VoiceFetcherWorker
from .schedule_worker import ScheduleWorker
from .global_media_worker import GlobalMediaWorker

__all__ = [
    "KickAuthWorker",
    "TwitchAuthWorker",
    "BugReportWorker",
    "CrashReportWorker",
    "KickChatWorker",
    "TwitchChatWorker",
    "YouTubeChatWorker",
    "TikTokChatWorker",
    "YouTubeResolveWorker",
    "YouTubeSearchWorker",
    "TwitchRewardWorker",
    "FetchRewardsWorker",
    "CreateRewardWorker",
    "UpdateRewardWorker",
    "TimerWorker",
    "UpdateCheckWorker",
    "UpdateDownloadWorker",
    "ReleaseNotesWorker",
    "VoiceFetcherWorker",
    "ScheduleWorker",
    "GlobalMediaWorker"
]
