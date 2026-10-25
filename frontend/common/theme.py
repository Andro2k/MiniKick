# frontend\common\theme.py

import os
import re
import tempfile
from functools import lru_cache
from pathlib import Path
from PySide6.QtGui import QPalette, QColor
from .paths import get_assets_path, resolve_icon_path

class Palette:
    NEUTRAL_999 = "#000000"
    NEUTRAL_950 = "#101010"
    NEUTRAL_900 = "#171717"
    NEUTRAL_750 = "#282A32"
    NEUTRAL_700 = "#343741"
    NEUTRAL_600 = "#4B5563"
    NEUTRAL_500 = "#6E7382"
    NEUTRAL_400 = "#9CA3AF"
    NEUTRAL_200 = "#E4E5E5"
    NEUTRAL_050 = "#F4F4F4"
    NEUTRAL_000 = "#FFFFFF"
    SURFACE_900 = "#1A1B1A"

class Semantic:
    SURFACE_BASE          = Palette.NEUTRAL_950
    DANGER_DEFAULT        = "#EF4444"
    TEXT_PRIMARY          = Palette.NEUTRAL_050
    TEXT_MUTED            = Palette.NEUTRAL_400
    NEUTRAL_999           = Palette.NEUTRAL_999
    NEUTRAL_950           = Palette.NEUTRAL_950
    NEUTRAL_900           = Palette.NEUTRAL_900
    NEUTRAL_750           = Palette.NEUTRAL_750
    NEUTRAL_700           = Palette.NEUTRAL_700
    NEUTRAL_600           = Palette.NEUTRAL_600
    NEUTRAL_500           = Palette.NEUTRAL_500
    NEUTRAL_400           = Palette.NEUTRAL_400
    NEUTRAL_200           = Palette.NEUTRAL_200
    NEUTRAL_050           = Palette.NEUTRAL_050
    NEUTRAL_000           = Palette.NEUTRAL_000
    SURFACE_900           = Palette.SURFACE_900
    BORDER_HOVER          = "#484C5A"
    BORDER_TOP_SHINE      = "#38363E"
    BORDER_LIGHT          = "#4B4951"
    BORDER_SUBTLE_GHOST   = "#313036"
    LIGHT_TEXT_PRIMARY    = "#0F172A"
    LIGHT_TEXT_MUTED      = "#64748B"
    DANGER_SURFACE        = "#2D1215"
    MEDIA_THUMB_BG        = "#1E293B"
    CALLOUT_NOTE_LIGHT    = "#60A5FA"
    CALLOUT_WARNING_LIGHT = "#FACC15"
    CALLOUT_TIP_LIGHT     = "#4ADE80"
    CALLOUT_CAUTION_LIGHT = "#F87171"
    CODE_LINK             = "#38BDF8"
    LATEX_MATH            = "#A5B4FC"
    WHITE_GLOW            = "rgba(250, 250, 250, 0.05)"
    GREEN_GLOW            = "rgba(46, 205, 112, 0.10)"
    RED_GLOW              = "rgba(239, 68, 68, 0.10)"
    AMBER_GLOW            = "rgba(245, 158, 11, 0.10)"
    BLUE_GLOW             = "rgba(59, 130, 246, 0.10)"
    PURPLE_GLOW           = "rgba(168, 85, 247, 0.10)"

class BrandColors:
    INDIGO         = "#818CF8"
    INDIGO_DARK    = "#6366F1"
    PINK           = "#EC4899"
    EMERALD        = "#10B981"
    GREEN          = "#2ECD70"
    PURPLE_LIGHT   = "#C084FC"
    RED_SOLID      = "#E03131"
    RED            = "#EF4444"
    RED_PRESSED    = "#C92A2A"
    GREEN_SOLID    = "#15803D"
    GREEN_HOVER    = "#166534"
    GREEN_PRESSED  = "#14532D"
    GREEN_DARK     = "#23A55A"
    RED_DARK       = "#DC2626"
    AMBER          = "#F59E0B"
    AMBER_DARK     = "#D97706"
    BLUE           = "#3B82F6"
    BLUE_DARK      = "#2563EB"
    PURPLE         = "#A855F7"
    PURPLE_DARK    = "#9333EA"
    ORANGE         = "#FF6B35"
    ORANGE_DARK    = "#E0481D"
    ORANGE_HOVER   = "#FF7E47"
    KICK_BORDER    = "#1A7A42"
    TIKTOK_ACCENT  = "#FF0050"
    TIKTOK_PRESSED = "#00747C"
    KICK           = "#53FC18"
    KICK_REWARDS   = "#00E701"
    TWITCH         = "#9146FF"
    TWITCH_DARK    = "#772CE8"
    TWITCH_LIGHT   = "#A970FF"
    YOUTUBE        = "#FF0000"
    YOUTUBE_DARK   = "#CC0000"
    TIKTOK         = "#00F2FE"
    TIKTOK_DARK    = "#00B8C4"
    PURPLE_500     = "#8B5CF6"
    PURPLE_600     = "#7C3AED"
    INDIGO_600     = "#4F46E5"
    PINK_600       = "#DB2777"
    RED_600        = "#E11D48"
    ORANGE_500     = "#F97316"
    AMBER_600      = "#CA8A04"
    GREEN_600      = "#059669"
    CYAN_500       = "#06B6D4"
    CYAN_600       = "#0891B2"
    GREEN_700      = "#188546"
    GREEN_800      = "#146133"
    GREEN_900      = "#0F4F29"

class MusicTheme:
    MUSIC_VINYL_BG_TOP    = "#3E5238"
    MUSIC_VINYL_BG_BOTTOM = "#243129"
    MUSIC_VINYL_ACCENT    = "#A7BD89"
    MUSIC_CARD_LIGHT      = "#F4E9D7"
    MUSIC_CARD_BORDER     = "#B29B8E"
    MUSIC_CARD_ACCENT     = "#76515E"
    MUSIC_CARD_TEXT       = "#35272B"
    MUSIC_CARD_TEXT_SUB   = "#503D41"
    MUSIC_ART_ACCENT      = "#F43F5E"
    MUSIC_VINYL_BLACK     = "#111114"
    MUSIC_VINYL_HOLE      = "#09090B"
    MUSIC_METAL_DARK      = "#1F2937"
    MUSIC_TONEARM         = "#D1D5DB"
    MUSIC_HEAD_BORDER     = "#374151"
    MUSIC_HEAD_BG         = "#111827"
    MUSIC_GROOVE          = "#303038"

class AlertTheme:
    ALERT_PREVIEW_BG        = "#121317"
    ALERT_PREVIEW_TILE_A    = "#11141C"
    ALERT_PREVIEW_TILE_B    = "#0B0D13"
    ALERT_PREVIEW_BORDER    = "#1F242F"
    ALERT_PREVIEW_MEDIA     = "#12161E"
    ALERT_PREVIEW_MEDIA_TOP = "#222632"

class ChatTheme:
    CHAT_PREVIEW_SURFACE = "#12121A"
    AVATAR_GRADIENTS     = (
        (BrandColors.INDIGO_DARK, BrandColors.INDIGO_600), (BrandColors.PURPLE_500, BrandColors.PURPLE_600),
        (BrandColors.PINK, BrandColors.PINK_600), (MusicTheme.MUSIC_ART_ACCENT, BrandColors.RED_600),
        (BrandColors.ORANGE_500, BrandColors.ORANGE_DARK), (BrandColors.AMBER, BrandColors.AMBER_600),
        (BrandColors.EMERALD, BrandColors.GREEN_600), (BrandColors.CYAN_500, BrandColors.CYAN_600),
    )

class BadgeTheme:
    BADGE_STR = "#E64747"
    BADGE_MOD = "#3EC669"
    BADGE_VIP = "#E08338"
    BADGE_SUB = "#389CE0"
    BADGE_BCG = "#29315A"

class SwitchTheme:
    SWITCH_TRACK_ON_0  = "#1E8E4D"
    SWITCH_TRACK_ON_1  = "#15733C"
    SWITCH_TRACK_DIS_0 = "#201E25"
    SWITCH_TRACK_DIS_1 = "#2A2830"
    SWITCH_THUMB_OFF_0 = "#6E6C78"
    SWITCH_THUMB_OFF_1 = "#504E58"
    SWITCH_THUMB_ON_1  = "#E4E3EA"
    SWITCH_THUMB_DIS_0 = "#D4D2DC"
    SWITCH_THUMB_DIS_1 = "#9D9AA8"

class Radius:
    RAD_XXS = 2
    RAD_XSM = 6
    RAD_MED = 8
    RAD_LRG = 12
    RAD_XLG = 16
    RAD_FUL = 24

class Margin:
    MRG_NON = (0, 0, 0, 0)
    MRG_XXS = (2, 2, 2, 2)
    MRG_XSM = (6, 6, 6, 6)
    MRG_MED = (8, 8, 8, 8)
    MRG_LRG = (12, 12, 12, 12)
    MRG_XLG = (16, 16, 16, 16)

    MRG_HXS = (2, 0, 2, 0)
    MRG_HSM = (6, 0, 6, 0)

    MRG_VXS = (0, 2, 0, 2)
    MRG_VSM = (0, 6, 0, 6)

    SEC_HDR = (2, 12, 2, 4)
    SEC_BDG = (4, 4, 8, 4)

class Padding: 
    PAD_COMP  = "2px 6px"
    FLAT_MIN  = "2px 8px"

    PAD_TINY  = "4px 4px"
    PAD_BASE  = "4px 6px"
    PAD_TGHT  = "4px 8px"
    PAD_LIST  = "4px 10px"
    ASYM_ONE  = "4px 20px 4px 10px"

    PAD_CORE  = "6px 10px"
    PAD_WIDE  = "6px 14px"
    PAD_CMBO  = "6px 28px 6px 14px"
    
    PAD_CALL  = "10px 14px"   

