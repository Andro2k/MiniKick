# frontend\dialogs\tiktok_connect_dialog.py

from .platform_connect_dialog import PlatformConnectDialog
from frontend.common import get_assets_path, COLOR_TIKTOK

class TikTokConnectDialog(PlatformConnectDialog):
    def __init__(self, i18n, initial_target: str = "", parent=None):
        super().__init__(
            i18n=i18n,
            title_key="dialogs.tiktok_connect.title",
            desc_key="dialogs.tiktok_connect.desc",
            placeholder_key="dialogs.tiktok_connect.placeholder",
            btn_connect_key="dialogs.tiktok_connect.btn_connect",
            icon_path=get_assets_path("icons/brand-tiktok.svg"),
            icon_bg_color=COLOR_TIKTOK,
            btn_role="action_tiktok",
            initial_target=initial_target,
            width=480,
            parent=parent
        )
