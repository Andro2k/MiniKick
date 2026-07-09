# frontend\common\theme.py

from frontend.common.utils import get_assets_path
PATH_ICON_HELP = get_assets_path("icons/help.svg")
PATH_ICON_CHEVRON_DOWN = get_assets_path("icons/chevron-down.svg").replace('\\', '/')
PATH_ICON_CHEVRON_UP = get_assets_path("icons/chevron-up.svg").replace('\\', '/')
PATH_ICON_CHECK = get_assets_path("icons/check.svg").replace('\\', '/')

COLOR_NEUTRAL_950  = "#09090B"
COLOR_NEUTRAL_900  = "#121214"
COLOR_NEUTRAL_850  = "#18181B"
COLOR_NEUTRAL_800  = "#27272A"
COLOR_NEUTRAL_750  = "#29292B"
COLOR_NEUTRAL_700  = "#3F3F46"
COLOR_NEUTRAL_500  = "#71717A"
COLOR_NEUTRAL_400  = "#767676"
COLOR_NEUTRAL_200  = "#CCCCCC"
COLOR_WHITE        = "#FAFAFA"
COLOR_BLACK        = "#000000"
COLOR_GREEN        = "#2ECD70"
COLOR_GREEN_DARK   = "#25AE60"
COLOR_RED          = "#EF4444"
COLOR_AMBER        = "#F59E0B"
COLOR_BLUE         = "#3B82F6"
COLOR_PURPLE       = "#A78BFA"

COLOR_WHITE_GLOW   = "rgba(255, 255, 255, 0.1)"
COLOR_GREEN_GLOW   = "rgba(46, 205, 112, 0.1)"
COLOR_RED_GLOW     = "rgba(239, 68, 68, 0.1)"
COLOR_AMBER_GLOW   = "rgba(245, 158, 11, 0.1)"
COLOR_BLUE_GLOW    = "rgba(59, 130, 246, 0.1)"
COLOR_PURPLE_GLOW  = "rgba(139, 92, 246, 0.1)"

FONT_FAMILY = "'Google Sans', '-apple-system', 'Segoe UI', sans-serif"

RADIUS_SM = 6
RADIUS_MD = 9
RADIUS_LG = 12

PADDING_INPUT   = "5px 10px"
PADDING_BUTTON  = "6px 12px"


def get_global_qss(base: int = 13) -> str:
    size_headline_1 = base + 15
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
QLineEdit, QTextEdit {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border: none; border-radius: {RADIUS_MD}px; padding: {PADDING_INPUT}; border: 1.5px solid {COLOR_NEUTRAL_800}; }}
QTextEdit {{ background-color: {COLOR_NEUTRAL_900}; border: 1.5px solid {COLOR_NEUTRAL_800}; }}
QLineEdit:focus, QTextEdit:focus {{ border: 1.5px solid {COLOR_GREEN}; background-color: {COLOR_NEUTRAL_800}; }}

QComboBox {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_INPUT}; border: 1.5px solid {COLOR_NEUTRAL_800}; combobox-popup: 0; }}
QComboBox:focus, QComboBox:hover {{ border-color: transparent; background-color: {COLOR_NEUTRAL_800}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 23px; border-left: 1.5px solid {COLOR_NEUTRAL_700}; border-top-right-radius: {RADIUS_MD}px; border-bottom-right-radius: {RADIUS_MD}px; }}
QComboBox:focus::drop-down, QComboBox:hover::drop-down {{ border-color: {COLOR_NEUTRAL_700}; }}
QComboBox::drop-down:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QComboBox::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 15px; height: 15px; }}
QComboBox::down-arrow:on {{ top: 1px; left: 1px; }}
QComboBox QAbstractItemView, QMenu {{ background-color: {COLOR_NEUTRAL_900}; color: {COLOR_NEUTRAL_200}; border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_MD}px; padding: 2px; selection-background-color: {COLOR_NEUTRAL_800}; selection-color: {COLOR_GREEN}; }}
QComboBox QAbstractItemView::item, QMenu::item {{ border-radius: {RADIUS_SM}px; padding: 2px; margin: 2px; }}
QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover, QComboBox QListView::item:selected, QComboBox QListView::item:hover, QMenu::item:selected, QMenu::item:hover {{ background-color: {COLOR_NEUTRAL_800}; color: {COLOR_GREEN}; }}

