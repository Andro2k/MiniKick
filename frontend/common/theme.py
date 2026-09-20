# frontend\common\theme.py

import os
import re
import tempfile
from functools import lru_cache
from pathlib import Path
from .paths import get_assets_path, resolve_icon_path

COLOR_NEUTRAL_950  = "#111215"
COLOR_NEUTRAL_900  = "#141519"
COLOR_NEUTRAL_850  = "#18191E"
COLOR_NEUTRAL_800  = "#202228"
COLOR_NEUTRAL_750  = "#282A32"
COLOR_NEUTRAL_700  = "#343741"
COLOR_NEUTRAL_500  = "#6E7382"
COLOR_NEUTRAL_400  = "#9CA3AF"
COLOR_NEUTRAL_200  = "#E4E5E9"
COLOR_WHITE        = "#F4F4F6"
COLOR_PURE_WHITE   = "#FFFFFF"
COLOR_BLACK        = "#000000"

# Surface & Interactive States (Antigravity Spec)
COLOR_SURFACE_HOVER         = "#282A31"
COLOR_SURFACE_ACTIVE        = "#26282E"
COLOR_SURFACE_ACTIVE_HOVER  = "#2D3038"
COLOR_SURFACE_PRESSED       = "#1A1B20"
COLOR_NAV_HOVER             = "#1A1C22"

# Borders & Highlights
COLOR_BORDER_HOVER          = "#484C5A"
COLOR_BORDER_FOCUS          = "#5A5E70"
COLOR_BORDER_MUTED_FOCUS    = "#5E5C66"
COLOR_BORDER_TOP_SHINE      = "#38363E"
COLOR_BORDER_TOP_FOCUS      = "#71717A"
COLOR_BORDER_LIGHT          = "#4B4951"
COLOR_BORDER_SUBTLE_GHOST   = "#313036"

# Action Red States
COLOR_RED_SOLID    = "#E03131"
COLOR_RED_HOVER    = "#EF4444"
COLOR_RED_PRESSED  = "#C92A2A"

COLOR_GREEN        = "#2ECD70"
COLOR_GREEN_DARK   = "#23A55A"
COLOR_RED          = "#EF4444"
COLOR_RED_DARK     = "#DC2626"
COLOR_AMBER        = "#F59E0B"
COLOR_AMBER_DARK   = "#D97706"
COLOR_BLUE         = "#3B82F6"
COLOR_BLUE_DARK    = "#2563EB"
COLOR_PURPLE       = "#A855F7"
COLOR_PURPLE_DARK  = "#9333EA"

# Platform Borders & Focus Accents
COLOR_KICK_BORDER               = "#1A7A42"
COLOR_KICK_BORDER_BOTTOM        = "#125E31"
COLOR_KICK_BORDER_HOVER         = "#1E8E4D"
COLOR_KICK_BORDER_TOP_HOVER     = "#3DE082"
COLOR_KICK_BORDER_BOTTOM_HOVER  = "#15733C"
COLOR_KICK_BORDER_TOP_PRESSED   = "#146133"

COLOR_TWITCH_BORDER             = "#6722CD"
COLOR_TWITCH_BORDER_BOTTOM      = "#4D0FA8"
COLOR_TWITCH_BORDER_HOVER       = "#772CE8"
COLOR_TWITCH_BORDER_TOP_HOVER   = "#A855F7"
COLOR_TWITCH_BORDER_BOTTOM_HOVER= "#5C16C5"

COLOR_YOUTUBE_BORDER            = "#B80323"
COLOR_YOUTUBE_BORDER_TOP        = "#EF233C"
COLOR_YOUTUBE_BORDER_BOTTOM     = "#8D0019"
COLOR_YOUTUBE_BORDER_HOVER      = "#D90429"
COLOR_YOUTUBE_BORDER_TOP_HOVER  = "#FF4D6D"
COLOR_YOUTUBE_BORDER_BOTTOM_HOVER = "#AA001E"

COLOR_TIKTOK_BORDER             = "#009DA8"
COLOR_TIKTOK_BORDER_BOTTOM      = "#00747C"
COLOR_TIKTOK_BORDER_HOVER       = "#00B8C4"
COLOR_TIKTOK_BORDER_TOP_HOVER   = "#5EF8FF"
COLOR_TIKTOK_BORDER_BOTTOM_HOVER= "#008891"

# Subtle Danger & Accent Action Borders
COLOR_DANGER_BORDER             = "#451B1D"
COLOR_DANGER_BORDER_TOP         = "#7F1D1D"
COLOR_DANGER_BORDER_BOTTOM      = "#331416"
COLOR_DANGER_BORDER_HOVER       = "#5C2326"
COLOR_DANGER_BORDER_TOP_HOVER   = "#991B1B"
COLOR_DANGER_BORDER_BOTTOM_HOVER= "#40181A"
COLOR_DANGER_TEXT_HOVER         = "#F87171"
COLOR_DANGER_BORDER_PRESSED     = "#2B1113"

COLOR_ACCENT_SUBTLE_BORDER            = "#1E3B27"
COLOR_ACCENT_SUBTLE_BORDER_TOP        = "#14532D"
COLOR_ACCENT_SUBTLE_BORDER_BOTTOM     = "#162B1D"
COLOR_ACCENT_SUBTLE_BORDER_HOVER       = "#285437"
COLOR_ACCENT_SUBTLE_BORDER_TOP_HOVER   = "#166534"
COLOR_ACCENT_SUBTLE_TEXT_HOVER        = "#4ADE80"
COLOR_ACCENT_SUBTLE_BORDER_PRESSED     = "#122418"

COLOR_TWITCH       = "#9146FF"
COLOR_TWITCH_DARK  = "#772CE8"
COLOR_TWITCH_GLOW  = "rgba(145, 70, 255, 0.12)"
COLOR_YOUTUBE      = "#FF0000"
COLOR_YOUTUBE_DARK = "#CC0000"
COLOR_YOUTUBE_GLOW = "rgba(255, 0, 0, 0.12)"
COLOR_TIKTOK       = "#00F2FE"
COLOR_TIKTOK_DARK  = "#00B8C4"
COLOR_TIKTOK_GLOW  = "rgba(0, 242, 254, 0.12)"

COLOR_WHITE_GLOW   = "rgba(250, 250, 250, 0.05)"
COLOR_GREEN_GLOW   = "rgba(46, 205, 112, 0.10)"
COLOR_RED_GLOW     = "rgba(239, 68, 68, 0.10)"
COLOR_AMBER_GLOW   = "rgba(245, 158, 11, 0.10)"
COLOR_BLUE_GLOW    = "rgba(59, 130, 246, 0.10)"
COLOR_PURPLE_GLOW  = "rgba(168, 85, 247, 0.10)"

FONT_FAMILY = "'Google Sans', '-apple-system', 'Segoe UI', sans-serif"

RADIUS_2XS         = 2
RADIUS_XS          = 4
RADIUS_SM          = 6
RADIUS_MD_INNER    = 7
RADIUS_MD          = 8
RADIUS_LG          = 12
RADIUS_XL          = 16
RADIUS_PILL        = 26

SPACING_NONE       = 0
SPACING_2XS        = 2
SPACING_XS         = 4
SPACING_SM         = 6
SPACING_MD         = 8
SPACING_LG         = 12
SPACING_XL         = 16
SPACING_2XL        = 20

MARGIN_NONE        = (0, 0, 0, 0)
MARGIN_2XS         = (2, 2, 2, 2)
MARGIN_XS          = (4, 4, 4, 4)
MARGIN_SM          = (6, 6, 6, 6)
MARGIN_MD          = (8, 8, 8, 8)
MARGIN_LG          = (12, 12, 12, 12)
MARGIN_XL          = (16, 16, 16, 16)
MARGIN_2XL         = (20, 20, 20, 20)

MARGIN_H_XS        = (4, 0, 4, 0)
MARGIN_H_SM        = (6, 0, 6, 0)
MARGIN_H_MD        = (8, 0, 8, 0)
MARGIN_H_LG        = (12, 0, 12, 0)
MARGIN_V_2XS       = (0, 2, 0, 2)
MARGIN_V_XS        = (0, 4, 0, 4)
MARGIN_V_SM        = (0, 6, 0, 6)
MARGIN_V_MD        = (0, 8, 0, 8)
MARGIN_V_LG        = (0, 12, 0, 12)

MARGIN_SETTING_ROW     = (16, 12, 16, 12)
MARGIN_SETTING_ROW_COMPACT = (14, 10, 14, 10)
MARGIN_HERO             = (14, 12, 14, 12)
MARGIN_PLATFORMS_GRID   = (12, 10, 12, 10)
MARGIN_SECTION_HEADER   = (2, 12, 2, 4)
MARGIN_SECTION_HEADER_FIRST = (2, 0, 2, 4)
MARGIN_TAB_PANEL        = (8, 8, 8, 8)
MARGIN_TAB_BAR          = (12, 4, 12, 4)
MARGIN_SCROLL_CONTENT   = (2, 2, 8, 2)
MARGIN_CHIP             = (4, 2, 4, 2)
MARGIN_TAG_BADGE        = (4, 4, 8, 4)

