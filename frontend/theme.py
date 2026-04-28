# frontend/theme.py
# ─────────────────────────────────────────────
# Design Tokens: Deep Dark Minimalism
# Estilo: Superficies profundas, bordes svelte (1px) y acentos Kick Green.
# ─────────────────────────────────────────────

# ─── Paleta de Colores (Inspiración: Slate & Onyx) ───
COLOR_BG_BASE       = "#0A0F12"   # Fondo ultra-profundo (Base)
COLOR_BG_SURFACE    = "#161D21"   # Superficie de tarjetas (Cards)
COLOR_BG_ELEVATED   = "#1F2937"   # Elementos sobre la superficie (Hover)
COLOR_BG_INPUT      = "#0F171A"   # Fondo para áreas de texto y inputs

COLOR_BORDER_SVELTE = "#1E293B"   # El "Hairline border" de 1px (Slate muy oscuro)
COLOR_BORDER_ACTIVE = "#334155"   # Borde más visible para estados activos

COLOR_ACCENT        = "#07BB43"   # Kick Green (Marca)
COLOR_ACCENT_HOVER  = "#048E32"   
COLOR_ACCENT_SOFT   = "rgba(12, 166, 120, 0.08)" # Fondo sutil para activos

COLOR_TEXT_PRIMARY  = "#F8FAFC"   # Blanco roto (Casi puro)
COLOR_TEXT_SECONDARY= "#94A3B8"   # Slate Grey (Secundario)
COLOR_TEXT_MUTED    = "#475569"   # Texto desactivado o labels sutiles

# ─── Tipografía & Radios ───
FONT_FAMILY = "'Inter', 'Aptos', 'Segoe UI', sans-serif"
RADIUS_SM = 6
RADIUS_MD = 12  # Radio estándar para tarjetas
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

/* ─── Contenedores Principales (Separación de Responsabilidades) ─── */
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

/* ─── Tipografía con Roles (Alta Cohesión) ─── */
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
    padding: 10px 12px;
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
QPushButton[role="action_accent"] {{
    background-color: {COLOR_ACCENT};
    border: none;
    border-radius: {RADIUS_SM}px;
    padding: 10px 20px;
    font-weight: 700;
    color: #FFFFFF;
}}

QPushButton[role="action_accent"]:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

/* ─── Scrollbars (Minimalistas e invisibles hasta el hover) ─── */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {COLOR_TEXT_MUTED};
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

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
"""