class Typography:
    FONT_FAMILY = "'Google Sans', 'Inter', -apple-system"

class Size:
    Radius     = Radius
    Margin     = Margin
    Padding    = Padding
    Typography = Typography
    SPACING_NN  = 0
    SPACING_XS  = 2
    SPACING_XXS = 4
    SPACING_SM  = 6
    SPACING_MD  = 8
    SPACING_LG  = 12
    SPACING_XL  = 16
    ICON_BASIC = 32
    ICON_SMALL = 24
    ICON_ACTION = 28
    BADGE_MIN  = 18
    BADGE_MAX  = 22

def get_border(color: str, width: float = 1.2, style: str = "solid") -> str:
    return f"{width:g}px {style} {color}"

class Borders:
    BRD_BASE = get_border(Semantic.NEUTRAL_750)
    BRD_SOFT = get_border(Semantic.NEUTRAL_900)
    BRD_MUTE = get_border(Semantic.NEUTRAL_700)
    BRD_NONE = get_border("transparent")
    BRD_THIN = get_border("transparent", 1)
    BRD_HOVR = get_border(Semantic.BORDER_HOVER, 1)
    GRN_THIN = get_border(BrandColors.GREEN, 1)
    GRN_MEDM = get_border(BrandColors.GREEN, 1.5)
    BRD_LITE = get_border(Semantic.BORDER_LIGHT)
    BRD_KICK = get_border(BrandColors.KICK_BORDER)
    PRP_MEDM = get_border(BrandColors.PURPLE, 1.5)
    BRD_FOCS = get_border(BrandColors.GREEN)
    BRD_FAIL = get_border(BrandColors.RED)
    BRD_SHIN = get_border(Semantic.BORDER_TOP_SHINE)

class Gradients:
    ACCENT_FILL    = (
        f"qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, "
        f"stop:0 {SwitchTheme.SWITCH_TRACK_ON_0}, stop:1 {SwitchTheme.SWITCH_TRACK_ON_1})"
    )
    ACCENT_HOVER   = (
        f"qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, "
        f"stop:0 {BrandColors.GREEN_DARK}, stop:1 {BrandColors.GREEN_700})"
    )
    ACCENT_PRESSED = (
        f"qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, "
        f"stop:0 {BrandColors.GREEN_800}, stop:1 {BrandColors.GREEN_900})"
    )

def rgba(color_hex: str, alpha: float) -> str:
    h = color_hex.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha:g})"

def get_qcolor_with_alpha(color_hex: str, alpha: int) -> QColor:
    color = QColor(color_hex)
    color.setAlpha(alpha)
    return color

_QSS_ICON_CACHE_DIR = Path(tempfile.gettempdir()) / "minikick_qss_icons"

