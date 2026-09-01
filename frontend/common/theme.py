# frontend\common\theme.py

import os
import re
import tempfile
from functools import lru_cache
from pathlib import Path
from frontend.common.paths import get_assets_path, resolve_icon_path

COLOR_NEUTRAL_950  = "#0C0B0E"
COLOR_NEUTRAL_900  = "#121115"
COLOR_NEUTRAL_850  = "#18171C"
COLOR_NEUTRAL_800  = "#201E25"
COLOR_NEUTRAL_750  = "#27262D"
COLOR_NEUTRAL_700  = "#38363E"
COLOR_NEUTRAL_500  = "#6E6C78"
COLOR_NEUTRAL_400  = "#9D9AA8"
COLOR_NEUTRAL_200  = "#E4E3EA"
COLOR_WHITE        = "#FAFAFA"
COLOR_BLACK        = "#000000"

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

PADDING_INPUT      = "6px 10px"
PADDING_BUTTON     = "6px 14px"
PADDING_SPINBOX    = "4px 20px 4px 10px"
PADDING_ITEM       = "4px 6px"
PADDING_BADGE      = "2px 8px"
PADDING_CHIP       = "4px 12px"
PADDING_TAB        = "6px 16px"
PADDING_MENU_ITEM  = "5px 12px 5px 18px"

BORDER_DEFAULT     = f"1.2px solid {COLOR_NEUTRAL_750}"
BORDER_SUBTLE      = f"1.2px solid {COLOR_NEUTRAL_800}"
BORDER_MUTED       = f"1.2px solid {COLOR_NEUTRAL_700}"
BORDER_TRANSPARENT = "1.2px solid transparent"
BORDER_FOCUS       = "1.2px solid #5E5C66"
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

PATH_ICON_HELP          = get_qss_colored_icon("icons/help.svg", COLOR_WHITE)
PATH_ICON_CHEVRON_DOWN  = get_qss_colored_icon("icons/chevron-down.svg", COLOR_NEUTRAL_400)
PATH_ICON_CHEVRON_UP    = get_qss_colored_icon("icons/chevron-up.svg", COLOR_NEUTRAL_400)
PATH_ICON_CHEVRON_LEFT  = get_qss_colored_icon("icons/chevron-left.svg", COLOR_NEUTRAL_400)
PATH_ICON_CHEVRON_RIGHT = get_qss_colored_icon("icons/chevron-right.svg", COLOR_NEUTRAL_400)
PATH_ICON_CHECK         = _get_qss_icon_url("icons/check.svg")
PATH_ICON_CHECK_GREEN   = get_qss_colored_icon("icons/check.svg", COLOR_GREEN)
PATH_ICON_CALENDAR      = get_qss_colored_icon("icons/calendar.svg", COLOR_NEUTRAL_400)

def _build_reset_and_typography_qss(h1: int, h2: int, h3: int, text1: int, text2: int) -> str:
    return f"""
/* --- 1. Reset & Root Surfaces --- */
* {{ font-family: {FONT_FAMILY}; font-size: {text1}px; color: {COLOR_NEUTRAL_400}; outline: none; }}
QMainWindow {{ background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 {COLOR_NEUTRAL_950}, stop:1 {COLOR_NEUTRAL_900}); }}
QDialog {{ background-color: {COLOR_NEUTRAL_950}; }}
QLabel {{ background-color: transparent; }}

/* --- 2. Typography Scale --- */
QLabel[role="h1"] {{ font-size: {h1}px; font-weight: 600; color: {COLOR_WHITE}; }}
QLabel[role="h2"] {{ font-size: {h2}px; font-weight: 600; color: {COLOR_NEUTRAL_200}; }}
QLabel[role="h3"] {{ font-size: {h3}px; font-weight: 600; color: {COLOR_NEUTRAL_200}; }}
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
QLabel[role="code"] {{ font-size: {text2}px; font-weight: 600; background-color: {COLOR_NEUTRAL_850}; padding: 2px 6px; border-radius: {RADIUS_SM}px; color: {COLOR_NEUTRAL_200}; border: {BORDER_SUBTLE}; }}
QLabel[role="category"] {{ font-weight: 600; color: {COLOR_GREEN}; margin-top: 6px; font-size: {text2}px; }}
"""