QSpinBox, QDoubleSpinBox {{ background-color: {COLOR_NEUTRAL_850}; color: {COLOR_NEUTRAL_200}; font-weight: 400; border-radius: {RADIUS_MD}px; padding: 3px 8px 3px 8px; border: 1.5px solid {COLOR_NEUTRAL_800}; }}
QSpinBox:focus, QDoubleSpinBox:focus, QSpinBox:hover, QDoubleSpinBox:hover {{ border-color: transparent; background-color: {COLOR_NEUTRAL_800}; }}
QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 24px; border-left: 1.5px solid {COLOR_NEUTRAL_700}; border-bottom: 1.2px solid {COLOR_NEUTRAL_700}; border-top-right-radius: {RADIUS_MD}px; }}
QSpinBox:focus::up-button, QDoubleSpinBox::focus::up-button, QSpinBox:hover::up-button, QDoubleSpinBox::hover::up-button {{ border-color: {COLOR_NEUTRAL_700}; }}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url("{PATH_ICON_CHEVRON_UP}"); width: 15px; height: 15px; }}
QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 24px; border-left: 1.5px solid {COLOR_NEUTRAL_700}; border-top: 1.2px solid {COLOR_NEUTRAL_700}; border-bottom-right-radius: {RADIUS_MD}px; }}
QSpinBox:focus::down-button, QDoubleSpinBox::focus::down-button, QSpinBox:hover::down-button, QDoubleSpinBox::hover::down-button {{ border-color: {COLOR_NEUTRAL_700}; }}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{ background-color: {COLOR_NEUTRAL_750}; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 15px; height: 15px; }}

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
QFrame[role="card"] {{ background-color: {COLOR_NEUTRAL_900}; border: none; border-radius: {RADIUS_LG}px; }}
QFrame[role="dialog"] {{ background-color: {COLOR_NEUTRAL_950}; border: 1.5px solid {COLOR_NEUTRAL_800}; border-radius: 16px; }}
QFrame[role="dialog"][state="accent"] {{ border-color: {COLOR_GREEN}; }}
QFrame[role="dialog"][state="danger"] {{ border-color: {COLOR_RED}; }}
QFrame[role="banner_danger"] {{ background-color: {COLOR_RED_GLOW}; border: 1px solid {COLOR_RED}; border-radius: {RADIUS_MD}px; }}
QFrame[role="banner_danger"] QLabel {{ color: {COLOR_NEUTRAL_200}; }}
QFrame[role="danger_icon"] {{ background-color: {COLOR_RED}; border-radius: 26px; }}
QFrame[role="accent_icon"] {{ background-color: {COLOR_GREEN}; border-radius: 26px; }}
QFrame[role="divider"] {{ background-color: {COLOR_WHITE_GLOW}; margin: 4px 0px; }}
QFrame[role="bot_tag"] {{ background-color: {COLOR_NEUTRAL_800}; border: 1.5px solid {COLOR_NEUTRAL_700}; border-radius: {RADIUS_MD}px; }}
QFrame[role="bot_tag"]:hover {{ border-color: {COLOR_RED}; }}
QFrame[role="bot_tag"] QLabel {{ color: {COLOR_NEUTRAL_200}; font-size: {size_textline_2}px; }}
QFrame[role="toast"] {{ background-color: {COLOR_BLACK}; border: 1px solid {COLOR_NEUTRAL_800}; border-radius: {RADIUS_MD}px; }}
QFrame[role="toast"][state="success"] {{ border-color: {COLOR_NEUTRAL_750}; }}
QFrame[role="toast"][state="danger"] {{ border-color: {COLOR_RED_GLOW}; }}
QFrame[role="toast"][state="warning"] {{ border-color: {COLOR_AMBER_GLOW}; }}
QFrame[role="toast"][state="info"] {{ border-color: {COLOR_BLUE_GLOW}; }}

QFrame[role="badge"] {{ background-color: {COLOR_NEUTRAL_850}; border-radius: {RADIUS_MD}px;}}
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

/* ==============================================================================
   5. SISTEMA DE TIPOGRAFÍA DE TEXTOS (Con Role)
   ============================================================================== */
QLabel[role="h1"] {{ font-size: {size_headline_1}px; font-weight: 400; color: {COLOR_NEUTRAL_200}; }}
QLabel[role="h2"] {{ font-size: {size_headline_2}px; font-weight: 400; color: {COLOR_NEUTRAL_200}; }}
QLabel[role="h3"] {{ font-size: {size_headline_3}px; font-weight: 400; color: {COLOR_NEUTRAL_200}; }}
QLabel[role="body"] {{ font-size: {size_textline_1}px; font-weight: 400; color: {COLOR_NEUTRAL_400}; }}
QLabel[role="caption"] {{ font-size: {size_textline_3}px; font-weight: 400; color: {COLOR_NEUTRAL_500}; }}
QLabel[role="monospace"] {{ font-size: {size_textline_2}px; color: {COLOR_NEUTRAL_400}; }}
QLabel[state="error"] {{ color: {COLOR_RED}; }}
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
QPushButton[role="action_neutral_border"] {{ background-color: transparent; color: {COLOR_NEUTRAL_200}; font-size: {size_textline_1}px; font-weight: 700; border: 1.5px solid {COLOR_NEUTRAL_700}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_neutral_border"]:hover {{ background-color: {COLOR_NEUTRAL_800}; }}
QPushButton[role="btn_ghost"] {{ background-color: transparent; border: none; border-radius: {RADIUS_SM}px; padding: 2px; }}
QPushButton[role="btn_ghost"]:hover {{ background-color: {COLOR_NEUTRAL_800}; }}

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
"""
GLOBAL_QSS = get_global_qss(13)