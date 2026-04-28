# frontend/theme.py
# ─────────────────────────────────────────────
# Design tokens y Hoja de Estilos Global (QSS)
# Inspirado en la sofisticación y paleta de image_2.png.
# ─────────────────────────────────────────────

# ─── Paleta de colores (Nueva y Refinada) ─────
COLOR_BG_BASE       = "#080808"   # Fondo de ventana principal (ultra-oscuro)
COLOR_BG_SURFACE    = "#151515"   # Paneles de tarjetas / Sidebar / Contenedores
COLOR_BG_ELEVATED   = "#1E1E1E"   # Inputs, Hover sobre elementos, botones sutiles
COLOR_BG_INPUT      = "#101010"   # Fondo específico para áreas de texto/inputs

COLOR_BORDER_SVELTE = "#252525"   # Bordes extremadamente sutiles y oscuros para paneles
COLOR_BORDER_INPUT  = "#333333"   # Bordes para inputs y botones

COLOR_ACCENT        = "#0ca678"   
COLOR_ACCENT_HOVER  = "#10c18c"   
COLOR_ACCENT_BG_OPAQUE = "rgba(12, 166, 120, 0.12)" 

COLOR_INDICATOR_CONNECTED = "#51cf66" 

COLOR_TEXT_PRIMARY  = "#f0f0f0"   
COLOR_TEXT_SECONDARY= "#a0a0a0"   
COLOR_TEXT_MUTED    = "#6a6a6a"   

# ─── Tipografía Modern & Minimalista ────────
FONT_FAMILY_STACK = "\"Aptos Font\", \"Inter\", \"Segoe UI\", \"San Francisco Pro Display\", \"Roboto\", sans-serif"
FONT_DISPLAY      = "\"Inter Semibold\", sans-serif" 
FONT_BODY         = FONT_FAMILY_STACK
FONT_MONO         = "\"Consolas\", \"Monospace\""

# ─── Radios y Espaciado (Svelte) ────────────
RADIUS_SM = 6
RADIUS_MD = 10
RADIUS_LG = 14
SPACING = 8

# ─── Stylesheet global QSS ───────────────────
GLOBAL_QSS = f"""
/* ── Reset y Base ─────────────────────────────── */
* {{
    font-family: {FONT_BODY};
    font-size: 13px;
    color: {COLOR_TEXT_PRIMARY};
}}

QMainWindow, QDialog {{
    background-color: {COLOR_BG_BASE};
}}

QWidget#TransparentWidget {{
    background: transparent;
}}

/* ── Scrollbar Minimalista (Invisible) ───────── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_BORDER_SVELTE};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_BORDER_INPUT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollArea, QScrollArea > QWidget > QWidget {{
    background: transparent;
    border: none;
}}

/* ── Labels (Textos con Roles) ───────────────── */
QLabel {{
    background: transparent;
}}
QLabel[role="title"] {{
    font-size: 26px;
    font-weight: 700;
    color: {COLOR_TEXT_PRIMARY};
}}
QLabel[role="subtitle"] {{
    font-size: 13px;
    color: {COLOR_TEXT_SECONDARY};
}}
QLabel[role="section"] {{
    font-family: {FONT_DISPLAY};
    font-size: 11px;
    letter-spacing: 1.5px;
    color: {COLOR_TEXT_MUTED};
    text-transform: uppercase;
}}
QLabel[role="stat_value"] {{
    font-size: 28px;
    font-weight: bold;
    color: {COLOR_TEXT_PRIMARY};
}}

QLabel#State_Connected {{
    color: {COLOR_INDICATOR_CONNECTED};
    font-weight: 600;
}}
QLabel#State_Dot {{
    font-size: 20px;
    color: {COLOR_INDICATOR_CONNECTED};
}}

/* ── Tarjetas (Cards y Paneles) ──────────────── */
QFrame#Card {{
    background-color: {COLOR_BG_SURFACE};
    border: 1.5px solid {COLOR_BORDER_SVELTE};
    border-radius: {RADIUS_LG}px;
}}

QFrame#Sidebar {{
    background-color: {COLOR_BG_SURFACE};
    border-right: 1.5px solid {COLOR_BORDER_SVELTE};
}}

/* ── Botones de Navegación ─────────────────── */
QPushButton#NavButton {{
    background: transparent;
    border: 1.5px solid {COLOR_BORDER_SVELTE};
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
    color: {COLOR_TEXT_SECONDARY};
}}
QPushButton#NavButton:hover {{  
    background: {COLOR_BG_ELEVATED}; 
    color: {COLOR_TEXT_PRIMARY};
    border-color: {COLOR_BORDER_INPUT};
}}
QPushButton#NavButton:checked {{
    background: {COLOR_ACCENT_BG_OPAQUE}; 
    font-weight: 700;
    color: {COLOR_ACCENT};
    border-color: {COLOR_ACCENT};
}}

/* REGLA NUEVA: Manejo automático del centrado cuando el sidebar se colapsa */
QPushButton#NavButton[collapsed="true"] {{
    text-align: center;
    padding: 10px 0px;
}}

/* ── Inputs y Botones de Acción (Inputs) ────── */
QPushButton#Input_Selector, QComboBox {{
    background-color: {COLOR_BG_ELEVATED};
    border: 1.5px solid {COLOR_BORDER_INPUT};
    border-radius: 8px;
    padding: 10px;
    text-align: left;
    color: {COLOR_TEXT_PRIMARY};
}}
QPushButton#Input_Selector:hover {{
    background-color: {COLOR_BORDER_SVELTE};
}}

QTextEdit, QPlainTextEdit {{
    background-color: {COLOR_BG_INPUT};
    border: 1.5px solid {COLOR_BORDER_SVELTE};
    border-radius: 8px;
    padding: SPACING;
    color: {COLOR_TEXT_PRIMARY};
}}

QPushButton[role="action_accent"] {{
    font-family: {FONT_DISPLAY};
    background-color: {COLOR_ACCENT};
    border: none;
    border-radius: 8px;
    padding: 12px;
    font-weight: 700;
    color: #ffffff; 
}}
QPushButton[role="action_accent"]:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

/* ── Slider (Barras de control) ───────────── */
QSlider::groove:horizontal {{
    background: {COLOR_BORDER_SVELTE};
    height: 6px;
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {COLOR_ACCENT};
    border: none;
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{
    background: {COLOR_ACCENT_HOVER};
}}

/* ── CheckBox ───────────────────────────────── */
QCheckBox {{
    spacing: 8px;
    font-size: 13px;
    background: transparent;
    color: {COLOR_TEXT_PRIMARY};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1.5px solid {COLOR_BORDER_SVELTE};
    border-radius: 4px;
    background: {COLOR_BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background: {COLOR_ACCENT};
    border-color: {COLOR_ACCENT};
}}
"""