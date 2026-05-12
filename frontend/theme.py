# frontend/theme.py

from frontend.utils import get_assets_path

PATH_CHEVRON = get_assets_path("icons/chevron-down.svg")
PATH_ICON_HELP = get_assets_path("icons/help-circle.svg")
PATH_ICON_UPDATE = get_assets_path("icons/download.svg")

# ─── Paleta de Colores ( Slate & Onyx) ───
COLOR_BG_BASE       = "#0A0F12"   
COLOR_BG_SURFACE    = "#161D21"   # Tarjetas
COLOR_BG_ELEVATED   = "#1F2937"   
COLOR_BG_INPUT      = "#0F171A"   

COLOR_BORDER_SVELTE = "#1E293B"   # Borde 1px
COLOR_BORDER_ACTIVE = "#334155"   

COLOR_ACCENT        = "#0FE25F"   # Kick Green
COLOR_ACCENT_HOVER  = "#3cb043"   
COLOR_ACCENT_SOFT   = "rgba(12, 166, 120, 0.08)" 

COLOR_TEXT_PRIMARY  = "#F8FAFC"   # Casi blanco
COLOR_TEXT_SECONDARY= "#94A3B8"   # Slate Grey
COLOR_TEXT_MUTED    = "#475569"   

# ─── Tipografía & Radios ───
FONT_FAMILY = "'Inter', 'Aptos', 'Segoe UI', sans-serif"
RADIUS_SM = 6
RADIUS_MD = 12  
RADIUS_LG = 16

