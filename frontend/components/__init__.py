# frontend\components\__init__.py

from . import chat
from . import music
from . import schedule
from . import widgets

from .chat import (
    BotMutePanel,
    ChatDisplayPanel,
    ChatOverlaySettingsPanel,
    ChatTtsSettingsPanel,
    VoiceSettingRow,
)
from .music import (
    MusicStatsPanel,
    MusicPlayerSettingsPanel,
    MusicSettingsPanel,
    MusicCommandsPanel,
    MusicQueuePanel,
    DragDropQueueTable,
    MusicOverlayMockupWidget,
)
from .schedule import (
    ScheduleQuickChangePanel,
    ScheduleFormPanel,
    ScheduleTablePanel,
)
from .widgets import (
    WidgetCard,
)

__all__ = [
    "chat",
    "music",
    "schedule",
    "widgets",
    "BotMutePanel",
    "ChatDisplayPanel",
    "ChatOverlaySettingsPanel",
    "ChatTtsSettingsPanel",
    "VoiceSettingRow",
    "MusicStatsPanel",
    "MusicPlayerSettingsPanel",
    "MusicSettingsPanel",
    "MusicCommandsPanel",
    "MusicQueuePanel",
    "DragDropQueueTable",
    "MusicOverlayMockupWidget",
    "ScheduleQuickChangePanel",
    "ScheduleFormPanel",
    "ScheduleTablePanel",
    "WidgetCard",
]
