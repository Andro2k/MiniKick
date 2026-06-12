# frontend/theme.py

from frontend.utils import get_assets_path

# ─── Recursos Base ───
PATH_ICON_HELP = get_assets_path("icons/help.svg")
PATH_ICON_UPDATE = get_assets_path("icons/cloud-download.svg")

# ─── Paleta de Colores ───
# Fondos
COLOR_BG_BASE       = "#0B0E11"   # Fondo de la aplicación (Negro profundo)
COLOR_BG_SURFACE    = "#1E2329"   # Tarjetas y paneles (Gris oscuro cálido)
COLOR_BG_INPUT      = "#42474D"   # Fondos de inputs y campos de texto
COLOR_BG_HOVER      = "#333333"   
COLOR_BG_CONSOLE    = "#0F172A"   # Fondo para terminal/logs

# Bordes
COLOR_BORDER_SVELTE = "#333333"   # Bordes inactivos y divisores
COLOR_BORDER_ACTIVE = "#53FC18"   # Borde activo al enfocar (Verde Menta)

# Acentos y Estados
COLOR_ACCENT        = "#53FC18"   # Verde Menta vibrante
COLOR_ACCENT_HOVER  = "#00C864"   
COLOR_ACCENT_SOFT   = "rgba(0, 229, 115, 0.15)" # Verde translúcido

COLOR_SUCCESS       = "#10B981"

COLOR_DANGER        = "#EF4444"
COLOR_DANGER_HOVER  = "#D74141"
COLOR_DANGER_SOFT   = "rgba(239, 68, 68, 0.15)"

# Textos
COLOR_TEXT_PRIMARY   = "#F3F4F6"   # Blanco suave
COLOR_TEXT_SECONDARY = "#9CA3AF"   # Gris para subtítulos
COLOR_TEXT_MUTED     = "#6B7280"
COLOR_TEXT_INVERSE   = "#000000"   # Texto oscuro para fondos claros
COLOR_TEXT_CONSOLE   = "#F8FAFC"   # Texto para terminal/logs

# ─── Tipografía, Radios & Espaciados (Paddings) ───
FONT_FAMILY = "'Inter', '-apple-system', 'Segoe UI', sans-serif"
FONT_MONO   = "'Consolas', 'Courier New', monospace"

RADIUS_SM = 6
RADIUS_MD = 8   # Cajas de texto y botones redondeados
RADIUS_LG = 12  # Tarjetas principales altamente redondeadas
RADIUS_XL = 26  # Iconos circulares grandes

PADDING_INPUT   = "4px 12px"
PADDING_BUTTON  = "4px 8px"

# ─── Stylesheet Global (QSS) ───
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

QMainWindow, QDialog {{
    background-color: {COLOR_BG_BASE};
}}

/* ============================================================================
   2. TIPOGRAFÍA Y ROLES COMUNES
   ============================================================================ */
QLabel {{
    background-color: transparent;
}}

QLabel[role="title"] {{
    font-size: 22px;
    font-weight: bold;
    color: {COLOR_TEXT_PRIMARY};
    letter-spacing: -0.5px;
}}

QLabel[role="section"] {{
    font-size: 14px;
    font-weight: bold;
    color: {COLOR_TEXT_PRIMARY};
}}

QLabel[role="section_small"] {{
    font-size: 13px;
    font-weight: bold;
}}

QLabel[role="subtitle"] {{
    font-size: 14px;
    color: {COLOR_TEXT_SECONDARY};
}}

QLabel[role="body"] {{
    font-size: 13px;
    color: {COLOR_TEXT_SECONDARY};
    line-height: 1.5;
}}

QLabel[role="monospace"] {{
    font-family: {FONT_MONO};
    color: {COLOR_TEXT_SECONDARY};
}}

/* ============================================================================
   3. COMPONENTES NATIVOS GENÉRICOS (Inputs, Botones, Tablas, Sliders)
   ============================================================================ */

/* --- Inputs y Áreas de Texto --- */
QLineEdit, QTextEdit {{
    background-color: {COLOR_BG_INPUT};
    border: none;
    border-radius: {RADIUS_MD}px;
    padding: {PADDING_INPUT};
    color: {COLOR_TEXT_PRIMARY};
}}

QTextEdit {{
    background-color: {COLOR_BG_SURFACE};
    border: 1.5px solid {COLOR_BORDER_SVELTE};
}}

QLineEdit:focus, QTextEdit:focus {{
    border: 1.5px solid {COLOR_BORDER_ACTIVE};
    background-color: {COLOR_BG_HOVER};
}}

/* --- Botones Genéricos (Roles) --- */
QPushButton[role="action_accent"] {{
    background-color: {COLOR_ACCENT};
    border: none;
    border-radius: {RADIUS_MD}px;
    padding: {PADDING_BUTTON};
    color: {COLOR_TEXT_INVERSE};
    font-weight: 800;
}}
QPushButton[role="action_accent"]:hover {{ background-color: {COLOR_ACCENT_HOVER}; }}