def _build_button_qss(text1: int, text2: int) -> str:
    return f"""
/* --- 3. Modern Figma Gradient Buttons --- */
QPushButton {{ border: {BORDER_TRANSPARENT}; font-size: {text1}px; font-weight: 600; }}
QPushButton:focus {{ outline: none; }}

/* Neutral & Outlined Buttons (Figma Spec) */
QPushButton[role="action_outlined"], QPushButton[role="action_neutral_border"] {{ background-color: {GRADIENT_NEUTRAL_FILL}; color: {COLOR_WHITE}; font-size: {text1}px; font-weight: 600; border: 1.2px solid #38363E; border-top: 1.2px solid #4B4951; border-bottom: 1.2px solid #313036; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_outlined"]:hover, QPushButton[role="action_neutral_border"]:hover {{ background-color: {GRADIENT_NEUTRAL_HOVER}; border: 1.2px solid #45434C; border-top: {BORDER_FOCUS}; border-bottom: 1.2px solid #38363E; color: {COLOR_WHITE}; }}
QPushButton[role="action_outlined"]:pressed, QPushButton[role="action_neutral_border"]:pressed {{ background-color: {GRADIENT_NEUTRAL_PRESSED}; border: 1.2px solid #28272D; border-top: 1.2px solid #201E25; border-bottom: 1.2px solid #35343A; }}
QPushButton[role="action_outlined"]:focus, QPushButton[role="action_neutral_border"]:focus {{ border: {BORDER_FOCUS}; border-top: 1.2px solid #71717A; }}

/* Primary Accent & Kick Buttons */
QPushButton[role="action_accent"], QPushButton[role="action_kick"] {{ background-color: {GRADIENT_ACCENT_FILL}; color: {COLOR_WHITE}; font-size: {text1}px; font-weight: 600; border: 1.2px solid #1A7A42; border-top: 1.2px solid #2ECD70; border-bottom: 1.2px solid #125E31; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_accent"]:hover, QPushButton[role="action_kick"]:hover {{ background-color: {GRADIENT_ACCENT_HOVER}; border: 1.2px solid #1E8E4D; border-top: 1.2px solid #3DE082; border-bottom: 1.2px solid #15733C; }}
QPushButton[role="action_accent"]:pressed, QPushButton[role="action_kick"]:pressed {{ background-color: {GRADIENT_ACCENT_PRESSED}; border: 1.2px solid #125E31; border-top: 1.2px solid #146133; border-bottom: 1.2px solid #1E8E4D; }}
QPushButton[role="action_accent"]:focus, QPushButton[role="action_kick"]:focus {{ border: 1.2px solid #2ECD70; }}
QPushButton[role="action_kick"]:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border: {BORDER_SUBTLE}; }}

/* Platform: Twitch Button */
QPushButton[role="action_twitch"] {{ background-color: {GRADIENT_TWITCH_FILL}; color: {COLOR_WHITE}; font-size: {text1}px; font-weight: 600; border: 1.2px solid #6722CD; border-top: 1.2px solid #9146FF; border-bottom: 1.2px solid #4D0FA8; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_twitch"]:hover {{ background-color: {GRADIENT_TWITCH_HOVER}; border: 1.2px solid #772CE8; border-top: 1.2px solid #A855F7; border-bottom: 1.2px solid #5C16C5; }}
QPushButton[role="action_twitch"]:pressed {{ background-color: {GRADIENT_TWITCH_PRESSED}; border: 1.2px solid #4D0FA8; }}
QPushButton[role="action_twitch"]:focus {{ border: 1.2px solid #9146FF; }}
QPushButton[role="action_twitch"]:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border: {BORDER_SUBTLE}; }}

/* Platform: YouTube Button */
QPushButton[role="action_youtube"] {{ background-color: {GRADIENT_YOUTUBE_FILL}; color: {COLOR_WHITE}; font-size: {text1}px; font-weight: 600; border: 1.2px solid #B80323; border-top: 1.2px solid #EF233C; border-bottom: 1.2px solid #8D0019; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_youtube"]:hover {{ background-color: {GRADIENT_YOUTUBE_HOVER}; border: 1.2px solid #D90429; border-top: 1.2px solid #FF4D6D; border-bottom: 1.2px solid #AA001E; }}
QPushButton[role="action_youtube"]:pressed {{ background-color: {GRADIENT_YOUTUBE_PRESSED}; border: 1.2px solid #8D0019; }}
QPushButton[role="action_youtube"]:focus {{ border: 1.2px solid #EF4444; }}
QPushButton[role="action_youtube"]:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border: {BORDER_SUBTLE}; }}

/* Platform: TikTok Button */
QPushButton[role="action_tiktok"] {{ background-color: {GRADIENT_TIKTOK_FILL}; color: {COLOR_BLACK}; font-size: {text1}px; font-weight: 700; border: 1.2px solid #009DA8; border-top: 1.2px solid #00F2FE; border-bottom: 1.2px solid #00747C; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_tiktok"]:hover {{ background-color: {GRADIENT_TIKTOK_HOVER}; border: 1.2px solid #00B8C4; border-top: 1.2px solid #5EF8FF; border-bottom: 1.2px solid #008891; }}
QPushButton[role="action_tiktok"]:pressed {{ background-color: {GRADIENT_TIKTOK_PRESSED}; border: 1.2px solid #00747C; }}
QPushButton[role="action_tiktok"]:focus {{ border: 1.2px solid #00F2FE; }}
QPushButton[role="action_tiktok"]:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border: {BORDER_SUBTLE}; }}

/* Subtle Danger Action Button */
QPushButton[role="action_danger_border"] {{ background-color: {GRADIENT_DANGER_FILL}; color: {COLOR_RED}; font-size: {text1}px; font-weight: 600; border: 1.2px solid #451B1D; border-top: 1.2px solid #7F1D1D; border-bottom: 1.2px solid #331416; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_danger_border"]:hover {{ background-color: {GRADIENT_DANGER_HOVER}; border: 1.2px solid #5C2326; border-top: 1.2px solid #991B1B; border-bottom: 1.2px solid #40181A; color: #F87171; }}
QPushButton[role="action_danger_border"]:pressed {{ background-color: {GRADIENT_DANGER_PRESSED}; border: 1.2px solid #2B1113; }}
QPushButton[role="action_danger_border"]:focus {{ border: 1.2px solid #991B1B; }}

/* Subtle Accent Action Button */
QPushButton[role="action_accent_border"] {{ background-color: {GRADIENT_ACCENT_SUBTLE_FILL}; color: {COLOR_GREEN}; font-size: {text1}px; font-weight: 600; border: 1.2px solid #1E3B27; border-top: 1.2px solid #14532D; border-bottom: 1.2px solid #162B1D; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_accent_border"]:hover {{ background-color: {GRADIENT_ACCENT_SUBTLE_HOVER}; border: 1.2px solid #285437; border-top: 1.2px solid #166534; border-bottom: 1.2px solid #1E3B27; color: #4ADE80; }}
QPushButton[role="action_accent_border"]:pressed {{ background-color: {GRADIENT_ACCENT_SUBTLE_PRESSED}; border: 1.2px solid #122418; }}
QPushButton[role="action_accent_border"]:focus {{ border: 1.2px solid #166534; }}

/* Ghost & Utility Buttons */
QPushButton[role="btn_ghost"] {{ background-color: transparent; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_SM}px; }}
QPushButton[role="btn_ghost"]:hover {{ background-color: {COLOR_NEUTRAL_800}; border: 1.2px solid #313036; border-top: 1.2px solid #38363E; }}
QPushButton[role="btn_ghost"]:focus {{ background-color: {COLOR_NEUTRAL_800}; border: 1.2px solid #38363E; }}
QPushButton[role="btn_dismiss"] {{ background-color: transparent; border: none; border-radius: {RADIUS_SM}px; padding: 2px; }}
QPushButton[role="btn_dismiss"]:hover {{ background-color: {COLOR_NEUTRAL_800}; }}

/* Sidebar Navigation Buttons */
QPushButton[role="nav_button"] {{ background: transparent; border-radius: {RADIUS_MD}px; padding: 10px; text-align: left; color: {COLOR_NEUTRAL_400}; font-weight: 500; border: {BORDER_TRANSPARENT}; }}
QPushButton[role="nav_button"]:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; border: 1.2px solid #27262D; border-top: 1.2px solid #313036; }}
QPushButton[role="nav_button"]:focus {{ border: 1.2px solid #38363E; }}
QPushButton[role="nav_button"]:checked {{ background-color: {GRADIENT_NEUTRAL_FILL}; color: {COLOR_GREEN}; font-weight: 600; border: 1.2px solid #313036; border-top: 1.2px solid #4B4951; }}
QPushButton[role="nav_button"][collapsed="false"] {{ text-align: left; padding-left: 10px; }}
QPushButton[role="nav_button"][collapsed="true"] {{ text-align: center; padding: 10px 0px; }}

/* Filter Chips */
QPushButton[role="filter_chip"] {{ background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #1D1C21, stop:1 #27262C); color: {COLOR_NEUTRAL_400}; border: 1.2px solid #313036; border-top: 1.2px solid #3F3D47; border-radius: {RADIUS_SM}px; padding: {PADDING_CHIP}; font-size: {text2}px; font-weight: 600; }}
QPushButton[role="filter_chip"]:hover {{ background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #25242A, stop:1 #323038); border-color: #4B4951; color: {COLOR_WHITE}; }}
QPushButton[role="filter_chip"]:focus {{ border-color: #5E5C66; }}
QPushButton[role="filter_chip"]:checked {{ background-color: {GRADIENT_ACCENT_FILL}; color: {COLOR_WHITE}; border: 1.2px solid #1A7A42; border-top: 1.2px solid #2ECD70; font-weight: 600; }}

/* Global Disabled Button States */
QPushButton:disabled, QPushButton[role="action_accent"]:disabled, QPushButton[role="action_outlined"]:disabled, QPushButton[role="action_danger_border"]:disabled, QPushButton[role="action_accent_border"]:disabled, QPushButton[role="action_neutral_border"]:disabled, QPushButton[role="btn_ghost"]:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border: {BORDER_SUBTLE}; padding: {PADDING_BUTTON}; }}
"""


