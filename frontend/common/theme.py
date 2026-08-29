# frontend\common\theme.py

import os
import re
import tempfile
from functools import lru_cache
from pathlib import Path
from frontend.common.paths import get_assets_path, resolve_icon_path

COLOR_NEUTRAL_950  = "#09090B"
COLOR_NEUTRAL_900  = "#121214"
COLOR_NEUTRAL_850  = "#18181B"
COLOR_NEUTRAL_800  = "#27272A"
COLOR_NEUTRAL_750  = "#29292B"
COLOR_NEUTRAL_700  = "#3F3F46"
COLOR_NEUTRAL_500  = "#71717A"
COLOR_NEUTRAL_400  = "#A1A1AA"
COLOR_NEUTRAL_200  = "#E4E4E7"
COLOR_WHITE        = "#FAFAFA"
COLOR_BLACK        = "#000000"

COLOR_GREEN        = "#2ECD70"
COLOR_GREEN_DARK   = "#27AA5E"
COLOR_RED          = "#EF4444"
COLOR_AMBER        = "#F59E0B"
COLOR_BLUE         = "#3B82F6"
COLOR_PURPLE       = "#C084FC"
COLOR_TWITCH       = "#9146FF"
COLOR_TWITCH_DARK  = "#772CE8"
COLOR_TWITCH_GLOW  = "rgba(145, 70, 255, 0.15)"
COLOR_YOUTUBE      = "#FF0000"
COLOR_YOUTUBE_DARK = "#CC0000"
COLOR_YOUTUBE_GLOW = "rgba(255, 0, 0, 0.15)"
COLOR_TIKTOK       = "#00F2FE"
COLOR_TIKTOK_DARK  = "#00B8C4"
COLOR_TIKTOK_GLOW  = "rgba(0, 242, 254, 0.15)"

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

PATH_ICON_HELP = get_qss_colored_icon("icons/help.svg", COLOR_WHITE)
PATH_ICON_CHEVRON_DOWN = get_qss_colored_icon("icons/chevron-down.svg", COLOR_NEUTRAL_400)
PATH_ICON_CHEVRON_UP = get_qss_colored_icon("icons/chevron-up.svg", COLOR_NEUTRAL_400)
PATH_ICON_CHEVRON_LEFT = get_qss_colored_icon("icons/chevron-left.svg", COLOR_NEUTRAL_400)
PATH_ICON_CHEVRON_RIGHT = get_qss_colored_icon("icons/chevron-right.svg", COLOR_NEUTRAL_400)
PATH_ICON_CHECK = _get_qss_icon_url("icons/check.svg")
PATH_ICON_CHECK_GREEN = get_qss_colored_icon("icons/check.svg", COLOR_GREEN)
PATH_ICON_CALENDAR = get_qss_colored_icon("icons/calendar.svg", COLOR_NEUTRAL_400)

COLOR_WHITE_GLOW   = "rgba(255, 255, 255, 0.1)"
COLOR_GREEN_GLOW   = "rgba(46, 205, 112, 0.12)"
COLOR_RED_GLOW     = "rgba(239, 68, 68, 0.12)"
COLOR_AMBER_GLOW   = "rgba(245, 158, 11, 0.12)"
COLOR_BLUE_GLOW    = "rgba(59, 130, 246, 0.12)"
COLOR_PURPLE_GLOW  = "rgba(192, 132, 252, 0.15)"

FONT_FAMILY = "'Google Sans', '-apple-system', 'Segoe UI', sans-serif"

RADIUS_2XS         = 2
RADIUS_XS          = 4
RADIUS_SM          = 6
RADIUS_MD_INNER    = 7
RADIUS_MD          = 9
RADIUS_LG          = 12
RADIUS_XL          = 16
RADIUS_PILL        = 26

PADDING_INPUT      = "5px"
PADDING_BUTTON     = "5px 10px"
PADDING_SPINBOX    = "3px 18px 3px 8px"
PADDING_ITEM       = "4px 8px"
PADDING_BADGE      = "2px 6px"
PADDING_CHIP       = "3px 10px"
PADDING_TAB        = "5px 15px"
PADDING_MENU_ITEM  = "4px 12px 4px 18px"

BORDER_DEFAULT     = f"1.5px solid {COLOR_NEUTRAL_800}"
BORDER_SUBTLE      = f"1.5px solid {COLOR_NEUTRAL_750}"
BORDER_MUTED       = f"1.5px solid {COLOR_NEUTRAL_700}"
BORDER_TRANSPARENT = "1.5px solid transparent"
BORDER_FOCUS       = f"1.5px solid {COLOR_GREEN}"
BORDER_ERROR       = f"1.5px solid {COLOR_RED}"

