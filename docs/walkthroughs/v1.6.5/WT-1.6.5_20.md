# Walkthrough Técnico — MiniKick v1.6.5 (Paso 20)

Se completó la migración del sistema visual a tokens arquitectónicos de tres niveles y se actualizaron los consumidores del frontend para dejar de depender de alias globales.

---

## Novedades

- La fachada común exporta las clases de tokens `Palette`, `Semantic`, `BrandColors`, `MusicTheme`, `AlertTheme`, `ChatTheme`, `BadgeTheme`, `SwitchTheme`, `Size`, `Borders` y `Gradients`.
- Los consumidores de color, geometría, bordes y gradientes del frontend usan las clases de dominio correspondientes.

## Mejoras

- `Palette` conserva únicamente la escala neutral y la superficie genérica. Los valores de marca y dominio residen junto al propósito que representan.
- Se eliminaron los alias globales antiguos del tema. Los iconos y el renderizado Markdown consumen tokens explícitos por clase.
- La fachada `frontend.common` dejó de publicar la lista de variables sueltas, reduciendo la ambigüedad y haciendo visibles las dependencias arquitectónicas.
- La generación de QSS conserva la caché y el punto de extensión para reglas personalizadas ya implementados.

## Correcciones

- Se migraron los imports y referencias de los módulos dependientes para evitar `ImportError` tras retirar las exportaciones antiguas.
- Se ajustaron llamadas de layout para que los parámetros de márgenes usen tokens `Size.Margin` y no valores de espaciado.

## Archivos Modificados

- `frontend/common/theme.py`
- `frontend/common/__init__.py`
- `frontend/common/icons.py`
- `frontend/common/markdown.py`
- Módulos del frontend y auditorías que consumían los alias anteriores

## Verificación

- `python -m compileall -q frontend resources/tests`: correcto.
- `git diff --check`: correcto tras corregir los espacios finales introducidos por la migración.
- Suite rápida de calidad MiniKick: 12/12 controles aprobados.
- PySide6 no está instalado en este entorno; falta validar imports completos de Qt y el renderizado visual real.