PADDING_INPUT      = "6px 10px"
PADDING_BUTTON     = "6px 14px"
PADDING_SPINBOX    = "4px 20px 4px 10px"
PADDING_ITEM       = "4px 6px"
PADDING_BADGE      = "2px 8px"
PADDING_CHIP       = "4px 12px"
PADDING_TAB        = "6px 16px"
PADDING_MENU_ITEM  = "5px 12px 5px 18px"

BORDER_DEFAULT     = f"1.2px solid {COLOR_NEUTRAL_750}"
BORDER_SUBTLE      = f"1.5px solid {COLOR_NEUTRAL_800}"
BORDER_MUTED       = f"1.2px solid {COLOR_NEUTRAL_700}"
BORDER_TRANSPARENT = "1.2px solid transparent"
BORDER_FOCUS       = f"1.2px solid {COLOR_BORDER_MUTED_FOCUS}"
BORDER_ERROR       = f"1.2px solid {COLOR_RED}"

GRADIENT_NEUTRAL_FILL          = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #201E25, stop:1 #323137)"
GRADIENT_NEUTRAL_HOVER         = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #2A2830, stop:1 #3D3B43)"
GRADIENT_NEUTRAL_PRESSED       = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #1A191E, stop:1 #25242A)"

GRADIENT_ACCENT_FILL           = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #1E8E4D, stop:1 #15733C)"
GRADIENT_ACCENT_HOVER          = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #23A55A, stop:1 #188546)"
GRADIENT_ACCENT_PRESSED        = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #146133, stop:1 #0F4F29)"

GRADIENT_TWITCH_FILL           = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #772CE8, stop:1 #5C16C5)"
GRADIENT_TWITCH_HOVER          = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #863DF0, stop:1 #6722CD)"
GRADIENT_TWITCH_PRESSED        = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #4D0FA8, stop:1 #3C0A85)"

GRADIENT_YOUTUBE_FILL          = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #D90429, stop:1 #AA001E)"
GRADIENT_YOUTUBE_HOVER         = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #EF233C, stop:1 #C10425)"
GRADIENT_YOUTUBE_PRESSED       = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #8D0019, stop:1 #6B0013)"

GRADIENT_TIKTOK_FILL           = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #00B8C4, stop:1 #008891)"
GRADIENT_TIKTOK_HOVER          = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #12D6E3, stop:1 #009DA8)"
GRADIENT_TIKTOK_PRESSED        = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #00747C, stop:1 #00565C)"

GRADIENT_DANGER_FILL           = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #2A1719, stop:1 #1E1213)"
GRADIENT_DANGER_HOVER          = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #381E21, stop:1 #281618)"
GRADIENT_DANGER_PRESSED        = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #1B0E0F, stop:1 #140A0B)"

GRADIENT_ACCENT_SUBTLE_FILL    = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #17241C, stop:1 #111A14)"
GRADIENT_ACCENT_SUBTLE_HOVER   = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #1E3326, stop:1 #15241B)"
GRADIENT_ACCENT_SUBTLE_PRESSED = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #0F1712, stop:1 #0A100C)"

_QSS_ICON_CACHE_DIR = Path(tempfile.gettempdir()) / "minikick_qss_icons"

@lru_cache(maxsize=128)
def get_qss_colored_icon(icon_name_or_rel_path: str, color_hex: str = COLOR_NEUTRAL_400) -> str:
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

PATH_ICON_HELP          = get_qss_colored_icon("icons/circle-info-filled.svg", COLOR_WHITE)
PATH_ICON_CHEVRON_DOWN  = get_qss_colored_icon("icons/chevron-down-filled.svg", COLOR_NEUTRAL_400)
PATH_ICON_CHEVRON_UP    = get_qss_colored_icon("icons/chevron-up-filled.svg", COLOR_NEUTRAL_400)
PATH_ICON_CHEVRON_LEFT  = get_qss_colored_icon("icons/chevron-left-filled.svg", COLOR_NEUTRAL_400)
PATH_ICON_CHEVRON_RIGHT = get_qss_colored_icon("icons/chevron-right-filled.svg", COLOR_NEUTRAL_400)
PATH_ICON_CHECK         = _get_qss_icon_url("icons/check-filled.svg")
PATH_ICON_CHECK_GREEN   = get_qss_colored_icon("icons/check-filled.svg", COLOR_GREEN)
PATH_ICON_MINUS         = _get_qss_icon_url("icons/minus-filled.svg")
PATH_ICON_RADIO_DOT     = _get_qss_icon_url("icons/radio-dot.svg")
PATH_ICON_CALENDAR      = get_qss_colored_icon("icons/calendar-days-filled.svg", COLOR_NEUTRAL_400)

def _build_reset_and_typography_qss(h1: int, h2: int, h3: int, text1: int, text2: int) -> str:
    return f"""
/* --- 1. Reset & Root Surfaces --- */
* {{ font-family: {FONT_FAMILY}; font-size: {text1}px; color: {COLOR_NEUTRAL_400}; outline: none; }}
QMainWindow {{ background-color: {COLOR_NEUTRAL_950}; }}
QDialog {{ background-color: {COLOR_NEUTRAL_950}; }}
QLabel {{ background-color: transparent; }}

/* --- 2. Typography Scale --- */
QLabel[role="h1"] {{ font-size: {h1}px; font-weight: 600; color: {COLOR_WHITE}; letter-spacing: -0.2px; }}
QLabel[role="h2"] {{ font-size: {h2}px; font-weight: 600; color: {COLOR_NEUTRAL_200}; }}
QLabel[role="h3"] {{ font-size: {h3}px; font-weight: 600; color: {COLOR_WHITE}; }}
QLabel[role="section_header"] {{ font-size: {h3}px; font-weight: 600; color: {COLOR_WHITE}; background: transparent; padding: 0px 0px 2px 0px; }}
QLabel[role="sidebar_section_header"] {{ font-size: 11px; font-weight: 600; color: {COLOR_NEUTRAL_500}; padding: 6px 8px 2px 8px; letter-spacing: 0.5px; background: transparent; }}
QLabel[role="profile_name"] {{ font-size: {text1}px; font-weight: 600; color: {COLOR_WHITE}; background: transparent; }}
QLabel[role="profile_role"] {{ font-size: {text2}px; font-weight: 400; color: {COLOR_NEUTRAL_400}; background: transparent; }}
QLabel[role="body"] {{ font-size: {text1}px; font-weight: 400; color: {COLOR_NEUTRAL_400}; }}
QLabel[role="caption"] {{ font-size: {text2}px; font-weight: 400; color: {COLOR_NEUTRAL_500}; }}
QLabel[role="monospace"] {{ font-size: {text2}px; color: {COLOR_NEUTRAL_400}; }}
QLabel[state="normal"] {{ color: {COLOR_NEUTRAL_400}; }}
QLabel[state="white"] {{ color: {COLOR_WHITE}; }}
QLabel[state="error"] {{ color: {COLOR_RED}; }}
QLabel[state="danger"] {{ color: {COLOR_RED}; }}
QLabel[state="success"] {{ color: {COLOR_GREEN}; }}
QLabel[state="info"] {{ color: {COLOR_BLUE}; }}
QLabel[state="warning"] {{ color: {COLOR_AMBER}; }}
QLabel[state="bold"] {{ font-weight: 600; }}
QLabel[role="code"] {{ font-size: {text2}px; font-weight: 500; background-color: {COLOR_NEUTRAL_850}; padding: 2px 6px; border-radius: {RADIUS_SM}px; color: {COLOR_NEUTRAL_200}; border: {BORDER_SUBTLE}; }}
QLabel[role="category"] {{ font-weight: 600; color: {COLOR_GREEN}; margin-top: 6px; font-size: {text2}px; }}
"""


