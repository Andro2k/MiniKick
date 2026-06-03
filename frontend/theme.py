# frontend/theme.py

from frontend.utils import get_assets_path

# ─── Recursos Base ───
PATH_ICON_HELP = get_assets_path("icons/help-circle.svg")
PATH_ICON_UPDATE = get_assets_path("icons/download.svg")

# ─── Paleta de Colores (Basada en la referencia Dark/Mint) ───
COLOR_BG_BASE       = "#0B0E11"   # Fondo de la aplicación (Negro profundo)
COLOR_BG_SURFACE    = "#1E2329"   # Tarjetas y paneles (Gris oscuro cálido)
COLOR_BG_INPUT      = "#2A2A2A"   # Fondos de inputs y campos de texto
COLOR_BG_HOVER      = "#333333"   

COLOR_BORDER_SVELTE = "#333333"   # Bordes inactivos y divisores
COLOR_BORDER_ACTIVE = "#53FC18"   # Borde activo al enfocar (Verde Menta)

COLOR_ACCENT        = "#53FC18"   # Verde Menta vibrante
COLOR_ACCENT_HOVER  = "#00C864"   
COLOR_ACCENT_SOFT   = "rgba(0, 229, 115, 0.15)" # Verde translúcido

COLOR_TEXT_PRIMARY  = "#F3F4F6"   # Blanco suave
COLOR_TEXT_SECONDARY= "#9CA3AF"   # Gris para subtítulos
COLOR_TEXT_MUTED    = "#6B7280"

# ─── Tipografía, Radios & Espaciados (Paddings) ───
FONT_FAMILY = "'Inter', '-apple-system', 'Segoe UI', sans-serif"
RADIUS_SM = 6
RADIUS_MD = 8  # Cajas de texto y botones redondeados
RADIUS_LG = 12  # Tarjetas principales altamente redondeadas