@lru_cache(maxsize=16)
def get_global_qss(base: int = 13) -> str:
    size_headline_1 = base + 12
    size_headline_2 = base + 9
    size_headline_3 = base + 3
    size_textline_1 = base
    size_textline_2 = max(10, base - 1)

    return f"""
/* ==============================================================================
   1. RESET Y ESTILOS GLOBALES
   ============================================================================== */
* {{ font-family: {FONT_FAMILY}; font-size: {size_textline_1}px; color: {COLOR_NEUTRAL_400}; outline: none; }}
QMainWindow {{ background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 {COLOR_NEUTRAL_950}, stop:1 {COLOR_NEUTRAL_850}); }}
QDialog {{ background-color: {COLOR_NEUTRAL_950}; }}
QLabel {{ background-color: transparent; }}

/* ==============================================================================
   2. ESTILOS DE ELEMENTOS QT COMUNES & NAVEGACIÓN TAB (FOCUS)
   ============================================================================== */
QLineEdit, QTextEdit, QPlainTextEdit {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_400}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_INPUT}; border: {BORDER_DEFAULT}; }}
QTextEdit, QPlainTextEdit {{ background-color: {COLOR_NEUTRAL_900}; }}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border: {BORDER_FOCUS}; background-color: {COLOR_NEUTRAL_800}; }}
QLineEdit[state="error"], QTextEdit[state="error"], QPlainTextEdit[state="error"] {{ border: {BORDER_ERROR}; }}

QComboBox {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_400}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_INPUT}; border: {BORDER_DEFAULT}; combobox-popup: 0; }}
QComboBox:focus, QComboBox:hover {{ background-color: {COLOR_NEUTRAL_800}; border-color: {COLOR_NEUTRAL_700}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 23px; border-left: {BORDER_DEFAULT}; border-top-right-radius: {RADIUS_MD}px; border-bottom-right-radius: {RADIUS_MD}px; }}
QComboBox:focus::drop-down, QComboBox:hover::drop-down {{ border-color: {COLOR_NEUTRAL_700}; }}
QComboBox::drop-down:hover {{ background-color: {COLOR_NEUTRAL_800}; border-color: {COLOR_NEUTRAL_700}; }}
QComboBox::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 15px; height: 15px; }}
QComboBox::down-arrow:on {{ top: 1px; left: 1px; }}
QComboBox QAbstractItemView {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_400}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_MD}px; padding: 3px 2px; selection-background-color: {COLOR_NEUTRAL_800}; selection-color: {COLOR_GREEN}; }}
QComboBox QAbstractItemView::item {{ border-radius: {RADIUS_SM}px; padding: {PADDING_ITEM}; margin: 1px 2px; }}
QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover, QComboBox QListView::item:selected, QComboBox QListView::item:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_GREEN}; border-color: {COLOR_NEUTRAL_700}; }}

QMenu {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_400}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_MD}px; padding: 4px 3px; }}
QMenu::item {{ padding: 5px 10px; margin: 1px 2px; border-radius: {RADIUS_SM}px; color: {COLOR_NEUTRAL_400}; font-size: {size_textline_2}px; font-weight: 500; }}
QMenu::item:disabled {{ color: {COLOR_NEUTRAL_500}; background-color: transparent; }}
QMenu::item:selected {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_GREEN}; }}
QMenu::icon {{ margin-left: 14px; }}
QMenu::indicator {{ width: 14px; height: 14px; left: 8px; }}
QMenu::indicator:checked {{ image: url("{PATH_ICON_CHECK_GREEN}"); }}
QMenu::indicator:unchecked {{ image: none; }}
QMenu::separator {{ height: 1px; background-color: {COLOR_NEUTRAL_800}; margin: 2px 4px; }}

QSpinBox, QDoubleSpinBox, QTimeEdit {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_400}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_SPINBOX}; border: {BORDER_DEFAULT}; selection-background-color: transparent; selection-color: {COLOR_NEUTRAL_400}; }}
QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {{ border-color: {COLOR_GREEN}; background-color: {COLOR_NEUTRAL_800}; }}
QSpinBox:hover, QDoubleSpinBox:hover, QTimeEdit:hover {{ background-color: {COLOR_NEUTRAL_800}; border-color: {COLOR_NEUTRAL_700}; }}
QSpinBox::up-button, QDoubleSpinBox::up-button, QTimeEdit::up-button {{ subcontrol-origin: border; subcontrol-position: center right; width: 22px; height: 22px; right: 28px; border: none; background-color: transparent; }}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QTimeEdit::up-button:hover {{ background-color: {COLOR_NEUTRAL_700}; border-radius: {RADIUS_SM}px; }}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed, QTimeEdit::up-button:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow, QTimeEdit::up-arrow {{ image: url("{PATH_ICON_CHEVRON_UP}"); width: 15px; height: 15px; }}
QSpinBox::down-button, QDoubleSpinBox::down-button, QTimeEdit::down-button {{ subcontrol-origin: border; subcontrol-position: center right; width: 22px; height: 22px; right: 6px; border: none; background-color: transparent; }}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover, QTimeEdit::down-button:hover {{ background-color: {COLOR_NEUTRAL_700}; border-radius: {RADIUS_SM}px; }}
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed, QTimeEdit::down-button:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow, QTimeEdit::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 15px; height: 15px; }}

QDateEdit {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_400}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_SPINBOX}; border: {BORDER_DEFAULT}; selection-background-color: transparent; selection-color: {COLOR_NEUTRAL_400}; }}
QDateEdit:focus {{ border-color: {COLOR_GREEN}; background-color: {COLOR_NEUTRAL_800}; }}
QDateEdit:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QDateEdit::up-button, QDateEdit::down-button {{ width: 0px; height: 0px; border: none; background: transparent; }}
QDateEdit::up-arrow, QDateEdit::down-arrow {{ image: none; width: 0px; height: 0px; }}
QDateEdit::drop-down {{ subcontrol-origin: border; subcontrol-position: center right; width: 24px; height: 24px; right: 4px; border: none; background-color: transparent; }}
QDateEdit::drop-down:hover {{ background-color: {COLOR_NEUTRAL_700}; border-radius: {RADIUS_SM}px; }}
QDateEdit::down-arrow {{ image: url("{PATH_ICON_CALENDAR}"); width: 18px; height: 18px; }}

/* ==============================================================================
   CALENDAR POPUP (QCalendarWidget)
   ============================================================================== */
QCalendarWidget {{ background-color: {COLOR_NEUTRAL_900}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_LG}px; padding: 4px; }}
QCalendarWidget QWidget#qt_calendar_navigationbar {{ background-color: transparent; border: none; min-height: 36px; margin-bottom: 4px; }}
QCalendarWidget QToolButton {{ background-color: transparent; color: {COLOR_WHITE}; font-weight: 600; font-size: {size_textline_1}px; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_SM}px; padding: {PADDING_ITEM}; margin: 2px; }}
QCalendarWidget QToolButton:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QCalendarWidget QToolButton:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}
QCalendarWidget QToolButton#qt_calendar_prevmonth {{ qproperty-icon: url("{PATH_ICON_CHEVRON_LEFT}"); icon-size: 16px; width: 26px; height: 26px; }}
QCalendarWidget QToolButton#qt_calendar_nextmonth {{ qproperty-icon: url("{PATH_ICON_CHEVRON_RIGHT}"); icon-size: 16px; width: 26px; height: 26px; }}
QCalendarWidget QToolButton#qt_calendar_monthbutton, QCalendarWidget QToolButton#qt_calendar_yearbutton {{ color: {COLOR_WHITE}; font-size: {size_textline_1 + 1}px; font-weight: 600; padding: {PADDING_ITEM}; }}
QCalendarWidget QMenu {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_400}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_MD}px; padding: 4px; }}
QCalendarWidget QSpinBox {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_WHITE}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_SM}px; padding: 2px 6px; font-weight: 600; }}
QCalendarWidget QSpinBox:focus {{ border-color: {COLOR_GREEN}; }}
QCalendarWidget QTableView {{ background-color: transparent; border: none; gridline-color: transparent; selection-background-color: {COLOR_WHITE}; selection-color: {COLOR_NEUTRAL_950}; outline: none; }}
QCalendarWidget QTableView:enabled {{ color: {COLOR_NEUTRAL_400}; }}
QCalendarWidget QTableView:disabled {{ color: {COLOR_NEUTRAL_700}; }}
QCalendarWidget QHeaderView::section {{ background-color: transparent; color: {COLOR_NEUTRAL_400}; font-size: {size_textline_2}px; font-weight: 600; padding: 3px 0px; border: none; text-align: center; }}
QCalendarWidget QTableView::item {{ border-radius: {RADIUS_MD_INNER}px; padding: 4px; margin: 2px; }}
QCalendarWidget QTableView::item:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; border-radius: {RADIUS_MD_INNER}px; }}
QCalendarWidget QTableView::item:selected {{ background-color: {COLOR_WHITE}; color: {COLOR_NEUTRAL_950}; font-weight: 700; border-radius: {RADIUS_MD_INNER}px; }}

QCheckBox {{ spacing: 8px; color: {COLOR_NEUTRAL_400}; background-color: transparent; }}
QCheckBox:hover {{ color: {COLOR_WHITE}; }}
QCheckBox:focus {{ color: {COLOR_WHITE}; border-color: {COLOR_GREEN}; }}
QCheckBox::indicator {{ width: 12px; height: 12px; border-radius: {RADIUS_SM}px; border: {BORDER_DEFAULT}; background-color: {COLOR_NEUTRAL_850}; }}
QCheckBox::indicator:focus, QCheckBox:focus::indicator {{ border-color: {COLOR_GREEN}; }}
QCheckBox::indicator:unchecked:hover {{ border-color: {COLOR_NEUTRAL_700}; background-color: {COLOR_NEUTRAL_800}; }}
QCheckBox::indicator:checked {{ border-color: {COLOR_GREEN}; background-color: {COLOR_GREEN}; image: url("{PATH_ICON_CHECK}"); }}
QCheckBox::indicator:checked:hover {{ border-color: {COLOR_GREEN_DARK}; background-color: {COLOR_GREEN_DARK}; }}
QCheckBox::indicator:disabled {{ border-color: {COLOR_NEUTRAL_700}; background-color: {COLOR_WHITE_GLOW}; }}
QCheckBox::indicator:checked:disabled {{ border-color: {COLOR_NEUTRAL_700}; background-color: {COLOR_WHITE_GLOW}; image: url("{PATH_ICON_CHECK}"); }}

QTableWidget {{ background-color: {COLOR_NEUTRAL_900}; border: none; gridline-color: transparent; }}
QTableWidget::item {{ padding: 4px; border-bottom: 1px solid {COLOR_NEUTRAL_800}; }}
QTableWidget::item:selected {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_GREEN}; }}
QHeaderView, QHeaderView::section {{ background-color: transparent; border: none; }}
QHeaderView::section {{ color: {COLOR_NEUTRAL_400}; font-weight: 700; padding: {PADDING_INPUT}; border-bottom: 2px solid {COLOR_NEUTRAL_800}; text-align: left; }}

QScrollBar:vertical {{ border: none; background: transparent; width: 12px; margin: 4px 2px 4px 2px; }}
QScrollBar::handle:vertical {{ background-color: {COLOR_NEUTRAL_800}; border-radius: {RADIUS_XS}px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background-color: {COLOR_NEUTRAL_400}; }}
QScrollBar::handle:vertical:pressed {{ background-color: {COLOR_GREEN}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ height: 5px; background: none; }}

QScrollBar:horizontal {{ border: none; background: transparent; height: 12px; margin: 2px 4px 2px 4px; }}
QScrollBar::handle:horizontal {{ background-color: {COLOR_NEUTRAL_800}; border-radius: {RADIUS_XS}px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background-color: {COLOR_NEUTRAL_400}; }}
QScrollBar::handle:horizontal:pressed {{ background-color: {COLOR_GREEN}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal, QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ width: 5px; background: none; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: transparent; border: none; }}

QProgressBar {{ background-color: {COLOR_NEUTRAL_850}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_XS}px; height: 6px; text-align: center; }}
QProgressBar::chunk {{ background-color: {COLOR_GREEN}; border-radius: 3px; }}
QProgressBar[role="update_progress"] {{ background-color: {COLOR_NEUTRAL_900}; border: none; border-radius: {RADIUS_SM}px; }}
QProgressBar[role="update_progress"]::chunk {{ background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_GREEN}, stop:1 {COLOR_GREEN}); border-radius: {RADIUS_SM}px; }}
QProgressBar[role="wizard_progress"] {{ background-color: {COLOR_NEUTRAL_700}; border: none; border-radius: {RADIUS_2XS}px; }}
QProgressBar[role="wizard_progress"]::chunk {{ background-color: {COLOR_GREEN}; border-radius: {RADIUS_2XS}px; }}
QProgressBar[role="top_command_progress"] {{ background-color: {COLOR_NEUTRAL_700}; border: none; border-radius: 4px; height: 8px; }}
QProgressBar[role="top_command_progress"]::chunk {{ background-color: {COLOR_BLUE}; border-radius: 4px; }}

QListWidget[role="transparent_list"] {{ background: transparent; border: none; }}
QListWidget[role="transparent_list"]::item {{ background: transparent; }}

QTabWidget::pane {{ border: {BORDER_DEFAULT}; border-radius: {RADIUS_LG}px; border-top-left-radius: 0px; background-color: {COLOR_NEUTRAL_900}; padding: 8px; }}
QTabBar::tab {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_400}; border: {BORDER_DEFAULT}; border-bottom-color: transparent; border-top-left-radius: 0px; border-top-right-radius: {RADIUS_MD}px; padding: {PADDING_TAB}; margin-right: 4px; font-weight: bold; }}
QTabBar::tab:selected {{ color: {COLOR_GREEN}; background-color: {COLOR_NEUTRAL_900}; border-color: {COLOR_NEUTRAL_800}; border-bottom-color: {COLOR_NEUTRAL_900}; }}
QTabBar::tab:hover:!selected {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QTabBar::tab:focus {{ border-color: {COLOR_GREEN}; }}
QTabWidget QFrame[role="card"] {{ background-color: transparent; border: none; }}

QToolTip {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_NEUTRAL_400}; padding: {PADDING_INPUT}; font-size: {size_textline_1}px; }}

QSlider::groove:horizontal {{ border: none; height: 6px; background: {COLOR_NEUTRAL_850}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {COLOR_GREEN}; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {COLOR_GREEN}; width: 14px; height: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }}
QSlider::handle:horizontal:hover, QSlider:focus::handle:horizontal {{ border-color: {COLOR_GREEN}; }}

/* ==============================================================================
   3. ELEMENTOS DE NAVEGACIÓN Y COMPONENTES ESPECÍFICOS (Con Role)
   ============================================================================== */
QFrame[role="canvas_container"] {{ background-color: {COLOR_NEUTRAL_950}; border: 2px solid {COLOR_NEUTRAL_750}; border-radius: {RADIUS_MD}px; }}
QFrame[role="sidebar"] {{ background-color: {COLOR_NEUTRAL_900}; border-right: {BORDER_DEFAULT}; }}
QFrame[role="profile_card"] {{ background-color: transparent; border-radius: {RADIUS_MD}px; }}
QFrame[role="profile_card"]:hover {{ background-color: {COLOR_NEUTRAL_800}; border-color: {COLOR_NEUTRAL_700}; }}
QFrame[role="update_banner_card"] {{ background-color: {COLOR_NEUTRAL_950}; border: 1px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_LG}px; }}
QFrame[role="update_banner_card"]:hover {{ border-color: {COLOR_NEUTRAL_700}; }}
QFrame[role="update_icon_box"] {{ background-color: {COLOR_GREEN_GLOW}; border: 1px solid {COLOR_GREEN}; border-radius: {RADIUS_MD}px; }}
QPushButton[role="btn_dismiss"] {{ background-color: transparent; border: none; border-radius: {RADIUS_SM}px; padding: 2px; }}
QPushButton[role="btn_dismiss"]:hover {{ background-color: {COLOR_NEUTRAL_800}; }}

/* ==============================================================================
   4. ESTRUCTURAS Y ROLES DE COMPONENTES GENERALES (Con Role)
   ============================================================================== */
QFrame[role="card"] {{ background-color: {COLOR_NEUTRAL_900}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_LG}px; }}
QFrame[role="dialog"] {{ background-color: {COLOR_NEUTRAL_950}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_XL}px; }}
QFrame[role="dialog"][state="accent"] {{ border-color: {COLOR_GREEN}; }}
QFrame[role="dialog"][state="success"] {{ border-color: {COLOR_GREEN}; }}
QFrame[role="dialog"][state="danger"] {{ border-color: {COLOR_RED}; }}
QFrame[role="dialog"][state="error"] {{ border-color: {COLOR_RED}; }}
QFrame[role="dialog"][state="warning"] {{ border-color: {COLOR_AMBER}; }}
QFrame[role="dialog"][state="info"] {{ border-color: {COLOR_BLUE}; }}
QFrame[role="dialog"][state="neutral"] {{ border-color: {COLOR_NEUTRAL_700}; }}
QFrame[role="banner_danger"] {{ background-color: {COLOR_RED_GLOW}; border: 1.5px solid {COLOR_RED}; border-radius: {RADIUS_MD}px; }}
QFrame[role="danger_icon"] {{ background-color: {COLOR_RED}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="warning_icon"] {{ background-color: {COLOR_AMBER}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="info_icon"] {{ background-color: {COLOR_BLUE}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="accent_icon"] {{ background-color: {COLOR_GREEN}; border-radius: {RADIUS_PILL}px; }}
QFrame[role="divider"] {{ background-color: {COLOR_NEUTRAL_750}; }}
QFrame[role="bot_tag"] {{ background-color: {COLOR_NEUTRAL_800}; border: {BORDER_MUTED}; border-radius: {RADIUS_MD}px; }}
QFrame[role="bot_tag"]:hover {{ border-color: {COLOR_RED}; }}
QFrame[role="bot_tag"] QLabel {{ color: {COLOR_NEUTRAL_400}; font-size: {size_textline_2}px; }}
QFrame[role="toast"] {{ background-color: {COLOR_BLACK}; border: {BORDER_MUTED}; border-radius: {RADIUS_MD}px; }}
QFrame[role="toast"][state="success"] {{ border-color: {COLOR_GREEN}; }}
QFrame[role="toast"][state="danger"] {{ border-color: {COLOR_RED}; }}
QFrame[role="toast"][state="warning"] {{ border-color: {COLOR_AMBER}; }}
QFrame[role="toast"][state="info"] {{ border-color: {COLOR_BLUE}; }}

QFrame[role="badge"] {{ background-color: {COLOR_NEUTRAL_850}; border-radius: {RADIUS_MD}px; }}
QFrame[role="badge"] QLabel {{ font-size: {size_textline_2}px; font-weight: 700; color: {COLOR_NEUTRAL_400}; background: transparent; }}
QFrame[role="badge"][state="everyone"] {{ background-color: {COLOR_GREEN_GLOW}; }}
QFrame[role="badge"][state="everyone"] QLabel {{ color: {COLOR_GREEN}; }}
QFrame[role="badge"][state="subscriber"] {{ background-color: {COLOR_BLUE_GLOW}; }}
QFrame[role="badge"][state="subscriber"] QLabel {{ color: {COLOR_BLUE}; }}
QFrame[role="badge"][state="vip"] {{ background-color: {COLOR_PURPLE_GLOW}; }}
QFrame[role="badge"][state="vip"] QLabel {{ color: {COLOR_PURPLE}; }}
QFrame[role="badge"][state="moderator"] {{ background-color: {COLOR_AMBER_GLOW}; }}
QFrame[role="badge"][state="moderator"] QLabel {{ color: {COLOR_AMBER}; }}
QFrame[role="badge"][state="broadcaster"] {{ background-color: {COLOR_RED_GLOW}; }}
QFrame[role="badge"][state="broadcaster"] QLabel {{ color: {COLOR_RED}; }}
QFrame[role="badge"][state="warning"] {{ background-color: {COLOR_AMBER_GLOW}; }}
QFrame[role="badge"][state="plugin"] {{ background-color: {COLOR_PURPLE_GLOW}; }}
QFrame[role="badge"][state="plugin"] QLabel {{ color: {COLOR_PURPLE}; }}
QFrame[role="badge"][state="kick"] {{ background-color: {COLOR_GREEN_GLOW}; }}
QFrame[role="badge"][state="kick"] QLabel {{ color: {COLOR_GREEN}; }}
QFrame[role="badge"][state="twitch"] {{ background-color: {COLOR_PURPLE_GLOW}; }}
QFrame[role="badge"][state="twitch"] QLabel {{ color: {COLOR_PURPLE}; }}
QLabel[role="badge_kick"] {{ background-color: {COLOR_GREEN_GLOW}; color: {COLOR_GREEN}; font-weight: 700; border-radius: {RADIUS_MD}px; padding: {PADDING_BADGE}; font-size: {size_textline_2}px; }}
QLabel[role="badge_twitch"] {{ background-color: {COLOR_PURPLE_GLOW}; color: {COLOR_PURPLE}; font-weight: 700; border-radius: {RADIUS_MD}px; padding: {PADDING_BADGE}; font-size: {size_textline_2}px; }}
QLabel[role="channel_avatar"] {{ border-radius: 48px; background-color: {COLOR_NEUTRAL_800}; border: 2px solid {COLOR_NEUTRAL_700}; }}
QLabel[role="rank_number"] {{ color: {COLOR_GREEN}; font-weight: bold; min-width: 20px; }}
QLineEdit[state="plugin"], QTextEdit[state="plugin"], QPlainTextEdit[state="plugin"] {{ border: 1.5px solid {COLOR_PURPLE}; color: {COLOR_PURPLE}; font-weight: bold; background-color: {COLOR_NEUTRAL_900}; }}
QTextEdit[role="ConsoleDisplay"] {{ font-family: 'GoogleSansCode Nerd Font', 'GoogleSansCode NF', Consolas, monospace; background-color: {COLOR_NEUTRAL_950}; color: {COLOR_NEUTRAL_400}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_MD}px; }}
QTextBrowser[role="release_notes_browser"] {{ background-color: {COLOR_NEUTRAL_950}; color: {COLOR_NEUTRAL_400}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_MD}px; padding: 12px; }}

/* ==============================================================================
   5. SISTEMA DE TIPOGRAFÍA DE TEXTOS (Con Role)
   ============================================================================== */
QLabel[role="h1"] {{ font-size: {size_headline_1}px; font-weight: 400; color: {COLOR_NEUTRAL_200}; }}
QLabel[role="h2"] {{ font-size: {size_headline_2}px; font-weight: 400; color: {COLOR_NEUTRAL_200}; }}
QLabel[role="h3"] {{ font-size: {size_headline_3}px; font-weight: 400; color: {COLOR_NEUTRAL_400}; }}
QLabel[role="body"] {{ font-size: {size_textline_1}px; font-weight: 400; color: {COLOR_NEUTRAL_400}; }}
QLabel[role="caption"] {{ font-size: {size_textline_2}px; font-weight: 400; color: {COLOR_NEUTRAL_500}; }}
QLabel[role="monospace"] {{ font-size: {size_textline_2}px; color: {COLOR_NEUTRAL_400}; }}
QLabel[state="normal"] {{ color: {COLOR_NEUTRAL_400}; }}
QLabel[state="white"] {{ color: {COLOR_WHITE}; }}
QLabel[state="error"] {{ color: {COLOR_RED}; }}
QLabel[state="danger"] {{ color: {COLOR_RED}; }}
QLabel[state="success"] {{ color: {COLOR_GREEN}; }}
QLabel[state="info"] {{ color: {COLOR_BLUE}; }}
QLabel[state="warning"] {{ color: {COLOR_AMBER}; }}
QLabel[state="bold"] {{ font-weight: bold; }}
QLabel[role="code"] {{ font-size: {size_textline_2}px; font-weight: bold; background-color: {COLOR_NEUTRAL_850}; padding: 1px 4px; border-radius: {RADIUS_SM}px; color: {COLOR_NEUTRAL_400}; }}
QLabel[role="category"] {{ font-weight: bold; color: {COLOR_GREEN}; margin-top: 6px; font-size: {size_textline_2}px; }}

/* ==============================================================================
   6. BOTONES Y ACCIONES (Con Role & Indicadores de Foco)
   ============================================================================== */
QPushButton {{ border: {BORDER_TRANSPARENT}; }}
QPushButton:focus {{ border: {BORDER_FOCUS}; }}
QPushButton[role="nav_button"] {{ background: transparent; border-radius: {RADIUS_MD}px; padding: 10px; text-align: left; color: {COLOR_NEUTRAL_400}; font-weight: 500; border: {BORDER_TRANSPARENT}; }}
QPushButton[role="nav_button"]:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_NEUTRAL_400}; }}
QPushButton[role="nav_button"]:focus {{ border-color: {COLOR_GREEN}; }}
QPushButton[role="nav_button"]:checked {{ background-color: {COLOR_NEUTRAL_750}; color: {COLOR_GREEN}; font-weight: 700; }}
QPushButton[role="nav_button"][collapsed="false"] {{ text-align: left; padding-left: 10px; }}
QPushButton[role="nav_button"][collapsed="true"] {{ text-align: center; padding: 10px 0px; }}
QPushButton[role="action_accent"] {{ background-color: {COLOR_GREEN}; color: {COLOR_NEUTRAL_950}; font-size: {size_textline_1}px; font-weight: 700; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_accent"]:hover {{ background-color: {COLOR_GREEN_DARK}; }}
QPushButton[role="action_accent"]:focus {{ border-color: {COLOR_NEUTRAL_700}; }}
QPushButton[role="action_kick"] {{ background-color: {COLOR_GREEN}; color: {COLOR_NEUTRAL_950}; font-size: {size_textline_1}px; font-weight: 700; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_kick"]:hover {{ background-color: {COLOR_GREEN_DARK}; }}
QPushButton[role="action_kick"]:focus {{ border-color: {COLOR_WHITE}; }}
QPushButton[role="action_kick"]:disabled {{ background-color: {COLOR_GREEN_GLOW}; color: {COLOR_GREEN}; border: 1.5px solid {COLOR_GREEN}; }}
QPushButton[role="action_twitch"] {{ background-color: {COLOR_TWITCH}; color: {COLOR_WHITE}; font-size: {size_textline_1}px; font-weight: 700; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_twitch"]:hover {{ background-color: {COLOR_TWITCH_DARK}; }}
QPushButton[role="action_twitch"]:focus {{ border-color: {COLOR_WHITE}; }}
QPushButton[role="action_twitch"]:disabled {{ background-color: {COLOR_TWITCH_GLOW}; color: {COLOR_TWITCH}; border: 1.5px solid {COLOR_TWITCH}; }}
QPushButton[role="action_youtube"] {{ background-color: {COLOR_YOUTUBE}; color: {COLOR_WHITE}; font-size: {size_textline_1}px; font-weight: 700; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_youtube"]:hover {{ background-color: {COLOR_YOUTUBE_DARK}; }}
QPushButton[role="action_youtube"]:focus {{ border-color: {COLOR_WHITE}; }}
QPushButton[role="action_youtube"]:disabled {{ background-color: {COLOR_YOUTUBE_GLOW}; color: {COLOR_YOUTUBE}; border: 1.5px solid {COLOR_YOUTUBE}; }}
QPushButton[role="action_tiktok"] {{ background-color: {COLOR_TIKTOK}; color: {COLOR_BLACK}; font-size: {size_textline_1}px; font-weight: 700; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_tiktok"]:hover {{ background-color: {COLOR_TIKTOK_DARK}; }}
QPushButton[role="action_tiktok"]:focus {{ border-color: {COLOR_WHITE}; }}
QPushButton[role="action_tiktok"]:disabled {{ background-color: {COLOR_TIKTOK_GLOW}; color: {COLOR_TIKTOK}; border: 1.5px solid {COLOR_TIKTOK}; }}
QPushButton[role="action_outlined"] {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_400}; font-size: {size_textline_1}px; font-weight: 700; border: {BORDER_DEFAULT}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_outlined"]:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QPushButton[role="action_outlined"]:focus {{ border-color: {COLOR_GREEN}; }}
QPushButton[role="action_danger_border"] {{ background-color: transparent; color: {COLOR_RED}; font-size: {size_textline_1}px; font-weight: 700; border: 1.5px solid {COLOR_RED}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_danger_border"]:hover {{ background-color: {COLOR_RED_GLOW}; }}
QPushButton[role="action_danger_border"]:focus {{ border-color: {COLOR_RED}; background-color: {COLOR_RED_GLOW}; }}
QPushButton[role="action_accent_border"] {{ background-color: transparent; color: {COLOR_GREEN}; font-size: {size_textline_1}px; font-weight: 700; border: 1.5px solid {COLOR_GREEN}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_accent_border"]:hover {{ background-color: {COLOR_GREEN_GLOW}; }}
QPushButton[role="action_accent_border"]:focus {{ border-color: {COLOR_GREEN}; background-color: {COLOR_GREEN_GLOW}; }}
QPushButton[role="action_neutral_border"] {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_400}; font-size: {size_textline_1}px; font-weight: 700; border: {BORDER_DEFAULT}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_neutral_border"]:hover {{ background-color: {COLOR_NEUTRAL_800}; border-color: {COLOR_NEUTRAL_700}; }}
QPushButton[role="action_neutral_border"]:focus {{ border-color: {COLOR_GREEN}; }}
QPushButton[role="btn_ghost"] {{ background-color: transparent; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_SM}px; padding: 2px; }}
QPushButton[role="btn_ghost"]:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QPushButton[role="btn_ghost"]:focus {{ background-color: {COLOR_NEUTRAL_800}; }}
QPushButton[role="filter_chip"] {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_400}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_SM}px; padding: {PADDING_CHIP}; font-size: {size_textline_2}px; font-weight: 600; }}
QPushButton[role="filter_chip"]:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QPushButton[role="filter_chip"]:focus {{ border-color: {COLOR_WHITE}; }}
QPushButton[role="filter_chip"]:checked {{ background-color: {COLOR_GREEN}; color: {COLOR_NEUTRAL_950}; border-color: {COLOR_GREEN}; font-weight: 700; }}

QFrame[role="segmented_control"] {{ background-color: {COLOR_NEUTRAL_900}; border: {BORDER_DEFAULT}; border-radius: {RADIUS_MD}px; padding: 2px; }}
QPushButton[role="segmented_item"] {{ background-color: transparent; border: {BORDER_TRANSPARENT}; border-radius: {RADIUS_SM}px; padding: 3px 5px; }}
QPushButton[role="segmented_item"]:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QPushButton[role="segmented_item"]:focus {{ border-color: {COLOR_GREEN}; }}
QPushButton[role="segmented_item"]:checked {{ background-color: {COLOR_NEUTRAL_750}; }}
QPushButton[role="segmented_item"]:pressed {{ background-color: {COLOR_NEUTRAL_700}; }}

/* ==============================================================================
   7. ESTADOS DESHABILITADOS (Global)
   ============================================================================== */
QPushButton:disabled, QPushButton[role="action_accent"]:disabled, QPushButton[role="action_outlined"]:disabled, QPushButton[role="action_danger_border"]:disabled, QPushButton[role="action_accent_border"]:disabled, QPushButton[role="action_neutral_border"]:disabled, QPushButton[role="btn_ghost"]:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border: {BORDER_DEFAULT}; padding: {PADDING_BUTTON}; }}
QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border-color: {COLOR_NEUTRAL_700}; padding: {PADDING_INPUT}; }}
QSpinBox:disabled, QDoubleSpinBox:disabled, QTimeEdit:disabled, QDateEdit:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border-color: {COLOR_NEUTRAL_700}; padding: {PADDING_SPINBOX}; }}
QCheckBox:disabled {{ color: {COLOR_NEUTRAL_500}; }}

/* ==============================================================================
   8. COMPONENTES COMPUESTOS (Search Bar y Segmented Pagination)
   ============================================================================== */
QFrame[role="search_bar"] {{ background-color: {COLOR_NEUTRAL_850}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_MD}px; }}
QFrame[role="search_bar"]:hover {{ border-color: {COLOR_NEUTRAL_700}; }}
QFrame[role="search_bar"]:focus-within {{ border-color: {COLOR_GREEN}; }}
QFrame[role="search_bar"] QLineEdit {{ background: transparent; border: none; padding: 0px 12px; color: {COLOR_WHITE}; font-size: {size_textline_1}px; }}
QFrame[role="search_bar"] QPushButton {{ background: transparent; border: none; border-left: {BORDER_SUBTLE}; border-top-right-radius: {RADIUS_MD_INNER}px; border-bottom-right-radius: {RADIUS_MD_INNER}px; min-width: 36px; max-width: 36px; min-height: 32px; max-height: 32px; }}
QFrame[role="search_bar"] QPushButton:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QFrame[role="search_bar"] QPushButton:focus {{ background-color: {COLOR_NEUTRAL_750}; }}
QFrame[role="search_bar"] QPushButton:pressed {{ background-color: {COLOR_NEUTRAL_700}; }}

QFrame[role="category_dropdown"] {{ background-color: {COLOR_NEUTRAL_950}; border: {BORDER_MUTED}; border-radius: {RADIUS_MD}px; }}
QListWidget[role="category_list"] {{ background: transparent; border: none; outline: none; }}
QListWidget[role="category_list"]::item {{ background: transparent; border-radius: {RADIUS_SM}px; padding: 2px; min-height: 32px; }}
QListWidget[role="category_list"]::item:hover, QListWidget[role="category_list"]::item:selected {{ background-color: {COLOR_NEUTRAL_800}; }}

QFrame[role="segmented_pagination"] {{ background-color: {COLOR_NEUTRAL_850}; border: {BORDER_SUBTLE}; border-radius: {RADIUS_MD}px; }}
QFrame[role="segmented_pagination"] QPushButton {{ background: transparent; border: none; border-left: {BORDER_SUBTLE}; min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; }}
QFrame[role="segmented_pagination"] QPushButton#btn_first {{ border-left: none; border-top-left-radius: {RADIUS_MD_INNER}px; border-bottom-left-radius: {RADIUS_MD_INNER}px; }}
QFrame[role="segmented_pagination"] QPushButton#btn_last {{ border-top-right-radius: {RADIUS_MD_INNER}px; border-bottom-right-radius: {RADIUS_MD_INNER}px; }}
QFrame[role="segmented_pagination"] QPushButton:hover:enabled {{ background-color: {COLOR_NEUTRAL_800}; }}
QFrame[role="segmented_pagination"] QPushButton:focus:enabled {{ background-color: {COLOR_NEUTRAL_750}; }}
QFrame[role="segmented_pagination"] QPushButton:pressed:enabled {{ background-color: {COLOR_NEUTRAL_700}; }}
QFrame[role="segmented_pagination"] QPushButton:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; }}
QFrame[role="segmented_pagination"] QLabel#lbl_page_status {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_WHITE}; font-size: {size_textline_1}px; font-weight: 600; padding: 0px 16px; min-height: 32px; max-height: 32px; border-left: {BORDER_DEFAULT}; }}
"""

GLOBAL_QSS = get_global_qss(13)

def get_swatch_qss(bg_color: str, border_width: int = 1, radius: int = RADIUS_SM) -> str:
    return f"background-color: {bg_color}; border: {border_width}px solid {COLOR_NEUTRAL_700}; border-radius: {radius}px;"
