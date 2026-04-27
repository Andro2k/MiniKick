# frontend/theme.py
# ─────────────────────────────────────────────
# Design tokens y Hoja de Estilos Global (QSS)
# ─────────────────────────────────────────────

# Paleta de colores
COLOR_BG_BASE       = "#16181D"   # Fondo principal
COLOR_BG_SURFACE    = "#1E2128"   # Tarjetas / Paneles / Sidebar
COLOR_BG_ELEVATED   = "#262A33"   # Inputs, Hover
COLOR_BORDER        = "#2E3340"   # Bordes sutiles
COLOR_ACCENT        = "#53fc18"   # Verde Kick (Ajustado a tu color original)
COLOR_ACCENT_HOVER  = "#45db12"
COLOR_TEXT_PRIMARY  = "#F1F5F9"
COLOR_TEXT_SECONDARY= "#848E9C"
COLOR_TEXT_MUTED    = "#3D4451"

# Tipografía
FONT_DISPLAY  = "Segoe UI"
FONT_BODY     = "Segoe UI"
FONT_MONO     = "Consolas"

# Radios y Espaciado
RADIUS_SM = 6
RADIUS_MD = 10
RADIUS_LG = 14
SPACING = 8

# ─── Stylesheet global QSS ───────────────────
# Aquí centralizamos TODO el diseño visual de la app.
# Usamos selectores de clase y de objeto (#nombreObjeto) para aplicar los estilos.

GLOBAL_QSS = f"""
/* ── Reset y Base ─────────────────────────────── */
* {{
    font-family: "{FONT_BODY}", sans-serif;
    color: {COLOR_TEXT_PRIMARY};
}}

QMainWindow, QDialog {{
    background-color: {COLOR_BG_BASE};
}}

/* Forzar fondos transparentes en contenedores genéricos para evitar solapamientos */
QWidget#TransparentWidget {{
    background: transparent;
}}

/* ── Scrollbar (Invisible/Minimalista) ────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_TEXT_SECONDARY};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollArea, QScrollArea > QWidget > QWidget {{
    background: transparent;
    border: none;
}}

/* ── Labels (Textos) ──────────────────────────── */
QLabel {{
    background: transparent;
}}
QLabel[role="title"] {{
    font-size: 24px;
    font-weight: 700;
    color: {COLOR_TEXT_PRIMARY};
}}
QLabel[role="subtitle"] {{
    font-size: 13px;
    color: {COLOR_TEXT_SECONDARY};
}}
QLabel[role="section"] {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: {COLOR_TEXT_MUTED};
    text-transform: uppercase;
}}
QLabel[role="stat_value"] {{
    font-family: "{FONT_DISPLAY}";
    font-size: 28px;
    font-weight: bold;
    color: {COLOR_TEXT_PRIMARY};
}}

/* ── Tarjetas (Cards y StatCards) ─────────────── */
QFrame#Card {{
    background: {COLOR_BG_SURFACE};
    border: 1.5px solid {COLOR_BORDER};
    border-radius: {RADIUS_LG}px;
}}

QLabel#StatIcon {{
    background: rgba(83, 252, 24, 0.1); /* Verde con opacidad */
    border-radius: 8px;
    font-size: 16px;
    color: {COLOR_ACCENT};
}}

/* ── Menú Lateral y Botones de Navegación ─────── */
QFrame#Sidebar {{
    background: {COLOR_BG_SURFACE};
    border-right: 1px solid {COLOR_BORDER};
}}

QPushButton#NavButton {{
    background: {COLOR_TEXT_SECONDARY};
    border: none;
    border-radius: 8px; /* Esquinas redondeadas como en tu imagen */
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
    color: {COLOR_TEXT_SECONDARY};
}}
QPushButton#NavButton:hover {{  
    background: {COLOR_BG_ELEVATED}; 
    color: {COLOR_TEXT_PRIMARY};
}}
QPushButton#NavButton:checked {{
    background: rgba(83, 252, 24, 0.12); /* Fondo verde translúcido */
    font-weight: 700;
    color: {COLOR_ACCENT};
}}

/* ── Contenedor del Chat ──────────────────────── */
QFrame#ChatContainer {{
    background: {COLOR_BG_SURFACE};
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 14px;
}}

/* ── CheckBox ─────────────────────────────────── */
QCheckBox {{
    spacing: 8px;
    font-size: 13px;
    background: transparent;
    color: {COLOR_TEXT_PRIMARY};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 4px;
    background: {COLOR_BG_ELEVATED};
}}
QCheckBox::indicator:checked {{
    background: {COLOR_ACCENT};
    border-color: {COLOR_ACCENT};
}}
"""