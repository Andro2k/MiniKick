# frontend\common\theme.py

from frontend.common.utils import get_assets_path
PATH_ICON_HELP = get_assets_path("icons/help.svg")
PATH_ICON_CHEVRON_DOWN = get_assets_path("icons/chevron-down.svg").replace('\\', '/')
PATH_ICON_CHEVRON_UP = get_assets_path("icons/chevron-up.svg").replace('\\', '/')
PATH_ICON_CHEVRON_LEFT = get_assets_path("icons/chevron-left.svg").replace('\\', '/')
PATH_ICON_CHEVRON_RIGHT = get_assets_path("icons/chevron-right.svg").replace('\\', '/')
PATH_ICON_CHECK = get_assets_path("icons/check.svg").replace('\\', '/')

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

COLOR_WHITE_GLOW   = "rgba(255, 255, 255, 0.1)"
COLOR_GREEN_GLOW   = "rgba(46, 205, 112, 0.12)"
COLOR_RED_GLOW     = "rgba(239, 68, 68, 0.12)"
COLOR_AMBER_GLOW   = "rgba(245, 158, 11, 0.12)"
COLOR_BLUE_GLOW    = "rgba(59, 130, 246, 0.12)"
COLOR_PURPLE_GLOW  = "rgba(192, 132, 252, 0.15)"

FONT_FAMILY = "'Google Sans', '-apple-system', 'Segoe UI', sans-serif"

RADIUS_SM = 6
RADIUS_MD = 9
RADIUS_LG = 12

PADDING_INPUT   = "5px 10px"
PADDING_BUTTON  = "6px 12px"


