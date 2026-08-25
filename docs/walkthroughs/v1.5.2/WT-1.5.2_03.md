# Walkthrough: Centralización de Variables y Tokens de Diseño en `frontend/common/theme.py`

## 1. Resumen Ejecutivo

Se refactorizó el sistema de estilos globales ([`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py)) introduciendo un sistema unificado de **Design Tokens**. Se reemplazaron valores literales repetitivos y números mágicos (como `1.5px solid ...` dispersos 35+ veces, radios manuales `2px`, `4px`, `8px`, `16px`, `26px`, y paddings compuestos) por constantes semánticas centralizadas, facilitando el mantenimiento y garantizando consistencia visual sin alterar el rendimiento ni los roles de componentes.

---

## 2. Tokens de Diseño Estandarizados

### A. Escala Modular de Radios de Borde
```python
RADIUS_2XS         = 2    # Barras de progreso internas y wizard
RADIUS_XS          = 4    # Scrollbars y bordes sutiles
RADIUS_SM          = 6    # Chips, badges y esquinas compactas
RADIUS_MD_INNER    = 7    # Esquinas internas de controles compuestos (search bar, pagination)
RADIUS_MD          = 9    # Inputs, botones, tarjetas estándar
RADIUS_LG          = 12   # Contenedores modales y tarjetas grandes
RADIUS_XL          = 16   # Ventanas de diálogo flotantes
RADIUS_PILL        = 26   # Iconos circulares e insignias tipo píldora
```

### B. Espaciados y Paddings Semánticos
```python
PADDING_INPUT      = "5px"
PADDING_BUTTON     = "6px 12px"
PADDING_SPINBOX    = "3px 24px 3px 8px"  # Estandarizado para SpinBox, DoubleSpinBox, TimeEdit, DateEdit
PADDING_ITEM       = "4px 8px"           # Items de desplegables y menús
PADDING_BADGE      = "2px 6px"           # Insignias Kick/Twitch
PADDING_CHIP       = "3px 10px"          # Chips de filtrado
PADDING_TAB        = "8px 16px"          # Pestañas de TabWidget
PADDING_MENU_ITEM  = "4px 12px 4px 18px" # Items de menú desplegable
```

### C. Bordes Reutilizables
```python
BORDER_DEFAULT     = f"1.5px solid {COLOR_NEUTRAL_800}"
BORDER_SUBTLE      = f"1.5px solid {COLOR_NEUTRAL_750}"
BORDER_MUTED       = f"1.5px solid {COLOR_NEUTRAL_700}"
BORDER_TRANSPARENT = "1.5px solid transparent"
BORDER_FOCUS       = f"1.5px solid {COLOR_GREEN}"
BORDER_ERROR       = f"1.5px solid {COLOR_RED}"
```

---

## 3. Verificación y Pruebas

1. **Suite de Pruebas Automatizadas**:
   - `pytest` ejecutado: **64 tests pasados en 2.69s (100% éxito)**.
2. **Integridad de Roles y Estados QSS**:
   - `test_roles_integrity.py` validó que todos los selectores de roles y estados (`role="..."`, `state="..."`) se mantengan íntegros y registrados.