QPushButton[role="action_outlined"] {{
    background-color: {COLOR_BG_INPUT};
    border: none;
    border-radius: {RADIUS_MD}px;
    padding: {PADDING_INPUT};
    color: {COLOR_TEXT_PRIMARY};
    font-weight: 500;
}}
QPushButton[role="action_outlined"]:hover {{ background-color: {COLOR_BG_HOVER}; }}

QPushButton[role="action_danger"] {{
    background-color: transparent;
    border: 1.5px solid {COLOR_DANGER}; 
    color: {COLOR_DANGER};
    border-radius: {RADIUS_MD}px;
    padding: {PADDING_BUTTON};
    font-weight: 600;
}}
QPushButton[role="action_danger"]:hover {{ background-color: {COLOR_DANGER_SOFT}; }}

QPushButton[role="action_success"] {{   
    background-color: transparent;
    border: 1.5px solid {COLOR_ACCENT}; 
    color: {COLOR_ACCENT};
    border-radius: {RADIUS_MD}px;
    padding: {PADDING_INPUT};
    font-weight: 600;
}}
QPushButton[role="action_success"]:hover {{ background-color: {COLOR_ACCENT_SOFT}; }}

/* --- Tablas (QTableWidget) --- */
QTableWidget {{
    background-color: {COLOR_BG_SURFACE};
    border: none;
    gridline-color: transparent;
    color: {COLOR_TEXT_PRIMARY};
    outline: none;
}}
QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {COLOR_BORDER_SVELTE};
}}
QTableWidget::item:selected {{
    background-color: {COLOR_BG_HOVER};
    color: {COLOR_ACCENT};
}}
QHeaderView::section {{
    background-color: {COLOR_BG_INPUT};
    color: {COLOR_TEXT_SECONDARY};
    font-weight: bold;
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid {COLOR_BORDER_SVELTE};
    text-align: left;
}}
QHeaderView {{ background-color: transparent; border: none; }}

/* --- ComboBox (Dropdowns) --- */
QComboBox {{
    background-color: {COLOR_BG_INPUT};
    color: {COLOR_TEXT_PRIMARY};
    border-radius: {RADIUS_MD}px;
    padding: {PADDING_INPUT};
    border: none;
}}
QComboBox:focus, QComboBox:hover {{
    border: 1.5px solid {COLOR_BORDER_SVELTE};
    background-color: {COLOR_BG_HOVER};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 35px;
    border-left: none;
}}
QComboBox::down-arrow {{ image: none; width: 10px; height: 10px; }}
QComboBox QAbstractItemView {{
    background-color: {COLOR_BG_SURFACE};
    color: {COLOR_TEXT_PRIMARY};
    border: 1.5px solid {COLOR_BORDER_SVELTE};
    border-radius: {RADIUS_MD}px;
    outline: none;
    padding: 2px;
}}
QComboBox QAbstractItemView::item {{
    border-radius: {RADIUS_SM}px;
    padding: 2px;
    margin: 2px;
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: {COLOR_BG_HOVER};
    color: {COLOR_ACCENT};
}}

/* --- Sliders --- */
QSlider {{ background-color: transparent; }}
QSlider::groove:horizontal {{
    border: none;
    background: {COLOR_BG_INPUT};
    border-radius: {RADIUS_SM}px;
}}
QSlider::sub-page:horizontal {{ background: {COLOR_ACCENT}; border-radius: {RADIUS_SM}px; }}
QSlider::handle:horizontal {{
    background: {COLOR_TEXT_PRIMARY};
    border: none;
    width: 10px;
    height: 16px;
    margin: -4px 0px;
}}

/* --- SpinBoxes --- */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLOR_BG_INPUT};
    color: {COLOR_TEXT_PRIMARY};
    border-radius: {RADIUS_MD}px;
    padding: 4px;
    border: none;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1.5px solid {COLOR_BORDER_ACTIVE};
    background-color: {COLOR_BG_HOVER};
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border; subcontrol-position: top right;
    width: 16px; background-color: {COLOR_ACCENT};
    border-top-left-radius: {RADIUS_SM}px; border-top-right-radius: {RADIUS_SM}px;
    margin-top: 4px; margin-right: 4px;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border; subcontrol-position: bottom right;
    width: 16px; background-color: {COLOR_ACCENT};
    border-bottom-left-radius: {RADIUS_SM}px; border-bottom-right-radius: {RADIUS_SM}px;
    margin-bottom: 4px; margin-right: 4px;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{ background-color: {COLOR_ACCENT}; }}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed,
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{ background-color: {COLOR_ACCENT_HOVER}; }}

