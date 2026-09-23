# frontend\components\__init__.py

from . import chat
from . import music
from . import schedule
from . import widgets

from .chat import (BotMutePanel, ChatDisplayPanel,
    ChatOverlaySettingsPanel, ChatOverlayMockupWidget,
    ChatTtsSettingsPanel, VoiceSettingRow,
)
from .music import (MusicStatsPanel,MusicPlayerSettingsPanel,
    MusicSettingsPanel,MusicCommandsPanel,
    MusicQueuePanel,DragDropQueueTable,
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
from .mockup_helpers import (
    init_mockup_painter,
    draw_mockup_canvas,
)

__all__ = [
    "chat",
    "music",
    "schedule",
    "widgets",
    "init_mockup_painter",
    "draw_mockup_canvas",
    "BotMutePanel",
    "ChatDisplayPanel",
    "ChatOverlaySettingsPanel",
    "ChatOverlayMockupWidget",
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
