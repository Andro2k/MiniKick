# frontend/theme.py

from frontend.utils import get_assets_path
PATH_ICON_HELP = get_assets_path("icons/help.svg")
PATH_ICON_UPDATE = get_assets_path("icons/cloud.svg")
PATH_ICON_CHEVRON_DOWN = get_assets_path("icons/chevron-down.svg").replace('\\', '/')
PATH_ICON_CHEVRON_UP = get_assets_path("icons/chevron-up.svg").replace('\\', '/')

COLOR_BG_BASE       = "#0B0E11"
COLOR_BG_SURFACE    = "#1E2329"
COLOR_BG_INPUT      = "#42474D"
COLOR_BG_HOVER      = "#333333"   
COLOR_BG_CONSOLE    = "#0F172A"

COLOR_BORDER_SVELTE = "#333333"
COLOR_BORDER_ACTIVE = "#53FC18"

COLOR_ACCENT        = "#53FC18"
COLOR_ACCENT_HOVER  = "#00C864"   
COLOR_ACCENT_SOFT   = "rgba(0, 229, 115, 0.15)"

COLOR_SUCCESS       = "#10B981"

COLOR_DANGER        = "#EF4444"
COLOR_DANGER_HOVER  = "#D74141"
COLOR_DANGER_SOFT   = "rgba(239, 68, 68, 0.15)"

COLOR_TEXT_PRIMARY   = "#F3F4F6"
COLOR_TEXT_SECONDARY = "#9CA3AF"
COLOR_TEXT_MUTED     = "#6B7280"
COLOR_TEXT_INVERSE   = "#000000"
COLOR_TEXT_CONSOLE   = "#F8FAFC"

FONT_FAMILY = "'Inter', '-apple-system', 'Segoe UI', sans-serif"

RADIUS_SM = 6
RADIUS_MD = 8
RADIUS_LG = 12

PADDING_INPUT   = "4px 12px"
PADDING_BUTTON  = "4px 8px"