# Variables para controlar el padding globalmente (Arriba/Abajo Izquierda/Derecha)
PADDING_INPUT   = "4px 12px"
PADDING_BUTTON  = "4px 8px"
PADDING_SPINBOX = "4px 12px 4px 12px"
# ─── Stylesheet Global (QSS) ───
GLOBAL_QSS = f"""
/* ─── Reset y Base ─── */
* {{
    font-family: {FONT_FAMILY};
    font-size: 14px;
    color: {COLOR_TEXT_PRIMARY};
    outline: none;
}}

QMainWindow, QDialog, QWidget {{
    background-color: {COLOR_BG_BASE} /* El fondo real lo maneja el contenedor principal */
}}

/* Evitar que componentes internos hereden el fondo negro por error */
QFrame#Card, QTextEdit, QComboBox {{
    background-color: {COLOR_BG_SURFACE};
}}

/* ─── Contenedores Principales ─── */
QFrame#Sidebar {{
    background-color: {COLOR_BG_BASE};
    border-right: 1px solid {COLOR_BORDER_SVELTE};
}}

/* Tarjetas altamente redondeadas de la imagen */
QFrame#Card {{
    background-color: {COLOR_BG_SURFACE};
    border: none; /* Sin borde agresivo */
    border-radius: {RADIUS_LG}px;
}}

/* ─── Tipografía con Roles ─── */
QLabel{{
    background-color: transparent;
}}

QLabel[role="title"] {{
    font-size: 22px;
    font-weight: bold;
    background-color: transparent;
    color: {COLOR_TEXT_PRIMARY};
    letter-spacing: -0.5px;
}}

QLabel[role="section"] {{
    font-size: 14px;
    font-weight: bold;
    background-color: transparent;
    color: {COLOR_TEXT_PRIMARY};
}}

QLabel[role="subtitle"] {{
    background-color: transparent;
    color: {COLOR_TEXT_SECONDARY};
    font-size: 14px;
}}

/* ─── Inputs de Texto (Una sola línea) ─── */
QLineEdit {{
    background-color: {COLOR_BG_INPUT};
    border: none;
    border-radius: {RADIUS_MD}px;
    padding: {PADDING_INPUT};
    color: {COLOR_TEXT_PRIMARY};
}}

QLineEdit:focus {{
    border: 1px solid {COLOR_BORDER_ACTIVE};
    background-color: {COLOR_BG_HOVER};
}}
/* ─── Áreas de Texto (Multilínea) ─── */
QTextEdit, QTextEdit#ChatContainer {{
    background-color: {COLOR_BG_SURFACE};
    border: 1px solid {COLOR_BORDER_SVELTE}; /* Borde sutil por defecto para distinguirlo */
    border-radius: {RADIUS_MD}px;
    padding: {PADDING_INPUT};
    color: {COLOR_TEXT_PRIMARY};
}}

QTextEdit:focus, QTextEdit#ChatContainer:focus {{
    border: 1px solid {COLOR_BORDER_ACTIVE};
    background-color: {COLOR_BG_HOVER};
}}

/* ─── Tablas (QTableWidget) ─── */
QTableWidget {{
    background-color: {COLOR_BG_SURFACE};
    border: none;
    gridline-color: transparent;
    color: {COLOR_TEXT_PRIMARY};
    outline: none;
}}

/* Celdas de la tabla */
QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {COLOR_BORDER_SVELTE};
}}

/* Celdas seleccionadas (aunque tengas la selección desactivada, es buena práctica) */
QTableWidget::item:selected {{
    background-color: {COLOR_BG_HOVER};
    color: {COLOR_ACCENT};
}}
/* ─── Contenedor de Acciones en Tablas ─── */
QFrame#TableActions {{
    background-color:  {COLOR_BG_SURFACE};
}}
/* Cabecera superior de la tabla */
QHeaderView::section {{
    background-color: {COLOR_BG_INPUT};
    color: {COLOR_TEXT_SECONDARY};
    font-weight: bold;
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid {COLOR_BORDER_SVELTE};
    text-align: left;
}}

QHeaderView {{
    background-color: transparent;
    border: none;
}}

/* ─── Botones de Acción ─── */
/* Estilo Principal (Verde con texto oscuro) */
QPushButton[role="action_accent"] {{
    background-color: {COLOR_ACCENT};
    border: none;
    border-radius: {RADIUS_LG}px;
    padding: {PADDING_BUTTON};
    color: #000000;
    font-weight: 800;
}}

QPushButton[role="action_accent"]:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

/* Estilo Secundario (Gris Oscuro) */
QPushButton[role="action_outlined"] {{
    background-color: {COLOR_BG_INPUT};
    border: none;
    border-radius: {RADIUS_MD}px;
    padding: {PADDING_BUTTON};
    color: {COLOR_TEXT_PRIMARY};
    font-weight: 500;
}}

QPushButton[role="action_outlined"]:hover {{
    background-color: {COLOR_BG_HOVER};
}}

/* Estilo Peligro / Advertencia (Rojo) */
QPushButton[role="action_danger"] {{
    background-color: transparent;
    border: 1px solid #ef4444; 
    color: #ef4444;
    border-radius: {RADIUS_MD}px;
    padding: {PADDING_BUTTON};
    font-weight: 600;
}}
QPushButton[role="action_danger"]:hover {{
    background-color: rgba(239, 68, 68, 0.1);
}}

/* Estilo Éxito (Verde Outline) */
QPushButton[role="action_success"] {{   
    background-color: transparent;
    border: 1px solid {COLOR_ACCENT}; 
    color: {COLOR_ACCENT};
    border-radius: {RADIUS_MD}px;
    padding: {PADDING_BUTTON};
    font-weight: 600;
}}
QPushButton[role="action_success"]:hover {{
    background-color: {COLOR_ACCENT_SOFT};
}}

/* ─── Navegación (Sidebar) ─── */
QPushButton#NavButton {{
    background: transparent;
    border-radius: {RADIUS_SM}px;
    padding: {PADDING_BUTTON};
    text-align: left;
    color: {COLOR_TEXT_SECONDARY};
    font-weight: 500;
}}

QPushButton#NavButton:hover {{
    background-color: {COLOR_BG_HOVER};
    color: {COLOR_TEXT_PRIMARY};
}}

QPushButton#NavButton:checked {{
    background-color: {COLOR_ACCENT_SOFT};
    color: {COLOR_ACCENT};
}}

/* ─── Dropdown (ComboBox) ─── */
QComboBox {{
    background-color: {COLOR_BG_INPUT};
    color: {COLOR_TEXT_PRIMARY};
    border-radius: {RADIUS_MD}px;
    padding: {PADDING_BUTTON};
    border: none;
}}

QComboBox:focus, QComboBox:hover {{
    border: 1px solid {COLOR_BORDER_SVELTE};
    background-color: {COLOR_BG_HOVER};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 35px;
    border-left: none;
}}

/* Forzamos a Qt a usar su flecha (triángulo) nativa */
QComboBox::down-arrow {{
    image: none; 
    width: 10px; 
    height: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLOR_BG_SURFACE};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER_SVELTE};
    border-radius: {RADIUS_MD}px;
    outline: none;
    padding: 4px;
}}

/* Diseño de los ítems internos del Dropdown (Como en Figma) */
QComboBox QAbstractItemView::item {{
    border-radius: {RADIUS_SM}px;
    padding: 4px;
    margin: 2px;
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: {COLOR_BG_HOVER};
    color: {COLOR_ACCENT};
}}

/* ─── Sliders (Volumen) ─── */
QSlider {{
    background-color: transparent;
}}

QSlider::groove:horizontal {{
    border: none;
    background: {COLOR_BG_INPUT};
    border-radius: 6px;
}}

QSlider::sub-page:horizontal {{
    background: {COLOR_ACCENT}; 
    border-radius: 6px;
}}

QSlider::handle:horizontal {{
    background: #F3F4F6;
    border: none;
    width: 10px;
    height: 16px;
    margin: -4px 0px;
    border-radius: 16px;
}}

/* ─── Checkboxes & Switches Nativos ─── */
QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 1px solid {COLOR_BORDER_SVELTE};
    background-color: {COLOR_BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background-color: {COLOR_ACCENT};
    border: 1px solid {COLOR_ACCENT};
}}

/* --- SCROLLBARS LIGEROS --- */
QScrollBar:vertical {{ border: none; background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {COLOR_BORDER_SVELTE}; border-radius: 4px; min-height: 20px; }}
QScrollBar::handle:vertical:hover {{ background: {COLOR_TEXT_MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

QScrollBar:horizontal {{ background: transparent; height: 8px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {COLOR_BORDER_SVELTE}; border-radius: 4px; min-width: 20px; }}
QScrollBar::handle:horizontal:hover {{ background: {COLOR_TEXT_MUTED}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}

/* ─── SpinBoxes (Contadores Numéricos / Stepper) ─── */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLOR_BG_INPUT};
    color: {COLOR_TEXT_PRIMARY};
    border-radius: {RADIUS_MD}px;
    padding: {PADDING_SPINBOX};
    border: none;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {COLOR_BORDER_ACTIVE};
    background-color: {COLOR_BG_HOVER};
}}

/* Contenedor Agrupado de las Flechas (El bloque oscuro de la imagen) */
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 16px;
    background-color: {COLOR_ACCENT};
    border-top-left-radius: {RADIUS_SM}px;
    border-top-right-radius: {RADIUS_SM}px;
    margin-top: 4px;
    margin-right: 4px;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 16px;
    background-color: {COLOR_ACCENT};
    border-bottom-left-radius: {RADIUS_SM}px;
    border-bottom-right-radius: {RADIUS_SM}px;
    margin-bottom: 4px;
    margin-right: 4px;
}}

/* Efectos de interacción en los botones del Stepper */
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {COLOR_ACCENT};
}}

QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed,
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{
    background-color: {COLOR_ACCENT_HOVER};
}}

"""