def _build_button_qss(text1: int, text2: int) -> str:
    return f"""
/* --- 3. Modern Figma Gradient Buttons --- */
QPushButton {{ border: {BORDER_TRANSPARENT}; font-size: {text1}px; font-weight: 500; }}
QPushButton:focus {{ outline: none; }}
QPushButton:default {{ border: 1.2px solid {COLOR_GREEN}; }}

/* Neutral & Outlined Buttons (Antigravity Spec) */
QPushButton[role="action_outlined"] {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_WHITE}; font-size: {text1}px; font-weight: 500; border: 1px solid {COLOR_NEUTRAL_700}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_outlined"]:hover {{ background-color: {COLOR_SURFACE_HOVER}; border: 1px solid {COLOR_BORDER_HOVER}; color: {COLOR_PURE_WHITE}; }}
QPushButton[role="action_outlined"]:pressed {{ background-color: {COLOR_SURFACE_PRESSED}; border: 1px solid {COLOR_NEUTRAL_750}; }}
QPushButton[role="action_outlined"]:focus {{ border: 1px solid {COLOR_BORDER_FOCUS}; }}

/* Antigravity Solid Danger Action Button */
QPushButton[role="action_danger_solid"], QPushButton[role="action_danger"] {{ background-color: {COLOR_RED_SOLID}; color: {COLOR_PURE_WHITE}; font-size: {text1}px; font-weight: 600; border: 1px solid {COLOR_RED_SOLID}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_danger_solid"]:hover, QPushButton[role="action_danger"]:hover {{ background-color: {COLOR_RED_HOVER}; border-color: {COLOR_RED_HOVER}; }}
QPushButton[role="action_danger_solid"]:pressed, QPushButton[role="action_danger"]:pressed {{ background-color: {COLOR_RED_PRESSED}; border-color: {COLOR_RED_PRESSED}; }}
QPushButton[role="action_danger_solid"]:focus, QPushButton[role="action_danger"]:focus {{ border: 1px solid {COLOR_PURE_WHITE}; }}

/* Platform: Kick Button */
QPushButton[role="action_kick"] {{ background-color: {GRADIENT_ACCENT_FILL}; color: {COLOR_WHITE}; font-size: {text1}px; font-weight: 500; border: 1.2px solid {COLOR_KICK_BORDER}; border-top: 1.2px solid {COLOR_GREEN}; border-bottom: 1.2px solid {COLOR_KICK_BORDER_BOTTOM}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_kick"]:hover {{ background-color: {GRADIENT_ACCENT_HOVER}; border: 1.2px solid {COLOR_KICK_BORDER_HOVER}; border-top: 1.2px solid {COLOR_KICK_BORDER_TOP_HOVER}; border-bottom: 1.2px solid {COLOR_KICK_BORDER_BOTTOM_HOVER}; }}
QPushButton[role="action_kick"]:pressed {{ background-color: {GRADIENT_ACCENT_PRESSED}; border: 1.2px solid {COLOR_KICK_BORDER_BOTTOM}; border-top: 1.2px solid {COLOR_KICK_BORDER_TOP_PRESSED}; border-bottom: 1.2px solid {COLOR_KICK_BORDER_HOVER}; }}
QPushButton[role="action_kick"]:focus {{ border: 1.2px solid {COLOR_GREEN}; }}
QPushButton[role="action_kick"]:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border: {BORDER_SUBTLE}; }}

/* Platform: Twitch Button */
QPushButton[role="action_twitch"] {{ background-color: {GRADIENT_TWITCH_FILL}; color: {COLOR_WHITE}; font-size: {text1}px; font-weight: 500; border: 1.2px solid {COLOR_TWITCH_BORDER}; border-top: 1.2px solid {COLOR_TWITCH}; border-bottom: 1.2px solid {COLOR_TWITCH_BORDER_BOTTOM}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_twitch"]:hover {{ background-color: {GRADIENT_TWITCH_HOVER}; border: 1.2px solid {COLOR_TWITCH_BORDER_HOVER}; border-top: 1.2px solid {COLOR_TWITCH_BORDER_TOP_HOVER}; border-bottom: 1.2px solid {COLOR_TWITCH_BORDER_BOTTOM_HOVER}; }}
QPushButton[role="action_twitch"]:pressed {{ background-color: {GRADIENT_TWITCH_PRESSED}; border: 1.2px solid {COLOR_TWITCH_BORDER_BOTTOM}; }}
QPushButton[role="action_twitch"]:focus {{ border: 1.2px solid {COLOR_TWITCH}; }}
QPushButton[role="action_twitch"]:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border: {BORDER_SUBTLE}; }}

/* Platform: YouTube Button */
QPushButton[role="action_youtube"] {{ background-color: {GRADIENT_YOUTUBE_FILL}; color: {COLOR_WHITE}; font-size: {text1}px; font-weight: 500; border: 1.2px solid {COLOR_YOUTUBE_BORDER}; border-top: 1.2px solid {COLOR_YOUTUBE_BORDER_TOP}; border-bottom: 1.2px solid {COLOR_YOUTUBE_BORDER_BOTTOM}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_youtube"]:hover {{ background-color: {GRADIENT_YOUTUBE_HOVER}; border: 1.2px solid {COLOR_YOUTUBE_BORDER_HOVER}; border-top: 1.2px solid {COLOR_YOUTUBE_BORDER_TOP_HOVER}; border-bottom: 1.2px solid {COLOR_YOUTUBE_BORDER_BOTTOM_HOVER}; }}
QPushButton[role="action_youtube"]:pressed {{ background-color: {GRADIENT_YOUTUBE_PRESSED}; border: 1.2px solid {COLOR_YOUTUBE_BORDER_BOTTOM}; }}
QPushButton[role="action_youtube"]:focus {{ border: 1.2px solid {COLOR_RED}; }}
QPushButton[role="action_youtube"]:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border: {BORDER_SUBTLE}; }}

/* Platform: TikTok Button */
QPushButton[role="action_tiktok"] {{ background-color: {GRADIENT_TIKTOK_FILL}; color: {COLOR_BLACK}; font-size: {text1}px; font-weight: 700; border: 1.2px solid {COLOR_TIKTOK_BORDER}; border-top: 1.2px solid {COLOR_TIKTOK}; border-bottom: 1.2px solid {COLOR_TIKTOK_BORDER_BOTTOM}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_tiktok"]:hover {{ background-color: {GRADIENT_TIKTOK_HOVER}; border: 1.2px solid {COLOR_TIKTOK_BORDER_HOVER}; border-top: 1.2px solid {COLOR_TIKTOK_BORDER_TOP_HOVER}; border-bottom: 1.2px solid {COLOR_TIKTOK_BORDER_BOTTOM_HOVER}; }}
QPushButton[role="action_tiktok"]:pressed {{ background-color: {GRADIENT_TIKTOK_PRESSED}; border: 1.2px solid {COLOR_TIKTOK_BORDER_BOTTOM}; }}
QPushButton[role="action_tiktok"]:focus {{ border: 1.2px solid {COLOR_TIKTOK}; }}
QPushButton[role="action_tiktok"]:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border: {BORDER_SUBTLE}; }}

/* Subtle Danger Action Button */
QPushButton[role="action_danger_border"] {{ background-color: {GRADIENT_DANGER_FILL}; color: {COLOR_RED}; font-size: {text1}px; font-weight: 500; border: 1.2px solid {COLOR_DANGER_BORDER}; border-top: 1.2px solid {COLOR_DANGER_BORDER_TOP}; border-bottom: 1.2px solid {COLOR_DANGER_BORDER_BOTTOM}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_danger_border"]:hover {{ background-color: {GRADIENT_DANGER_HOVER}; border: 1.2px solid {COLOR_DANGER_BORDER_HOVER}; border-top: 1.2px solid {COLOR_DANGER_BORDER_TOP_HOVER}; border-bottom: 1.2px solid {COLOR_DANGER_BORDER_BOTTOM_HOVER}; color: {COLOR_DANGER_TEXT_HOVER}; }}
QPushButton[role="action_danger_border"]:pressed {{ background-color: {GRADIENT_DANGER_PRESSED}; border: 1.2px solid {COLOR_DANGER_BORDER_PRESSED}; }}
QPushButton[role="action_danger_border"]:focus {{ border: 1.2px solid {COLOR_DANGER_BORDER_TOP_HOVER}; }}

/* Subtle Accent Action Button */
QPushButton[role="action_accent_border"] {{ background-color: {GRADIENT_ACCENT_SUBTLE_FILL}; color: {COLOR_GREEN}; font-size: {text1}px; font-weight: 500; border: 1.2px solid {COLOR_ACCENT_SUBTLE_BORDER}; border-top: 1.2px solid {COLOR_ACCENT_SUBTLE_BORDER_TOP}; border-bottom: 1.2px solid {COLOR_ACCENT_SUBTLE_BORDER_BOTTOM}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_accent_border"]:hover {{ background-color: {GRADIENT_ACCENT_SUBTLE_HOVER}; border: 1.2px solid {COLOR_ACCENT_SUBTLE_BORDER_HOVER}; border-top: 1.2px solid {COLOR_ACCENT_SUBTLE_BORDER_TOP_HOVER}; border-bottom: 1.2px solid {COLOR_ACCENT_SUBTLE_BORDER}; color: {COLOR_ACCENT_SUBTLE_TEXT_HOVER}; }}
QPushButton[role="action_accent_border"]:pressed {{ background-color: {GRADIENT_ACCENT_SUBTLE_PRESSED}; border: 1.2px solid {COLOR_ACCENT_SUBTLE_BORDER_PRESSED}; }}
QPushButton[role="action_accent_border"]:focus {{ border: 1.2px solid {COLOR_ACCENT_SUBTLE_BORDER_TOP_HOVER}; }}

/* Ghost & Utility Buttons */
QPushButton[role="btn_ghost"] {{ background-color: transparent; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_SM}px; }}
QPushButton[role="btn_ghost"]:hover {{ background-color: {COLOR_NEUTRAL_800}; border: 1.2px solid {COLOR_BORDER_SUBTLE_GHOST}; border-top: 1.2px solid {COLOR_BORDER_TOP_SHINE}; }}
QPushButton[role="btn_ghost"]:focus {{ background-color: {COLOR_NEUTRAL_800}; border: 1.2px solid {COLOR_BORDER_TOP_SHINE}; }}
QPushButton[role="btn_ghost"]:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}
QPushButton[role="btn_icon_sm"] {{ background-color: transparent; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_SM}px; min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px; }}
QPushButton[role="btn_icon_sm"]:hover {{ background-color: {COLOR_NEUTRAL_800}; border: 1.2px solid {COLOR_BORDER_SUBTLE_GHOST}; border-top: 1.2px solid {COLOR_BORDER_TOP_SHINE}; }}
QPushButton[role="btn_icon_sm"]:focus {{ background-color: {COLOR_NEUTRAL_800}; border: 1.2px solid {COLOR_BORDER_TOP_SHINE}; }}
QPushButton[role="btn_icon_sm"]:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}
QPushButton[role="btn_dismiss"] {{ background-color: transparent; border: none; border-radius: {RADIUS_SM}px; padding: 2px; }}
QPushButton[role="btn_dismiss"]:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QPushButton[role="btn_dismiss"]:focus {{ background-color: {COLOR_NEUTRAL_800}; border: 1.2px solid {COLOR_BORDER_TOP_SHINE}; }}
QPushButton[role="btn_dismiss"]:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}

/* Sidebar Navigation Buttons (Antigravity Pill Spec) */
QPushButton[role="nav_button"] {{ background-color: transparent; border-radius: {RADIUS_MD}px; padding: 8px 12px; text-align: left; color: {COLOR_NEUTRAL_400}; font-size: {text1}px; font-weight: 500; border: 1px solid transparent; }}
QPushButton[role="nav_button"]:hover {{ background-color: {COLOR_NAV_HOVER}; color: {COLOR_WHITE}; border: 1px solid transparent; }}
QPushButton[role="nav_button"]:focus {{ border: 1px solid {COLOR_NEUTRAL_700}; }}
QPushButton[role="nav_button"]:pressed {{ background-color: {COLOR_NEUTRAL_800}; }}
QPushButton[role="nav_button"]:checked {{ background-color: {COLOR_SURFACE_ACTIVE}; color: {COLOR_PURE_WHITE}; font-weight: 600; border: 1px solid rgba(255, 255, 255, 0.08); }}
QPushButton[role="nav_button"]:checked:hover {{ background-color: {COLOR_SURFACE_ACTIVE_HOVER}; border: 1px solid rgba(255, 255, 255, 0.12); color: {COLOR_PURE_WHITE}; }}
QPushButton[role="nav_button"]:checked:pressed {{ background-color: {COLOR_NEUTRAL_800}; }}
QPushButton[role="nav_button"][collapsed="false"] {{ text-align: left; padding-left: 12px; }}
QPushButton[role="nav_button"][collapsed="true"] {{ text-align: center; padding: 8px 0px; }}

/* Global Disabled Button States */
QPushButton:disabled, QPushButton[role="action_outlined"]:disabled, QPushButton[role="action_danger_solid"]:disabled, QPushButton[role="action_danger_border"]:disabled, QPushButton[role="action_accent_border"]:disabled, QPushButton[role="btn_ghost"]:disabled, QPushButton[role="btn_icon_sm"]:disabled, QPushButton[role="btn_dismiss"]:disabled, QPushButton[role="nav_button"]:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border: {BORDER_SUBTLE}; padding: {PADDING_BUTTON}; }}
"""


