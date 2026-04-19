# frontend/theme.py

import sys
import os
import tempfile
from frontend.utils import get_icon_colored

# ==========================================
# 1. SISTEMA DE RUTAS (Para CSS/QSS)
# ==========================================
def asset_url(filename: str) -> str:
    """Obtiene la ruta absoluta de un asset (útil para combobox chevrons)."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   
    return os.path.join(base_path, "assets", "icons", filename).replace("\\", "/")

# ==========================================
# 2. DEFINICIONES DE DISEÑO (TOKENS)
# ==========================================
class Palette:
    """Sistema de Color 'Kick Midnight' (Exclusivo Dark Mode)."""
    Black_N1       = "#141414"
    Black_N2       = "#1C1C1C"
    Black_N3       = "#252525"
    Black_N4       = "#404040"
    
    Gray_N1        = "#8B8B8B"
    Gray_N2        = "#666666"
    
    White_N1       = "#FFFFFF"
    White_N2       = "rgba(255,255,255,0.08)"
    
    NeonGreen_Main  = "#53fc18"
    NeonGreen_Light = "#6aff2e"
    NeonGreen_Dark  = "#3da812"
    
    status_error    = "#FF453A"
    status_success  = "#32D74B"
    status_warning  = "#FFD60A"
    status_info     = "#0A84FF"

class Dims:
    """Dimensiones y Espaciados."""
    radius = {
        "card": "12px", "input": "8px", "scroll": "4px"
    }
    layout = {
        "level_01": (10,10,10,10), "level_02": (16,16,16,16), 
        "level_03": (20,20,20,20), "space_01": 12
    }

class Fonts:
    """Configuración tipográfica."""
    family = "Segoe UI"
    h1 = "18pt"; h2 = "14pt"; h3 = "12pt"; body = "10pt"

# ==========================================
# 3. HOJA DE ESTILOS GLOBAL (QSS MAESTRO)
# ==========================================
def get_sheet() -> str:
    """Devuelve la hoja de estilos principal (Siempre Dark)."""
    c = Palette
    r = Dims.radius
    f = Fonts
    
    return f"""
    /* --- BASE --- */
    QMainWindow, QWidget {{ 
        background-color: {c.Black_N1}; color: {c.White_N1}; 
        font-family: "{f.family}"; font-size: {f.body};
    }}
    
    /* --- TEXTOS --- */
    QLabel {{ background: transparent; border: none; padding: 0px; }}
    QLabel#h1 {{ font-size: {f.h1}; font-weight: bold; padding: 0px 5px 0px -5px; }}
    QLabel#h2 {{ font-size: {f.h2}; font-weight: bold; padding: 0px 5px 0px -5px; }}
    QLabel#h3 {{ font-size: {f.h3}; font-weight: bold; color: {c.White_N1}; padding: 0px 5px 0px -5px; }}
    QLabel#h4 {{ font-size: {f.h3}; font-weight: bold; color: {c.White_N1}; border-bottom: 1px solid #333; padding: 0px 5px 8px -3px; }}
    QLabel#h5 {{ font-size: {f.body}; font-weight: bold; color: {c.Gray_N1}; padding: 0px 5px 0px -3px; }}
    QLabel#normal {{ font-size: {f.body}; font-weight: 500; color: {c.Gray_N2}; }}
    QLabel#subtitle {{ font-size: {f.body}; color: {c.Gray_N2}; }}
    
    /* --- CONTENEDORES --- */
    QFrame {{ border: none; }}
    QFrame#Sidebar {{ background-color: {c.Black_N2}; }}
    QScrollArea {{ background: transparent; border: none; }}

    /* --- INPUTS --- */
    QLineEdit, QPlainTextEdit {{ 
        background-color: {c.Black_N2}; color: {c.White_N1}; 
        border-radius: {r['input']}; padding: 4px; 
    }}
    QLineEdit:focus, QPlainTextEdit:focus {{ border: 1px solid {c.NeonGreen_Main}; background-color: {c.Black_N3}; }}
    QLineEdit[readOnly="true"] {{ color: {c.NeonGreen_Main}; font-family: Consolas; }}
    
    /* Botón Sidebar Menu Mini */
    QPushButton#MenuBtnMini {{ background: transparent; border: none; margin: 4px; padding: 8px; border-radius: 12px; }}
    QPushButton#MenuBtnMini:hover {{ background-color: {c.White_N2}; }}
    QPushButton#MenuBtnMini:checked {{ background-color: rgba(83, 252, 24, 0.1); border: 1px solid {c.NeonGreen_Dark}; }}

    /* --- SLIDERS --- */
    QSlider::groove:horizontal {{ background-color: {c.Black_N3}; height: 6px; border-radius: 3px; }}
    QSlider::handle:horizontal {{ background-color: {c.NeonGreen_Main}; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; }}

    /* --- SCROLLBARS --- */
    QScrollBar:vertical {{ background: {c.Black_N1}; width: 8px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: #444; border-radius: {r['scroll']}; min-height: 20px; }}
    QScrollBar::handle:vertical:hover {{ background: {c.NeonGreen_Main}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

    QScrollBar:horizontal {{ background: {c.Black_N1}; height: 8px; margin: 0; }}
    QScrollBar::handle:horizontal {{ background: #444; border-radius: {r['scroll']}; min-width: 20px; }}
    QScrollBar::handle:horizontal:hover {{ background: {c.NeonGreen_Main}; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}
    """

# ==========================================
# 4. ESTILOS ESPECÍFICOS (REUTILIZABLES)
# ==========================================
c = Palette
r = Dims.radius

STYLES = {
    # --- CONTENEDORES ---
    "card": f"""
        QFrame {{
            background-color: {c.Black_N2}; 
            border-radius: {r['card']}; 
        }}
    """,
    "card_large": f"""
        QFrame {{
            background-color: {c.Black_N2}; 
            border-radius: 16px; 
        }}
    """,
    # --- LABELS ---
    "label_readonly": f"""
        QLabel {{ 
            background: {c.Black_N3}; color: {c.Gray_N1}; 
            font-family: Consolas; 
            border-radius: {r['input']}; padding: 4px;
        }}
    """,
    "label_text": f"""
        QLabel {{font-weight: bold; font-size: 13px; color: white; border: none; background: transparent;}}
    """,
    "label_title": f"""
        QLabel {{ 
            border:none; font-size: 14px; 
            font-weight: bold; color: white;
        }}
    """,
    # --- INPUTS ---
    "input": f"""
        QLineEdit {{ background: {c.Black_N3}; border-radius: {r['input']}; padding: 6px; color: white; }}
        QLineEdit:focus {{ border: 1px solid {c.Gray_N1}; }}
    """,
    "input_cmd": f"""
        QLineEdit {{ 
            background: {c.Black_N3}; color: {c.Gray_N1}; font-weight: bold; font-family: Consolas;
            border-radius: 4px; padding: 6px;
        }}
        QLineEdit:focus {{ border-color: {c.Gray_N1}; }}
    """,
    "input_readonly": f"""
        QLineEdit {{ 
            background: {c.Black_N3}; color: {c.Gray_N1}; 
            font-family: Consolas;
            border-radius: {r['input']}; padding: 4px;
        }}
    """,
    
    # --- LOGS Y CONSOLAS ---
    "text_edit_log": f"""
        QTextEdit {{
            background-color: {c.Black_N3};
            color: {c.White_N1};
            padding: 8px;
            font-size: 12px;
        }}
    """,
    "text_edit_console": f"""
         QTextEdit {{
            background-color: {c.Black_N3}; color: {c.Gray_N1};
            font-family: Consolas, monospace; font-size: 12px; padding: 10px; border: none;
        }}
    """,

    # --- BOTONES ---
    # Botón estándar para barra superior (Importar/Exportar)
    "btn_nav": f"""
        QPushButton {{
            background-color: {c.Black_N2}; color: {c.White_N1};
            padding: 6px 12px; border: 1px solid {c.Black_N2}; border-radius: 6px; 
            font-size: 12px; font-weight: bold;
            
        }}
        QPushButton:hover {{ 
            background-color: {c.Black_N4}; border-color: {c.NeonGreen_Main}; 
        }}
    """,
    # Botón sólido primario (Aplicar, Guardar)
    "btn_primary": f"""
        QPushButton {{ 
            background-color: rgba(83, 252, 24, 0.15); border: 1px solid {c.NeonGreen_Main};
            color: {c.NeonGreen_Main};
            padding: 6px 12px; margin: 2px; border-radius: 6px;
            font-size: 12px; font-weight: bold; 
        }}
        QPushButton:hover {{ background-color: {c.Black_N3}; }}
    """,
    # Botón "Peligroso" delineado (Desvincular, Borrar todo)
    "btn_danger_outlined": f"""
        QPushButton {{
            background-color: rgba(239, 83, 80, 0.2); color: {c.White_N1};
            padding: 6px 12px; border: 1px solid {c.status_error}; border-radius: 6px;
            font-weight: 500;
        }}
        QPushButton:hover {{ background-color: {c.status_error}; color: white; }}
    """,
    # Botón pequeño de acción (Editar, Borrar en tablas)
    "btn_icon_ghost": f"""
        QPushButton {{ background: transparent; border: none; border-radius: 6px; }} 
        QPushButton:hover {{ background-color: {c.White_N2}; }}
    """,
    # Botón verde translucido
    "btn_toggle": f"""
        QPushButton {{
            background-color: {c.Black_N3};
            
            border-radius: 6px;
            color: {c.White_N1};
            padding: 6px 12px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {c.Black_N4};
            border-color: {c.Gray_N1};
        }}
        /* ESTADO ACTIVO (CHECKED) - Reemplaza tu lógica manual */
        QPushButton:checked {{
            background-color: rgba(83, 252, 24, 0.15); 
            border: 1px solid {c.NeonGreen_Main};
            color: {c.NeonGreen_Main};
        }}
    """,

    # --- LISTAS Y TABLAS ---
    "table_clean": f"""
        QTableWidget {{
            background-color: {c.Black_N2}; gridline-color: {c.Black_N4}; outline: none; border: none;
        }}
        QHeaderView::section {{
            background-color: {c.Black_N3}; color: {c.Gray_N1}; border: none;
            padding: 8px; font-weight: bold; text-transform: uppercase; font-size: 12px;
        }}
        QTableWidget::item {{ padding: 6px; }}
        QTableWidget::item:selected {{ background-color: {c.White_N2}; color: {c.NeonGreen_Main}; }}
    """,
    
    # --- COMPLEX WIDGETS ---
    "combobox_modern": f"""
        QComboBox {{
            background-color: {c.Black_N3}; 
            color: {c.White_N1}; border-radius: 6px; padding: 6px; min-height: 18px;
        }}
        QComboBox:hover, QComboBox:focus {{
            background-color: {c.Black_N1};
        }}
        
        QComboBox::drop-down{{border: none;}}
        QComboBox::down-arrow {{image: url({asset_url("chevron-down.svg")}); margin-right: 4px;}}
        QComboBox::down-arrow::on {{image: url({asset_url("chevron-up.svg")}); margin-right: 4px;}}

        QComboBox QAbstractItemView {{
            background-color: {c.NeonGreen_Dark}; color: {c.Black_N3};
            selection-background-color: {c.NeonGreen_Light}; selection-color: {c.Black_N2}; padding: 4px;
        }}
    """,
    
    "spinbox_modern": f"""
        QSpinBox, QDoubleSpinBox {{
            background-color: {c.Black_N3}; color: {c.White_N1}; border-radius: {r['input']};
            padding: 6px 10px; padding-right: 25px; selection-color: {c.Black_N2}; selection-background-color: {c.NeonGreen_Light};
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{  background-color: {c.Black_N3}; }}
        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            subcontrol-origin: border; subcontrol-position: top right; width: 16px; border: none;
            border-left: 1px solid {c.Black_N1}; border-top-right-radius: {r['input']}; background-color: {c.Black_N3};
        }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            subcontrol-origin: border; subcontrol-position: bottom right; width: 16px; border: none;
            border-left: 1px solid {c.Black_N1}; border-bottom-right-radius: {r['input']}; background-color: {c.Black_N3};
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background-color: {c.Black_N4}; }}
    """
}

# ==========================================
# 5. HELPERS VISUALES
# ==========================================
def get_switch_style(on_icon_name: str = "switch-on.svg", *args, **kwargs) -> str:
    off_path = asset_url("switch-off.svg")
    colored_icon = get_icon_colored(on_icon_name, Palette.NeonGreen_Main, size=21)
    temp_dir = tempfile.gettempdir()
    on_path = os.path.join(temp_dir, "kick_switch_on_colored.png").replace("\\", "/")

    if not colored_icon.isNull():
        colored_icon.pixmap(21, 21).save(on_path, "PNG")
    else:
        on_path = asset_url(on_icon_name)

    return f"""
        QCheckBox {{ 
            background: transparent; 
            spacing: 8px; 
            color: {Palette.Gray_N1}; 
            font-weight: bold; 
            font-size: 12px; 
        }}
        QCheckBox::indicator {{ 
            width: 21px; /* Ajustado al tamaño de tu SVG original */
            height: 21px; 
            border: none; 
        }}
        QCheckBox::indicator:unchecked {{ image: url({off_path}); }}
        QCheckBox::indicator:checked {{ image: url({on_path}); }}
    """

# ==========================================
# 6. EXPORTACIONES
# ==========================================
COLORS = {k: v for k, v in Palette.__dict__.items() if not k.startswith("__")}
LAYOUT = Dims.layout
RADIUS = Dims.radius
THEME_DARK = COLORS