# ─── Stylesheet Global (QSS) ───
GLOBAL_QSS = f"""
/* ─── Reset y Base ─── */
* {{
    font-family: {FONT_FAMILY};
    font-size: 13px;
    color: {COLOR_TEXT_PRIMARY};
    outline: none;
}}

QMainWindow, QDialog {{
    background-color: {COLOR_BG_BASE};
}}

/* ─── Contenedores Principales ─── */
QFrame#Sidebar {{
    background-color: {COLOR_BG_INPUT};
    border: none;
    border-right: 1px solid {COLOR_BORDER_SVELTE};
}}

QFrame#Card {{
    background-color: {COLOR_BG_SURFACE};
    border: 1px solid {COLOR_BORDER_SVELTE};
    border-radius: {RADIUS_MD}px;
}}

/* ─── Tipografía con Roles ─── */
QLabel[role="title"] {{
    font-size: 24px;
    font-weight: 700;
    color: {COLOR_TEXT_PRIMARY};
    letter-spacing: -0.5px;
}}

QLabel[role="subtitle"] {{
    color: {COLOR_TEXT_SECONDARY};
    font-weight: 500;
}}

/* ─── Navegación (Sidebar) ─── */
QPushButton#NavButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: {RADIUS_SM}px;
    padding: 10px;
    text-align: left;
    color: {COLOR_TEXT_SECONDARY};
}}

QPushButton#NavButton:hover {{
    background-color: {COLOR_BG_ELEVATED};
    color: {COLOR_TEXT_PRIMARY};
}}

QPushButton#NavButton:checked {{
    background-color: {COLOR_ACCENT_SOFT};
    color: {COLOR_ACCENT};
    border: 1px solid {COLOR_ACCENT};
    font-weight: 600;
}}

/* ─── Inputs y Controles (Chat View) ─── */
QTextEdit#ChatContainer {{
    background-color: {COLOR_BG_INPUT};
    border: 1px solid {COLOR_BORDER_SVELTE};
    border-radius: {RADIUS_MD}px;
    padding: 12px;
    line-height: 1.6;
}}

QLineEdit {{
    background-color: {COLOR_BG_INPUT};
    border: 1px solid {COLOR_BORDER_SVELTE};
    border-radius: {RADIUS_SM}px;
    padding: 8px 12px;
    selection-background-color: {COLOR_ACCENT};
}}

QLineEdit:focus {{
    border: 1px solid {COLOR_ACCENT};
}}

/* ─── Botones de Acción ─── */
/* Estilo Principal (Lleno) */
QPushButton[role="action_accent"] {{
    background-color: {COLOR_ACCENT};
    border: none;
    border-radius: {RADIUS_SM}px;
    padding: 10px 20px;
    font-weight: 700;
    color: #000000;
}}

QPushButton[role="action_accent"]:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

/* Estilo Secundario (Outlined / Esquemático) */
QPushButton[role="action_outlined"] {{
    background-color: transparent;
    border: 1px solid {COLOR_BORDER_ACTIVE};
    border-radius: {RADIUS_SM}px;
    padding: 10px 20px;
    font-weight: 500;
    color: {COLOR_TEXT_SECONDARY};
}}

QPushButton[role="action_outlined"]:hover {{
    background-color: {COLOR_BG_ELEVATED};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_TEXT_SECONDARY};
}}

/* Estilo Peligro / Advertencia (Rojo) */
QPushButton[role="action_danger"] {{
    background-color: transparent;
    border: 1px solid #ef4444; 
    color: #ef4444;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: bold;
}}
QPushButton[role="action_danger"]:hover {{
    background-color: rgba(239, 68, 68, 0.1);
}}

/* Estilo Éxito / Actualización (Verde Neón) */
QPushButton[role="action_success"] {{   
    background-color: transparent;
    border: 1px solid #53ff1a; 
    color: #53ff1a;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: bold;
}}
QPushButton[role="action_success"]:hover {{
    background-color: rgba(83, 255, 26, 0.1);
}}

/* ─── Segmented Toggle (Botón Doble) ─── */
QPushButton#ToggleLeft, QPushButton#ToggleRight {{
    background-color: {COLOR_BG_INPUT};
    border: 1px solid {COLOR_BORDER_SVELTE};
    padding: 6px 16px;
    font-weight: 600;
    color: {COLOR_TEXT_SECONDARY};
}}

/* Redondeo solo en los extremos exteriores */
QPushButton#ToggleLeft {{
    border-top-left-radius: {RADIUS_SM}px;
    border-bottom-left-radius: {RADIUS_SM}px;
    border-right: none; /* Evitamos borde doble en el centro */
}}

QPushButton#ToggleRight {{
    border-top-right-radius: {RADIUS_SM}px;
    border-bottom-right-radius: {RADIUS_SM}px;
    border-left: 1px solid {COLOR_BORDER_SVELTE};
}}

/* Estado Activo: Izquierda (LOCAL - Rojo/Gris) */
QPushButton#ToggleLeft[active="true"] {{
    background-color: rgba(239, 68, 68, 0.1);
    color: #ef4444;
    border: 1px solid #ef4444;
}}

/* Estado Activo: Derecha (WEB IA - Verde) */
QPushButton#ToggleRight[active="true"] {{
    background-color: {COLOR_ACCENT_SOFT};
    color: {COLOR_ACCENT};
    border: 1px solid {COLOR_ACCENT};
}}

/* ─── Barra de Progreso (Minimalista) ─── */
QProgressBar {{
    background-color: {COLOR_BG_INPUT};
    border: 1px solid {COLOR_BORDER_SVELTE};
    border-radius: {RADIUS_SM}px;
    text-align: center;
    color: transparent; /* Ocultar texto de porcentaje */
    height: 10px;
}}

QProgressBar::chunk {{
    background-color: {COLOR_ACCENT};
    border-radius: {RADIUS_SM - 1}px;
    margin: 1px;
}}

/* --- SCROLLBARS --- */
QScrollBar:vertical {{ border: none; background: {COLOR_BG_BASE}; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {COLOR_TEXT_MUTED}; border-radius: {RADIUS_SM}; min-height: 20px; }}
QScrollBar::handle:vertical:hover {{ background: {COLOR_ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

QScrollBar:horizontal {{ background: {COLOR_BG_BASE}; height: 8px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: #444; border-radius: {RADIUS_SM}; min-width: 20px; }}
QScrollBar::handle:horizontal:hover {{ background: {COLOR_ACCENT}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}

/* ─── Sliders (Volumen) ─── */
QSlider::groove:horizontal {{
    border: 1px solid {COLOR_BORDER_SVELTE};
    height: 4px;
    background: {COLOR_BG_INPUT};
    margin: 2px 0;
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {COLOR_ACCENT};
    border: none;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

/* ─── ComboBox ─── */
QComboBox {{
    background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_PRIMARY};
    border-radius: {RADIUS_SM}px; padding: 10px; border: 1px solid {COLOR_BORDER_SVELTE}; 
}}
QComboBox:hover {{ border: 1px solid {COLOR_ACCENT}; }}
QComboBox::drop-down {{ border: none;}}
QComboBox::down-arrow {{ image: url('{PATH_CHEVRON}'); width: 14px; height: 14px; margin-right: 8px; }}

QComboBox QAbstractItemView {{
    background-color: {COLOR_BG_SURFACE}; color: {COLOR_TEXT_PRIMARY};
    selection-background-color: {COLOR_ACCENT_SOFT}; selection-color: {COLOR_ACCENT};
    border: 1px solid {COLOR_BORDER_SVELTE}; outline: none;
}}
"""