/* --- ScrollBars --- */
QScrollBar:vertical {{ border: none; background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {COLOR_BORDER_SVELTE}; border-radius: {RADIUS_SM}px; min-height: 20px; }}
QScrollBar::handle:vertical:hover {{ background: {COLOR_TEXT_MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

QScrollBar:horizontal {{ background: transparent; height: 8px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {COLOR_BORDER_SVELTE}; border-radius: {RADIUS_SM}px; min-width: 20px; }}
QScrollBar::handle:horizontal:hover {{ background: {COLOR_TEXT_MUTED}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}

/* --- Contenedores de Scroll --- */
QScrollArea, QScrollArea > QWidget > QWidget {{
    background-color: transparent;
    border: none;
}}

QWidget#ScrollContent {{
    background-color: transparent;
}}
/* ============================================================================
   4. ESTILOS ESPECÍFICOS DE VISTAS (Alta Cohesión Visual)
   ============================================================================ */

/* --- Tarjetas Principales --- */
QFrame#Card {{
    background-color: {COLOR_BG_SURFACE};
    border: none;
    border-radius: {RADIUS_LG}px;
}}

/* --- Sidebar --- */
QFrame#Sidebar {{
    background-color: {COLOR_BG_BASE};
    border-right: 1px solid {COLOR_BORDER_SVELTE};
}}
QLabel#SidebarTitle {{
    font-size: 16px; 
    font-weight: bold; 
    padding-left: 6px;
}}
QPushButton#LogoBtn {{ border: none; background: transparent; }}
QPushButton#NavButton {{
    background: transparent; border-radius: {RADIUS_MD}px;
    padding: 10px; text-align: left;
    color: {COLOR_TEXT_SECONDARY}; font-weight: 700;
}}
QPushButton#NavButton:hover {{ background-color: {COLOR_BG_HOVER}; color: {COLOR_TEXT_PRIMARY}; }}
QPushButton#NavButton:checked {{ background-color: {COLOR_ACCENT_SOFT}; color: {COLOR_ACCENT}; }}
QPushButton#NavButton[collapsed="false"] {{ text-align: left; padding-left: 12px; }}
QPushButton#NavButton[collapsed="true"] {{ text-align: center; padding: 10px; }}

/* --- Diálogos --- */
QFrame#SquareDialog {{
    background-color: {COLOR_BG_BASE};
    border: 1px solid {COLOR_BORDER_SVELTE};
    border-radius: 16px;
}}
QFrame[dialog_role="danger_icon"] {{ background-color: {COLOR_DANGER}; border-radius: {RADIUS_XL}px; border: none; }}
QFrame[dialog_role="accent_icon"] {{ background-color: {COLOR_ACCENT}; border-radius: {RADIUS_XL}px; border: none; }}

/* --- Dashboard --- */
QLabel#AvatarLabel {{ font-size: 40px; color: {COLOR_BORDER_SVELTE}; font-weight: bold; }}
QLabel#AvatarLabel[has_image="true"] {{ border: none; }}

/* --- Componentes de Tablas --- */
QFrame#TableActions {{ background-color: {COLOR_BG_SURFACE}; }}

/* --- Chat y Bots --- */
QListWidget#BotsList {{ background: transparent; border: none; outline: none; }}
QListWidget#BotsList::item {{ background: transparent; }}
QFrame#BotTag {{
    background-color: {COLOR_BG_INPUT};
    border: 1.5px solid {COLOR_BORDER_SVELTE};
    border-radius: {RADIUS_MD}px;
}}
QFrame#BotTag:hover {{ border: 1.5px solid {COLOR_DANGER_HOVER}; }}
QFrame#BotTag > QLabel {{ color: {COLOR_TEXT_PRIMARY}; padding-right: 4px; font-size: 13px; }}
QFrame#BotTag > QPushButton {{ background: transparent; border: none; border-radius: 4px; padding: 2px; }}
QFrame#BotTag > QPushButton:hover {{ background-color: {COLOR_DANGER_SOFT}; }}

/* --- Consola (Logs) --- */
QTextEdit#ConsoleDisplay {{
    background-color: {COLOR_BG_CONSOLE};
    color: {COLOR_TEXT_CONSOLE};
    font-family: {FONT_MONO};
    font-size: 12px;
    border-radius: {RADIUS_MD}px;
    padding: 10px;
}}

/* --- Menús Contextuales (Bandeja del Sistema) --- */
QMenu {{
    background-color: {COLOR_BG_SURFACE};
    color: {COLOR_TEXT_PRIMARY};
    border: 1.5px solid {COLOR_BORDER_SVELTE};
    border-radius: {RADIUS_MD}px;
    padding: 4px;
}}

QMenu::item {{
    background-color: transparent;
    padding: 4px;
    border-radius: {RADIUS_SM}px;
}}

/* Efecto hover sobre las opciones del menú minimizado */
QMenu::item:selected {{
    background-color: {COLOR_BG_HOVER};
    color: {COLOR_ACCENT};
}}

/* El separador (la línea que divide "Abrir Panel" de "Cerrar") */
QMenu::separator {{
    height: 1px;
    background-color: {COLOR_BORDER_SVELTE};
}}
"""