def _build_input_qss(text1: int, text2: int) -> str:
    return f"""
/* --- 4. Form Controls & Inputs --- */
QLineEdit, QTextEdit, QPlainTextEdit {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_INPUT}; border: {BORDER_DEFAULT}; border-top: 1.2px solid {COLOR_BORDER_TOP_SHINE}; }}
QTextEdit, QPlainTextEdit {{ background-color: {COLOR_NEUTRAL_900}; }}
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{ border-color: {COLOR_NEUTRAL_700}; }}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border: {BORDER_FOCUS}; border-top: 1.2px solid {COLOR_BORDER_TOP_FOCUS}; background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QLineEdit:read-only, QTextEdit:read-only, QPlainTextEdit:read-only {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_400}; border: {BORDER_SUBTLE}; }}
QLineEdit:read-only:focus, QTextEdit:read-only:focus, QPlainTextEdit:read-only:focus {{ border: {BORDER_SUBTLE}; background-color: {COLOR_NEUTRAL_900}; }}
QLineEdit[state="error"], QTextEdit[state="error"], QPlainTextEdit[state="error"] {{ border: {BORDER_ERROR}; }}
QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border-color: {COLOR_NEUTRAL_750}; padding: {PADDING_INPUT}; }}

/* ComboBox */
QComboBox {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; font-size: {text1}px; font-weight: 400; border-radius: {RADIUS_MD}px; padding: 6px 12px; border: 1px solid {COLOR_NEUTRAL_700}; combobox-popup: 0; min-width: 120px; }}
QComboBox:focus, QComboBox:hover {{ background-color: {COLOR_SURFACE_HOVER}; border-color: {COLOR_BORDER_HOVER}; color: {COLOR_WHITE}; }}
QComboBox:pressed {{ background-color: {COLOR_SURFACE_PRESSED}; }}
QComboBox:on, QComboBox[state="active"], QComboBox[state="active"]:hover, QComboBox[state="active"]:focus {{ background-color: {COLOR_SURFACE_HOVER}; border: 1px solid {COLOR_BORDER_FOCUS}; color: {COLOR_WHITE}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 24px; border-left: none; border-top-right-radius: {RADIUS_MD}px; border-bottom-right-radius: {RADIUS_MD}px; }}
QComboBox:focus::drop-down, QComboBox:hover::drop-down {{ border-color: transparent; }}
QComboBox::drop-down:hover {{ background-color: transparent; border-color: transparent; }}
QComboBox::drop-down:disabled {{ border-color: transparent; }}
QComboBox::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 14px; height: 14px; }}
QComboBox::down-arrow:on, QComboBox[state="active"]::down-arrow {{ image: url("{PATH_ICON_CHEVRON_UP}"); }}
QComboBox:disabled::down-arrow {{ opacity: 0.4; }}
QComboBox QAbstractItemView {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-size: {text1}px; border: 1px solid {COLOR_NEUTRAL_700}; border-radius: {RADIUS_MD}px; selection-background-color: {COLOR_SURFACE_ACTIVE}; selection-color: {COLOR_WHITE}; padding: 4px; }}
QComboBox QAbstractItemView::item {{ font-size: {text1}px; border-radius: {RADIUS_SM}px; padding: {PADDING_ITEM}; margin: 1px 2px; }}
QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover, QComboBox QListView::item:selected, QComboBox QListView::item:hover {{ background-color: {COLOR_SURFACE_ACTIVE}; color: {COLOR_WHITE}; border: none; }}

/* Searchable ComboBox Popup */
QFrame[role="searchable_combo_popup"] {{ background-color: {COLOR_NEUTRAL_850}; border: 1.2px solid {COLOR_BORDER_TOP_SHINE}; border-radius: {RADIUS_MD}px; }}
QFrame[role="searchable_combo_search_bar"] {{ background-color: {COLOR_NEUTRAL_850}; border: {BORDER_DEFAULT}; border-top: 1.2px solid {COLOR_BORDER_TOP_SHINE}; border-radius: {RADIUS_MD}px; }}
QLineEdit[role="searchable_combo_input"] {{ background-color: transparent; border: none; color: {COLOR_WHITE}; font-size: {text1}px; font-weight: 400; padding: 0px 4px; }}
QLineEdit[role="searchable_combo_input"]:focus {{ border: none; background-color: transparent; }}
QListWidget[role="searchable_combo_list"] {{ background-color: {COLOR_NEUTRAL_850}; border: none; outline: none; }}
QListWidget[role="searchable_combo_list"]::item {{ color: {COLOR_NEUTRAL_200}; font-size: {text1}px; font-weight: 400; padding: 6px 10px; border-radius: {RADIUS_SM}px; border: none; outline: none; }}
QListWidget[role="searchable_combo_list"]::item:hover, QListWidget[role="searchable_combo_list"]::item:selected {{ background-color: {COLOR_NEUTRAL_750}; color: {COLOR_WHITE}; border: none; outline: none; }}
QListWidget[role="searchable_combo_list"] QScrollBar:vertical {{ background: {COLOR_NEUTRAL_850}; width: 10px; margin: 4px 2px 4px 0px; border-radius: 2px; }}
QListWidget[role="searchable_combo_list"] QScrollBar::handle:vertical {{ background: {COLOR_NEUTRAL_700}; min-height: 20px; border-radius: 2px; }}
QListWidget[role="searchable_combo_list"] QScrollBar::handle:vertical:hover {{ background: {COLOR_NEUTRAL_800}; }}
QListWidget[role="searchable_combo_list"] QScrollBar::add-line:vertical, QListWidget[role="searchable_combo_list"] QScrollBar::sub-line:vertical {{ height: 0px; background: none; }}
QLabel[role="searchable_combo_empty"] {{ color: {COLOR_NEUTRAL_500}; font-size: {text2}px; padding: 16px 8px; }}

/* Context Menus */
QMenu {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_200}; border: 1.2px solid {COLOR_BORDER_TOP_SHINE}; border-radius: {RADIUS_MD}px; padding: 4px; }}
QMenu::item {{ padding: 5px 12px; margin: 1px 2px; border-radius: {RADIUS_SM}px; color: {COLOR_NEUTRAL_200}; font-size: {text2}px; font-weight: 500; }}
QMenu::item:disabled {{ color: {COLOR_NEUTRAL_500}; background-color: transparent; }}
QMenu::item:selected {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; border: 1.2px solid {COLOR_BORDER_SUBTLE_GHOST}; }}
QMenu::item:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}
QMenu::icon {{ margin-left: 14px; }}
QMenu::indicator {{ width: 14px; height: 14px; left: 8px; }}
QMenu::indicator:checked {{ image: url("{PATH_ICON_CHECK_GREEN}"); }}
QMenu::indicator:unchecked {{ image: none; }}
QMenu::separator {{ height: 1px; background-color: {COLOR_NEUTRAL_800}; margin: 1px 2px; }}

/* SpinBoxes */
QSpinBox, QDoubleSpinBox, QTimeEdit {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_SPINBOX}; border: {BORDER_DEFAULT}; border-top: 1.2px solid {COLOR_BORDER_TOP_SHINE}; selection-background-color: transparent; selection-color: {COLOR_WHITE}; }}
QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {{ border: {BORDER_FOCUS}; border-top: 1.2px solid {COLOR_BORDER_TOP_FOCUS}; background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QSpinBox:hover, QDoubleSpinBox:hover, QTimeEdit:hover {{ background-color: {COLOR_NEUTRAL_800}; border-color: {COLOR_NEUTRAL_700}; }}
QSpinBox:read-only, QDoubleSpinBox:read-only, QTimeEdit:read-only {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_400}; border: {BORDER_SUBTLE}; }}
QSpinBox::up-button, QDoubleSpinBox::up-button, QTimeEdit::up-button {{ subcontrol-origin: border; subcontrol-position: center right; width: 22px; height: 22px; right: 26px; border: none; background-color: transparent; }}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QTimeEdit::up-button:hover {{ background-color: {COLOR_NEUTRAL_750}; border-radius: {RADIUS_SM}px; }}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed, QTimeEdit::up-button:pressed {{ background-color: {COLOR_NEUTRAL_700}; }}
QSpinBox::up-button:disabled, QDoubleSpinBox::up-button:disabled, QTimeEdit::up-button:disabled {{ background-color: transparent; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow, QTimeEdit::up-arrow {{ image: url("{PATH_ICON_CHEVRON_UP}"); width: 14px; height: 14px; }}
QSpinBox::down-button, QDoubleSpinBox::down-button, QTimeEdit::down-button {{ subcontrol-origin: border; subcontrol-position: center right; width: 22px; height: 22px; right: 4px; border: none; background-color: transparent; }}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover, QTimeEdit::down-button:hover {{ background-color: {COLOR_NEUTRAL_750}; border-radius: {RADIUS_SM}px; }}
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed, QTimeEdit::down-button:pressed {{ background-color: {COLOR_NEUTRAL_700}; }}
QSpinBox::down-button:disabled, QDoubleSpinBox::down-button:disabled, QTimeEdit::down-button:disabled {{ background-color: transparent; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow, QTimeEdit::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 14px; height: 14px; }}
QSpinBox:disabled, QDoubleSpinBox:disabled, QTimeEdit:disabled, QDateEdit:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border-color: {COLOR_NEUTRAL_750}; padding: {PADDING_SPINBOX}; }}

/* DateEdit */
QDateEdit {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_SPINBOX}; border: {BORDER_DEFAULT}; border-top: 1.2px solid {COLOR_BORDER_TOP_SHINE}; selection-background-color: transparent; selection-color: {COLOR_WHITE}; }}
QDateEdit:focus {{ border: {BORDER_FOCUS}; border-top: 1.2px solid {COLOR_BORDER_TOP_FOCUS}; background-color: {COLOR_NEUTRAL_800}; }}
QDateEdit:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QDateEdit:read-only {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_400}; border: {BORDER_SUBTLE}; }}
QDateEdit::up-button, QDateEdit::down-button {{ width: 0px; height: 0px; border: none; background: transparent; }}
QDateEdit::up-arrow, QDateEdit::down-arrow {{ image: none; width: 0px; height: 0px; }}
QDateEdit::drop-down {{ subcontrol-origin: border; subcontrol-position: center right; width: 24px; height: 24px; right: 4px; border: none; background-color: transparent; }}
QDateEdit::drop-down:hover {{ background-color: {COLOR_NEUTRAL_750}; border-radius: {RADIUS_SM}px; }}
QDateEdit::drop-down:pressed {{ background-color: {COLOR_NEUTRAL_700}; border-radius: {RADIUS_SM}px; }}
QDateEdit::down-arrow {{ image: url("{PATH_ICON_CALENDAR}"); width: 16px; height: 16px; }}

/* CheckBox */
QCheckBox {{ spacing: 8px; color: {COLOR_NEUTRAL_400}; background-color: transparent; }}
QCheckBox:hover {{ color: {COLOR_WHITE}; }}
QCheckBox:focus {{ color: {COLOR_WHITE}; }}
QCheckBox::indicator {{ width: 14px; height: 14px; border-radius: {RADIUS_SM}px; border: 1.2px solid {COLOR_BORDER_TOP_SHINE}; border-top: 1.2px solid {COLOR_BORDER_LIGHT}; background-color: {COLOR_NEUTRAL_850}; }}
QCheckBox::indicator:focus, QCheckBox:focus::indicator {{ border-color: {COLOR_BORDER_MUTED_FOCUS}; }}
QCheckBox::indicator:unchecked:hover {{ border-color: {COLOR_NEUTRAL_700}; background-color: {COLOR_NEUTRAL_800}; }}
QCheckBox::indicator:unchecked:pressed {{ background-color: {COLOR_NEUTRAL_700}; }}
QCheckBox::indicator:checked {{ border: 1.2px solid {COLOR_KICK_BORDER}; border-top: 1.2px solid {COLOR_GREEN}; background-color: {GRADIENT_ACCENT_FILL}; image: url("{PATH_ICON_CHECK}"); }}
QCheckBox::indicator:checked:hover {{ background-color: {GRADIENT_ACCENT_HOVER}; }}
QCheckBox::indicator:checked:pressed {{ background-color: {GRADIENT_ACCENT_PRESSED}; }}
QCheckBox::indicator:indeterminate {{ border: 1.2px solid {COLOR_KICK_BORDER}; border-top: 1.2px solid {COLOR_GREEN}; background-color: {GRADIENT_ACCENT_FILL}; image: url("{PATH_ICON_MINUS}"); }}
QCheckBox::indicator:indeterminate:hover {{ background-color: {GRADIENT_ACCENT_HOVER}; }}
QCheckBox::indicator:indeterminate:pressed {{ background-color: {GRADIENT_ACCENT_PRESSED}; }}
QCheckBox:disabled {{ color: {COLOR_NEUTRAL_500}; }}
QCheckBox::indicator:disabled {{ border-color: {COLOR_NEUTRAL_750}; background-color: {COLOR_WHITE_GLOW}; }}
QCheckBox::indicator:checked:disabled {{ border-color: {COLOR_NEUTRAL_750}; background-color: {COLOR_WHITE_GLOW}; image: url("{PATH_ICON_CHECK}"); }}
QCheckBox::indicator:indeterminate:disabled {{ border-color: {COLOR_NEUTRAL_750}; background-color: {COLOR_WHITE_GLOW}; image: url("{PATH_ICON_MINUS}"); }}

/* RadioButton */
QRadioButton {{ spacing: 8px; color: {COLOR_NEUTRAL_400}; background-color: transparent; }}
QRadioButton:hover {{ color: {COLOR_WHITE}; }}
QRadioButton:focus {{ color: {COLOR_WHITE}; }}
QRadioButton::indicator {{ width: 14px; height: 14px; border-radius: 8px; border: 1.2px solid {COLOR_BORDER_TOP_SHINE}; border-top: 1.2px solid {COLOR_BORDER_LIGHT}; background-color: {COLOR_NEUTRAL_850}; }}
QRadioButton::indicator:focus, QRadioButton:focus::indicator {{ border-color: {COLOR_BORDER_MUTED_FOCUS}; }}
QRadioButton::indicator:unchecked:hover {{ border-color: {COLOR_NEUTRAL_700}; background-color: {COLOR_NEUTRAL_800}; }}
QRadioButton::indicator:unchecked:pressed {{ background-color: {COLOR_NEUTRAL_700}; }}
QRadioButton::indicator:checked {{ border: 1.2px solid {COLOR_KICK_BORDER}; border-top: 1.2px solid {COLOR_GREEN}; background-color: {GRADIENT_ACCENT_FILL}; image: url("{PATH_ICON_RADIO_DOT}"); }}
QRadioButton::indicator:checked:hover {{ background-color: {GRADIENT_ACCENT_HOVER}; }}
QRadioButton::indicator:checked:pressed {{ background-color: {GRADIENT_ACCENT_PRESSED}; }}
QRadioButton:disabled {{ color: {COLOR_NEUTRAL_500}; }}
QRadioButton::indicator:disabled {{ border-color: {COLOR_NEUTRAL_750}; background-color: {COLOR_WHITE_GLOW}; }}
QRadioButton::indicator:checked:disabled {{ border-color: {COLOR_NEUTRAL_750}; background-color: {COLOR_WHITE_GLOW}; image: url("{PATH_ICON_RADIO_DOT}"); }}

/* Slider */
QSlider::groove:horizontal {{ border: none; height: 6px; background: {COLOR_NEUTRAL_800}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {COLOR_GREEN}; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {COLOR_WHITE}; width: 14px; height: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; border: 1.2px solid {COLOR_BORDER_LIGHT}; }}
QSlider::handle:horizontal:hover {{ background-color: {COLOR_WHITE}; border: 1.2px solid {COLOR_GREEN}; }}
QSlider::handle:horizontal:pressed {{ background-color: {COLOR_NEUTRAL_200}; border: 1.2px solid {COLOR_GREEN_DARK}; }}
QSlider:disabled {{ opacity: 0.5; }}
QSlider::groove:horizontal:disabled {{ background: {COLOR_NEUTRAL_750}; }}
QSlider::sub-page:horizontal:disabled {{ background: {COLOR_NEUTRAL_700}; }}
QSlider::handle:horizontal:disabled {{ background-color: {COLOR_NEUTRAL_500}; border-color: {COLOR_NEUTRAL_700}; }}
"""


