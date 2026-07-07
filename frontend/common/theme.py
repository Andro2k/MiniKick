# frontend\common\theme.py

from frontend.common.utils import get_assets_path
PATH_ICON_HELP = get_assets_path("icons/help.svg")
PATH_ICON_CHEVRON_DOWN = get_assets_path("icons/chevron-down.svg").replace('\\', '/')
PATH_ICON_CHEVRON_UP = get_assets_path("icons/chevron-up.svg").replace('\\', '/')
PATH_ICON_CHECK = get_assets_path("icons/check.svg").replace('\\', '/')

COLOR_BG_BASE        = "#09090B"
COLOR_BG_SURFACE     = "#121214"
COLOR_BG_INPUT       = "#18181B"
COLOR_BG_HOVER       = "#27272A"

COLOR_BORDER_SVELTE  = "#27272A"
COLOR_BORDER_HOVER   = "#3F3F46"
COLOR_BORDER_GLOW    = "rgba(255, 255, 255, 0.1)"

COLOR_ACCENT         = "#2ECD70"
COLOR_ACCENT_HOVER   = "#25AE60"   
COLOR_ACCENT_GLOW    = "rgba(46, 205, 112, 0.1)"

COLOR_DANGER         = "#EF4444"
COLOR_DANGER_GLOW    = "rgba(239, 68, 68, 0.1)"

COLOR_WARNING        = "#F59E0B"
COLOR_WARNING_GLOW   = "rgba(245, 158, 11, 0.1)"

COLOR_INFO           = "#3B82F6"
COLOR_INFO_GLOW      = "rgba(59, 130, 246, 0.1)"

COLOR_VIP            = "#A78BFA"
COLOR_VIP_GLOW       = "rgba(139, 92, 246, 0.1)"

COLOR_BG_TOAST       = "#070707"
COLOR_CHECK          = "#29292B"

COLOR_TEXT_PRIMARY   = "#CCCCCC"
COLOR_TEXT_SECONDARY = "#767676"
COLOR_TEXT_MUTED     = "#71717A"
COLOR_BLACK          = "#000000"
COLOR_WHITE          = "#FAFAFA"

FONT_FAMILY = "'Geist', '-apple-system', 'Segoe UI', sans-serif"

RADIUS_SM = 6
RADIUS_MD = 8
RADIUS_LG = 12

PADDING_INPUT   = "5px 10px"
PADDING_BUTTON  = "6px 12px"


