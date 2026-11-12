# frontend\components\music\__init__.py

from .stats_panel import MusicStatsPanel
from .player_settings import MusicPlayerSettingsPanel
from .music_settings_panel import MusicSettingsPanel
from .commands_panel import MusicCommandsPanel
from .queue_panel import MusicQueuePanel, DragDropQueueTable
from .history_panel import MusicHistoryPanel
from .music_mockup import MusicOverlayMockupWidget

__all__ = [
    "MusicStatsPanel",
    "MusicPlayerSettingsPanel",
    "MusicSettingsPanel",
    "MusicCommandsPanel",
    "MusicQueuePanel",
    "DragDropQueueTable",
    "MusicHistoryPanel",
    "MusicOverlayMockupWidget"
]
