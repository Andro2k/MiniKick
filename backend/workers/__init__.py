# backend\workers\__init__.py

from .auth_worker import AuthWorker
from .bug_report_worker import BugReportWorker
from .crash_report_worker import CrashReportWorker
from .chat_worker import ChatWorker
from .music_worker import SpotifyAuthWorker, YouTubeResolveWorker, YouTubeSearchWorker
from .network_worker import NetworkWorker
from .rewards_worker import RewardWorker, FetchRewardsWorker
from .timers_worker import TimerWorker
from .update_worker import UpdateCheckWorker, UpdateDownloadWorker
from .voice_worker import VoiceFetcherWorker

__all__ = [
    "AuthWorker",
    "BugReportWorker",
    "CrashReportWorker",
    "ChatWorker",
    "SpotifyAuthWorker",
    "YouTubeResolveWorker",
    "YouTubeSearchWorker",
    "NetworkWorker",
    "RewardWorker",
    "FetchRewardsWorker",
    "TimerWorker",
    "UpdateCheckWorker",
    "UpdateDownloadWorker",
    "VoiceFetcherWorker"
]