def get_global_qss(base: int = 13) -> str:
    h1 = base + 9
    h2 = base + 3
    h3 = base
    caption = max(9, base - 2)
    btn_txt = max(10, base - 1)
    badge_txt = max(8, base - 4)
    base_pt = max(9, int(base * 0.75))

    return f"""
/* --- 1. RESET Y BASE GLOBAL --- */
* {{
    font-family: {FONT_FAMILY};
    font-size: {base}px;
    color: {COLOR_TEXT_PRIMARY};
    outline: none;
}}

QMainWindow, QDialog {{ background-color: {COLOR_BG_BASE}; }}
QLabel {{ background-color: transparent; }}

/* --- 2. SISTEMA DE TIPOGRAFÍA --- */
QLabel[role="h1"] {{ font-size: {h1}px; font-weight: 800; color: {COLOR_TEXT_PRIMARY}; }}
QLabel[role="h2"] {{ font-size: {h2}px; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; }}
QLabel[role="h3"] {{ font-size: {h3}px; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; }}
QLabel[role="body"] {{ font-size: {base}px; font-weight: 400; color: {COLOR_TEXT_SECONDARY}; line-height: 1.5; }}
QLabel[role="caption"] {{ font-size: {caption}px; font-weight: 400; color: {COLOR_TEXT_MUTED}; }}
QLabel[role="wizard_step_num"] {{ font-size: {caption}px; font-weight: 400; color: {COLOR_TEXT_SECONDARY}; }}
QLabel[role="wizard_subtitle"] {{ font-size: {base}px; font-weight: 400; color: {COLOR_TEXT_SECONDARY}; }}
QLabel[role="monospace"] {{ font-family: {FONT_FAMILY}; font-size: {btn_txt}px; color: {COLOR_TEXT_SECONDARY};}}
QLabel[role="subtitle"] {{ font-size: {caption}px; font-weight: 600; color: {COLOR_TEXT_SECONDARY}; }}
QLabel[state="error"] {{ color: {COLOR_DANGER}; }}

/* --- 3. CONTENEDORES --- */
QFrame[role="card"] {{ background-color: {COLOR_BG_SURFACE}; border: none; border-radius: {RADIUS_LG}px; }}
QFrame[role="dialog"] {{ background-color: {COLOR_BG_BASE}; border: 1.5px solid {COLOR_BORDER_SVELTE}; border-radius: 16px; }}
QFrame[role="dialog"][state="accent"] {{ border-color: {COLOR_ACCENT}; }}
QFrame[role="dialog"][state="danger"] {{ border-color: {COLOR_DANGER}; }}
QFrame[role="banner_danger"] {{ background-color: {COLOR_DANGER_GLOW}; border: 1px solid {COLOR_DANGER}; border-radius: {RADIUS_MD}px; }}
QFrame[role="banner_danger"] QLabel {{ color: {COLOR_TEXT_PRIMARY}; }}
QFrame[dialog_role="danger_icon"] {{ background-color: {COLOR_DANGER}; border-radius: 26px; }}
QFrame[dialog_role="accent_icon"] {{ background-color: {COLOR_ACCENT}; border-radius: 26px; }}
QFrame#CanvasContainer {{ background-color: {COLOR_BG_BASE}; border: 2px solid {COLOR_BORDER_SVELTE}; border-radius: {RADIUS_MD}px; }}
QFrame[role="divider"] {{ background-color: {COLOR_BORDER_GLOW}; margin: 4px 0px; }}
QFrame#Sidebar {{ background-color: {COLOR_BG_SURFACE}; border-right: 1.5px solid {COLOR_BORDER_SVELTE}; }}
QLabel[role="section_header"] {{ font-size: {caption}px; font-weight: 700; color: {COLOR_TEXT_MUTED}; margin-top: 10px; margin-bottom: 2px; margin-left: 8px; }}
QFrame#ProfileCard {{ background-color: transparent; border: 1.5px solid transparent; border-radius: {RADIUS_MD}px; }}
QFrame#ProfileCard:hover {{ background-color: {COLOR_BG_HOVER}; border-color: {COLOR_BORDER_SVELTE}; }}
QLabel#ProfileName {{ font-size: {btn_txt}px; font-weight: 600; color: {COLOR_TEXT_PRIMARY}; background-color: transparent; }}
QLabel#ProfileSub {{ font-size: {caption}px; font-weight: 400; color: {COLOR_TEXT_MUTED}; background-color: transparent; }}
QFrame[role="bot_tag"] {{ background-color: {COLOR_BG_HOVER}; border: 1.5px solid {COLOR_BORDER_HOVER}; border-radius: {RADIUS_MD}px; }}
QFrame[role="bot_tag"]:hover {{ border-color: {COLOR_DANGER}; }}
QFrame[role="bot_tag"] QLabel {{ color: {COLOR_TEXT_PRIMARY}; font-size: {btn_txt}px; }}

/* --- 4. BOTONES --- */
QPushButton[role="action_accent"] {{ background-color: {COLOR_ACCENT}; color: {COLOR_BG_BASE}; font-size: {btn_txt}px; font-weight: 700; border: none; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_accent"]:hover {{ background-color: {COLOR_ACCENT_HOVER}; }}
QPushButton[role="action_outlined"] {{ background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_PRIMARY}; font-size: {btn_txt}px; font-weight: 700; border: none; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_outlined"]:hover {{ background-color: {COLOR_BG_HOVER}; }}
QPushButton[role="action_danger_border"] {{ background-color: transparent; color: {COLOR_DANGER}; font-size: {btn_txt}px; font-weight: 700; border: 1.5px solid {COLOR_DANGER}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_danger_border"]:hover {{ background-color: {COLOR_DANGER_GLOW}; }}
QPushButton[role="action_accent_border"] {{ background-color: transparent; color: {COLOR_ACCENT}; font-size: {btn_txt}px; font-weight: 700; border: 1.5px solid {COLOR_ACCENT}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_accent_border"]:hover {{ background-color: {COLOR_ACCENT_GLOW}; }}
QPushButton[role="action_neutral_border"] {{ background-color: transparent; color: {COLOR_TEXT_PRIMARY}; font-size: {btn_txt}px; font-weight: 700; border: 1.5px solid {COLOR_BORDER_HOVER}; border-radius: {RADIUS_MD}px; padding: {PADDING_BUTTON}; }}
QPushButton[role="action_neutral_border"]:hover {{ background-color: {COLOR_BG_HOVER}; }}
QPushButton[role="btn_ghost"] {{ background-color: transparent; border: none; border-radius: {RADIUS_SM}px; padding: 2px; }}
QPushButton[role="btn_ghost"]:hover {{ background-color: {COLOR_BG_HOVER}; }}
QPushButton#NavButton {{ background: transparent; border-radius: {RADIUS_MD}px; padding: 10px; text-align: left; color: {COLOR_TEXT_SECONDARY}; font-weight: 500; }}
QPushButton#NavButton:hover {{ background-color: {COLOR_BG_HOVER}; color: {COLOR_TEXT_PRIMARY};}}
QPushButton#NavButton:checked {{ background-color: {COLOR_CHECK}; color: {COLOR_ACCENT}; font-weight: 700;}}
QPushButton#NavButton[collapsed="false"] {{ text-align: left; padding-left: 10px; }}
QPushButton#NavButton[collapsed="true"] {{ text-align: center; padding: 10px; }}

/* --- 5. CONTROLES DE FORMULARIO Y TABLAS --- */
QLineEdit, QTextEdit {{ background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_PRIMARY}; font-size: {base}px; font-weight: 400; border: none; border-radius: {RADIUS_MD}px; padding: {PADDING_INPUT}; border: 1.5px solid {COLOR_BORDER_SVELTE};}}
QTextEdit {{ background-color: {COLOR_BG_SURFACE}; border: 1.5px solid {COLOR_BORDER_SVELTE}; }}
QLineEdit:focus, QTextEdit:focus {{ border: 1.5px solid {COLOR_ACCENT}; background-color: {COLOR_BG_HOVER}; }}

QComboBox {{ background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_PRIMARY}; font-size: {base}px; font-weight: 400; border-radius: {RADIUS_MD}px; padding: {PADDING_INPUT}; border: 1.5px solid {COLOR_BORDER_SVELTE}; combobox-popup: 0; }}
QComboBox:focus, QComboBox:hover {{ border-color: transparent; background-color: {COLOR_BG_HOVER}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 23px; border-left: 1.5px solid {COLOR_BORDER_HOVER}; border-top-right-radius: {RADIUS_MD}px; border-bottom-right-radius: {RADIUS_MD}px; }}
QComboBox:focus::drop-down, QComboBox:hover::drop-down {{ border-color: {COLOR_BORDER_HOVER}; }}
QComboBox::drop-down:hover {{ background-color: {COLOR_BG_HOVER}; }}
QComboBox::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 15px; height: 15px; }}
QComboBox::down-arrow:on {{ top: 1px; left: 1px; }}
QComboBox QAbstractItemView, QMenu {{ font-size: {base_pt}pt; background-color: {COLOR_BG_SURFACE}; color: {COLOR_TEXT_PRIMARY}; border: 1.5px solid {COLOR_BORDER_SVELTE}; border-radius: {RADIUS_MD}px; outline: none; padding: 2px; selection-background-color: {COLOR_BG_HOVER}; selection-color: {COLOR_ACCENT}; }}
QComboBox QAbstractItemView::item, QMenu::item {{ border-radius: {RADIUS_SM}px; padding: 2px; margin: 2px; }}
QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover, QComboBox QListView::item:selected, QComboBox QListView::item:hover, QMenu::item:selected, QMenu::item:hover {{ background-color: {COLOR_BG_HOVER}; color: {COLOR_ACCENT}; }}

QSpinBox, QDoubleSpinBox {{ background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_PRIMARY}; font-size: {base}px; font-weight: 400; border-radius: {RADIUS_MD}px; padding: 3px 20px 3px 8px; border: 1.5px solid {COLOR_BORDER_SVELTE}; }}
QSpinBox:focus, QDoubleSpinBox:focus, QSpinBox:hover, QDoubleSpinBox:hover {{ border-color: transparent; background-color: {COLOR_BG_HOVER}; }}

QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 24px; border-left: 1.5px solid {COLOR_BORDER_HOVER}; border-bottom: 1.2px solid {COLOR_BORDER_HOVER}; border-top-right-radius: {RADIUS_MD}px; }}
QSpinBox:focus::up-button, QDoubleSpinBox::focus::up-button, QSpinBox:hover::up-button, QDoubleSpinBox::hover::up-button {{ border-color: {COLOR_BORDER_HOVER};}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{ background-color: {COLOR_BG_HOVER}; }}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {{ background-color: {COLOR_CHECK}; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url("{PATH_ICON_CHEVRON_UP}"); width: 15px; height: 15px; }}

QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 24px; border-left: 1.5px solid {COLOR_BORDER_HOVER}; border-top: 1.2px solid {COLOR_BORDER_HOVER}; border-bottom-right-radius: {RADIUS_MD}px; }}
QSpinBox:focus::down-button, QDoubleSpinBox::focus::down-button, QSpinBox:hover::down-button, QDoubleSpinBox::hover::down-button {{ border-color: {COLOR_BORDER_HOVER};}}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{ background-color: {COLOR_BG_HOVER}; }}
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{ background-color: {COLOR_CHECK}; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url("{PATH_ICON_CHEVRON_DOWN}"); width: 15px; height: 15px; }}

QCheckBox {{ spacing: 8px; color: {COLOR_TEXT_PRIMARY}; background-color: transparent; }}
QCheckBox:hover {{ color: {COLOR_WHITE}; }}
QCheckBox::indicator {{ width: 12px; height: 12px; border-radius: {RADIUS_SM}px; border: 1.5px solid {COLOR_BORDER_SVELTE}; background-color: {COLOR_BG_INPUT}; }}
QCheckBox::indicator:unchecked:hover {{ border-color: {COLOR_BORDER_HOVER}; background-color: {COLOR_BG_HOVER}; }}
QCheckBox::indicator:checked {{ border-color: {COLOR_ACCENT}; background-color: {COLOR_ACCENT}; image: url("{PATH_ICON_CHECK}"); }}
QCheckBox::indicator:checked:hover {{ border-color: {COLOR_ACCENT_HOVER}; background-color: {COLOR_ACCENT_HOVER}; }}
QCheckBox::indicator:disabled {{ border-color: {COLOR_BORDER_SVELTE}; background-color: {COLOR_BORDER_GLOW}; }}
QCheckBox::indicator:checked:disabled {{ border-color: {COLOR_BORDER_SVELTE}; background-color: {COLOR_BORDER_GLOW}; image: url("{PATH_ICON_CHECK}"); }}

QTableWidget {{ background-color: {COLOR_BG_SURFACE}; border: none; gridline-color: transparent; outline: none; }}
QTableWidget::item {{ padding: 4px; border-bottom: 1px solid {COLOR_BORDER_SVELTE}; }}
QTableWidget::item:selected {{ background-color: {COLOR_BG_HOVER}; color: {COLOR_ACCENT}; }}
QHeaderView::section {{ background-color: transparent; color: {COLOR_TEXT_SECONDARY}; font-weight: 700; padding: {PADDING_INPUT}; border: none; border-bottom: 2px solid {COLOR_BORDER_SVELTE}; text-align: left; }}
QHeaderView {{ background-color: transparent; border: none; }}

/* --- 6. SCROLLS Y TABS --- */
QScrollBar:vertical {{ border: none; background: transparent; width: 10px; margin: 2px 2px 2px 0px; }}
QScrollBar::handle:vertical {{ background-color: {COLOR_TEXT_MUTED}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background-color: {COLOR_TEXT_PRIMARY}; }}
QScrollBar::handle:vertical:pressed {{ background-color: {COLOR_ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ height: 5px; background: none; }}

QScrollBar:horizontal {{ border: none; background: transparent; height: 10px; margin: 0px 2px 2px 2px; }}
QScrollBar::handle:horizontal {{ background-color: {COLOR_TEXT_MUTED}; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background-color: {COLOR_TEXT_PRIMARY}; }}
QScrollBar::handle:horizontal:pressed {{ background-color: {COLOR_ACCENT}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal, QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ width: 5px; background: none; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: transparent; border: none; }}

/* --- 7. MISCELÁNEA Y CONSOLA --- */
QProgressBar[role="update_progress"] {{ background-color: {COLOR_BG_SURFACE}; border: none; border-radius: {RADIUS_SM}px; }}
QProgressBar[role="update_progress"]::chunk {{ background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_ACCENT}, stop:1 {COLOR_ACCENT}); border-radius: {RADIUS_SM}px; }}
QProgressBar[role="wizard_progress"] {{ background-color: {COLOR_BORDER_HOVER}; border: none; border-radius: 2px; }}
QProgressBar[role="wizard_progress"]::chunk {{ background-color: {COLOR_ACCENT}; border-radius: 2px; }}
QTextEdit[role="ConsoleDisplay"] {{ background-color: {COLOR_BG_BASE}; color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: {btn_txt}px; border-radius: {RADIUS_MD}px; padding: {PADDING_INPUT}; }}
QListWidget[role="transparent_list"] {{ background: transparent; border: none; outline: none; }}
QListWidget[role="transparent_list"]::item {{ background: transparent; }}

/* --- 8. TOAST NOTIFICATIONS (HUD) --- */
QFrame[role="toast"] {{ background-color: {COLOR_BG_TOAST}; border: 1px solid {COLOR_BORDER_SVELTE}; border-radius: {RADIUS_MD}px; }}
QFrame[role="toast"][state="success"] {{ border-color: {COLOR_CHECK}; }}
QFrame[role="toast"][state="danger"] {{ border-color: {COLOR_DANGER_GLOW}; }}
QFrame[role="toast"][state="warning"] {{ border-color: {COLOR_WARNING_GLOW}; }}
QFrame[role="toast"][state="info"]    {{ border-color: {COLOR_INFO_GLOW}; }}

/* --- 9. TOOLTIPS (Desacoplados del Desktop OS) --- */
QToolTip {{
    background-color: {COLOR_BG_HOVER};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER_HOVER};
    border-radius: 4px;
    padding: 4px 8px;
    font-family: {FONT_FAMILY};
    font-size: {caption}px;
}}

/* --- 10. TAG PILLS Y BADGES (TABLA COMANDOS) --- */
QFrame[role="tag_pill"] {{ background-color: {COLOR_BG_INPUT}; border-radius: {RADIUS_MD}px; padding: 0px 4px; }}
QFrame[role="tag_pill"] QLabel[role="pill_text"] {{ font-size: {caption}px; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; background: transparent; }}
QFrame[role="tag_pill"][perm_level="everyone"] {{ background-color: {COLOR_ACCENT_GLOW};}}
QFrame[role="tag_pill"][perm_level="everyone"] QLabel[role="pill_text"] {{ color: {COLOR_ACCENT}; }}
QFrame[role="tag_pill"][perm_level="subscriber"] {{ background-color: {COLOR_INFO_GLOW};}}
QFrame[role="tag_pill"][perm_level="subscriber"] QLabel[role="pill_text"] {{ color: {COLOR_INFO}; }}
QFrame[role="tag_pill"][perm_level="vip"] {{ background-color: {COLOR_VIP_GLOW};}}
QFrame[role="tag_pill"][perm_level="vip"] QLabel[role="pill_text"] {{ color: {COLOR_VIP}; }}
QFrame[role="tag_pill"][perm_level="moderator"] {{ background-color: {COLOR_WARNING_GLOW}; }}
QFrame[role="tag_pill"][perm_level="moderator"] QLabel[role="pill_text"] {{ color: {COLOR_WARNING}; }}
QFrame[role="tag_pill"][perm_level="broadcaster"] {{ background-color: {COLOR_DANGER_GLOW}; }}
QFrame[role="tag_pill"][perm_level="broadcaster"] QLabel[role="pill_text"] {{ color: {COLOR_DANGER}; }}

QFrame[role="badge_regex"] {{ background-color: {COLOR_WARNING_GLOW}; border-radius: {RADIUS_MD}px; padding: 0px 4px; }}
QLabel[role="badge_regex_text"] {{ color: {COLOR_WARNING}; font-size: {caption}px; font-weight: bold; }}

/* --- 11. ASISTENTE REGEX --- */
QLabel[role="regex_helper_title"] {{ font-size: {h3}px; font-weight: bold; color: {COLOR_ACCENT}; margin-bottom: 2px; }}
QLabel[role="regex_helper_category"] {{ font-weight: bold; color: {COLOR_ACCENT}; margin-top: 6px; font-size: {btn_txt}px; }}
QLabel[role="regex_helper_code"] {{ font-size: {btn_txt}px; font-weight: bold; background-color: {COLOR_BG_INPUT}; padding: 1px 3px; border-radius: {RADIUS_SM}px; }}
QLabel[role="regex_helper_desc"] {{ font-size: {btn_txt}px; color: {COLOR_TEXT_SECONDARY}; }}

/* --- 12. QSLIDER (SIMPLE Y MODERNO) --- */
QSlider::groove:horizontal {{ border: none; height: 6px; background: {COLOR_BG_INPUT}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {COLOR_ACCENT}; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {COLOR_ACCENT}; width: 14px; height: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }}
QSlider::handle:horizontal:hover {{ border-color: {COLOR_ACCENT_HOVER}; }}

/* --- 13. ESTADOS DESHABILITADOS --- */
QPushButton:disabled,
QPushButton[role="action_accent"]:disabled,
QPushButton[role="action_outlined"]:disabled,
QPushButton[role="action_danger_border"]:disabled,
QPushButton[role="action_accent_border"]:disabled,
QPushButton[role="action_neutral_border"]:disabled,
QPushButton[role="btn_ghost"]:disabled {{ background-color: {COLOR_BORDER_GLOW}; color: {COLOR_TEXT_MUTED}; border: 1.5px solid {COLOR_BG_HOVER}; padding: {PADDING_BUTTON}; }}

QLineEdit:disabled,
QTextEdit:disabled,
QComboBox:disabled,
QSpinBox:disabled,
QDoubleSpinBox:disabled {{ background-color: {COLOR_BORDER_GLOW}; color: {COLOR_TEXT_MUTED}; border-color: {COLOR_BG_HOVER}; padding: {PADDING_INPUT};}}
QCheckBox:disabled {{ color: {COLOR_TEXT_MUTED}; }}
"""

GLOBAL_QSS = get_global_qss(13)