GLOBAL_QSS = f"""
/* ============================================================================
   1. RESET Y BASE GLOBAL
   ============================================================================ */
* {{
    font-family: {FONT_FAMILY};
    font-size: 14px;
    color: {COLOR_TEXT_PRIMARY};
    outline: none;
}}

QMainWindow, QDialog {{ background-color: {COLOR_BG_BASE}; }}
QLabel {{ background-color: transparent; }}

/* ============================================================================
   2. SISTEMA DE TIPOGRAFÍA (ESTANDARIZADO)
   ============================================================================ */
QLabel[role="h1"] {{ font-size: 24px; font-weight: 800; color: {COLOR_TEXT_PRIMARY}; }}
QLabel[role="h2"] {{ font-size: 18px; font-weight: bold; color: {COLOR_TEXT_PRIMARY}; }}
QLabel[role="h3"] {{ font-size: 14px; font-weight: bold; color: {COLOR_TEXT_PRIMARY}; }}
QLabel[role="body"] {{ font-size: 14px; color: {COLOR_TEXT_SECONDARY}; line-height: 1.5; }}
QLabel[role="caption"] {{ font-size: 14px; color: {COLOR_TEXT_MUTED}; }}
QLabel[role="text_accent"] {{ font-size: 12px; font-weight: bold; color: {COLOR_ACCENT}; }}
QLabel[role="text_danger"] {{ font-size: 12px; font-weight: bold; color: {COLOR_DANGER}; }}
QLabel[role="monospace"] {{ font-family: {FONT_FAMILY}; color: {COLOR_TEXT_SECONDARY}; }}
QLabel[role="status_dot"][state="active"] {{ color: {COLOR_SUCCESS}; font-size: 14px; margin-right: 2px; }}
QLabel[role="status_dot"][state="inactive"] {{ color: {COLOR_DANGER}; font-size: 14px; margin-right: 2px; }}

QLabel[role="tag_permission"] {{ 
    background-color: {COLOR_ACCENT}; 
    color: #000000; 
    font-size: 10px; 
    font-weight: bold; 
    padding: 2px 4px; 
    border-radius: 4px; 
}}
QLabel[role="stat_value"] {{ 
    font-size: 18px; 
    font-weight: 800; 
    color: {COLOR_TEXT_PRIMARY}; 
}}
/* ============================================================================
   3. SISTEMA DE CONTENEDORES (CARDS, DIALOGS, BANNERS)
   ============================================================================ */
QFrame[role="card"] {{
    background-color: {COLOR_BG_SURFACE};
    border: none;
    border-radius: {RADIUS_LG}px;
}}

QFrame[role="dialog"] {{
    background-color: {COLOR_BG_BASE};
    border: 1.5px solid {COLOR_BORDER_SVELTE};
    border-radius: 16px;
}}
QFrame[role="dialog"][state="accent"] {{ border-color: rgba(83, 252, 24, 0.4); }}
QFrame[role="dialog"][state="danger"] {{ border-color: rgba(239, 68, 68, 0.4); }}

QFrame[role="banner_danger"] {{
    background-color: {COLOR_DANGER_SOFT};
    border: 1px solid {COLOR_DANGER};
    border-radius: {RADIUS_MD}px;
}}
QFrame[role="banner_danger"] QLabel {{ color: {COLOR_TEXT_PRIMARY}; }}
QFrame[dialog_role="danger_icon"] {{ background-color: {COLOR_DANGER}; border-radius: 26px; }}
QFrame[dialog_role="accent_icon"] {{ background-color: {COLOR_ACCENT}; border-radius: 26px; }}

QFrame#CanvasContainer {{
    background-color: {COLOR_BG_BASE};
    border: 2px solid {COLOR_BORDER_SVELTE};
    border-radius: {RADIUS_MD}px;
}}

QFrame[role="step_indicator"] {{
    background-color: {COLOR_BORDER_SVELTE};
    border-radius: 2px;
}}

QFrame[role="step_indicator"][state="active"] {{
    background-color: {COLOR_ACCENT};
}}
QFrame[role="divider"] {{ background-color: rgba(255, 255, 255, 0.05); margin: 4px 0px; }}
/* ============================================================================
   4. SISTEMA DE BOTONES
   ============================================================================ */
QPushButton[role="action_accent"] {{
    background-color: {COLOR_ACCENT}; border: none; border-radius: {RADIUS_MD}px;
    padding: {PADDING_BUTTON}; color: {COLOR_TEXT_INVERSE}; font-weight: 800;
}}
QPushButton[role="action_accent"]:hover {{ background-color: {COLOR_ACCENT_HOVER}; }}

QPushButton[role="action_outlined"] {{
    background-color: {COLOR_BG_INPUT}; border: none; border-radius: {RADIUS_MD}px;
    padding: {PADDING_INPUT}; color: {COLOR_TEXT_PRIMARY}; font-weight: 500;
}}
QPushButton[role="action_outlined"]:hover {{ background-color: {COLOR_BG_HOVER}; }}

QPushButton[role="action_danger"] {{
    background-color: transparent; border: 1.5px solid {COLOR_DANGER}; 
    color: {COLOR_DANGER}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; font-weight: 600;
}}
QPushButton[role="action_danger"]:hover {{ background-color: {COLOR_DANGER_SOFT}; }}

QPushButton[role="btn_ghost"] {{
    background-color: transparent; border: none; border-radius: 4px; padding: 2px;
}}
QPushButton[role="btn_ghost"]:hover {{ background-color: {COLOR_BG_HOVER}; }}

/* ============================================================================
   5. CONTROLES NATIVOS (Inputs, Tablas, Combos, Scrolls, Tabs)
   ============================================================================ */
QLineEdit, QTextEdit {{
    background-color: {COLOR_BG_INPUT}; border: none;
    border-radius: {RADIUS_MD}px; padding: {PADDING_INPUT}; color: {COLOR_TEXT_PRIMARY};
}}
QTextEdit {{ background-color: {COLOR_BG_SURFACE}; border: 1.5px solid {COLOR_BORDER_SVELTE}; }}
QLineEdit:focus, QTextEdit:focus {{ border: 1.5px solid {COLOR_BORDER_ACTIVE}; background-color: {COLOR_BG_HOVER}; }}

QComboBox {{
    background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_PRIMARY};
    border-radius: {RADIUS_MD}px; padding: 6px 28px 6px 8px; border: 1.5px solid transparent;
}}
QComboBox:focus, QComboBox:hover {{ 
    border: 1.5px solid {COLOR_BORDER_SVELTE}; background-color: {COLOR_BG_HOVER}; 
}}
QComboBox::drop-down {{ 
    subcontrol-origin: padding; subcontrol-position: top right; width: 30px; 
    border-left: 1.5px solid {COLOR_BORDER_SVELTE};
    border-top-right-radius: {RADIUS_MD}px; border-bottom-right-radius: {RADIUS_MD}px;
}}
QComboBox::drop-down:hover {{ background-color: {COLOR_BG_HOVER}; }}
QComboBox::down-arrow {{ 
    image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 14px; height: 14px; 
}}
QComboBox::down-arrow:on {{ top: 1px; left: 1px; }}
QComboBox QAbstractItemView, QMenu {{
    background-color: {COLOR_BG_SURFACE}; color: {COLOR_TEXT_PRIMARY};
    border: 1.5px solid {COLOR_BORDER_SVELTE}; border-radius: {RADIUS_MD}px; outline: none; padding: 2px;
}}
QComboBox QAbstractItemView::item, QMenu::item {{ border-radius: {RADIUS_SM}px; padding: 2px; margin: 2px; }}
QComboBox QAbstractItemView::item:selected, QMenu::item:selected {{ background-color: {COLOR_BG_HOVER}; color: {COLOR_ACCENT}; }}

QSpinBox, QDoubleSpinBox {{
    background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_PRIMARY};
    border-radius: {RADIUS_MD}px; padding: 4px 28px 4px 8px; border: 1.5px solid transparent;
    min-height: 20px;
}}
QSpinBox:focus, QDoubleSpinBox:focus, QSpinBox:hover, QDoubleSpinBox:hover {{ 
    border: 1.5px solid {COLOR_BORDER_SVELTE}; background-color: {COLOR_BG_HOVER}; 
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border; subcontrol-position: top right;
    width: 24px; background-color: transparent;
    border-left: 1.5px solid {COLOR_BORDER_SVELTE};
    border-bottom: 1.5px solid {COLOR_BORDER_SVELTE};
    border-top-right-radius: {RADIUS_MD}px;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{ background-color: {COLOR_BG_HOVER}; }}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {{ background-color: {COLOR_ACCENT_SOFT}; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url("{PATH_ICON_CHEVRON_UP}"); width: 10px; height: 10px;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border; subcontrol-position: bottom right;
    width: 24px; background-color: transparent;
    border-left: 1.5px solid {COLOR_BORDER_SVELTE};
    border-bottom-right-radius: {RADIUS_MD}px;
}}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{ background-color: {COLOR_BG_HOVER}; }}
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{ background-color: {COLOR_ACCENT_SOFT}; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 10px; height: 10px;
}}

QTableWidget {{ background-color: {COLOR_BG_SURFACE}; border: none; gridline-color: transparent; outline: none; }}
QTableWidget::item {{ padding: 4px; border-bottom: 1px solid {COLOR_BORDER_SVELTE}; }}
QTableWidget::item:selected {{ background-color: {COLOR_BG_HOVER}; color: {COLOR_ACCENT}; }}
QHeaderView::section {{ background-color: transparent; color: {COLOR_TEXT_SECONDARY}; font-weight: bold; padding: 6px 8px; border: none; border-bottom: 2px solid {COLOR_BORDER_SVELTE}; text-align: left; }}
QHeaderView {{ background-color: transparent; border: none; }}

QScrollBar:vertical {{ border: none; background: transparent; width: 14px; margin: 2px 4px 2px 0px; }}
QScrollBar::handle:vertical {{ background-color: {COLOR_TEXT_MUTED}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background-color: {COLOR_TEXT_PRIMARY}; }}
QScrollBar::handle:vertical:pressed {{ background-color: {COLOR_ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ height: 0px; background: none; }}

QScrollBar:horizontal {{ border: none; background: transparent; height: 14px; margin: 0px 2px 4px 2px; }}
QScrollBar::handle:horizontal {{ background-color: {COLOR_TEXT_MUTED}; border-radius: 5px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background-color: {COLOR_TEXT_PRIMARY}; }}
QScrollBar::handle:horizontal:pressed {{ background-color: {COLOR_ACCENT}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal, QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ width: 0px; background: none; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: transparent; border: none; }}

QTabWidget::pane {{ border: none; background-color: transparent; border-top: 1px solid {COLOR_BORDER_SVELTE}; }}
QTabBar::tab {{ background-color: transparent; color: {COLOR_TEXT_SECONDARY}; padding: 10px 20px; font-size: 12px; font-weight: 600; border-bottom: 2px solid transparent; }}
QTabBar::tab:hover {{ color: {COLOR_TEXT_PRIMARY}; background-color: {COLOR_BG_HOVER}; }}
QTabBar::tab:selected {{ color: {COLOR_ACCENT}; border-bottom: 2px solid {COLOR_ACCENT}; }}

/* ============================================================================
   6. EXCEPCIONES Y COMPONENTES ESPECÍFICOS DE LA APP
   ============================================================================ */
QFrame#Sidebar {{ background-color: {COLOR_BG_BASE}; border-right: 1px solid {COLOR_BORDER_SVELTE}; }}
QPushButton#NavButton {{ background: transparent; border-radius: {RADIUS_MD}px; padding: 10px; text-align: left; color: {COLOR_TEXT_SECONDARY}; font-weight: 700; }}
QPushButton#NavButton:hover {{ background-color: {COLOR_BG_HOVER}; color: {COLOR_TEXT_PRIMARY}; }}
QPushButton#NavButton:checked {{ background-color: {COLOR_ACCENT_SOFT}; color: {COLOR_ACCENT}; }}
QPushButton#NavButton[collapsed="false"] {{ text-align: left; padding-left: 12px; }}
QPushButton#NavButton[collapsed="true"] {{ text-align: center; padding: 10px; }}
QProgressBar[role="update_progress"] {{ background-color: {COLOR_BG_SURFACE}; border: none; border-radius: 5px; }}
QProgressBar[role="update_progress"]::chunk {{ background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_ACCENT}, stop:1 #22C55E); border-radius: 5px; }}
QTextEdit#ConsoleDisplay {{ background-color: {COLOR_BG_CONSOLE}; color: {COLOR_TEXT_CONSOLE}; font-family: {FONT_FAMILY}; font-size: 12px; border-radius: {RADIUS_MD}px; padding: 10px; }}

/* ============================================================================
   8. COMPONENTES ESPECÍFICOS: TAGS Y CONSOLA
   ============================================================================ */
QListWidget[role="transparent_list"] {{ 
    background: transparent; 
    border: none; 
    outline: none; 
}}
QListWidget[role="transparent_list"]::item {{ 
    background: transparent; 
}}

QFrame[role="tag"] {{
    background-color: {COLOR_BG_INPUT};
    border: 1.5px solid {COLOR_BORDER_SVELTE};
    border-radius: {RADIUS_MD}px;
}}
QFrame[role="tag"]:hover {{ 
    border: 1.5px solid {COLOR_DANGER_HOVER}; 
}}
QFrame[role="tag"] QLabel {{ 
    color: {COLOR_TEXT_PRIMARY}; 
    padding-right: 4px; 
    font-size: 12px; 
}}

QTextEdit[role="console"] {{
    background-color: {COLOR_BG_CONSOLE};
    color: {COLOR_TEXT_CONSOLE};
    font-family: {FONT_FAMILY};
    font-size: 12px;
    border-radius: {RADIUS_MD}px;
    padding: 10px;
}}
"""