def _build_input_qss(text1: int, text2: int) -> str:
    return f"""
/* --- 4. Form Controls & Inputs --- */
QLineEdit, QTextEdit, QPlainTextEdit {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_INPUT}; border: {BORDER_DEFAULT}; border-top: 1.2px solid #38363E; }}
QTextEdit, QPlainTextEdit {{ background-color: {COLOR_NEUTRAL_900}; }}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border: {BORDER_FOCUS}; border-top: 1.2px solid #71717A; background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QLineEdit[state="error"], QTextEdit[state="error"], QPlainTextEdit[state="error"] {{ border: {BORDER_ERROR}; }}
QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border-color: {COLOR_NEUTRAL_750}; padding: {PADDING_INPUT}; }}

/* ComboBox */
QComboBox {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_INPUT}; border: {BORDER_DEFAULT}; border-top: 1.2px solid #38363E; combobox-popup: 0; }}
QComboBox:focus, QComboBox:hover {{ background-color: {COLOR_NEUTRAL_800}; border-color: {COLOR_NEUTRAL_700}; color: {COLOR_WHITE}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 24px; border-left: {BORDER_SUBTLE}; border-top-right-radius: {RADIUS_MD}px; border-bottom-right-radius: {RADIUS_MD}px; }}
QComboBox:focus::drop-down, QComboBox:hover::drop-down {{ border-color: {COLOR_NEUTRAL_700}; }}
QComboBox::drop-down:hover {{ background-color: {COLOR_NEUTRAL_800}; border-color: {COLOR_NEUTRAL_700}; }}
QComboBox::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 14px; height: 14px; }}
QComboBox::down-arrow:on {{ top: 1px; left: 1px; }}
QComboBox QAbstractItemView {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_200}; border: 1.2px solid #38363E; border-radius: {RADIUS_MD}px; selection-background-color: {COLOR_NEUTRAL_800}; selection-color: {COLOR_WHITE}; }}
QComboBox QAbstractItemView::item {{ border-radius: {RADIUS_SM}px; padding: {PADDING_ITEM}; margin: 1px 2px; }}
QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover, QComboBox QListView::item:selected, QComboBox QListView::item:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; border: 1.2px solid #313036; }}

/* Context Menus */
QMenu {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_200}; border: 1.2px solid #38363E; border-radius: {RADIUS_MD}px; padding: 4px; }}
QMenu::item {{ padding: 5px 12px; margin: 1px 2px; border-radius: {RADIUS_SM}px; color: {COLOR_NEUTRAL_200}; font-size: {text2}px; font-weight: 500; }}
QMenu::item:disabled {{ color: {COLOR_NEUTRAL_500}; background-color: transparent; }}
QMenu::item:selected {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; border: 1.2px solid #313036; }}
QMenu::icon {{ margin-left: 14px; }}
QMenu::indicator {{ width: 14px; height: 14px; left: 8px; }}
QMenu::indicator:checked {{ image: url("{PATH_ICON_CHECK_GREEN}"); }}
QMenu::indicator:unchecked {{ image: none; }}
QMenu::separator {{ height: 1px; background-color: {COLOR_NEUTRAL_800}; margin: 1px 2px; }}

/* SpinBoxes */
QSpinBox, QDoubleSpinBox, QTimeEdit {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_SPINBOX}; border: {BORDER_DEFAULT}; border-top: 1.2px solid #38363E; selection-background-color: transparent; selection-color: {COLOR_WHITE}; }}
QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {{ border: {BORDER_FOCUS}; border-top: 1.2px solid #71717A; background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QSpinBox:hover, QDoubleSpinBox:hover, QTimeEdit:hover {{ background-color: {COLOR_NEUTRAL_800}; border-color: {COLOR_NEUTRAL_700}; }}
QSpinBox::up-button, QDoubleSpinBox::up-button, QTimeEdit::up-button {{ subcontrol-origin: border; subcontrol-position: center right; width: 22px; height: 22px; right: 26px; border: none; background-color: transparent; }}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QTimeEdit::up-button:hover {{ background-color: {COLOR_NEUTRAL_750}; border-radius: {RADIUS_SM}px; }}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed, QTimeEdit::up-button:pressed {{ background-color: {COLOR_NEUTRAL_700}; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow, QTimeEdit::up-arrow {{ image: url("{PATH_ICON_CHEVRON_UP}"); width: 14px; height: 14px; }}
QSpinBox::down-button, QDoubleSpinBox::down-button, QTimeEdit::down-button {{ subcontrol-origin: border; subcontrol-position: center right; width: 22px; height: 22px; right: 4px; border: none; background-color: transparent; }}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover, QTimeEdit::down-button:hover {{ background-color: {COLOR_NEUTRAL_750}; border-radius: {RADIUS_SM}px; }}
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed, QTimeEdit::down-button:pressed {{ background-color: {COLOR_NEUTRAL_700}; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow, QTimeEdit::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 14px; height: 14px; }}
QSpinBox:disabled, QDoubleSpinBox:disabled, QTimeEdit:disabled, QDateEdit:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border-color: {COLOR_NEUTRAL_750}; padding: {PADDING_SPINBOX}; }}

/* DateEdit */
QDateEdit {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_SPINBOX}; border: {BORDER_DEFAULT}; border-top: 1.2px solid #38363E; selection-background-color: transparent; selection-color: {COLOR_WHITE}; }}
QDateEdit:focus {{ border: {BORDER_FOCUS}; border-top: 1.2px solid #71717A; background-color: {COLOR_NEUTRAL_800}; }}
QDateEdit:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QDateEdit::up-button, QDateEdit::down-button {{ width: 0px; height: 0px; border: none; background: transparent; }}
QDateEdit::up-arrow, QDateEdit::down-arrow {{ image: none; width: 0px; height: 0px; }}
QDateEdit::drop-down {{ subcontrol-origin: border; subcontrol-position: center right; width: 24px; height: 24px; right: 4px; border: none; background-color: transparent; }}
QDateEdit::drop-down:hover {{ background-color: {COLOR_NEUTRAL_750}; border-radius: {RADIUS_SM}px; }}
QDateEdit::down-arrow {{ image: url("{PATH_ICON_CALENDAR}"); width: 16px; height: 16px; }}

/* CheckBox */
QCheckBox {{ spacing: 8px; color: {COLOR_NEUTRAL_400}; background-color: transparent; }}
QCheckBox:hover {{ color: {COLOR_WHITE}; }}
QCheckBox:focus {{ color: {COLOR_WHITE}; }}
QCheckBox::indicator {{ width: 14px; height: 14px; border-radius: {RADIUS_SM}px; border: 1.2px solid #38363E; border-top: 1.2px solid #4B4951; background-color: {COLOR_NEUTRAL_850}; }}
QCheckBox::indicator:focus, QCheckBox:focus::indicator {{ border-color: #5E5C66; }}
QCheckBox::indicator:unchecked:hover {{ border-color: {COLOR_NEUTRAL_700}; background-color: {COLOR_NEUTRAL_800}; }}
QCheckBox::indicator:checked {{ border: 1.2px solid #1A7A42; border-top: 1.2px solid #2ECD70; background-color: {GRADIENT_ACCENT_FILL}; image: url("{PATH_ICON_CHECK}"); }}
QCheckBox::indicator:checked:hover {{ background-color: {GRADIENT_ACCENT_HOVER}; }}
QCheckBox:disabled {{ color: {COLOR_NEUTRAL_500}; }}
QCheckBox::indicator:disabled {{ border-color: {COLOR_NEUTRAL_750}; background-color: {COLOR_WHITE_GLOW}; }}
QCheckBox::indicator:checked:disabled {{ border-color: {COLOR_NEUTRAL_750}; background-color: {COLOR_WHITE_GLOW}; image: url("{PATH_ICON_CHECK}"); }}

/* Slider */
QSlider::groove:horizontal {{ border: none; height: 6px; background: {COLOR_NEUTRAL_800}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {COLOR_GREEN}; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {COLOR_WHITE}; width: 14px; height: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; border: 1.2px solid #4B4951; }}
"""