def get_global_qss(base: int = 13) -> str:
    size_headline_1 = base + 12
    size_headline_2 = base + 9
    size_headline_3 = base + 3
    size_textline_1 = base
    size_textline_2 = max(10, base - 1)
    size_textline_3 = max(9, base - 2)

    return f"""
/* ==============================================================================
   1. RESET Y ESTILOS GLOBALES
   ============================================================================== */
* {{ font-family: {FONT_FAMILY}; font-size: {size_textline_1}px; color: {COLOR_NEUTRAL_200}; outline: none; }}
QMainWindow, QDialog {{ background-color: {COLOR_NEUTRAL_950}; }}
QLabel {{ background-color: transparent; }}

/* ==============================================================================
   2. ESTILOS DE ELEMENTOS QT COMUNES
   ============================================================================== */
QLineEdit, QTextEdit, QPlainTextEdit {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border: none; border-radius: {RADIUS_MD}px; padding: {PADDING_INPUT}; border: 1.5px solid {COLOR_NEUTRAL_800}; }}
QTextEdit, QPlainTextEdit {{ background-color: {COLOR_NEUTRAL_900}; border: 1.5px solid {COLOR_NEUTRAL_800}; }}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border: 1.5px solid {COLOR_GREEN}; background-color: {COLOR_NEUTRAL_800}; }}
QLineEdit[state="error"], QTextEdit[state="error"], QPlainTextEdit[state="error"] {{ border: 1.5px solid {COLOR_RED}; }}

QComboBox {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_INPUT}; border: 1.5px solid {COLOR_NEUTRAL_800}; combobox-popup: 0; }}
QComboBox:focus, QComboBox:hover {{ border-color: transparent; background-color: {COLOR_NEUTRAL_800}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 23px; border-left: 1.5px solid {COLOR_NEUTRAL_800}; border-top-right-radius: {RADIUS_MD}px; border-bottom-right-radius: {RADIUS_MD}px; }}
QComboBox:focus::drop-down, QComboBox:hover::drop-down {{ border-color: {COLOR_NEUTRAL_800}; }}
QComboBox::drop-down:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QComboBox::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 15px; height: 15px; }}
QComboBox::down-arrow:on {{ top: 1px; left: 1px; }}
QComboBox QAbstractItemView, QMenu {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_200}; border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_MD}px; padding: 3px 2px; selection-background-color: {COLOR_NEUTRAL_800}; selection-color: {COLOR_GREEN}; }}
QComboBox QAbstractItemView::item {{ border-radius: {RADIUS_SM}px; padding: 4px 8px; margin: 1px 2px; }}
QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover, QComboBox QListView::item:selected, QComboBox QListView::item:hover, QMenu::item:selected, QMenu::item:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_GREEN}; }}
QMenu::item {{ padding: 4px 12px 4px 18px; margin: 1px 2px; border-radius: {RADIUS_SM}px; color: {COLOR_NEUTRAL_200}; font-size: 12px; }}
QMenu::item:disabled {{ color: {COLOR_NEUTRAL_400}; font-weight: 600; padding: 4px 8px; background-color: transparent; }}
QMenu::item:selected {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_GREEN}; }}
QMenu::separator {{ height: 1px; background-color: {COLOR_NEUTRAL_800}; margin: 3px 6px; }}

QSpinBox, QDoubleSpinBox, QTimeEdit, QDateTimeEdit {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: 3px 56px 3px 8px; border: 1.5px solid {COLOR_NEUTRAL_800}; selection-background-color: transparent; selection-color: {COLOR_NEUTRAL_200}; }}
QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus, QDateTimeEdit:focus {{ border-color: {COLOR_GREEN}; background-color: {COLOR_NEUTRAL_800}; }}
QSpinBox:hover, QDoubleSpinBox:hover, QTimeEdit:hover, QDateTimeEdit:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QSpinBox::up-button, QDoubleSpinBox::up-button, QTimeEdit::up-button, QDateTimeEdit::up-button {{ subcontrol-origin: border; subcontrol-position: center right; width: 24px; height: 24px; right: 28px; border: none; background-color: transparent; }}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QTimeEdit::up-button:hover, QDateTimeEdit::up-button:hover {{ background-color: {COLOR_NEUTRAL_700}; border-radius: {RADIUS_SM}px; }}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed, QTimeEdit::up-button:pressed, QDateTimeEdit::up-button:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow, QTimeEdit::up-arrow, QDateTimeEdit::up-arrow {{ image: url("{PATH_ICON_CHEVRON_UP}"); width: 16px; height: 16px; }}
QSpinBox::down-button, QDoubleSpinBox::down-button, QTimeEdit::down-button, QDateTimeEdit::down-button {{ subcontrol-origin: border; subcontrol-position: center right; width: 24px; height: 24px; right: 4px; border: none; background-color: transparent; }}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover, QTimeEdit::down-button:hover, QDateTimeEdit::down-button:hover {{ background-color: {COLOR_NEUTRAL_700}; border-radius: {RADIUS_SM}px; }}
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed, QTimeEdit::down-button:pressed, QDateTimeEdit::down-button:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow, QTimeEdit::down-arrow, QDateTimeEdit::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 16px; height: 16px; }}

QDateEdit {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: 3px 32px 3px 8px; border: 1.5px solid {COLOR_NEUTRAL_800}; selection-background-color: transparent; selection-color: {COLOR_NEUTRAL_200}; }}
QDateEdit:focus {{ border-color: {COLOR_GREEN}; background-color: {COLOR_NEUTRAL_800}; }}
QDateEdit:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QDateEdit::drop-down {{ subcontrol-origin: border; subcontrol-position: center right; width: 24px; height: 24px; right: 4px; border: none; background-color: transparent; }}
QDateEdit::drop-down:hover {{ background-color: {COLOR_NEUTRAL_700}; border-radius: {RADIUS_SM}px; }}
QDateEdit::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 16px; height: 16px; }}

/* ==============================================================================
   CALENDAR POPUP (QCalendarWidget - Minimalist Dark Aesthetic)
   ============================================================================== */
QCalendarWidget {{ background-color: {COLOR_NEUTRAL_900}; border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_LG}px; padding: 6px; }}
QCalendarWidget QWidget#qt_calendar_navigationbar {{ background-color: transparent; border: none; min-height: 38px; margin-bottom: 4px; }}
QCalendarWidget QToolButton {{ background-color: transparent; color: {COLOR_WHITE}; font-weight: 600; font-size: 13px; border: none; border-radius: {RADIUS_SM}px; padding: 4px 8px; margin: 2px; }}
QCalendarWidget QToolButton:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QCalendarWidget QToolButton:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}
QCalendarWidget QToolButton#qt_calendar_prevmonth {{ qproperty-icon: url("{PATH_ICON_CHEVRON_LEFT}"); icon-size: 16px; width: 28px; height: 28px; }}
QCalendarWidget QToolButton#qt_calendar_nextmonth {{ qproperty-icon: url("{PATH_ICON_CHEVRON_RIGHT}"); icon-size: 16px; width: 28px; height: 28px; }}
QCalendarWidget QToolButton#qt_calendar_monthbutton, QCalendarWidget QToolButton#qt_calendar_yearbutton {{ color: {COLOR_WHITE}; font-size: 14px; font-weight: 600; }}
QCalendarWidget QMenu {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_200}; border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_MD}px; padding: 4px; }}
QCalendarWidget QSpinBox {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_WHITE}; border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_SM}px; padding: 2px 6px; font-weight: 600; }}
QCalendarWidget QSpinBox:focus {{ border-color: {COLOR_GREEN}; }}
QCalendarWidget QTableView {{ background-color: transparent; border: none; gridline-color: transparent; selection-background-color: {COLOR_WHITE}; selection-color: {COLOR_NEUTRAL_950}; }}
QCalendarWidget QTableView:enabled {{ color: {COLOR_NEUTRAL_200}; }}
QCalendarWidget QTableView:disabled {{ color: {COLOR_NEUTRAL_700}; }}
QCalendarWidget QHeaderView::section {{ background-color: transparent; color: {COLOR_NEUTRAL_500}; font-size: 11px; font-weight: 600; padding: 4px 0px; border: none; text-align: center; }}
QCalendarWidget QTableView::item {{ border-radius: 8px; padding: 4px; margin: 2px; }}
QCalendarWidget QTableView::item:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; border-radius: 8px; }}
QCalendarWidget QTableView::item:selected {{ background-color: {COLOR_WHITE}; color: {COLOR_NEUTRAL_950}; font-weight: 700; border-radius: 8px; }}

QCheckBox {{ spacing: 8px; color: {COLOR_NEUTRAL_200}; background-color: transparent; }}
QCheckBox:hover {{ color: {COLOR_WHITE}; }}
QCheckBox::indicator {{ width: 12px; height: 12px; border-radius: {RADIUS_SM}px; border: 1.5px solid {COLOR_NEUTRAL_800}; background-color: {COLOR_NEUTRAL_850}; }}
QCheckBox::indicator:unchecked:hover {{ border-color: {COLOR_NEUTRAL_700}; background-color: {COLOR_NEUTRAL_800}; }}
QCheckBox::indicator:checked {{ border-color: {COLOR_GREEN}; background-color: {COLOR_GREEN}; image: url("{PATH_ICON_CHECK}"); }}
QCheckBox::indicator:checked:hover {{ border-color: {COLOR_GREEN_DARK}; background-color: {COLOR_GREEN_DARK}; }}
QCheckBox::indicator:disabled {{ border-color: {COLOR_NEUTRAL_800}; background-color: {COLOR_WHITE_GLOW}; }}
QCheckBox::indicator:checked:disabled {{ border-color: {COLOR_NEUTRAL_800}; background-color: {COLOR_WHITE_GLOW}; image: url("{PATH_ICON_CHECK}"); }}

QTableWidget {{ background-color: {COLOR_NEUTRAL_900}; border: none; gridline-color: transparent; }}
QTableWidget::item {{ padding: 4px; border-bottom: 1px solid {COLOR_NEUTRAL_800}; }}
QTableWidget::item:selected {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_GREEN}; }}
QHeaderView::section {{ background-color: transparent; color: {COLOR_NEUTRAL_400}; font-weight: 700; padding: {PADDING_INPUT}; border: none; border-bottom: 2px solid {COLOR_NEUTRAL_800}; text-align: left; }}
QHeaderView {{ background-color: transparent; border: none; }}

QScrollBar:vertical {{ border: none; background: transparent; width: 10px; margin: 2px 2px 2px 0px; }}
QScrollBar::handle:vertical {{ background-color: {COLOR_NEUTRAL_500}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background-color: {COLOR_NEUTRAL_200}; }}
QScrollBar::handle:vertical:pressed {{ background-color: {COLOR_GREEN}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ height: 5px; background: none; }}
QScrollBar:horizontal {{ border: none; background: transparent; height: 10px; margin: 0px 2px 2px 2px; }}
QScrollBar::handle:horizontal {{ background-color: {COLOR_NEUTRAL_500}; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background-color: {COLOR_NEUTRAL_200}; }}
QScrollBar::handle:horizontal:pressed {{ background-color: {COLOR_GREEN}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal, QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ width: 5px; background: none; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: transparent; border: none; }}

QProgressBar[role="update_progress"] {{ background-color: {COLOR_NEUTRAL_900}; border: none; border-radius: {RADIUS_SM}px; }}
QProgressBar[role="update_progress"]::chunk {{ background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_GREEN}, stop:1 {COLOR_GREEN}); border-radius: {RADIUS_SM}px; }}
QProgressBar[role="wizard_progress"] {{ background-color: {COLOR_NEUTRAL_700}; border: none; border-radius: 2px; }}
QProgressBar[role="wizard_progress"]::chunk {{ background-color: {COLOR_GREEN}; border-radius: 2px; }}

QListWidget[role="transparent_list"] {{ background: transparent; border: none; }}
QListWidget[role="transparent_list"]::item {{ background: transparent; }}

QTabWidget::pane {{ border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_LG}px; border-top-left-radius: 0px; background-color: {COLOR_NEUTRAL_900}; padding: 8px; }}
QTabBar::tab {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_400}; border: 1.5px solid {COLOR_NEUTRAL_800}; border-bottom-color: transparent; border-top-left-radius: 0px; border-top-right-radius: {RADIUS_MD}px; padding: 8px 16px; margin-right: 4px; font-weight: bold; }}
QTabBar::tab:selected {{ color: {COLOR_GREEN}; background-color: {COLOR_NEUTRAL_900}; border-color: {COLOR_NEUTRAL_800}; border-bottom-color: {COLOR_NEUTRAL_900}; }}
QTabBar::tab:hover:!selected {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QTabWidget QFrame[role="card"] {{ background-color: transparent; border: none; }}

QToolTip {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_NEUTRAL_200}; padding: {PADDING_INPUT}; font-size: {size_textline_1}px; }}

QSlider::groove:horizontal {{ border: none; height: 6px; background: {COLOR_NEUTRAL_850}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {COLOR_GREEN}; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {COLOR_GREEN}; width: 14px; height: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }}
QSlider::handle:horizontal:hover {{ border-color: {COLOR_GREEN_DARK}; }}

/* ==============================================================================
   3. ELEMENTOS DE NAVEGACIÓN Y COMPONENTES ESPECÍFICOS (Con Role)
   ============================================================================== */
QFrame[role="canvas_container"] {{ background-color: {COLOR_NEUTRAL_950}; border: 2px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_MD}px; }}
QFrame[role="sidebar"] {{ background-color: {COLOR_NEUTRAL_900}; border-right: 1.5px solid {COLOR_NEUTRAL_800}; }}
QFrame[role="profile_card"] {{ background-color: transparent; border-radius: {RADIUS_MD}px; }}
QFrame[role="profile_card"]:hover {{ background-color: {COLOR_NEUTRAL_800}; border-color: {COLOR_NEUTRAL_800}; }}

/* ==============================================================================
   4. ESTRUCTURAS Y ROLES DE COMPONENTES GENERALES (Con Role)
   ============================================================================== */
QFrame[role="card"] {{ background-color: {COLOR_NEUTRAL_900}; border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_LG}px; }}
QFrame[role="dialog"] {{ background-color: {COLOR_NEUTRAL_950}; border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: 16px; }}
QFrame[role="dialog"][state="accent"] {{ border-color: {COLOR_GREEN}; }}
QFrame[role="dialog"][state="danger"] {{ border-color: {COLOR_RED}; }}
QFrame[role="banner_danger"] {{ background-color: {COLOR_RED_GLOW}; border: 1px solid {COLOR_RED}; border-radius: {RADIUS_MD}px; }}
QFrame[role="banner_danger"] QLabel {{ color: {COLOR_NEUTRAL_200}; }}
QFrame[role="danger_icon"] {{ background-color: {COLOR_RED}; border-radius: 26px; }}
QFrame[role="accent_icon"] {{ background-color: {COLOR_GREEN}; border-radius: 26px; }}
QFrame[role="divider"] {{ background-color: {COLOR_WHITE_GLOW}; }}
QFrame[role="bot_tag"] {{ background-color: {COLOR_NEUTRAL_800}; border: 1.5px solid {COLOR_NEUTRAL_700}; border-radius: {RADIUS_MD}px; }}
QFrame[role="bot_tag"]:hover {{ border-color: {COLOR_RED}; }}
QFrame[role="bot_tag"] QLabel {{ color: {COLOR_NEUTRAL_200}; font-size: {size_textline_2}px; }}
QFrame[role="toast"] {{ background-color: {COLOR_BLACK}; border: 1px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_MD}px; }}
QFrame[role="toast"][state="success"] {{ border-color: {COLOR_NEUTRAL_750}; }}
QFrame[role="toast"][state="danger"] {{ border-color: {COLOR_RED_GLOW}; }}
QFrame[role="toast"][state="warning"] {{ border-color: {COLOR_AMBER_GLOW}; }}
QFrame[role="toast"][state="info"] {{ border-color: {COLOR_BLUE_GLOW}; }}
QProgressBar {{ background-color: {COLOR_NEUTRAL_850}; border: 1px solid {COLOR_NEUTRAL_800}; border-radius: 4px; height: 6px; text-align: center; }}
QProgressBar::chunk {{ background-color: {COLOR_GREEN}; border-radius: 3px; }}

QFrame[role="badge"] {{ background-color: {COLOR_NEUTRAL_850}; border-radius: {RADIUS_MD}px; }}
QFrame[role="badge"] QLabel {{ font-size: {size_textline_3}px; font-weight: 700; color: {COLOR_NEUTRAL_200}; background: transparent; }}
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
QFrame[role="badge"][state="warning"] QLabel {{ color: {COLOR_AMBER}; }}
QFrame[role="badge"][state="plugin"] {{ background-color: {COLOR_PURPLE_GLOW}; }}
QFrame[role="badge"][state="plugin"] QLabel {{ color: {COLOR_PURPLE}; }}
QLabel[role="badge_kick"] {{ background-color: {COLOR_GREEN_GLOW}; color: {COLOR_GREEN}; font-weight: bold; border-radius: {RADIUS_SM}px; padding: 2px 6px; font-size: {size_textline_3}px; }}
QLabel[role="badge_twitch"] {{ background-color: {COLOR_PURPLE_GLOW}; color: {COLOR_PURPLE}; font-weight: bold; border-radius: {RADIUS_SM}px; padding: 2px 6px; font-size: {size_textline_3}px; }}
QLineEdit[state="plugin"], QTextEdit[state="plugin"], QPlainTextEdit[state="plugin"] {{ border: 1.5px solid {COLOR_PURPLE}; color: {COLOR_PURPLE}; font-weight: bold; background-color: {COLOR_NEUTRAL_900}; }}
QTextEdit[role="ConsoleDisplay"], QTextEdit[role="console"] {{ background-color: {COLOR_NEUTRAL_950}; color: {COLOR_NEUTRAL_200}; border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_MD}px; }}

/* ==============================================================================
   5. SISTEMA DE TIPOGRAFÍA DE TEXTOS (Con Role)
   ============================================================================== */
QLabel[role="h1"] {{ font-size: {size_headline_1}px; font-weight: 400; color: {COLOR_NEUTRAL_200}; }}
QLabel[role="h2"] {{ font-size: {size_headline_2}px; font-weight: 400; color: {COLOR_NEUTRAL_200}; }}
QLabel[role="h3"] {{ font-size: {size_headline_3}px; font-weight: 400; color: {COLOR_NEUTRAL_200}; }}
QLabel[role="body"] {{ font-size: {size_textline_1}px; font-weight: 400; color: {COLOR_NEUTRAL_400}; }}
QLabel[role="caption"] {{ font-size: {size_textline_3}px; font-weight: 400; color: {COLOR_NEUTRAL_500}; }}
QLabel[role="monospace"] {{ font-size: {size_textline_2}px; color: {COLOR_NEUTRAL_400}; }}
QLabel[state="normal"] {{ color: {COLOR_NEUTRAL_200}; }}
QLabel[state="error"] {{ color: {COLOR_RED}; }}
QLabel[state="danger"] {{ color: {COLOR_RED}; }}
QLabel[state="success"] {{ color: {COLOR_GREEN}; }}
QLabel[state="info"] {{ color: {COLOR_BLUE}; }}
QLabel[state="warning"] {{ color: {COLOR_AMBER}; }}
QLabel[state="bold"] {{ font-weight: bold; }}
QLabel[role="code"] {{ font-size: {size_textline_2}px; font-weight: bold; background-color: {COLOR_NEUTRAL_850}; padding: 1px 4px; border-radius: {RADIUS_SM}px; color: {COLOR_NEUTRAL_200}; }}
QLabel[role="category"] {{ font-weight: bold; color: {COLOR_GREEN}; margin-top: 6px; font-size: {size_textline_2}px; }}

/* ==============================================================================
   6. BOTONES Y ACCIONES (Con Role)
   ============================================================================== */
QPushButton[role="nav_button"] {{ background: transparent; border-radius: {RADIUS_MD}px; padding: 10px; text-align: left; color: {COLOR_NEUTRAL_400}; font-weight: 500; }}
QPushButton[role="nav_button"]:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_NEUTRAL_200}; }}
QPushButton[role="nav_button"]:checked {{ background-color: {COLOR_NEUTRAL_750}; color: {COLOR_GREEN}; font-weight: 700; }}
QPushButton[role="nav_button"][collapsed="false"] {{ text-align: left; padding-left: 10px; }}
QPushButton[role="nav_button"][collapsed="true"] {{ text-align: center; padding: 10px; }}
QPushButton[role="action_accent"] {{ background-color: {COLOR_GREEN}; color: {COLOR_NEUTRAL_950}; font-size: {size_textline_1}px; font-weight: 700; border: none; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_accent"]:hover {{ background-color: {COLOR_GREEN_DARK}; }}
QPushButton[role="action_outlined"] {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-size: {size_textline_1}px; font-weight: 700; border: none; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_outlined"]:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QPushButton[role="action_danger_border"] {{ background-color: transparent; color: {COLOR_RED}; font-size: {size_textline_1}px; font-weight: 700; border: 1.5px solid {COLOR_RED}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_danger_border"]:hover {{ background-color: {COLOR_RED_GLOW}; }}
QPushButton[role="action_accent_border"] {{ background-color: transparent; color: {COLOR_GREEN}; font-size: {size_textline_1}px; font-weight: 700; border: 1.5px solid {COLOR_GREEN}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_accent_border"]:hover {{ background-color: {COLOR_GREEN_GLOW}; }}
QPushButton[role="action_neutral_border"] {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-size: {size_textline_1}px; font-weight: 700; border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_neutral_border"]:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QPushButton[role="btn_ghost"] {{ background-color: transparent; border: none; border-radius: {RADIUS_SM}px; padding: 2px; }}
QPushButton[role="btn_ghost"]:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QPushButton[role="filter_chip"] {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_400}; border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_SM}px; padding: 3px 10px; font-size: {size_textline_2}px; font-weight: 600; }}
QPushButton[role="filter_chip"]:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_WHITE}; }}
QPushButton[role="filter_chip"]:checked {{ background-color: {COLOR_GREEN}; color: {COLOR_NEUTRAL_950}; border-color: {COLOR_GREEN}; font-weight: 700; }}

/* ==============================================================================
   7. ESTADOS DESHABILITADOS (Global)
   ============================================================================== */
QPushButton:disabled, QPushButton[role="action_accent"]:disabled,
QPushButton[role="action_outlined"]:disabled, QPushButton[role="action_danger_border"]:disabled,
QPushButton[role="action_accent_border"]:disabled, QPushButton[role="action_neutral_border"]:disabled,
QPushButton[role="btn_ghost"]:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border: 1.5px solid {COLOR_NEUTRAL_800}; padding: {PADDING_BUTTON}; }}
QLineEdit:disabled, QTextEdit:disabled,
QComboBox:disabled, QSpinBox:disabled,
QDoubleSpinBox:disabled {{ background-color: {COLOR_WHITE_GLOW}; color: {COLOR_NEUTRAL_500}; border-color: {COLOR_NEUTRAL_800}; padding: {PADDING_INPUT}; }}
QCheckBox:disabled {{ color: {COLOR_NEUTRAL_500}; }}

/* ==============================================================================
   8. COMPONENTES COMPUESTOS (Search Bar y Segmented Pagination)
   ============================================================================== */
QFrame[role="search_bar"] {{ background-color: {COLOR_NEUTRAL_850}; border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_MD}px; }}
QFrame[role="search_bar"]:hover {{ border-color: {COLOR_NEUTRAL_700}; }}
QFrame[role="search_bar"]:focus-within {{ border-color: {COLOR_GREEN}; }}
QFrame[role="search_bar"] QLineEdit {{ background: transparent; border: none; padding: 0px 12px; color: {COLOR_WHITE}; font-size: {size_textline_1}px; }}
QFrame[role="search_bar"] QPushButton {{ background: transparent; border: none; border-left: 1.5px solid {COLOR_NEUTRAL_800}; border-top-right-radius: {RADIUS_MD - 2}px; border-bottom-right-radius: {RADIUS_MD - 2}px; min-width: 36px; max-width: 36px; min-height: 32px; max-height: 32px; }}
QFrame[role="search_bar"] QPushButton:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QFrame[role="search_bar"] QPushButton:pressed {{ background-color: {COLOR_NEUTRAL_700}; }}

QFrame[role="segmented_pagination"] {{ background-color: {COLOR_NEUTRAL_850}; border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_MD}px; }}
QFrame[role="segmented_pagination"] QPushButton {{ background: transparent; border: none; border-left: 1.5px solid {COLOR_NEUTRAL_800}; min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; }}
QFrame[role="segmented_pagination"] QPushButton#btn_first {{ border-left: none; border-top-left-radius: {RADIUS_MD - 2}px; border-bottom-left-radius: {RADIUS_MD - 2}px; }}
QFrame[role="segmented_pagination"] QPushButton#btn_last {{ border-top-right-radius: {RADIUS_MD - 2}px; border-bottom-right-radius: {RADIUS_MD - 2}px; }}
QFrame[role="segmented_pagination"] QPushButton:hover:enabled {{ background-color: {COLOR_NEUTRAL_800}; }}
QFrame[role="segmented_pagination"] QPushButton:pressed:enabled {{ background-color: {COLOR_NEUTRAL_700}; }}
QFrame[role="segmented_pagination"] QPushButton:disabled {{ opacity: 0.5; }}
QFrame[role="segmented_pagination"] QLabel#lbl_page_status {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_WHITE}; font-size: {size_textline_1}px; font-weight: 600; padding: 0px 16px; min-height: 32px; max-height: 32px; border-left: 1.5px solid {COLOR_NEUTRAL_800}; }}
"""
GLOBAL_QSS = get_global_qss(13)

def get_swatch_qss(bg_color: str, border_width: int = 1, radius: int = RADIUS_SM) -> str:
    return f"background-color: {bg_color}; border: {border_width}px solid {COLOR_NEUTRAL_700}; border-radius: {radius}px;"
