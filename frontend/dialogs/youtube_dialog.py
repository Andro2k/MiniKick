# frontend\dialogs\youtube_connect_dialog.py

from .platform_dialog import PlatformConnectDialog
from frontend.common import get_assets_path, COLOR_YOUTUBE

class YouTubeConnectDialog(PlatformConnectDialog):
    def __init__(self, i18n, initial_target: str = "", parent=None):
        super().__init__(
            i18n=i18n,
            title_key="dialogs.youtube_connect.title",
            desc_key="dialogs.youtube_connect.desc",
            placeholder_key="dialogs.youtube_connect.placeholder",
            btn_connect_key="dialogs.youtube_connect.btn_connect",
            icon_path=get_assets_path("icons/brand-youtube.svg"),
            icon_bg_color=COLOR_YOUTUBE,
            btn_role="action_youtube",
            initial_target=initial_target,
            width=480,
            parent=parent
        )