def _build_surface_qss(h1: int, h2: int, h3: int, text1: int, text2: int) -> str:
    return f"""
/* --- 5. Surfaces, Containers & Badges --- */
QFrame[role="canvas_container"] {{ background-color: {COLOR_NEUTRAL_950}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_MD}px; }}
QFrame[role="sidebar"] {{ background-color: {COLOR_NEUTRAL_900}; border-right: 1px solid {COLOR_NEUTRAL_750}; }}
QFrame[role="profile_card"] {{ background-color: transparent; border-radius: {RADIUS_MD}px; border: 1px solid transparent; }}
QFrame[role="profile_card"]:hover {{ background-color: {COLOR_NAV_HOVER}; border: 1px solid {COLOR_NEUTRAL_750}; }}
QFrame[role="update_banner_card"] {{ background-color: {COLOR_NEUTRAL_850}; border: 1px solid {COLOR_NEUTRAL_750}; border-radius: {RADIUS_LG}px; }}
QFrame[role="update_banner_card"]:hover {{ border-color: {COLOR_NEUTRAL_700}; }}
QFrame[role="update_icon_box"] {{ background-color: {COLOR_GREEN_GLOW}; border: 1.2px solid {COLOR_GREEN}; border-radius: {RADIUS_MD}px; }}
QFrame[role="card"] {{ background-color: {COLOR_NEUTRAL_850}; border: 1px solid {COLOR_NEUTRAL_750}; border-radius: {RADIUS_LG}px; }}
QFrame[role="danger_card"] {{ background-color: {COLOR_NEUTRAL_850}; border: 1px solid rgba(224, 49, 49, 0.35); border-radius: {RADIUS_LG}px; }}
QFrame[role="dialog"] {{ background-color: {COLOR_NEUTRAL_950}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_XL}px; }}
QFrame[role="dialog"][state="accent"] {{ border-color: {COLOR_GREEN}; }}
QFrame[role="dialog"][state="success"] {{ border-color: {COLOR_GREEN}; }}
QFrame[role="dialog"][state="danger"] {{ border-color: {COLOR_RED}; }}
QFrame[role="dialog"][state="error"] {{ border-color: {COLOR_RED}; }}
QFrame[role="dialog"][state="warning"] {{ border-color: {COLOR_AMBER}; }}
QFrame[role="dialog"][state="info"] {{ border-color: {COLOR_BLUE}; }}
QFrame[role="dialog"][state="neutral"] {{ border-color: {COLOR_NEUTRAL_700}; }}

QFrame[role="banner_danger"] {{ background-color: {COLOR_RED_GLOW}; border: 1.2px solid {COLOR_RED_DARK}; border-radius: {RADIUS_MD}px; }}
QFrame[role="banner_scope_card"] {{ background-color: {COLOR_NEUTRAL_900}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_LG}px; }}
QFrame[role="banner_scope_card"][state="kick"] {{ background-color: {COLOR_NEUTRAL_900}; border: 1.5px solid {COLOR_GREEN}; }}
QFrame[role="banner_scope_card"][state="twitch"] {{ background-color: {COLOR_NEUTRAL_900}; border: 1.5px solid {COLOR_PURPLE}; }}
QFrame[role="danger_icon"] {{ background-color: {COLOR_RED}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="warning_icon"] {{ background-color: {COLOR_AMBER}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="info_icon"] {{ background-color: {COLOR_BLUE}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="accent_icon"] {{ background-color: {COLOR_GREEN}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="tiktok_icon"] {{ background-color: {COLOR_TIKTOK}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="youtube_icon"] {{ background-color: {COLOR_YOUTUBE}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="twitch_icon"] {{ background-color: {COLOR_TWITCH}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="black_icon"] {{ background-color: {COLOR_BLACK}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="divider"] {{ background-color: {COLOR_NEUTRAL_750}; min-height: 1px; max-height: 1px; border: none; margin: 0px; padding: 0px; }}

QFrame[role="bot_tag"] {{ background-color: {COLOR_NEUTRAL_850}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_MD}px; }}
QFrame[role="bot_tag"]:hover {{ border-color: {COLOR_RED}; }}
QFrame[role="bot_tag"] QLabel {{ color: {COLOR_NEUTRAL_400}; font-size: {text2}px; }}
QFrame[role="toast"] {{ background-color: {COLOR_NEUTRAL_900}; border: {BORDER_MUTED}; border-radius: {RADIUS_MD}px; }}
QFrame[role="toast"][state="success"] {{ border-color: {COLOR_GREEN}; }}
QFrame[role="toast"][state="danger"] {{ border-color: {COLOR_RED}; }}
QFrame[role="toast"][state="warning"] {{ border-color: {COLOR_AMBER}; }}
QFrame[role="toast"][state="info"] {{ border-color: {COLOR_BLUE}; }}

/* Badges & Tags */
QFrame[role="badge"] {{ background-color: {COLOR_NEUTRAL_850}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_MD}px; min-height: 20px; max-height: 22px; }}
QFrame[role="badge"] QLabel {{ font-size: {text2}px; font-weight: 500; color: {COLOR_NEUTRAL_400}; background: transparent; }}
QFrame[role="badge"][state="everyone"] {{ background-color: {COLOR_GREEN_GLOW}; border-color: {COLOR_GREEN}; }}
QFrame[role="badge"][state="everyone"] QLabel {{ color: {COLOR_GREEN}; }}
QFrame[role="badge"][state="subscriber"] {{ background-color: {COLOR_BLUE_GLOW}; border-color: {COLOR_BLUE}; }}
QFrame[role="badge"][state="subscriber"] QLabel {{ color: {COLOR_BLUE}; }}
QFrame[role="badge"][state="vip"] {{ background-color: {COLOR_PURPLE_GLOW}; border-color: {COLOR_PURPLE}; }}
QFrame[role="badge"][state="vip"] QLabel {{ color: {COLOR_PURPLE}; }}
QFrame[role="badge"][state="moderator"] {{ background-color: {COLOR_AMBER_GLOW}; border-color: {COLOR_AMBER}; }}
QFrame[role="badge"][state="moderator"] QLabel {{ color: {COLOR_AMBER}; }}
QFrame[role="badge"][state="broadcaster"] {{ background-color: {COLOR_RED_GLOW}; border-color: {COLOR_RED}; }}
QFrame[role="badge"][state="broadcaster"] QLabel {{ color: {COLOR_RED}; }}
QFrame[role="badge"][state="warning"] {{ background-color: {COLOR_AMBER_GLOW}; border-color: {COLOR_AMBER}; }}
QFrame[role="badge"][state="warning"] QLabel {{ color: {COLOR_AMBER}; }}
QFrame[role="badge"][state="plugin"] {{ background-color: {COLOR_PURPLE_GLOW}; border-color: {COLOR_PURPLE}; }}
QFrame[role="badge"][state="plugin"] QLabel {{ color: {COLOR_PURPLE}; }}
QFrame[role="badge"][state="kick"] {{ background-color: {COLOR_GREEN_GLOW}; border-color: {COLOR_GREEN}; }}
QFrame[role="badge"][state="kick"] QLabel {{ color: {COLOR_GREEN}; }}
QFrame[role="badge"][state="twitch"] {{ background-color: {COLOR_PURPLE_GLOW}; border-color: {COLOR_PURPLE}; }}
QFrame[role="badge"][state="twitch"] QLabel {{ color: {COLOR_PURPLE}; }}

QLabel[role="badge_kick"] {{ background-color: {COLOR_GREEN_GLOW}; color: {COLOR_GREEN}; font-weight: 500; border-radius: {RADIUS_MD}px; padding: {PADDING_BADGE}; font-size: {text2}px; border: 1.5px solid {COLOR_GREEN}; min-height: 18px; max-height: 22px; }}
QLabel[role="badge_twitch"] {{ background-color: {COLOR_PURPLE_GLOW}; color: {COLOR_PURPLE}; font-weight: 500; border-radius: {RADIUS_MD}px; padding: {PADDING_BADGE}; font-size: {text2}px; border: 1.5px solid {COLOR_PURPLE}; min-height: 18px; max-height: 22px; }}
QLabel[role="channel_avatar"] {{ border-radius: 48px; background-color: {COLOR_NEUTRAL_800}; border: 2px solid {COLOR_NEUTRAL_700}; }}
QLabel[role="rank_number"] {{ color: {COLOR_GREEN}; font-weight: 500; min-width: 20px; }}
QLineEdit[state="plugin"], QTextEdit[state="plugin"], QPlainTextEdit[state="plugin"] {{ border: 1.2px solid {COLOR_PURPLE}; color: {COLOR_PURPLE}; font-weight: 500; background-color: {COLOR_NEUTRAL_900}; }}
QTextEdit[role="ConsoleDisplay"] {{ font-family: 'GoogleSansCode Nerd Font', 'GoogleSansCode NF', Consolas, monospace; background-color: {COLOR_NEUTRAL_950}; color: {COLOR_NEUTRAL_200}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_MD}px; }}
QTextBrowser[role="release_notes_browser"] {{ background-color: {COLOR_NEUTRAL_950}; color: {COLOR_NEUTRAL_400}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_MD}px; padding: 12px; }}

/* Table Widget */
QTableWidget {{ background-color: {COLOR_NEUTRAL_850}; border: none; gridline-color: transparent; border-bottom-left-radius: {RADIUS_LG}px; border-bottom-right-radius: {RADIUS_LG}px; }}
QTableWidget::item {{ padding: 2px 8px; border-bottom: 1.2px solid {COLOR_NEUTRAL_800}; }}
QTableWidget::item:hover:!selected {{ background-color: {COLOR_NEUTRAL_900}; }}
QTableWidget::item:selected {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QTableWidget::item:disabled {{ color: {COLOR_NEUTRAL_500}; }}
QHeaderView, QHeaderView::section {{ background-color: transparent; border: none; }}
QHeaderView::section {{ color: {COLOR_NEUTRAL_400}; font-weight: 500; padding: {PADDING_INPUT}; border-bottom: 1.2px solid {COLOR_NEUTRAL_750}; text-align: left; }}
QHeaderView::section:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QHeaderView::section:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}

/* Scrollbars */
QScrollBar:vertical {{ border: none; background: transparent; width: 12px; margin: 4px 2px 4px 2px; }}
QScrollBar::handle:vertical {{ background-color: rgba(255, 255, 255, 0.16); border-radius: {RADIUS_XS}px; min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background-color: rgba(255, 255, 255, 0.32); }}
QScrollBar::handle:vertical:pressed {{ background-color: rgba(255, 255, 255, 0.48); }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ height: 0px; background: none; }}

QScrollBar:horizontal {{ border: none; background: transparent; height: 10px; margin: 2px 4px 2px 4px; }}
QScrollBar::handle:horizontal {{ background-color: rgba(255, 255, 255, 0.16); border-radius: {RADIUS_XS}px; min-width: 28px; }}
QScrollBar::handle:horizontal:hover {{ background-color: rgba(255, 255, 255, 0.32); }}
QScrollBar::handle:horizontal:pressed {{ background-color: rgba(255, 255, 255, 0.48); }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal, QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ width: 0px; background: none; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: transparent; border: none; }}

/* Progress Bars */
QProgressBar {{ background-color: {COLOR_NEUTRAL_850}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_XS}px; height: 6px; text-align: center; }}
QProgressBar::chunk {{ background-color: {COLOR_GREEN}; border-radius: 3px; }}
QProgressBar:disabled {{ background-color: {COLOR_WHITE_GLOW}; border-color: {COLOR_NEUTRAL_800}; }}
QProgressBar::chunk:disabled {{ background-color: {COLOR_NEUTRAL_700}; }}
QProgressBar[role="update_progress"] {{ background-color: {COLOR_NEUTRAL_900}; border: none; border-radius: {RADIUS_SM}px; }}
QProgressBar[role="update_progress"]::chunk {{ background-color: {COLOR_GREEN}; border-radius: {RADIUS_SM}px; }}
QProgressBar[role="wizard_progress"] {{ background-color: {COLOR_NEUTRAL_750}; border: none; border-radius: {RADIUS_2XS}px; }}
QProgressBar[role="wizard_progress"]::chunk {{ background-color: {COLOR_GREEN}; border-radius: {RADIUS_2XS}px; }}
QProgressBar[role="top_command_progress"] {{ background-color: {COLOR_NEUTRAL_750}; border: none; border-radius: 4px; height: 8px; }}
QProgressBar[role="top_command_progress"]::chunk {{ background-color: {COLOR_BLUE}; border-radius: 4px; }}

/* Tab Widget */
QTabWidget::pane {{ border: {BORDER_SUBTLE}; border-radius: {RADIUS_LG}px; border-top-left-radius: 0px; background-color: {COLOR_NEUTRAL_900}; padding: 0px; }}
QTabBar::tab {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_400}; border: {BORDER_SUBTLE}; border-bottom-color: transparent; border-top-left-radius: 0px; border-top-right-radius: {RADIUS_MD}px; padding: {PADDING_TAB}; margin-right: 4px; font-weight: 500; }}
QTabBar::tab:selected {{ color: {COLOR_WHITE}; background-color: {COLOR_NEUTRAL_900}; border-color: {COLOR_NEUTRAL_750}; border-bottom-color: {COLOR_NEUTRAL_900}; }}
QTabBar::tab:hover:!selected {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QTabBar::tab:pressed:!selected {{ background-color: {COLOR_NEUTRAL_750}; }}
QTabBar::tab:focus {{ border-color: {COLOR_NEUTRAL_700}; }}
QTabBar::tab:disabled {{ background-color: {COLOR_NEUTRAL_950}; color: {COLOR_NEUTRAL_500}; border-color: {COLOR_NEUTRAL_800}; }}
QTabWidget QFrame[role="tab_panel"] {{ background-color: transparent; border: none; }}

/* ToolTip */
QToolTip {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; border: {BORDER_MUTED}; border-radius: {RADIUS_SM}px; padding: {PADDING_INPUT}; font-size: {text1}px; }}
QListWidget[role="transparent_list"] {{ background: transparent; border: none; }}
QListWidget[role="transparent_list"]::item {{ background: transparent; }}
"""