def _build_surface_qss(h1: int, h2: int, h3: int, text1: int, text2: int) -> str:
    return f"""
/* --- 5. Surfaces, Containers & Badges --- */
QFrame[role="canvas_container"] {{ background-color: {COLOR_NEUTRAL_950}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_MD}px; }}
QFrame[role="sidebar"] {{ background-color: {COLOR_NEUTRAL_900}; border-right: 1.2px solid {COLOR_NEUTRAL_800}; }}
QFrame[role="profile_card"] {{ background-color: transparent; border-radius: {RADIUS_MD}px; }}
QFrame[role="profile_card"]:hover {{ background-color: {COLOR_NEUTRAL_800}; border: {BORDER_DEFAULT}; }}
QFrame[role="update_banner_card"] {{ background-color: {COLOR_NEUTRAL_950}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_LG}px; }}
QFrame[role="update_banner_card"]:hover {{ border-color: {COLOR_NEUTRAL_700}; }}
QFrame[role="update_icon_box"] {{ background-color: {COLOR_GREEN_GLOW}; border: 1.2px solid {COLOR_GREEN}; border-radius: {RADIUS_MD}px; }}
QFrame[role="card"] {{ background-color: {COLOR_NEUTRAL_900}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_LG}px; }}
QFrame[role="dialog"] {{ background-color: {COLOR_NEUTRAL_950}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_XL}px; }}
QFrame[role="dialog"][state="accent"] {{ border-color: {COLOR_GREEN}; }}
QFrame[role="dialog"][state="success"] {{ border-color: {COLOR_GREEN}; }}
QFrame[role="dialog"][state="danger"] {{ border-color: {COLOR_RED}; }}
QFrame[role="dialog"][state="error"] {{ border-color: {COLOR_RED}; }}
QFrame[role="dialog"][state="warning"] {{ border-color: {COLOR_AMBER}; }}
QFrame[role="dialog"][state="info"] {{ border-color: {COLOR_BLUE}; }}
QFrame[role="dialog"][state="neutral"] {{ border-color: {COLOR_NEUTRAL_700}; }}

QFrame[role="banner_danger"] {{ background-color: {COLOR_RED_GLOW}; border: 1.2px solid {COLOR_RED_DARK}; border-radius: {RADIUS_MD}px; }}
QFrame[role="danger_icon"] {{ background-color: {COLOR_RED}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="warning_icon"] {{ background-color: {COLOR_AMBER}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="info_icon"] {{ background-color: {COLOR_BLUE}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="accent_icon"] {{ background-color: {COLOR_GREEN}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="tiktok_icon"] {{ background-color: {COLOR_TIKTOK}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="youtube_icon"] {{ background-color: {COLOR_YOUTUBE}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="twitch_icon"] {{ background-color: {COLOR_TWITCH}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="black_icon"] {{ background-color: {COLOR_BLACK}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="divider"] {{ background-color: {COLOR_NEUTRAL_800}; }}

QFrame[role="bot_tag"] {{ background-color: {COLOR_NEUTRAL_850}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_MD}px; }}
QFrame[role="bot_tag"]:hover {{ border-color: {COLOR_RED}; }}
QFrame[role="bot_tag"] QLabel {{ color: {COLOR_NEUTRAL_400}; font-size: {text2}px; }}
QFrame[role="toast"] {{ background-color: {COLOR_NEUTRAL_900}; border: {BORDER_MUTED}; border-radius: {RADIUS_MD}px; }}
QFrame[role="toast"][state="success"] {{ border-color: {COLOR_GREEN}; }}
QFrame[role="toast"][state="danger"] {{ border-color: {COLOR_RED}; }}
QFrame[role="toast"][state="warning"] {{ border-color: {COLOR_AMBER}; }}
QFrame[role="toast"][state="info"] {{ border-color: {COLOR_BLUE}; }}

/* Badges & Tags */
QFrame[role="badge"] {{ background-color: {COLOR_NEUTRAL_850}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_MD}px; }}
QFrame[role="badge"] QLabel {{ font-size: {text2}px; font-weight: 600; color: {COLOR_NEUTRAL_400}; background: transparent; }}
QFrame[role="badge"][state="everyone"] {{ background-color: {COLOR_GREEN_GLOW}; border-color: rgba(46, 205, 112, 0.2); }}
QFrame[role="badge"][state="everyone"] QLabel {{ color: {COLOR_GREEN}; }}
QFrame[role="badge"][state="subscriber"] {{ background-color: {COLOR_BLUE_GLOW}; border-color: rgba(59, 130, 246, 0.2); }}
QFrame[role="badge"][state="subscriber"] QLabel {{ color: {COLOR_BLUE}; }}
QFrame[role="badge"][state="vip"] {{ background-color: {COLOR_PURPLE_GLOW}; border-color: rgba(168, 85, 247, 0.2); }}
QFrame[role="badge"][state="vip"] QLabel {{ color: {COLOR_PURPLE}; }}
QFrame[role="badge"][state="moderator"] {{ background-color: {COLOR_AMBER_GLOW}; border-color: rgba(245, 158, 11, 0.2); }}
QFrame[role="badge"][state="moderator"] QLabel {{ color: {COLOR_AMBER}; }}
QFrame[role="badge"][state="broadcaster"] {{ background-color: {COLOR_RED_GLOW}; border-color: rgba(239, 68, 68, 0.2); }}
QFrame[role="badge"][state="broadcaster"] QLabel {{ color: {COLOR_RED}; }}
QFrame[role="badge"][state="warning"] {{ background-color: {COLOR_AMBER_GLOW}; border-color: rgba(245, 158, 11, 0.2); }}
QFrame[role="badge"][state="warning"] QLabel {{ color: {COLOR_AMBER}; }}
QFrame[role="badge"][state="plugin"] {{ background-color: {COLOR_PURPLE_GLOW}; border-color: rgba(168, 85, 247, 0.2); }}
QFrame[role="badge"][state="plugin"] QLabel {{ color: {COLOR_PURPLE}; }}
QFrame[role="badge"][state="kick"] {{ background-color: {COLOR_GREEN_GLOW}; border-color: rgba(46, 205, 112, 0.2); }}
QFrame[role="badge"][state="kick"] QLabel {{ color: {COLOR_GREEN}; }}
QFrame[role="badge"][state="twitch"] {{ background-color: {COLOR_PURPLE_GLOW}; border-color: rgba(168, 85, 247, 0.2); }}
QFrame[role="badge"][state="twitch"] QLabel {{ color: {COLOR_PURPLE}; }}

QLabel[role="badge_kick"] {{ background-color: {COLOR_GREEN_GLOW}; color: {COLOR_GREEN}; font-weight: 600; border-radius: {RADIUS_MD}px; padding: {PADDING_BADGE}; font-size: {text2}px; border: 1.2px solid rgba(46, 205, 112, 0.2); }}
QLabel[role="badge_twitch"] {{ background-color: {COLOR_PURPLE_GLOW}; color: {COLOR_PURPLE}; font-weight: 600; border-radius: {RADIUS_MD}px; padding: {PADDING_BADGE}; font-size: {text2}px; border: 1.2px solid rgba(168, 85, 247, 0.2); }}
QLabel[role="channel_avatar"] {{ border-radius: 48px; background-color: {COLOR_NEUTRAL_800}; border: 2px solid {COLOR_NEUTRAL_700}; }}
QLabel[role="rank_number"] {{ color: {COLOR_GREEN}; font-weight: 600; min-width: 20px; }}
QLineEdit[state="plugin"], QTextEdit[state="plugin"], QPlainTextEdit[state="plugin"] {{ border: 1.2px solid {COLOR_PURPLE}; color: {COLOR_PURPLE}; font-weight: 600; background-color: {COLOR_NEUTRAL_900}; }}
QTextEdit[role="ConsoleDisplay"] {{ font-family: 'GoogleSansCode Nerd Font', 'GoogleSansCode NF', Consolas, monospace; background-color: {COLOR_NEUTRAL_950}; color: {COLOR_NEUTRAL_200}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_MD}px; }}
QTextBrowser[role="release_notes_browser"] {{ background-color: {COLOR_NEUTRAL_950}; color: {COLOR_NEUTRAL_400}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_MD}px; padding: 12px; }}

/* Table Widget */
QTableWidget {{ background-color: {COLOR_NEUTRAL_900}; border: none; gridline-color: transparent; }}
QTableWidget::item {{ padding: 6px; border-bottom: 1.2px solid {COLOR_NEUTRAL_800}; }}
QTableWidget::item:selected {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QHeaderView, QHeaderView::section {{ background-color: transparent; border: none; }}
QHeaderView::section {{ color: {COLOR_NEUTRAL_400}; font-weight: 600; padding: {PADDING_INPUT}; border-bottom: 1.2px solid {COLOR_NEUTRAL_750}; text-align: left; }}

/* Scrollbars */
QScrollBar:vertical {{ border: none; background: transparent; width: 12px; margin: 4px 2px 4px 2px; }}
QScrollBar::handle:vertical {{ background-color: {COLOR_NEUTRAL_750}; border-radius: {RADIUS_XS}px; min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background-color: {COLOR_NEUTRAL_500}; }}
QScrollBar::handle:vertical:pressed {{ background-color: {COLOR_NEUTRAL_400}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ height: 0px; background: none; }}
QScrollBar:horizontal {{ border: none; background: transparent; height: 10px; margin: 2px 4px 2px 4px; }}
QScrollBar::handle:horizontal {{ background-color: {COLOR_NEUTRAL_750}; border-radius: {RADIUS_XS}px; min-width: 28px; }}
QScrollBar::handle:horizontal:hover {{ background-color: {COLOR_NEUTRAL_500}; }}
QScrollBar::handle:horizontal:pressed {{ background-color: {COLOR_NEUTRAL_400}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal, QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ width: 0px; background: none; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: transparent; border: none; }}

/* Progress Bars */
QProgressBar {{ background-color: {COLOR_NEUTRAL_850}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_XS}px; height: 6px; text-align: center; }}
QProgressBar::chunk {{ background-color: {COLOR_GREEN}; border-radius: 3px; }}
QProgressBar[role="update_progress"] {{ background-color: {COLOR_NEUTRAL_900}; border: none; border-radius: {RADIUS_SM}px; }}
QProgressBar[role="update_progress"]::chunk {{ background-color: {COLOR_GREEN}; border-radius: {RADIUS_SM}px; }}
QProgressBar[role="wizard_progress"] {{ background-color: {COLOR_NEUTRAL_750}; border: none; border-radius: {RADIUS_2XS}px; }}
QProgressBar[role="wizard_progress"]::chunk {{ background-color: {COLOR_GREEN}; border-radius: {RADIUS_2XS}px; }}
QProgressBar[role="top_command_progress"] {{ background-color: {COLOR_NEUTRAL_750}; border: none; border-radius: 4px; height: 8px; }}
QProgressBar[role="top_command_progress"]::chunk {{ background-color: {COLOR_BLUE}; border-radius: 4px; }}

/* Tab Widget */
QTabWidget::pane {{ border: {BORDER_SUBTLE}; border-radius: {RADIUS_LG}px; border-top-left-radius: 0px; background-color: {COLOR_NEUTRAL_900}; padding: 8px; }}
QTabBar::tab {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_400}; border: {BORDER_SUBTLE}; border-bottom-color: transparent; border-top-left-radius: 0px; border-top-right-radius: {RADIUS_MD}px; padding: {PADDING_TAB}; margin-right: 4px; font-weight: 600; }}
QTabBar::tab:selected {{ color: {COLOR_WHITE}; background-color: {COLOR_NEUTRAL_900}; border-color: {COLOR_NEUTRAL_750}; border-bottom-color: {COLOR_NEUTRAL_900}; }}
QTabBar::tab:hover:!selected {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QTabBar::tab:focus {{ border-color: {COLOR_NEUTRAL_700}; }}
QTabWidget QFrame[role="card"] {{ background-color: transparent; border: none; }}

/* ToolTip */
QToolTip {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; border: {BORDER_MUTED}; border-radius: {RADIUS_SM}px; padding: {PADDING_INPUT}; font-size: {text1}px; }}
QListWidget[role="transparent_list"] {{ background: transparent; border: none; }}
QListWidget[role="transparent_list"]::item {{ background: transparent; }}
"""


