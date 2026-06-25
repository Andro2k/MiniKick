# frontend\common\theme.py

from frontend.common.utils import get_assets_path
PATH_ICON_HELP = get_assets_path("icons/help.svg")
PATH_ICON_UPDATE = get_assets_path("icons/cloud.svg")
PATH_ICON_CHEVRON_DOWN = get_assets_path("icons/chevron-down.svg").replace('\\', '/')
PATH_ICON_CHEVRON_UP = get_assets_path("icons/chevron-up.svg").replace('\\', '/')

COLOR_BG_BASE       = "#0B0E11"
COLOR_BG_SURFACE    = "#1E2329"
COLOR_BG_INPUT      = "#42474D"
COLOR_BG_HOVER      = "#333333"

COLOR_BORDER_SVELTE = "#333333"

COLOR_ACCENT        = "#64EB5F"
COLOR_ACCENT_HOVER  = "#2FBF45"   

COLOR_DANGER        = "#EF4444"
COLOR_WARNING       = "#F59E0B"
COLOR_INFO          = "#3B82F6"

COLOR_BG_TOAST      = "#090C10"
COLOR_ACCENT_GLOW   = "rgba(100, 235, 95, 0.3)"
COLOR_DANGER_GLOW   = "rgba(239, 68, 68, 0.3)"
COLOR_WARNING_GLOW  = "rgba(245, 158, 11, 0.3)"
COLOR_INFO_GLOW     = "rgba(59, 130, 246, 0.3)"

COLOR_TEXT_PRIMARY   = "#F3F4F6"
COLOR_TEXT_SECONDARY = "#9CA3AF"
COLOR_TEXT_MUTED     = "#6B7280"
COLOR_BLACK          = "#000000"

FONT_FAMILY = "'Inter', '-apple-system', 'Segoe UI', sans-serif"

RADIUS_SM = 6
RADIUS_MD = 8
RADIUS_LG = 12

PADDING_INPUT   = "5px 10px"
PADDING_BUTTON  = "6px 12px"