def _build_complex_qss(text1: int, text2: int) -> str:
    return f"""
/* --- 6. Complex Composite Widgets --- */

/* Search Bar */
QFrame[role="search_bar"] {{ background-color: {COLOR_NEUTRAL_850}; border: {BORDER_DEFAULT}; border-top: 1.2px solid {COLOR_BORDER_TOP_SHINE}; border-radius: {RADIUS_MD}px; min-height: 34px; }}
QFrame[role="search_bar"]:hover {{ border-color: {COLOR_NEUTRAL_700}; }}
QFrame[role="search_bar"]:focus, QFrame[role="search_bar"][state="focused"] {{ border: {BORDER_FOCUS}; border-top: 1.2px solid {COLOR_BORDER_TOP_FOCUS}; }}
QFrame[role="search_bar"] QLineEdit {{ background: transparent; border: none; padding: {PADDING_INPUT}; color: {COLOR_WHITE}; font-size: {text1}px; }}
QFrame[role="search_bar"] QPushButton {{ background: transparent; border: none; border-left: 1.2px solid {COLOR_NEUTRAL_750}; border-top-right-radius: {RADIUS_MD_INNER}px; border-bottom-right-radius: {RADIUS_MD_INNER}px; min-width: 36px; max-width: 36px; min-height: 32px; max-height: 32px; }}
QFrame[role="search_bar"] QPushButton:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QFrame[role="search_bar"] QPushButton:focus {{ background-color: {COLOR_NEUTRAL_750}; }}
QFrame[role="search_bar"] QPushButton:pressed {{ background-color: {COLOR_NEUTRAL_700}; }}

/* Category Dropdown */
QFrame[role="category_dropdown"] {{ background-color: {COLOR_NEUTRAL_950}; border: {BORDER_MUTED}; border-radius: {RADIUS_MD}px; }}
QListWidget[role="category_list"] {{ background: transparent; border: none; outline: none; }}
QListWidget[role="category_list"]::item {{ background: transparent; border-radius: {RADIUS_SM}px; padding: 2px; min-height: 32px; }}
QListWidget[role="category_list"]::item:hover, QListWidget[role="category_list"]::item:selected {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}

/* Segmented Control */
QFrame[role="segmented_control"] {{ background-color: {COLOR_NEUTRAL_900}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_MD}px; padding: 3px; }}
QPushButton[role="segmented_item"] {{ background-color: transparent; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_SM}px; padding: 4px 8px; color: {COLOR_NEUTRAL_400}; }}
QPushButton[role="segmented_item"]:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QPushButton[role="segmented_item"]:focus {{ border: {BORDER_MUTED}; }}
QPushButton[role="segmented_item"]:checked {{ background-color: {GRADIENT_NEUTRAL_FILL}; border: 1.2px solid {COLOR_BORDER_TOP_SHINE}; border-top: 1.2px solid {COLOR_BORDER_LIGHT}; color: {COLOR_WHITE}; font-weight: 500; }}
QPushButton[role="segmented_item"]:checked:hover {{ background-color: {GRADIENT_NEUTRAL_HOVER}; }}
QPushButton[role="segmented_item"]:checked:pressed {{ background-color: {GRADIENT_NEUTRAL_PRESSED}; }}
QPushButton[role="segmented_item"]:pressed {{ background-color: {GRADIENT_NEUTRAL_PRESSED}; }}
QPushButton[role="segmented_item"]:disabled {{ color: {COLOR_NEUTRAL_500}; }}

/* Segmented Pagination */
QFrame[role="segmented_pagination"] {{ background-color: {GRADIENT_NEUTRAL_FILL}; border: 1.2px solid {COLOR_BORDER_TOP_SHINE}; border-top: 1.2px solid {COLOR_BORDER_LIGHT}; border-radius: {RADIUS_MD}px; }}
QFrame[role="segmented_pagination"] QPushButton {{ background: transparent; border: none; border-left: 1.2px solid {COLOR_NEUTRAL_750}; min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; }}
QFrame[role="segmented_pagination"] QPushButton#btn_first {{ border-left: none; border-top-left-radius: {RADIUS_MD_INNER}px; border-bottom-left-radius: {RADIUS_MD_INNER}px; }}
QFrame[role="segmented_pagination"] QPushButton#btn_last {{ border-top-right-radius: {RADIUS_MD_INNER}px; border-bottom-right-radius: {RADIUS_MD_INNER}px; }}
QFrame[role="segmented_pagination"] QPushButton:hover:enabled {{ background-color: {COLOR_NEUTRAL_750}; }}
QFrame[role="segmented_pagination"] QPushButton:focus:enabled {{ background-color: {COLOR_NEUTRAL_700}; }}
QFrame[role="segmented_pagination"] QPushButton:pressed:enabled {{ background-color: {COLOR_NEUTRAL_800}; }}
QFrame[role="segmented_pagination"] QPushButton:disabled {{ background-color: transparent; color: {COLOR_NEUTRAL_500}; }}
QFrame[role="segmented_pagination"] QLabel#lbl_page_status {{ background-color: transparent; color: {COLOR_WHITE}; font-size: {text1}px; font-weight: 500; padding: 0px 16px; min-height: 32px; max-height: 32px; border-left: 1.2px solid {COLOR_NEUTRAL_750}; }}

/* Calendar Pop-up (QCalendarWidget) */
QCalendarWidget {{ background-color: {COLOR_NEUTRAL_900}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_LG}px; padding: 4px; }}
QCalendarWidget QWidget#qt_calendar_navigationbar {{ background-color: transparent; border: none; min-height: 36px; margin-bottom: 4px; }}
QCalendarWidget QToolButton {{ background-color: transparent; color: {COLOR_WHITE}; font-weight: 500; font-size: {text1}px; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_SM}px; padding: {PADDING_ITEM}; margin: 2px; }}
QCalendarWidget QToolButton:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QCalendarWidget QToolButton:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}
QCalendarWidget QToolButton#qt_calendar_prevmonth {{ qproperty-icon: url("{PATH_ICON_CHEVRON_LEFT}"); icon-size: 16px; width: 26px; height: 26px; }}
QCalendarWidget QToolButton#qt_calendar_nextmonth {{ qproperty-icon: url("{PATH_ICON_CHEVRON_RIGHT}"); icon-size: 16px; width: 26px; height: 26px; }}
QCalendarWidget QToolButton#qt_calendar_monthbutton, QCalendarWidget QToolButton#qt_calendar_yearbutton {{ color: {COLOR_WHITE}; font-size: {text1 + 1}px; font-weight: 500; padding: {PADDING_ITEM}; }}
QCalendarWidget QMenu {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_400}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_MD}px; padding: 4px; }}
QCalendarWidget QSpinBox {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_WHITE}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_SM}px; padding: 2px 6px; font-weight: 500; }}
QCalendarWidget QSpinBox:focus {{ border-color: {COLOR_BORDER_MUTED_FOCUS}; }}
QCalendarWidget QTableView {{ background-color: transparent; border: none; gridline-color: transparent; selection-background-color: {COLOR_WHITE}; selection-color: {COLOR_NEUTRAL_950}; outline: none; }}
QCalendarWidget QTableView:enabled {{ color: {COLOR_NEUTRAL_400}; }}
QCalendarWidget QTableView:disabled {{ color: {COLOR_NEUTRAL_700}; }}
QHeaderView, QCalendarWidget QHeaderView::section {{ background-color: transparent; color: {COLOR_NEUTRAL_400}; font-size: {text2}px; font-weight: 500; padding: 3px 0px; border: none; text-align: center; }}
QCalendarWidget QTableView::item {{ border-radius: {RADIUS_MD_INNER}px; padding: 4px; margin: 2px; }}
QCalendarWidget QTableView::item:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; border-radius: {RADIUS_MD_INNER}px; }}
QCalendarWidget QTableView::item:selected {{ background-color: {COLOR_WHITE}; color: {COLOR_NEUTRAL_950}; font-weight: 700; border-radius: {RADIUS_MD_INNER}px; }}
"""

@lru_cache(maxsize=16)
def get_global_qss(base: int = 13) -> str:
    size_h1 = base + 12
    size_h2 = base + 9
    size_h3 = base + 3
    size_text1 = base
    size_text2 = max(10, base - 1)

    sections = [
        _build_reset_and_typography_qss(size_h1, size_h2, size_h3, size_text1, size_text2),
        _build_button_qss(size_text1, size_text2),
        _build_input_qss(size_text1, size_text2),
        _build_surface_qss(size_h1, size_h2, size_h3, size_text1, size_text2),
        _build_complex_qss(size_text1, size_text2),
    ]
    return "\n".join(sections)

GLOBAL_QSS = get_global_qss(13)

def get_swatch_qss(bg_color: str, border_width: int = 1, radius: int = RADIUS_SM) -> str:
    return f"background-color: {bg_color}; border: {border_width}px solid {COLOR_NEUTRAL_700}; border-radius: {radius}px;"
