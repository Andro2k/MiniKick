# backend\workers\__init__.py

from .auth_worker import AuthWorker
from .twitch_auth_worker import TwitchAuthWorker
from .bug_report_worker import BugReportWorker
from .crash_report_worker import CrashReportWorker
from .chat_worker import ChatWorker
from .twitch_chat_worker import TwitchChatWorker
from .music_worker import YouTubeResolveWorker, YouTubeSearchWorker
from .network_worker import NetworkWorker
from .rewards_worker import RewardWorker, FetchRewardsWorker, CreateRewardWorker, UpdateRewardWorker
from .timers_worker import TimerWorker
from .update_worker import UpdateCheckWorker, UpdateDownloadWorker, ReleaseNotesWorker
from .voice_worker import VoiceFetcherWorker
from .schedule_worker import ScheduleWorker

__all__ = [
    "AuthWorker",
    "TwitchAuthWorker",
    "BugReportWorker",
    "CrashReportWorker",
    "ChatWorker",
    "TwitchChatWorker",
    "YouTubeResolveWorker",
    "YouTubeSearchWorker",
    "NetworkWorker",
    "RewardWorker",
    "FetchRewardsWorker",
    "CreateRewardWorker",
    "UpdateRewardWorker",
    "TimerWorker",
    "UpdateCheckWorker",
    "UpdateDownloadWorker",
    "ReleaseNotesWorker",
    "VoiceFetcherWorker",
    "ScheduleWorker"
]