GLOBAL_QSS = f"""
/* --- 1. RESET Y BASE GLOBAL --- */
* {{
    font-family: {FONT_FAMILY};
    font-size: 13px;
    color: {COLOR_TEXT_PRIMARY};
    outline: none;
}}

QMainWindow, QDialog {{ background-color: {COLOR_BG_BASE}; }}
QLabel {{ background-color: transparent; }}

/* --- 2. SISTEMA DE TIPOGRAFÍA --- */
QLabel[role="h1"] {{ font-size: 22px; font-weight: 800; color: {COLOR_TEXT_PRIMARY}; }}
QLabel[role="h2"] {{ font-size: 16px; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; }}
QLabel[role="h3"] {{ font-size: 13px; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; }}
QLabel[role="body"] {{ font-size: 13px; font-weight: 400; color: {COLOR_TEXT_SECONDARY}; line-height: 1.5; }}
QLabel[role="caption"] {{ font-size: 11px; font-weight: 400; color: {COLOR_TEXT_MUTED}; }}
QLabel[role="text_accent"] {{ font-size: 12px; font-weight: 700; color: {COLOR_ACCENT}; }}
QLabel[role="text_danger"] {{ font-size: 12px; font-weight: 700; color: {COLOR_DANGER}; }}
QLabel[role="monospace"] {{ font-family: {FONT_FAMILY}; font-size: 12px; color: {COLOR_TEXT_SECONDARY}; }}
QLabel[role="status_dot"][state="active"] {{ color: {COLOR_ACCENT}; font-size: 13px; margin-right: 2px; }}
QLabel[role="status_dot"][state="inactive"] {{ color: {COLOR_DANGER}; font-size: 13px; margin-right: 2px; }}
QLabel[role="tag_permission"] {{ background-color: {COLOR_ACCENT}; color: {COLOR_BLACK}; font-size: 10px; font-weight: 700; padding: 2px 4px; border-radius: 4px; }}
QLabel[role="stat_value"] {{ font-size: 18px; font-weight: 800; color: {COLOR_TEXT_PRIMARY}; }}

/* --- 3. CONTENEDORES --- */
QFrame[role="card"] {{ background-color: {COLOR_BG_SURFACE}; border: none; border-radius: {RADIUS_LG}px; }}
QFrame[role="dialog"] {{ background-color: {COLOR_BG_BASE}; border: 1.5px solid {COLOR_BORDER_SVELTE}; border-radius: 16px; }}
QFrame[role="dialog"][state="accent"] {{ border-color: rgba(83, 252, 24, 0.4); }}
QFrame[role="dialog"][state="danger"] {{ border-color: rgba(239, 68, 68, 0.4); }}
QFrame[role="banner_danger"] {{ background-color: {COLOR_DANGER_GLOW}; border: 1px solid {COLOR_DANGER}; border-radius: {RADIUS_MD}px; }}
QFrame[role="banner_danger"] QLabel {{ color: {COLOR_TEXT_PRIMARY}; }}
QFrame[dialog_role="danger_icon"] {{ background-color: {COLOR_DANGER}; border-radius: 26px; }}
QFrame[dialog_role="accent_icon"] {{ background-color: {COLOR_ACCENT}; border-radius: 26px; }}
QFrame#CanvasContainer {{ background-color: {COLOR_BG_BASE}; border: 2px solid {COLOR_BORDER_SVELTE}; border-radius: {RADIUS_MD}px; }}
QFrame[role="step_indicator"] {{ background-color: {COLOR_BORDER_SVELTE}; border-radius: 2px; }}
QFrame[role="step_indicator"][state="active"] {{ background-color: {COLOR_ACCENT}; }}
QFrame[role="divider"] {{ background-color: rgba(255, 255, 255, 0.05); margin: 4px 0px; }}
QFrame#Sidebar {{ background-color: {COLOR_BG_BASE}; border-right: 1px solid {COLOR_BORDER_SVELTE}; }}
QFrame[role="tag"] {{ background-color: {COLOR_BG_INPUT}; border: 1.5px solid {COLOR_BORDER_SVELTE}; border-radius: {RADIUS_MD}px; }}
QFrame[role="tag"]:hover {{ border-color: {COLOR_DANGER}; }}
QFrame[role="tag"] QLabel {{ color: {COLOR_TEXT_PRIMARY}; padding-right: 4px; font-size: 12px; }}

/* --- 4. BOTONES --- */
QPushButton[role="action_accent"] {{ background-color: {COLOR_ACCENT}; color: {COLOR_BG_BASE}; font-size: 12px; font-weight: 700; border: none; border-radius: {RADIUS_MD}px; padding: 7px 16px; }}
QPushButton[role="action_accent"]:hover {{ background-color: {COLOR_ACCENT_HOVER}; }}
QPushButton[role="action_outlined"] {{ background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: 700; border: none; border-radius: {RADIUS_MD}px; padding: 7px 16px; }}
QPushButton[role="action_outlined"]:hover {{ background-color: {COLOR_BG_HOVER}; }}
QPushButton[role="action_danger"] {{ background-color: transparent; color: {COLOR_DANGER}; font-size: 12px; font-weight: 700; border: 1.5px solid {COLOR_DANGER}; border-radius: {RADIUS_MD}px; padding: 7px 16px; }}
QPushButton[role="action_danger"]:hover {{ background-color: {COLOR_DANGER_GLOW}; }}
QPushButton[role="btn_ghost"] {{ background-color: transparent; border: none; border-radius: 4px; padding: 2px; }}
QPushButton[role="btn_ghost"]:hover {{ background-color: {COLOR_BG_HOVER}; }}
QPushButton#NavButton {{ background: transparent; border-radius: {RADIUS_MD}px; padding: 10px; text-align: left; color: {COLOR_TEXT_SECONDARY}; font-weight: 500; }}
QPushButton#NavButton:hover {{ background-color: {COLOR_BG_HOVER}; color: {COLOR_TEXT_PRIMARY};}}
QPushButton#NavButton:checked {{ background-color: {COLOR_ACCENT_GLOW}; color: {COLOR_ACCENT}; font-weight: 700;}}
QPushButton#NavButton[collapsed="false"] {{ text-align: left; padding-left: 12px; }}
QPushButton#NavButton[collapsed="true"] {{ text-align: center; padding: 10px; }}

/* --- 5. CONTROLES DE FORMULARIO Y TABLAS --- */
QLineEdit, QTextEdit {{ background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 400; border: none; border-radius: {RADIUS_MD}px; padding: 6px 10px; }}
QTextEdit {{ background-color: {COLOR_BG_SURFACE}; border: 1.5px solid {COLOR_BORDER_SVELTE}; }}
QLineEdit:focus, QTextEdit:focus {{ border: 1.5px solid {COLOR_ACCENT}; background-color: {COLOR_BG_HOVER}; }}

QComboBox {{ background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 400; border-radius: {RADIUS_MD}px; padding: 5px 28px 5px 10px; border: 1.5px solid transparent; }}
QComboBox:focus, QComboBox:hover {{ border-color: {COLOR_BORDER_SVELTE}; background-color: {COLOR_BG_HOVER}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 23px; border-left: 1.5px solid {COLOR_BORDER_SVELTE}; border-top-right-radius: {RADIUS_MD}px; border-bottom-right-radius: {RADIUS_MD}px; }}
QComboBox::drop-down:hover {{ background-color: {COLOR_BG_HOVER}; }}
QComboBox::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 15px; height: 15px; }}
QComboBox::down-arrow:on {{ top: 1px; left: 1px; }}
QComboBox QAbstractItemView, QMenu {{ background-color: {COLOR_BG_SURFACE}; color: {COLOR_TEXT_PRIMARY}; border: 1.5px solid {COLOR_BORDER_SVELTE}; border-radius: {RADIUS_MD}px; outline: none; padding: 2px; }}
QComboBox QAbstractItemView::item, QMenu::item {{ border-radius: {RADIUS_SM}px; padding: 2px; margin: 2px; }}
QComboBox QAbstractItemView::item:selected, QMenu::item:selected {{ background-color: {COLOR_BG_HOVER}; color: {COLOR_ACCENT}; }}

QSpinBox, QDoubleSpinBox {{ background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 400; border-radius: {RADIUS_MD}px; padding: 3px 20px 3px 8px; border: 1.5px solid transparent; }}
QSpinBox:focus, QDoubleSpinBox:focus, QSpinBox:hover, QDoubleSpinBox:hover {{ border-color: {COLOR_BORDER_SVELTE}; background-color: {COLOR_BG_HOVER}; }}
QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 24px; background-color: transparent; border-left: 1.5px solid {COLOR_BORDER_SVELTE}; border-bottom: 1.5px solid {COLOR_BORDER_SVELTE}; border-top-right-radius: {RADIUS_MD}px; }}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{ background-color: {COLOR_BG_HOVER}; }}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {{ background-color: {COLOR_ACCENT_GLOW}; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url("{PATH_ICON_CHEVRON_UP}"); width: 15px; height: 15px; }}
QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 24px; background-color: transparent; border-left: 1.5px solid {COLOR_BORDER_SVELTE}; border-bottom-right-radius: {RADIUS_MD}px; }}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{ background-color: {COLOR_BG_HOVER}; }}
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{ background-color: {COLOR_ACCENT_GLOW}; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 15px; height: 15px; }}

QTableWidget {{ background-color: {COLOR_BG_SURFACE}; border: none; gridline-color: transparent; outline: none; }}
QTableWidget::item {{ padding: 4px; border-bottom: 1px solid {COLOR_BORDER_SVELTE}; }}
QTableWidget::item:selected {{ background-color: {COLOR_BG_HOVER}; color: {COLOR_ACCENT}; }}
QHeaderView::section {{ background-color: transparent; color: {COLOR_TEXT_SECONDARY}; font-weight: 700; padding: 6px 8px; border: none; border-bottom: 2px solid {COLOR_BORDER_SVELTE}; text-align: left; }}
QHeaderView {{ background-color: transparent; border: none; }}

/* --- 6. SCROLLS Y TABS --- */
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

/* --- 7. MISCELÁNEA Y CONSOLA --- */
QProgressBar[role="update_progress"] {{ background-color: {COLOR_BG_SURFACE}; border: none; border-radius: 5px; }}
QProgressBar[role="update_progress"]::chunk {{ background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_ACCENT}, stop:1 #22C55E); border-radius: 5px; }}
QTextEdit#ConsoleDisplay, QTextEdit[role="console"] {{ background-color: {COLOR_BG_BASE}; color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: 12px; border-radius: {RADIUS_MD}px; padding: 10px; }}
QListWidget[role="transparent_list"] {{ background: transparent; border: none; outline: none; }}
QListWidget[role="transparent_list"]::item {{ background: transparent; }}

/* --- 8. TOAST NOTIFICATIONS (HUD) --- */
QFrame[role="toast"] {{ background-color: {COLOR_BG_TOAST}; border: 1px solid {COLOR_BORDER_SVELTE}; border-radius: 10px;
}}
QFrame[role="toast"][state="success"] {{ border-color: {COLOR_ACCENT_GLOW}; }}
QFrame[role="toast"][state="danger"] {{ border-color: {COLOR_DANGER_GLOW}; }}
QFrame[role="toast"][state="warning"] {{ border-color: {COLOR_WARNING_GLOW}; }}
QFrame[role="toast"][state="info"]    {{ border-color: {COLOR_INFO_GLOW}; }}

/* --- 9. TOOLTIPS (Desacoplados del Desktop OS) --- */
QToolTip {{
    background-color: {COLOR_BLACK}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {COLOR_BORDER_SVELTE}; padding: 2px 4px;
    font-family: {FONT_FAMILY}; font-size: 11px;
}}

/* --- 10. TAG PILLS Y BADGES (TABLA COMANDOS) --- */
QLabel[role="cmd_trigger"] {{ font-size: 13px; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; }}

QFrame[role="tag_pill"] {{ border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; }}
QLabel[role="pill_dot"] {{ font-size: 10px; font-weight: bold; background: transparent; }}
QLabel[role="pill_text"] {{ color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: 600; background: transparent; }}

QFrame[role="tag_pill"][perm_level="everyone"] {{ background-color: rgba(16, 185, 129, 0.12); }}
QFrame[role="tag_pill"][perm_level="everyone"] QLabel[role="pill_dot"] {{ color: #10B981; }}

QFrame[role="tag_pill"][perm_level="subscriber"] {{ background-color: rgba(59, 130, 246, 0.12); }}
QFrame[role="tag_pill"][perm_level="subscriber"] QLabel[role="pill_dot"] {{ color: #3B82F6; }}

QFrame[role="tag_pill"][perm_level="vip"] {{ background-color: rgba(139, 92, 246, 0.12); }}
QFrame[role="tag_pill"][perm_level="vip"] QLabel[role="pill_dot"] {{ color: #8B5CF6; }}

QFrame[role="tag_pill"][perm_level="moderator"] {{ background-color: rgba(245, 158, 11, 0.12); }}
QFrame[role="tag_pill"][perm_level="moderator"] QLabel[role="pill_dot"] {{ color: #F59E0B; }}

QFrame[role="tag_pill"][perm_level="broadcaster"] {{ background-color: rgba(239, 68, 68, 0.12); }}
QFrame[role="tag_pill"][perm_level="broadcaster"] QLabel[role="pill_dot"] {{ color: {COLOR_DANGER}; }}

QFrame[role="badge_regex"] {{ background-color: {COLOR_BG_INPUT}; border-radius: 4px; padding: 0px 4px; }}
QLabel[role="badge_regex_text"] {{ color: {COLOR_WARNING}; font-size: 9px; font-weight: bold; }}
"""