def _build_complex_qss(text1: int, text2: int) -> str:
    return f"""
/* --- 6. Complex Composite Widgets --- */

/* Search Bar */
QFrame[role="search_bar"] {{ background-color: {COLOR_NEUTRAL_850}; border: {BORDER_DEFAULT}; border-top: 1.2px solid #38363E; border-radius: {RADIUS_MD}px; }}
QFrame[role="search_bar"]:hover {{ border-color: {COLOR_NEUTRAL_700}; }}
QFrame[role="search_bar"]:focus-within {{ border: {BORDER_FOCUS}; border-top: 1.2px solid #71717A; }}
QFrame[role="search_bar"] QLineEdit {{ background: transparent; border: none; padding: 0px 12px; color: {COLOR_WHITE}; font-size: {text1}px; }}
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
QPushButton[role="segmented_item"]:checked {{ background-color: {GRADIENT_NEUTRAL_FILL}; border: 1.2px solid #38363E; border-top: 1.2px solid #4B4951; color: {COLOR_WHITE}; font-weight: 600; }}
QPushButton[role="segmented_item"]:pressed {{ background-color: {GRADIENT_NEUTRAL_PRESSED}; }}

/* Segmented Pagination */
QFrame[role="segmented_pagination"] {{ background-color: {GRADIENT_NEUTRAL_FILL}; border: 1.2px solid #38363E; border-top: 1.2px solid #4B4951; border-radius: {RADIUS_MD}px; }}
QFrame[role="segmented_pagination"] QPushButton {{ background: transparent; border: none; border-left: 1.2px solid {COLOR_NEUTRAL_750}; min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; }}
QFrame[role="segmented_pagination"] QPushButton#btn_first {{ border-left: none; border-top-left-radius: {RADIUS_MD_INNER}px; border-bottom-left-radius: {RADIUS_MD_INNER}px; }}
QFrame[role="segmented_pagination"] QPushButton#btn_last {{ border-top-right-radius: {RADIUS_MD_INNER}px; border-bottom-right-radius: {RADIUS_MD_INNER}px; }}
QFrame[role="segmented_pagination"] QPushButton:hover:enabled {{ background-color: {COLOR_NEUTRAL_750}; }}
QFrame[role="segmented_pagination"] QPushButton:focus:enabled {{ background-color: {COLOR_NEUTRAL_700}; }}
QFrame[role="segmented_pagination"] QPushButton:pressed:enabled {{ background-color: {COLOR_NEUTRAL_800}; }}
QFrame[role="segmented_pagination"] QPushButton:disabled {{ background-color: transparent; color: {COLOR_NEUTRAL_500}; }}
QFrame[role="segmented_pagination"] QLabel#lbl_page_status {{ background-color: transparent; color: {COLOR_WHITE}; font-size: {text1}px; font-weight: 600; padding: 0px 16px; min-height: 32px; max-height: 32px; border-left: 1.2px solid {COLOR_NEUTRAL_750}; }}

/* Calendar Pop-up (QCalendarWidget) */
QCalendarWidget {{ background-color: {COLOR_NEUTRAL_900}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_LG}px; padding: 4px; }}
QCalendarWidget QWidget#qt_calendar_navigationbar {{ background-color: transparent; border: none; min-height: 36px; margin-bottom: 4px; }}
QCalendarWidget QToolButton {{ background-color: transparent; color: {COLOR_WHITE}; font-weight: 600; font-size: {text1}px; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_SM}px; padding: {PADDING_ITEM}; margin: 2px; }}
QCalendarWidget QToolButton:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QCalendarWidget QToolButton:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}
QCalendarWidget QToolButton#qt_calendar_prevmonth {{ qproperty-icon: url("{PATH_ICON_CHEVRON_LEFT}"); icon-size: 16px; width: 26px; height: 26px; }}
QCalendarWidget QToolButton#qt_calendar_nextmonth {{ qproperty-icon: url("{PATH_ICON_CHEVRON_RIGHT}"); icon-size: 16px; width: 26px; height: 26px; }}
QCalendarWidget QToolButton#qt_calendar_monthbutton, QCalendarWidget QToolButton#qt_calendar_yearbutton {{ color: {COLOR_WHITE}; font-size: {text1 + 1}px; font-weight: 600; padding: {PADDING_ITEM}; }}
QCalendarWidget QMenu {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_400}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_MD}px; padding: 4px; }}
QCalendarWidget QSpinBox {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_WHITE}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_SM}px; padding: 2px 6px; font-weight: 600; }}
QCalendarWidget QSpinBox:focus {{ border-color: #5E5C66; }}
QCalendarWidget QTableView {{ background-color: transparent; border: none; gridline-color: transparent; selection-background-color: {COLOR_WHITE}; selection-color: {COLOR_NEUTRAL_950}; outline: none; }}
QCalendarWidget QTableView:enabled {{ color: {COLOR_NEUTRAL_400}; }}
QCalendarWidget QTableView:disabled {{ color: {COLOR_NEUTRAL_700}; }}
QCalendarWidget QHeaderView::section {{ background-color: transparent; color: {COLOR_NEUTRAL_400}; font-size: {text2}px; font-weight: 600; padding: 3px 0px; border: none; text-align: center; }}
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