@lru_cache(maxsize=128)
def get_qss_colored_icon(icon_name_or_rel_path: str, color_hex: str = Palette.NEUTRAL_400) -> str:
    clean_name = os.path.basename(icon_name_or_rel_path)
    orig_path = resolve_icon_path(clean_name)
    if not orig_path or not os.path.exists(orig_path):
        orig_path = get_assets_path(icon_name_or_rel_path)
        if not os.path.exists(orig_path):
            return ""

    try:
        _QSS_ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        clean_hex = color_hex.lstrip("#")
        stem = Path(clean_name).stem
        cached_file = _QSS_ICON_CACHE_DIR / f"{stem}_{clean_hex}.svg"

        if not cached_file.exists():
            with open(orig_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            content = content.replace("currentColor", color_hex)
            content = re.sub(r'stroke=["\'](?!none)[^"\']+["\']', f'stroke="{color_hex}"', content)
            content = re.sub(r'fill=["\'](?!none)[^"\']+["\']', f'fill="{color_hex}"', content)

            with open(cached_file, "w", encoding="utf-8") as f:
                f.write(content)

        return str(cached_file).replace('\\', '/')
    except Exception:
        return get_assets_path(icon_name_or_rel_path).replace('\\', '/')

def _get_qss_icon_url(relative_path: str) -> str:
    return get_assets_path(relative_path).replace('\\', '/')

PATH_ICON_HELP          = get_qss_colored_icon("icons/circle-info-filled.svg"   ,Palette.NEUTRAL_050)
PATH_ICON_CHEVRON_DW    = get_qss_colored_icon("icons/chevron-down-filled.svg"  ,Palette.NEUTRAL_400)
PATH_ICON_CHEVRON_UP    = get_qss_colored_icon("icons/chevron-up-filled.svg"    ,Palette.NEUTRAL_400)
PATH_ICON_CHEVRON_LF    = get_qss_colored_icon("icons/chevron-left-filled.svg"  ,Palette.NEUTRAL_400)
PATH_ICON_CHEVRON_RT    = get_qss_colored_icon("icons/chevron-right-filled.svg" ,Palette.NEUTRAL_400)
PATH_ICON_CALENDAR      = get_qss_colored_icon("icons/calendar-days-filled.svg" ,Palette.NEUTRAL_400)
PATH_ICON_CHECK_GREEN   = get_qss_colored_icon("icons/check-filled.svg"         ,BrandColors.GREEN)
PATH_ICON_CHECK         = _get_qss_icon_url("icons/check-filled.svg")
PATH_ICON_MINUS         = _get_qss_icon_url("icons/minus-filled.svg")
PATH_ICON_RADIO_DOT     = _get_qss_icon_url("icons/radio-dot.svg")


def _build_reset_and_typography_qss(h1: int, h2: int, h3: int, text1: int, text2: int) -> str:
    return f"""
/* --- 1. Reset & Root Surfaces --- */
* {{ font-family: {Size.Typography.FONT_FAMILY}; font-size: {text1}px; color: {Semantic.NEUTRAL_400}; }}
QMainWindow {{ background-color: {Semantic.NEUTRAL_950}; }}
QDialog {{ background-color: {Semantic.NEUTRAL_950}; }}
QLabel {{ background-color: transparent; }}

/* --- 2. Typography Scale --- */
QLabel[role="h1"] {{ font-size: {h1}px; font-weight: 600; color: {Semantic.NEUTRAL_050}; letter-spacing: -0.2px; }}
QLabel[role="h2"] {{ font-size: {h2}px; font-weight: 600; color: {Semantic.NEUTRAL_200}; }}
QLabel[role="h3"] {{ font-size: {h3}px; font-weight: 600; color: {Semantic.NEUTRAL_050}; }}
QLabel[role="section_header"] {{ font-size: {h3}px; font-weight: 600; color: {Semantic.NEUTRAL_050}; background: transparent; padding: {Size.SPACING_NN}px {Size.SPACING_NN}px {Size.SPACING_XS}px {Size.SPACING_NN}px; }}
QLabel[role="sidebar_section_header"] {{ font-size: 11px; font-weight: 600; color: {Semantic.NEUTRAL_400}; padding: {Size.SPACING_SM}px {Size.SPACING_MD}px {Size.SPACING_XS}px {Size.SPACING_MD}px; letter-spacing: 0.5px; background: transparent; }}
QLabel[role="profile_name"] {{ font-size: {text1}px; font-weight: 600; color: {Semantic.NEUTRAL_050}; background: transparent; }}
QLabel[role="profile_role"] {{ font-size: {text2}px; font-weight: 400; color: {Semantic.NEUTRAL_400}; background: transparent; }}
QLabel[role="body"]     {{ font-size: {text1}px; font-weight: 400; color: {Semantic.NEUTRAL_400}; }}
QLabel[role="caption"]  {{ font-size: {text2}px; font-weight: 400; color: {Semantic.NEUTRAL_400}; }}
QLabel[role="monospace"]{{ font-size: {text2}px; color: {Semantic.NEUTRAL_400}; }}
QLabel[state="normal"]  {{ color: {Semantic.NEUTRAL_400}; }}
QLabel[state="white"]   {{ color: {Semantic.NEUTRAL_050}; }}
QLabel[state="error"]   {{ color: {BrandColors.RED}; }}
QLabel[state="success"] {{ color: {BrandColors.GREEN}; }}
QLabel[state="info"]    {{ color: {BrandColors.BLUE}; }}
QLabel[state="warning"] {{ color: {BrandColors.AMBER}; }}
QLabel[state="bold"]    {{ font-weight: 600; }}
"""

ROW_ACTION_COLORS = {
    "row_action":        Palette.NEUTRAL_200,
    "row_action_accent": BrandColors.GREEN,
    "row_action_danger": BrandColors.RED,
}

def _tonal_role_qss(role: str, color: str) -> str:
    sel = f'QPushButton[role="{role}"]'
    return (
        f"{sel}           {{ background-color: {rgba(color, 0.14)}; border: 1px solid {rgba(color, 0.30)}; }}\n"
        f"{sel}:focus     {{ background-color: {rgba(color, 0.26)}; border: 1px solid {rgba(color, 0.80)}; }}\n"
        f"{sel}:hover     {{ background-color: {rgba(color, 0.26)}; border-color: {rgba(color, 0.55)}; }}\n"
        f"{sel}:pressed   {{ background-color: {rgba(color, 0.36)}; }}\n"
        f"{sel}:disabled  {{ background-color: {Semantic.WHITE_GLOW}; border: {Borders.BRD_SOFT}; }}\n"
    )

_ROW_ACTION_QSS = "".join(_tonal_role_qss(role, color) for role, color in ROW_ACTION_COLORS.items())

def _build_button_qss(text1: int) -> str:
    return f"""
/* --- 3. Flat Buttons --- */
QPushButton                     {{ background-color: transparent; color: {Semantic.NEUTRAL_000}; border: {Borders.BRD_THIN}; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.PAD_BASE}; font-size: {text1}px; font-weight: 500; outline: none; }}
QPushButton[icon_only="true"]   {{ padding: {Size.SPACING_NN}px; }}
QPushButton:focus               {{ border: {Borders.BRD_FOCS}; background-color: {Semantic.NEUTRAL_950}; outline: none; }}
QPushButton:default             {{ border-color: transparent; outline: none; }}

/* Neutral Action */
QPushButton[role="action_outlined"]         {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_000}; border: {Borders.BRD_BASE}; }}
QPushButton[role="action_outlined"]:hover   {{ background-color: {Semantic.NEUTRAL_750}; border-color: {Semantic.BORDER_HOVER}; }}
QPushButton[role="action_outlined"]:pressed {{ background-color: {Semantic.SURFACE_900}; border-color: {Semantic.NEUTRAL_750}; }}
QPushButton[role="action_outlined"]:focus   {{ border: {Borders.BRD_FOCS}; background-color: {Semantic.NEUTRAL_750}; outline: none; }}

/* Destructive Action */
QPushButton[role="action_danger_solid"]         {{ background-color: {BrandColors.RED_DARK}; color: {Semantic.NEUTRAL_000}; border-color: {BrandColors.RED_DARK}; font-weight: 600; }}
QPushButton[role="action_danger_solid"]:hover   {{ background-color: {BrandColors.RED_PRESSED}; border-color: {BrandColors.RED_PRESSED}; }}
QPushButton[role="action_danger_solid"]:pressed {{ background-color: {BrandColors.RED_SOLID}; border-color: {BrandColors.RED_SOLID}; }}
QPushButton[role="action_danger_solid"]:focus   {{ border: 1.5px solid {Semantic.NEUTRAL_050}; outline: none; }}

/* Primary Action */
QPushButton[role="action_accent_solid"]             {{ background-color: {BrandColors.GREEN_SOLID}; color: {Semantic.NEUTRAL_000}; border-color: {BrandColors.GREEN_SOLID}; font-weight: 600; }}
QPushButton[role="action_accent_solid"]:hover       {{ background-color: {BrandColors.GREEN_HOVER}; border-color: {BrandColors.GREEN_HOVER}; }}
QPushButton[role="action_accent_solid"]:pressed     {{ background-color: {BrandColors.GREEN_PRESSED}; border-color: {BrandColors.GREEN_PRESSED}; }}
QPushButton[role="action_accent_solid"]:focus       {{ border: 1.5px solid {Semantic.NEUTRAL_050}; outline: none; }}

QPushButton[role="action_danger_solid"]:disabled, QPushButton[role="action_accent_solid"]:disabled {{ background-color: {Semantic.WHITE_GLOW}; color: {Semantic.NEUTRAL_500}; border: {Borders.BRD_SOFT}; }}

/* Row actions: tonal buttons for table cells */
{_ROW_ACTION_QSS}
/* Platform actions use their brand color without gradients or bevels. */
QPushButton[role="action_kick"]             {{ background-color: {BrandColors.GREEN_SOLID}; color: {Semantic.NEUTRAL_000}; border-color: {BrandColors.GREEN_SOLID}; }}
QPushButton[role="action_kick"]:hover       {{ background-color: {BrandColors.GREEN_HOVER}; border-color: {BrandColors.GREEN_HOVER}; }}
QPushButton[role="action_kick"]:pressed     {{ background-color: {BrandColors.GREEN_PRESSED}; border-color: {BrandColors.GREEN_PRESSED}; }}
QPushButton[role="action_twitch"]           {{ background-color: {BrandColors.TWITCH_DARK}; color: {Semantic.NEUTRAL_000}; border-color: {BrandColors.TWITCH_DARK}; }}
QPushButton[role="action_twitch"]:hover     {{ background-color: {BrandColors.TWITCH}; border-color: {BrandColors.TWITCH}; }}
QPushButton[role="action_twitch"]:pressed   {{ background-color: {BrandColors.PURPLE_DARK}; border-color: {BrandColors.PURPLE_DARK}; }}
QPushButton[role="action_youtube"]          {{ background-color: {BrandColors.YOUTUBE_DARK}; color: {Semantic.NEUTRAL_000}; border-color: {BrandColors.YOUTUBE_DARK}; }}
QPushButton[role="action_youtube"]:hover    {{ background-color: {BrandColors.RED_DARK}; border-color: {BrandColors.RED_DARK}; }}
QPushButton[role="action_youtube"]:pressed  {{ background-color: {BrandColors.RED_PRESSED}; border-color: {BrandColors.RED_PRESSED}; }}
QPushButton[role="action_tiktok"]           {{ background-color: {BrandColors.TIKTOK_DARK}; color: {Semantic.NEUTRAL_999}; border-color: {BrandColors.TIKTOK_DARK}; }}
QPushButton[role="action_tiktok"]:hover     {{ background-color: {BrandColors.TIKTOK}; border-color: {BrandColors.TIKTOK}; }}
QPushButton[role="action_tiktok"]:pressed   {{ background-color: {BrandColors.TIKTOK_PRESSED}; color: {Semantic.NEUTRAL_000}; border-color: {BrandColors.TIKTOK_PRESSED}; }}

QPushButton[role="action_kick"]:focus, QPushButton[role="action_twitch"]:focus, QPushButton[role="action_youtube"]:focus, QPushButton[role="action_tiktok"]:focus {{ border-color: transparent; }}

/* Utility and navigation buttons */
QPushButton[role="btn_ghost"], QPushButton[role="btn_dismiss"] {{ background-color: transparent; border-color: transparent; border-radius: {Size.Radius.RAD_XSM}px; padding: {Size.Padding.PAD_COMP}; }}
QPushButton[role="btn_ghost"]:hover, QPushButton[role="btn_dismiss"]:hover {{ background-color: {Semantic.NEUTRAL_750}; }}
QPushButton[role="btn_ghost"]:pressed, QPushButton[role="btn_dismiss"]:pressed {{ background-color: {Semantic.SURFACE_900}; }}
QPushButton[role="btn_ghost"]:focus, QPushButton[role="btn_dismiss"]:focus {{ border-color: transparent; }}
QPushButton[icon_only="true"][role="btn_ghost"], QPushButton[icon_only="true"][role="btn_dismiss"] {{ padding: {Size.SPACING_NN}px; }}

QPushButton[role="nav_button"]                      {{ background-color: transparent; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.SPACING_MD}px {Size.SPACING_LG}px; text-align: left; color: {Semantic.NEUTRAL_400}; font-size: {text1}px; font-weight: 500; border: {Borders.BRD_THIN}; }}
QPushButton[role="nav_button"]:hover                {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_000}; }}
QPushButton[role="nav_button"]:focus                {{ border-color: transparent; }}
QPushButton[role="nav_button"]:pressed              {{ background-color: {Semantic.SURFACE_900}; }}
QPushButton[role="nav_button"]:checked              {{ background-color: {Semantic.NEUTRAL_750}; color: {Semantic.NEUTRAL_000}; font-weight: 600; }}
QPushButton[role="nav_button"]:checked:hover        {{ background-color: {Semantic.NEUTRAL_750}; color: {Semantic.NEUTRAL_000}; }}
QPushButton[role="nav_button"]:checked:pressed      {{ background-color: {Semantic.SURFACE_900}; }}
QPushButton[role="nav_button"][collapsed="false"]   {{ text-align: left; padding-left: {Size.SPACING_LG}px; }}
QPushButton[role="nav_button"][collapsed="true"]    {{ text-align: center; padding: {Size.SPACING_NN}px; }}
QPushButton[icon_only="true"][role="nav_button"]    {{ padding: {Size.SPACING_NN}px; }}

/* Global Disabled Button States */
QPushButton:disabled, QPushButton[role="action_outlined"]:disabled, QPushButton[role="action_danger_solid"]:disabled, QPushButton[role="action_accent_solid"]:disabled, QPushButton[role="btn_ghost"]:disabled, QPushButton[role="btn_dismiss"]:disabled, QPushButton[role="nav_button"]:disabled {{ background-color: {Semantic.WHITE_GLOW}; color: {Semantic.NEUTRAL_500}; border: {Borders.BRD_SOFT}; padding: {Size.Padding.PAD_WIDE}; }}
QPushButton[icon_only="true"]:disabled {{ padding: {Size.SPACING_NN}px; }}
"""

def _build_input_qss(text1: int, text2: int) -> str:
    return f"""
/* Form Controls & Inputs */
QLineEdit, QTextEdit, QPlainTextEdit {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_200}; font-weight: 400; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.PAD_CORE}; border: {Borders.BRD_BASE}; }}
QTextEdit, QPlainTextEdit {{ background-color: {Semantic.NEUTRAL_950}; }}
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{ border-color: {Semantic.NEUTRAL_700}; }}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border: {Borders.BRD_FOCS}; background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_050}; }}
QLineEdit:read-only, QTextEdit:read-only, QPlainTextEdit:read-only {{ background-color: {Semantic.NEUTRAL_950}; color: {Semantic.NEUTRAL_400}; border: {Borders.BRD_SOFT}; }}
QLineEdit:read-only:focus, QTextEdit:read-only:focus, QPlainTextEdit:read-only:focus {{ border: {Borders.BRD_SOFT}; background-color: {Semantic.NEUTRAL_950}; }}
QLineEdit[state="error"], QTextEdit[state="error"], QPlainTextEdit[state="error"] {{ border: {Borders.BRD_FAIL}; }}
QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled {{ background-color: {Semantic.WHITE_GLOW}; color: {Semantic.NEUTRAL_500}; border-color: {Semantic.NEUTRAL_750}; padding: {Size.Padding.PAD_CORE}; }}
QLineEdit[state="plugin"], QTextEdit[state="plugin"], QPlainTextEdit[state="plugin"] {{ border: 1.2px solid {BrandColors.PURPLE}; color: {BrandColors.PURPLE}; font-weight: 500; background-color: {Semantic.NEUTRAL_950}; }}
QTextEdit[role="ConsoleDisplay"] {{ font-family: 'GoogleSansCode Nerd Font'; background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_200}; border: {Borders.BRD_SOFT}; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.SPACING_XS}px {Size.SPACING_XXS}px; }}

/* ComboBox */
QComboBox                           {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_050}; font-size: {text1}px; font-weight: 500; border: {Borders.BRD_BASE}; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.PAD_CMBO}; combobox-popup: 0; min-width: 120px; }}
QComboBox:hover                     {{ background-color: {Semantic.NEUTRAL_750}; border: {Borders.BRD_HOVR}; color: {Semantic.NEUTRAL_000}; }}
QComboBox:focus                     {{ border: {Borders.GRN_THIN}; }}
QComboBox:pressed                   {{ background-color: {Semantic.SURFACE_900}; border: 1px solid {Semantic.NEUTRAL_750}; }}
QComboBox:on, QComboBox[state="active"], QComboBox[state="active"]:hover, QComboBox[state="active"]:focus {{ background-color: {Semantic.NEUTRAL_750}; border: {Borders.GRN_THIN}; color: {Semantic.NEUTRAL_000}; }}
QComboBox::drop-down                {{ subcontrol-origin: padding; subcontrol-position: center right; width: 24px; border-top-right-radius: {Size.Radius.RAD_MED}px; border-bottom-right-radius: {Size.Radius.RAD_MED}px; }}
QComboBox::drop-down:hover, QComboBox::drop-down:focus {{ background-color: transparent; border-color: transparent; }}
QComboBox::drop-down:disabled       {{ border-color: transparent; }}
QComboBox::down-arrow               {{ image: url("{PATH_ICON_CHEVRON_DW}"); width: 16px; height: 16px; }}
QComboBox::down-arrow:on, QComboBox[state="active"]::down-arrow {{ image: url("{PATH_ICON_CHEVRON_UP}"); }}
QComboBox:disabled::down-arrow      {{ opacity: 0.4; }}
QComboBox QAbstractItemView         {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_200}; font-size: {text1}px; border: 1px solid {Semantic.NEUTRAL_700}; border-radius: {Size.Radius.RAD_MED}px; selection-background-color: {Semantic.NEUTRAL_750}; selection-color: {Semantic.NEUTRAL_050}; padding: {Size.Padding.PAD_TINY}; outline: none; }}
QComboBox QAbstractItemView::item   {{ font-size: {text1}px; border-radius: {Size.Radius.RAD_XSM}px; padding: {Size.Padding.PAD_BASE}; margin: 1px 2px; }}
QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:focus, QComboBox QListView::item:selected, QComboBox QListView::item:hover {{ background-color: {Semantic.NEUTRAL_750}; color: {Semantic.NEUTRAL_050}; border: none; }}

/* Searchable ComboBox Popup */
QFrame[role="searchable_combo_popup"] {{ background-color: {Semantic.NEUTRAL_900}; border: {Borders.BRD_SHIN}; border-radius: {Size.Radius.RAD_MED}px; }}
QFrame[role="searchable_combo_search_bar"] {{ background-color: {Semantic.NEUTRAL_900}; border: {Borders.BRD_BASE}; border-radius: {Size.Radius.RAD_MED}px; }}
QLineEdit[role="searchable_combo_input"] {{ background-color: {Semantic.NEUTRAL_900}; border: none; color: {Semantic.NEUTRAL_050}; font-size: {text1}px; font-weight: 400; padding: {Size.SPACING_NN}px {Size.SPACING_XXS}px; }}
QLineEdit[role="searchable_combo_input"]:focus {{ border: none; background-color: transparent; }}
QListWidget[role="searchable_combo_list"] {{ background-color: {Semantic.NEUTRAL_900}; border: none; outline: none; }}
QListWidget[role="searchable_combo_list"]::item {{ color: {Semantic.NEUTRAL_200}; font-size: {text1}px; font-weight: 400; padding: {Size.Padding.PAD_CORE}; border-radius: {Size.Radius.RAD_XSM}px; border: none; outline: none; }}
QListWidget[role="searchable_combo_list"]::item:hover, QListWidget[role="searchable_combo_list"]::item:selected {{ background-color: {Semantic.NEUTRAL_750}; color: {Semantic.NEUTRAL_050}; border: none; outline: none; }}
QListWidget[role="searchable_combo_list"] QScrollBar:vertical {{ background: {Semantic.NEUTRAL_900}; width: 10px; margin: 4px 2px 4px 0px; border-radius: {Size.Radius.RAD_XXS}px; }}
QListWidget[role="searchable_combo_list"] QScrollBar::handle:vertical {{ background: {Semantic.NEUTRAL_700}; min-height: 20px; border-radius: {Size.Radius.RAD_XXS}px; }}
QListWidget[role="searchable_combo_list"] QScrollBar::handle:vertical:hover {{ background: {Semantic.NEUTRAL_900}; }}
QListWidget[role="searchable_combo_list"] QScrollBar::add-line:vertical, QListWidget[role="searchable_combo_list"] QScrollBar::sub-line:vertical {{ height: 0px; background: none; }}
QLabel[role="searchable_combo_empty"] {{ color: {Semantic.NEUTRAL_500}; font-size: {text2}px; padding: {Size.SPACING_XL}px {Size.SPACING_MD}px; }}

/* Context Menus */
QMenu {{ background-color: {Semantic.NEUTRAL_950}; color: {Semantic.NEUTRAL_200}; border: {Borders.BRD_SHIN}; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.PAD_TINY}; }}
QMenu::item {{ padding: {Size.Padding.PAD_LIST}; margin: 1px 2px; border-radius: {Size.Radius.RAD_XSM}px; color: {Semantic.NEUTRAL_200}; font-size: {text2}px; font-weight: 500; }}
QMenu::item:disabled {{ color: {Semantic.NEUTRAL_500}; background-color: transparent; }}
QMenu::item:selected {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_050}; border: 1.2px solid {Semantic.BORDER_SUBTLE_GHOST}; }}
QMenu::item:pressed {{ background-color: {Semantic.NEUTRAL_750}; }}
QMenu::icon {{ margin-left: 14px; }}
QMenu::indicator {{ width: 16px; height: 16px; left: 8px; }}
QMenu::indicator:checked {{ image: url("{PATH_ICON_CHECK_GREEN}"); }}
QMenu::indicator:unchecked {{ image: none; }}
QMenu::separator {{ height: 1px; background-color: {Semantic.NEUTRAL_900}; margin: 1px 2px; }}

/* SpinBoxes */
QSpinBox, QDoubleSpinBox, QTimeEdit {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_200}; font-weight: 400; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.ASYM_ONE}; border: {Borders.BRD_BASE}; selection-background-color: transparent; selection-color: {Semantic.NEUTRAL_050}; }}
QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {{ border: {Borders.BRD_FOCS}; background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_050}; }}
QSpinBox:hover, QDoubleSpinBox:hover, QTimeEdit:hover {{ background-color: {Semantic.NEUTRAL_900}; border-color: {Semantic.NEUTRAL_700}; }}
QSpinBox:read-only, QDoubleSpinBox:read-only, QTimeEdit:read-only {{ background-color: {Semantic.NEUTRAL_950}; color: {Semantic.NEUTRAL_400}; border: {Borders.BRD_SOFT}; }}
QSpinBox::up-button, QDoubleSpinBox::up-button, QTimeEdit::up-button {{ subcontrol-origin: border; subcontrol-position: center right; width: 24px; height: 24px; right: 26px; border: none; background-color: transparent; }}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QTimeEdit::up-button:hover {{ background-color: {Semantic.NEUTRAL_750}; border-radius: {Size.Radius.RAD_XSM}px; }}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed, QTimeEdit::up-button:pressed {{ background-color: {Semantic.NEUTRAL_700}; }}
QSpinBox::up-button:disabled, QDoubleSpinBox::up-button:disabled, QTimeEdit::up-button:disabled {{ background-color: transparent; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow, QTimeEdit::up-arrow {{ image: url("{PATH_ICON_CHEVRON_UP}"); width: 16px; height: 16px; }}
QSpinBox::down-button, QDoubleSpinBox::down-button, QTimeEdit::down-button {{ subcontrol-origin: border; subcontrol-position: center right; width: 24px; height: 24px; right: 4px; border: none; background-color: transparent; }}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover, QTimeEdit::down-button:hover {{ background-color: {Semantic.NEUTRAL_750}; border-radius: {Size.Radius.RAD_XSM}px; }}
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed, QTimeEdit::down-button:pressed {{ background-color: {Semantic.NEUTRAL_700}; }}
QSpinBox::down-button:disabled, QDoubleSpinBox::down-button:disabled, QTimeEdit::down-button:disabled {{ background-color: transparent; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow, QTimeEdit::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DW}"); width: 16px; height: 16px; }}
QSpinBox:disabled, QDoubleSpinBox:disabled, QTimeEdit:disabled, QDateEdit:disabled {{ background-color: {Semantic.WHITE_GLOW}; color: {Semantic.NEUTRAL_500}; border-color: {Semantic.NEUTRAL_750}; padding: {Size.Padding.ASYM_ONE}; }}

/* DateEdit */
QDateEdit {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_200}; font-weight: 400; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.ASYM_ONE}; border: {Borders.BRD_BASE}; selection-background-color: transparent; selection-color: {Semantic.NEUTRAL_050}; }}
QDateEdit:focus {{ border: {Borders.BRD_FOCS}; background-color: {Semantic.NEUTRAL_900}; }}
QDateEdit:hover {{ background-color: {Semantic.NEUTRAL_900}; }}
QDateEdit:read-only {{ background-color: {Semantic.NEUTRAL_950}; color: {Semantic.NEUTRAL_400}; border: {Borders.BRD_SOFT}; }}
QDateEdit::up-button, QDateEdit::down-button {{ width: 0px; height: 0px; border: none; background: transparent; }}
QDateEdit::up-arrow, QDateEdit::down-arrow {{ image: none; width: 0px; height: 0px; }}
QDateEdit::drop-down {{ subcontrol-origin: border; subcontrol-position: center right; width: 24px; height: 24px; right: 4px; border: none; background-color: transparent; }}
QDateEdit::drop-down:hover {{ background-color: {Semantic.NEUTRAL_750}; border-radius: {Size.Radius.RAD_XSM}px; }}
QDateEdit::drop-down:pressed {{ background-color: {Semantic.NEUTRAL_700}; border-radius: {Size.Radius.RAD_XSM}px; }}
QDateEdit::down-arrow {{ image: url("{PATH_ICON_CALENDAR}"); width: 16px; height: 16px; }}

/* CheckBox */
QCheckBox {{ spacing: 8px; color: {Semantic.NEUTRAL_400}; background-color: transparent; }}
QCheckBox:hover {{ color: {Semantic.NEUTRAL_050}; }}
QCheckBox:focus {{ color: {Semantic.NEUTRAL_050}; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: {Size.Radius.RAD_XSM}px; border: {Borders.BRD_SHIN}; background-color: {Semantic.NEUTRAL_900}; }}
QCheckBox::indicator:focus, QCheckBox:focus::indicator {{ border-color: {BrandColors.GREEN}; }}
QCheckBox::indicator:unchecked:hover {{ border-color: {Semantic.NEUTRAL_700}; background-color: {Semantic.NEUTRAL_900}; }}
QCheckBox::indicator:unchecked:pressed {{ background-color: {Semantic.NEUTRAL_700}; }}
QCheckBox::indicator:checked {{ border: {Borders.BRD_KICK}; background-color: {Gradients.ACCENT_FILL}; image: url("{PATH_ICON_CHECK}"); }}
QCheckBox::indicator:checked:hover {{ background-color: {Gradients.ACCENT_HOVER}; }}
QCheckBox::indicator:checked:pressed {{ background-color: {Gradients.ACCENT_PRESSED}; }}
QCheckBox::indicator:indeterminate {{ border: {Borders.BRD_KICK}; background-color: {Gradients.ACCENT_FILL}; image: url("{PATH_ICON_MINUS}"); }}
QCheckBox::indicator:indeterminate:hover {{ background-color: {Gradients.ACCENT_HOVER}; }}
QCheckBox::indicator:indeterminate:pressed {{ background-color: {Gradients.ACCENT_PRESSED}; }}
QCheckBox:disabled {{ color: {Semantic.NEUTRAL_500}; }}
QCheckBox::indicator:disabled {{ border-color: {Semantic.NEUTRAL_750}; background-color: {Semantic.WHITE_GLOW}; }}
QCheckBox::indicator:checked:disabled {{ border-color: {Semantic.NEUTRAL_750}; background-color: {Semantic.WHITE_GLOW}; image: url("{PATH_ICON_CHECK}"); }}
QCheckBox::indicator:indeterminate:disabled {{ border-color: {Semantic.NEUTRAL_750}; background-color: {Semantic.WHITE_GLOW}; image: url("{PATH_ICON_MINUS}"); }}

/* RadioButton */
QRadioButton {{ spacing: 8px; color: {Semantic.NEUTRAL_400}; background-color: transparent; }}
QRadioButton:hover {{ color: {Semantic.NEUTRAL_050}; }}
QRadioButton:focus {{ color: {Semantic.NEUTRAL_050}; }}
QRadioButton::indicator {{ width: 16px; height: 16px; border-radius: {Size.Radius.RAD_MED}px; border: {Borders.BRD_SHIN}; background-color: {Semantic.NEUTRAL_900}; }}
QRadioButton::indicator:focus, QRadioButton:focus::indicator {{ border-color: {BrandColors.GREEN}; }}
QRadioButton::indicator:unchecked:hover {{ border-color: {Semantic.NEUTRAL_700}; background-color: {Semantic.NEUTRAL_900}; }}
QRadioButton::indicator:unchecked:pressed {{ background-color: {Semantic.NEUTRAL_700}; }}
QRadioButton::indicator:checked {{ border: {Borders.BRD_KICK}; background-color: {Gradients.ACCENT_FILL}; image: url("{PATH_ICON_RADIO_DOT}"); }}
QRadioButton::indicator:checked:hover {{ background-color: {Gradients.ACCENT_HOVER}; }}
QRadioButton::indicator:checked:pressed {{ background-color: {Gradients.ACCENT_PRESSED}; }}
QRadioButton:disabled {{ color: {Semantic.NEUTRAL_500}; }}
QRadioButton::indicator:disabled {{ border-color: {Semantic.NEUTRAL_750}; background-color: {Semantic.WHITE_GLOW}; }}
QRadioButton::indicator:checked:disabled {{ border-color: {Semantic.NEUTRAL_750}; background-color: {Semantic.WHITE_GLOW}; image: url("{PATH_ICON_RADIO_DOT}"); }}

/* Slider */
QSlider::groove:horizontal {{ border: none; height: 6px; background: {Semantic.NEUTRAL_900}; border-radius: {Size.Radius.RAD_XSM}px; }}
QSlider::sub-page:horizontal {{ background: {BrandColors.GREEN}; border-radius: {Size.Radius.RAD_XSM}px; }}
QSlider::handle:horizontal {{ background: {Semantic.NEUTRAL_050}; width: 16px; height: 16px; margin-top: -4px; margin-bottom: -4px; border-radius: {Size.Radius.RAD_MED}px; border: {Borders.BRD_LITE}; }}
QSlider::handle:horizontal:hover {{ background-color: {Semantic.NEUTRAL_050}; border: {Borders.BRD_FOCS}; }}
QSlider::handle:horizontal:pressed {{ background-color: {Semantic.NEUTRAL_200}; border: 1.2px solid {BrandColors.GREEN_DARK}; }}
QSlider:disabled {{ opacity: 0.5; }}
QSlider::groove:horizontal:disabled {{ background: {Semantic.NEUTRAL_750}; }}
QSlider::sub-page:horizontal:disabled {{ background: {Semantic.NEUTRAL_700}; }}
QSlider::handle:horizontal:disabled {{ background-color: {Semantic.NEUTRAL_500}; border-color: {Semantic.NEUTRAL_700}; }}
"""

def _build_surface_qss(text1: int, text2: int) -> str:
    return f"""
/* --- 5. Surfaces, Containers & Badges --- */
QFrame[role="canvas_container"] {{ background-color: {Semantic.NEUTRAL_900}; border: {Borders.BRD_BASE}; border-radius: {Size.Radius.RAD_MED}px; }}
QFrame[role="sidebar"] {{ background-color: {Semantic.NEUTRAL_950}; border-right: 1px solid {Semantic.NEUTRAL_750}; }}
QFrame[role="profile_card"] {{ background-color: transparent; border-radius: {Size.Radius.RAD_MED}px; border: {Borders.BRD_THIN}; }}
QFrame[role="profile_card"]:hover {{ background-color: {Semantic.SURFACE_900}; border: 1px solid {Semantic.NEUTRAL_750}; }}
QFrame[role="update_banner_card"] {{ background-color: {Semantic.NEUTRAL_900}; border: 1px solid {Semantic.NEUTRAL_750}; border-radius: {Size.Radius.RAD_LRG}px; }}
QFrame[role="update_banner_card"]:hover {{ border-color: {Semantic.NEUTRAL_700}; }}
QFrame[role="update_icon_box"] {{ background-color: {Semantic.GREEN_GLOW}; border: {Borders.BRD_FOCS}; border-radius: {Size.Radius.RAD_MED}px; }}
QFrame[role="card"] {{ background-color: {Semantic.NEUTRAL_950}; border: 1px solid {Semantic.NEUTRAL_750}; border-radius: {Size.Radius.RAD_XLG}px; }}
QFrame[role="dashboard_welcome"] {{ background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Semantic.SURFACE_900}, stop:1 {Semantic.NEUTRAL_950}); border: 1px solid {Semantic.NEUTRAL_750}; border-radius: {Size.Radius.RAD_XLG}px; }}
QFrame[role="dashboard_distribution_panel"] {{ background-color: {Semantic.NEUTRAL_950}; border: {Borders.BRD_BASE}; border-radius: {Size.Radius.RAD_LRG}px; }}
QLabel[role="dashboard_channel_name"] {{ color: {Semantic.NEUTRAL_050}; font-size: 16px; font-weight: 700; }}
QLabel[role="dashboard_channel_description"] {{ color: {Semantic.NEUTRAL_400}; font-size: 12px; }}
QFrame[role="dialog"] {{ background-color: {Semantic.NEUTRAL_950}; border: {Borders.BRD_BASE}; border-radius: {Size.Radius.RAD_XLG}px; }}
QFrame[role="dialog"][state="accent"] {{ border-color: {BrandColors.GREEN}; }}
QFrame[role="dialog"][state="success"] {{ border-color: {BrandColors.GREEN}; }}
QFrame[role="dialog"][state="danger"] {{ border-color: {BrandColors.RED}; }}
QFrame[role="dialog"][state="error"] {{ border-color: {BrandColors.RED}; }}
QFrame[role="dialog"][state="warning"] {{ border-color: {BrandColors.AMBER}; }}
QFrame[role="dialog"][state="info"] {{ border-color: {BrandColors.BLUE}; }}
QFrame[role="dialog"][state="neutral"] {{ border-color: {Semantic.NEUTRAL_700}; }}
QFrame[role="splash_card"] {{ background-color: transparent; border: none; }}
QWidget[role="splash_window"] {{ background-color: {Semantic.NEUTRAL_950}; }}

QFrame[role="banner_danger"]        {{ background-color: {Semantic.RED_GLOW}; border: 1.2px solid {BrandColors.RED_DARK}; border-radius: {Size.Radius.RAD_MED}px; }}
QFrame[role="banner_warning"]       {{ background-color: {Semantic.AMBER_GLOW}; border: 1.2px solid {BrandColors.AMBER_DARK}; border-radius: {Size.Radius.RAD_MED}px; }}
QFrame[role="banner_scope_card"]    {{ background-color: {Semantic.NEUTRAL_950}; border: {Borders.BRD_BASE}; border-radius: {Size.Radius.RAD_LRG}px; }}
QFrame[role="banner_scope_card"][state="kick"] {{ background-color: {Semantic.NEUTRAL_950}; border: {Borders.GRN_MEDM}; }}
QFrame[role="banner_scope_card"][state="twitch"] {{ background-color: {Semantic.NEUTRAL_950}; border: {Borders.PRP_MEDM}; }}
QFrame[role="danger_icon"]  {{ background-color: {BrandColors.RED}; border-radius: {Size.Radius.RAD_FUL}px; }}
QFrame[role="warning_icon"] {{ background-color: {BrandColors.AMBER}; border-radius: {Size.Radius.RAD_FUL}px; }}
QFrame[role="info_icon"]    {{ background-color: {BrandColors.BLUE}; border-radius: {Size.Radius.RAD_FUL}px; }}
QFrame[role="accent_icon"]  {{ background-color: {BrandColors.GREEN}; border-radius: {Size.Radius.RAD_FUL}px; }}
QFrame[role="tiktok_icon"]  {{ background-color: {BrandColors.TIKTOK}; border-radius: {Size.Radius.RAD_FUL}px; }}
QFrame[role="youtube_icon"] {{ background-color: {BrandColors.YOUTUBE}; border-radius: {Size.Radius.RAD_FUL}px; }}
QFrame[role="twitch_icon"]  {{ background-color: {BrandColors.TWITCH}; border-radius: {Size.Radius.RAD_FUL}px; }}
QFrame[role="black_icon"]   {{ background-color: {Semantic.NEUTRAL_999}; border-radius: {Size.Radius.RAD_FUL}px; }}
QFrame[role="divider"]      {{ background-color: {Semantic.NEUTRAL_750}; min-height: 1px; max-height: 1px; border: none; margin: 0px; padding: {Size.SPACING_NN}px; }}

QFrame[role="bot_tag"] {{ background-color: {Semantic.NEUTRAL_900}; border: {Borders.BRD_BASE}; border-radius: {Size.Radius.RAD_MED}px; }}
QFrame[role="bot_tag"]:hover {{ border-color: {BrandColors.RED}; }}
QFrame[role="bot_tag"] QLabel {{ color: {Semantic.NEUTRAL_400}; font-size: {text2}px; }}
QFrame[role="toast"] {{ background-color: {Semantic.NEUTRAL_950}; border: {Borders.BRD_MUTE}; border-radius: {Size.Radius.RAD_MED}px; }}
QFrame[role="toast"][state="success"] {{ border-color: {BrandColors.GREEN}; }}
QFrame[role="toast"][state="danger"] {{ border-color: {BrandColors.RED}; }}
QFrame[role="toast"][state="warning"] {{ border-color: {BrandColors.AMBER}; }}
QFrame[role="toast"][state="info"] {{ border-color: {BrandColors.BLUE}; }}

/* Badges & Tags */
QFrame[role="badge"] {{ background-color: {Semantic.NEUTRAL_900}; border: {Borders.BRD_SOFT}; border-radius: {Size.Radius.RAD_MED}px; min-height: 20px; max-height: {Size.BADGE_MAX}px; }}
QFrame[role="badge"] QLabel {{ font-size: {text2}px; font-weight: 500; color: {Semantic.NEUTRAL_400}; background: transparent; }}
QFrame[role="badge"][state="everyone"] {{ background-color: {Semantic.GREEN_GLOW}; border-color: {BrandColors.GREEN}; }}
QFrame[role="badge"][state="everyone"] QLabel {{ color: {BrandColors.GREEN}; }}
QFrame[role="badge"][state="subscriber"] {{ background-color: {Semantic.BLUE_GLOW}; border-color: {BrandColors.BLUE}; }}
QFrame[role="badge"][state="subscriber"] QLabel {{ color: {BrandColors.BLUE}; }}
QFrame[role="badge"][state="vip"] {{ background-color: {Semantic.PURPLE_GLOW}; border-color: {BrandColors.PURPLE}; }}
QFrame[role="badge"][state="vip"] QLabel {{ color: {BrandColors.PURPLE}; }}
QFrame[role="badge"][state="moderator"] {{ background-color: {Semantic.AMBER_GLOW}; border-color: {BrandColors.AMBER}; }}
QFrame[role="badge"][state="moderator"] QLabel {{ color: {BrandColors.AMBER}; }}
QFrame[role="badge"][state="broadcaster"] {{ background-color: {Semantic.RED_GLOW}; border-color: {BrandColors.RED}; }}
QFrame[role="badge"][state="broadcaster"] QLabel {{ color: {BrandColors.RED}; }}
QFrame[role="badge"][state="warning"] {{ background-color: {Semantic.AMBER_GLOW}; border-color: {BrandColors.AMBER}; }}
QFrame[role="badge"][state="warning"] QLabel {{ color: {BrandColors.AMBER}; }}
QFrame[role="badge"][state="plugin"] {{ background-color: {Semantic.PURPLE_GLOW}; border-color: {BrandColors.PURPLE}; }}
QFrame[role="badge"][state="plugin"] QLabel {{ color: {BrandColors.PURPLE}; }}
QFrame[role="badge"][state="kick"] {{ background-color: {Semantic.GREEN_GLOW}; border-color: {BrandColors.GREEN}; }}
QFrame[role="badge"][state="kick"] QLabel {{ color: {BrandColors.GREEN}; }}
QFrame[role="badge"][state="twitch"] {{ background-color: {Semantic.PURPLE_GLOW}; border-color: {BrandColors.PURPLE}; }}
QFrame[role="badge"][state="twitch"] QLabel {{ color: {BrandColors.PURPLE}; }}
QLabel[role="badge"] {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_400}; font-weight: 500; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.FLAT_MIN}; font-size: {text2}px; border: {Borders.BRD_SOFT}; min-height: {Size.BADGE_MIN}px; max-height: {Size.BADGE_MAX}px; }}
QLabel[role="badge_kick"] {{ background-color: {Semantic.GREEN_GLOW}; color: {BrandColors.GREEN}; font-weight: 500; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.FLAT_MIN}; font-size: {text2}px; border: {Borders.GRN_MEDM}; min-height: {Size.BADGE_MIN}px; max-height: {Size.BADGE_MAX}px; }}
QLabel[role="badge_twitch"] {{ background-color: {Semantic.PURPLE_GLOW}; color: {BrandColors.PURPLE}; font-weight: 500; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.FLAT_MIN}; font-size: {text2}px; border: {Borders.PRP_MEDM}; min-height: {Size.BADGE_MIN}px; max-height: {Size.BADGE_MAX}px; }}
QLabel[role="tag_badge"] {{ background-color: {Semantic.PURPLE_GLOW}; color: {BrandColors.PURPLE}; font-weight: 600; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.FLAT_MIN}; font-size: {text2}px; border: {Borders.PRP_MEDM}; min-height: {Size.BADGE_MIN}px; max-height: {Size.BADGE_MAX}px; }}
QLabel[role="rank_number"] {{ color: {BrandColors.GREEN}; font-weight: 500; min-width: 20px; }}
QLabel[role="rank_number"][state="gold"] {{ color: {BrandColors.AMBER}; font-weight: 700; font-size: 13px; }}
QLabel[role="rank_number"][state="silver"] {{ color: {Semantic.NEUTRAL_400}; font-weight: 700; font-size: 13px; }}
QLabel[role="rank_number"][state="bronze"] {{ color: {BrandColors.AMBER_DARK}; font-weight: 700; font-size: 13px; }}
QLabel[role="rank_number"][state="normal"] {{ color: {Semantic.NEUTRAL_500}; font-weight: 500; }}
QLabel[role="status_pill"] {{ border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.PAD_COMP}; font-size: 12px; font-weight: 500; }}
QLabel[role="status_pill"][state="online"] {{ background-color: {Semantic.GREEN_GLOW}; color: {BrandColors.GREEN}; border: {Borders.GRN_THIN}; font-weight: 600; }}
QLabel[role="status_pill"][state="connecting"] {{ background-color: {Semantic.AMBER_GLOW}; color: {BrandColors.AMBER}; border: 1px solid {BrandColors.AMBER}; font-weight: 600; }}
QLabel[role="status_pill"][state="offline"] {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_400}; border: {Borders.BRD_SOFT}; }}
QLabel[role="badge_new"] {{ background-color: {BrandColors.ORANGE}; color: {Semantic.NEUTRAL_000}; font-weight: 700; border-radius: {Size.Radius.RAD_MED}px; min-width: {Size.BADGE_MIN}px; max-width: {Size.BADGE_MIN}px; min-height: {Size.BADGE_MIN}px; max-height: {Size.BADGE_MIN}px; font-size: 10px; qproperty-alignment: AlignCenter; }}
QLabel[role="badge_new"][state="collapsed"] {{ border-radius: {Size.Radius.RAD_MED}px; min-width: 12px; max-width: 12px; min-height: 12px; max-height: 12px; font-size: 7px; font-weight: 800; }}
QFrame[role="whats_new_card"] {{ background-color: {Semantic.NEUTRAL_900}; border: {Borders.BRD_SOFT}; border-radius: {Size.Radius.RAD_LRG}px; }}
QFrame[role="whats_new_card"]:hover {{ background-color: {Semantic.NEUTRAL_750}; border: {Borders.BRD_BASE}; }}
QTextBrowser[role="release_notes_browser"] {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_400}; border: {Borders.BRD_SOFT}; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.SPACING_LG}px; }}

/* Table Widget */
QTableWidget {{ background-color: {Semantic.NEUTRAL_900}; border: none; gridline-color: transparent; border-bottom-left-radius: {Size.Radius.RAD_LRG}px; border-bottom-right-radius: {Size.Radius.RAD_LRG}px; }}
QTableWidget::item {{ padding: {Size.Padding.PAD_CORE}; border-bottom: {Borders.BRD_SOFT}; }}
QTableWidget::item:selected {{ background-color: {Semantic.NEUTRAL_750}; color: {Semantic.NEUTRAL_050}; }}
QTableWidget::item:disabled {{ color: {Semantic.NEUTRAL_500}; }}
QHeaderView, QHeaderView::section {{ background-color: transparent; border: none; }}
QHeaderView::section {{ color: {Semantic.NEUTRAL_400}; font-weight: 500; padding: {Size.Padding.PAD_CORE}; border-bottom: {Borders.BRD_BASE}; text-align: left; }}
QHeaderView::section:hover {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_050}; }}
QHeaderView::section:pressed {{ background-color: {Semantic.NEUTRAL_750}; }}
QWidget[role="table_no_results"] {{ background-color: {Semantic.NEUTRAL_950}; }}

/* Scrollbars */
QScrollBar:vertical                 {{ border: none; background: transparent; width: 9px; margin: 4px 1px 4px 1px; }}
QScrollBar::handle:vertical         {{ background-color: rgba(255, 255, 255, 0.16); border-radius: {Size.Radius.RAD_XXS}px; min-height: 24px; }}
QScrollBar::handle:vertical:hover   {{ background-color: rgba(255, 255, 255, 0.32); }}
QScrollBar::handle:vertical:pressed {{ background-color: rgba(255, 255, 255, 0.48); }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ height: 0px; background: none; }}

QScrollBar:horizontal                   {{ border: none; background: transparent; height: 9px; margin: 1px 4px 1px 4px; }}
QScrollBar::handle:horizontal           {{ background-color: rgba(255, 255, 255, 0.16); border-radius: {Size.Radius.RAD_XXS}px; min-width: 24px; }}
QScrollBar::handle:horizontal:hover     {{ background-color: rgba(255, 255, 255, 0.32); }}
QScrollBar::handle:horizontal:pressed   {{ background-color: rgba(255, 255, 255, 0.48); }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal, QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ width: 0px; background: none; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: transparent; border: none; }}

/* Progress Bars */
QProgressBar                                        {{ background-color: {Semantic.NEUTRAL_900}; border: {Borders.BRD_SOFT}; border-radius: {Size.Radius.RAD_XSM}px; height: 6px; text-align: center; }}
QProgressBar::chunk                                 {{ background-color: {BrandColors.GREEN}; border-radius: {Size.Radius.RAD_XSM}px; }}
QProgressBar:disabled                               {{ background-color: {Semantic.WHITE_GLOW}; border-color: {Semantic.NEUTRAL_900}; }}
QProgressBar::chunk:disabled                        {{ background-color: {Semantic.NEUTRAL_700}; }}
QProgressBar[role="update_progress"]                {{ background-color: {Semantic.NEUTRAL_950}; border: none; border-radius: {Size.Radius.RAD_XSM}px; }}
QProgressBar[role="update_progress"]::chunk         {{ background-color: {BrandColors.GREEN}; border-radius: {Size.Radius.RAD_XSM}px; }}
QProgressBar[role="wizard_progress"]                {{ background-color: {Semantic.NEUTRAL_750}; border: none; border-radius: {Size.Radius.RAD_XSM}px; }}
QProgressBar[role="wizard_progress"]::chunk         {{ background-color: {BrandColors.GREEN}; border-radius: {Size.Radius.RAD_XSM}px; }}
QProgressBar[role="top_command_progress"]           {{ background-color: {Semantic.NEUTRAL_750}; border: none; border-radius: {Size.Radius.RAD_XSM}px; height: 8px; }}
QProgressBar[role="top_command_progress"]::chunk    {{ background-color: {BrandColors.BLUE}; border-radius: {Size.Radius.RAD_XSM}px; }}
QProgressBar[role="splash_progress"]                {{ background-color: {Semantic.NEUTRAL_900}; border: none; border-radius: {Size.Radius.RAD_XXS}px; height: 4px; text-align: center; }}
QProgressBar[role="splash_progress"]::chunk         {{ background-color: {BrandColors.GREEN}; border-radius: {Size.Radius.RAD_XXS}px; }}

/* Tab Widget */
QTabWidget::pane                    {{ background-color: {Semantic.NEUTRAL_950}; border: {Borders.BRD_BASE}; border-radius: {Size.Radius.RAD_LRG}px; border-top-left-radius: 0px;  padding: {Size.SPACING_NN}px; }}
QTabBar::tab                        {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_400}; border: {Borders.BRD_BASE}; border-top-left-radius: 0px; border-top-right-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.PAD_WIDE}; margin-right: 4px; font-weight: 500; }}
QTabBar::tab:selected               {{ background-color: {Semantic.NEUTRAL_950}; color: {Semantic.NEUTRAL_050}; border-color: {Semantic.NEUTRAL_750}; }}
QTabBar::tab:hover:!selected        {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_050}; }}
QTabBar::tab:pressed:!selected      {{ background-color: {Semantic.NEUTRAL_750}; }}
QTabBar::tab:focus                  {{ border-color: {Semantic.NEUTRAL_700}; }}
QTabBar::tab:disabled               {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_500}; border-color: {Semantic.NEUTRAL_900}; }}
QTabWidget QFrame[role="tab_panel"] {{ background-color: transparent; border: none; }}

/* ToolTip */
QToolTip {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_050}; border: {Borders.BRD_MUTE}; border-radius: {Size.Radius.RAD_XSM}px; padding: {Size.Padding.PAD_CORE}; font-size: {text1}px; }}
QListWidget[role="transparent_list"] {{ background: transparent; border: none; }}
QListWidget[role="transparent_list"]::item {{ background: transparent; }}
"""

def _build_complex_qss(text1: int, text2: int) -> str:
    return f"""
/* --- 6. Complex Composite Widgets --- */

/* Search Bar */
QFrame[role="search_bar"]                       {{ background-color: {Semantic.NEUTRAL_900}; border: {Borders.BRD_BASE}; border-radius: {Size.Radius.RAD_MED}px; min-height: 32px; }}
QFrame[role="search_bar"]:hover                 {{ border-color: {Semantic.NEUTRAL_700}; }}
QFrame[role="search_bar"]:focus, QFrame[role="search_bar"][state="focused"] {{ border: {Borders.BRD_FOCS}; }}
QFrame[role="search_bar"] QLineEdit             {{ background: transparent; border: none; padding: {Size.Padding.PAD_CORE}; color: {Semantic.NEUTRAL_050}; font-size: {text1}px; }}
QFrame[role="search_bar"] QPushButton           {{ background: transparent; border: none; border-top-right-radius: {Size.Radius.RAD_MED}px; border-bottom-right-radius: {Size.Radius.RAD_MED}px; margin: 1px; padding: {Size.SPACING_NN}px; }}
QFrame[role="search_bar"] QPushButton:hover     {{ background-color: {Semantic.NEUTRAL_900}; }}
QFrame[role="search_bar"] QPushButton:focus     {{ background-color: {Semantic.NEUTRAL_750}; }}
QFrame[role="search_bar"] QPushButton:pressed   {{ background-color: {Semantic.NEUTRAL_700}; }}

/* Category Dropdown */
QFrame[role="category_dropdown"] {{ background-color: {Semantic.NEUTRAL_900}; border: {Borders.BRD_MUTE}; border-radius: {Size.Radius.RAD_MED}px; }}
QListWidget[role="category_list"] {{ background: transparent; border: none; outline: none; }}
QListWidget[role="category_list"]::item {{ background: transparent; border-radius: {Size.Radius.RAD_XSM}px; padding: {Size.SPACING_XS}px; min-height: 32px; }}
QListWidget[role="category_list"]::item:hover, QListWidget[role="category_list"]::item:selected {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_050}; }}

/* Segmented Control */
QFrame[role="segmented_control"] {{ background-color: {Semantic.NEUTRAL_950}; border: 1px solid {Semantic.NEUTRAL_700}; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.SPACING_XS}px; }}
QPushButton[role="segmented_item"] {{ background-color: transparent; border: {Borders.BRD_THIN}; border-radius: {Size.Radius.RAD_XSM}px; padding: {Size.Padding.PAD_TGHT}; color: {Semantic.NEUTRAL_400}; }}
QPushButton[role="segmented_item"]:hover {{ background-color: {Semantic.NEUTRAL_750}; border: {Borders.BRD_HOVR}; color: {Semantic.NEUTRAL_000}; }}
QPushButton[role="segmented_item"]:focus {{ border-color: transparent; }}
QPushButton[role="segmented_item"]:checked {{ background-color: {Semantic.NEUTRAL_900}; border: 1px solid {Semantic.NEUTRAL_700}; color: {Semantic.NEUTRAL_050}; font-weight: 500; }}
QPushButton[role="segmented_item"]:checked:hover {{ background-color: {Semantic.NEUTRAL_750}; border: {Borders.BRD_HOVR}; color: {Semantic.NEUTRAL_000}; }}
QPushButton[role="segmented_item"]:checked:pressed {{ background-color: {Semantic.SURFACE_900}; border: 1px solid {Semantic.NEUTRAL_750}; }}
QPushButton[role="segmented_item"]:pressed {{ background-color: {Semantic.SURFACE_900}; border: 1px solid {Semantic.NEUTRAL_750}; }}
QPushButton[icon_only="true"][role="segmented_item"] {{ padding: {Size.SPACING_NN}px; }}
QPushButton[role="segmented_item"]:disabled {{ color: {Semantic.NEUTRAL_500}; opacity: 0.4; }}

/* Segmented Pagination */
QFrame[role="segmented_pagination"] {{ background-color: {Semantic.NEUTRAL_900}; border: 1px solid {Semantic.NEUTRAL_700}; border-radius: {Size.Radius.RAD_MED}px; }}
QFrame[role="segmented_pagination"] QPushButton {{ background: transparent; border: none; min-width: {Size.ICON_BASIC}px; max-width: {Size.ICON_BASIC}px; min-height: {Size.ICON_BASIC}px; max-height: {Size.ICON_BASIC}px; }}
QFrame[role="segmented_pagination"] QPushButton#btn_first {{ border-top-left-radius: {Size.Radius.RAD_MED}px; border-bottom-left-radius: {Size.Radius.RAD_MED}px; }}
QFrame[role="segmented_pagination"] QPushButton#btn_last {{ border-top-right-radius: {Size.Radius.RAD_MED}px; border-bottom-right-radius: {Size.Radius.RAD_MED}px; }}
QFrame[role="segmented_pagination"] QPushButton:hover:enabled {{ background-color: {Semantic.NEUTRAL_750}; }}
QFrame[role="segmented_pagination"] QPushButton:focus:enabled {{ border-color: transparent; }}
QFrame[role="segmented_pagination"] QPushButton:pressed:enabled {{ background-color: {Semantic.SURFACE_900}; }}
QFrame[role="segmented_pagination"] QPushButton:disabled {{ background-color: transparent; opacity: 0.35; color: {Semantic.NEUTRAL_500}; }}
QFrame[role="segmented_pagination"] QLabel#lbl_page_status {{ background-color: transparent; color: {Semantic.NEUTRAL_050}; font-size: {text1}px; font-weight: 500; padding: {Size.Padding.FLAT_MIN}; min-height: 32px; max-height: 32px; }}

/* Calendar Pop-up (QCalendarWidget) */
QWidget#qt_datetimedit_calendar {{ background-color: {Semantic.NEUTRAL_950}; border: {Borders.BRD_SHIN}; border-radius: {Size.Radius.RAD_LRG}px; padding: {Size.Padding.PAD_TINY}; }}
QCalendarWidget {{ background-color: {Semantic.NEUTRAL_950}; border: {Borders.BRD_BASE}; border-radius: {Size.Radius.RAD_LRG}px; padding: {Size.Padding.PAD_TINY}; }}
QCalendarWidget QWidget#qt_calendar_navigationbar {{ background-color: {Semantic.NEUTRAL_950}; border: none; min-height: 36px; margin-bottom: 4px; }}
QCalendarWidget QToolButton {{ background-color: transparent; color: {Semantic.NEUTRAL_050}; font-weight: 500; font-size: {text1}px; border: {Borders.BRD_NONE}; border-radius: {Size.Radius.RAD_XSM}px; padding: {Size.Padding.PAD_COMP}; }}
QCalendarWidget QToolButton:hover {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_050}; }}
QCalendarWidget QToolButton:pressed {{ background-color: {Semantic.NEUTRAL_750}; }}
QCalendarWidget QToolButton#qt_calendar_prevmonth {{ qproperty-icon: url("{PATH_ICON_CHEVRON_LF}"); icon-size: 16px; width: 26px; height: 26px; }}
QCalendarWidget QToolButton#qt_calendar_nextmonth {{ qproperty-icon: url("{PATH_ICON_CHEVRON_RT}"); icon-size: 16px; width: 26px; height: 26px; }}
QCalendarWidget QToolButton#qt_calendar_monthbutton, QCalendarWidget QToolButton#qt_calendar_yearbutton {{ color: {Semantic.NEUTRAL_050}; font-size: {text1}px; font-weight: 500; padding: {Size.Padding.PAD_COMP}; }}
QCalendarWidget QMenu {{ background-color: {Semantic.NEUTRAL_950}; color: {Semantic.NEUTRAL_400}; border: {Borders.BRD_BASE}; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.PAD_TINY}; }}
QCalendarWidget QSpinBox {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_050}; border: {Borders.BRD_BASE}; border-radius: {Size.Radius.RAD_XSM}px; padding: {Size.Padding.PAD_COMP}; font-weight: 500; }}
QCalendarWidget QSpinBox:focus {{ border-color: {BrandColors.GREEN}; }}
QCalendarWidget QTableView {{ background-color: {Semantic.NEUTRAL_950}; border: none; gridline-color: transparent; selection-background-color: {Semantic.NEUTRAL_050}; selection-color: {Semantic.NEUTRAL_900}; outline: none; }}
QCalendarWidget QTableView QWidget {{ background-color: {Semantic.NEUTRAL_950}; }}
QCalendarWidget QTableView:enabled {{ color: {Semantic.NEUTRAL_400}; }}
QCalendarWidget QTableView:disabled {{ color: {Semantic.NEUTRAL_700}; }}
QHeaderView, QCalendarWidget QHeaderView::section {{ background-color: transparent; color: {Semantic.NEUTRAL_400}; font-size: {text2}px; font-weight: 500; padding: {Size.SPACING_XXS}px {Size.SPACING_NN}px; border: none; text-align: center; }}
QCalendarWidget QTableView::item {{ border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.PAD_TINY}; margin: 2px; }}
QCalendarWidget QTableView::item:hover {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_050}; border-radius: {Size.Radius.RAD_MED}px; }}
QCalendarWidget QTableView::item:selected {{ background-color: {Semantic.NEUTRAL_050}; color: {Semantic.NEUTRAL_900}; font-weight: 700; border-radius: {Size.Radius.RAD_MED}px; }}

/* Autocomplete Pop-up (VariableTextEdit) */
QListWidget[role="variable_autocomplete_popup"] {{ background-color: {Semantic.NEUTRAL_900}; border: {Borders.BRD_SHIN}; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.PAD_TINY}; outline: none; color: {Semantic.NEUTRAL_050}; }}
QListWidget[role="variable_autocomplete_popup"]::item {{ height: 28px; padding: {Size.Padding.PAD_LIST}; border-radius: {Size.Radius.RAD_XSM}px; color: {Semantic.NEUTRAL_200}; font-weight: 500; }}
QListWidget[role="variable_autocomplete_popup"]::item:hover {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_050}; }}
QListWidget[role="variable_autocomplete_popup"]::item:selected {{ background-color: {Semantic.NEUTRAL_750}; color: {Semantic.NEUTRAL_050}; font-weight: 600; }}

/* Global Context Menus & Tooltips */
QMenu {{ background-color: {Semantic.NEUTRAL_950}; color: {Semantic.NEUTRAL_050}; border: {Borders.BRD_SHIN}; border-radius: {Size.Radius.RAD_MED}px; padding: {Size.Padding.PAD_TINY}; }}
QMenu::item {{ padding: {Size.Padding.PAD_WIDE}; border-radius: {Size.Radius.RAD_XSM}px; color: {Semantic.NEUTRAL_200}; }}
QMenu::item:selected {{ background-color: {Semantic.NEUTRAL_750}; color: {Semantic.NEUTRAL_050}; }}
QMenu::separator {{ height: 1px; background-color: {Semantic.BORDER_SUBTLE_GHOST}; margin: 4px 6px; }}

QToolTip {{ background-color: {Semantic.NEUTRAL_900}; color: {Semantic.NEUTRAL_050}; border: 1px solid {Semantic.BORDER_TOP_SHINE}; border-radius: {Size.Radius.RAD_XSM}px; padding: {Size.Padding.PAD_TGHT}; font-size: {text2}px; }}
"""

@lru_cache(maxsize=16)
def get_global_qss(base: int = 12, custom_qss: tuple[str, ...] = ()) -> str:
    size_head1 = base + 12
    size_head2 = base + 9
    size_head3 = base + 3
    size_text1 = base
    size_text2 = max(10, base - 1)

    sections = [
        _build_reset_and_typography_qss(size_head1, size_head2, size_head3, size_text1, size_text2),
        _build_button_qss   (size_text1),
        _build_input_qss    (size_text1, size_text2),
        _build_surface_qss  (size_text1, size_text2),
        _build_complex_qss  (size_text1, size_text2),
    ]
    sections.extend(rule.strip() for rule in custom_qss if rule and rule.strip())
    return "\n".join(sections)

GLOBAL_QSS = get_global_qss(12)

def create_dark_palette() -> QPalette:
    palette = QPalette()
    dark_window     = QColor(Palette.NEUTRAL_950)
    dark_base       = QColor(Palette.NEUTRAL_900)
    dark_alt_base   = QColor(Palette.NEUTRAL_900)
    text_white      = QColor(Palette.NEUTRAL_050)
    text_disabled   = QColor(Palette.NEUTRAL_500)
    accent          = QColor(BrandColors.BLUE)

    palette.setColor(QPalette.ColorRole.Window, dark_window)
    palette.setColor(QPalette.ColorRole.WindowText, text_white)
    palette.setColor(QPalette.ColorRole.Base, dark_base)
    palette.setColor(QPalette.ColorRole.AlternateBase, dark_alt_base)
    palette.setColor(QPalette.ColorRole.ToolTipBase, dark_base)
    palette.setColor(QPalette.ColorRole.ToolTipText, text_white)
    palette.setColor(QPalette.ColorRole.Text, text_white)
    palette.setColor(QPalette.ColorRole.Button, dark_base)
    palette.setColor(QPalette.ColorRole.ButtonText, text_white)
    palette.setColor(QPalette.ColorRole.BrightText, QColor(BrandColors.RED))
    palette.setColor(QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorRole.HighlightedText, text_white)
    palette.setColor(QPalette.ColorRole.Link, accent)
    palette.setColor(QPalette.ColorRole.LinkVisited, QColor(BrandColors.PURPLE))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, text_disabled)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, text_disabled)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, text_disabled)
    return palette

@lru_cache(maxsize=128)
def get_swatch_qss(bg_color: str, border_width: int = 1, radius: int = Size.Radius.RAD_XSM) -> str:
    return f"background-color: {bg_color}; border: {get_border(Semantic.NEUTRAL_700, border_width)}; border-radius: {radius}px;"
