# frontend/components/switch.py

from PySide6.QtWidgets import QAbstractButton
from PySide6.QtGui import QPainter, QColor, QPainterPath
from PySide6.QtCore import Qt, QPropertyAnimation, Property, QRectF, QSize

from frontend.theme import COLOR_ACCENT, COLOR_BG_ELEVATED
from frontend.utils import get_icon_colored

class IconSwitch(QAbstractButton):
    def __init__(self, icon_on: str = "", icon_off: str = "", parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(48, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Estado de la animación (0.0 es apagado, 1.0 es encendido)
        self._position = 0.0
        self.anim = QPropertyAnimation(self, b"position")
        self.anim.setDuration(250) # Milisegundos que dura el deslizamiento

        self.toggled.connect(self._start_animation)

        # Pre-cargar los íconos (tamaño 14x14)
        # Si no pasas nombres de archivos, simplemente no dibujará íconos.
        self.pix_on = None
        self.pix_off = None
        
        if icon_on:
            self.pix_on = get_icon_colored(icon_on, COLOR_ACCENT, 14).pixmap(14, 14)
        if icon_off:
            self.pix_off = get_icon_colored(icon_off, "#6a6a6a", 14).pixmap(14, 14)

    # ─── PROPIEDAD ANIMABLE ───
    @Property(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update() # Forzar re-dibujado cada vez que cambia la posición

    def _start_animation(self, checked: bool):
        self.anim.stop()
        self.anim.setEndValue(1.0 if checked else 0.0)
        self.anim.start()

    # ─── MOTOR DE RENDERIZADO VISUAL ───
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Dibujar el fondo (Píldora)
        rect = QRectF(0, 0, self.width(), self.height())
        path = QPainterPath()
        path.addRoundedRect(rect, self.height() / 2, self.height() / 2)

        # Interpolar colores (Gris cuando está apagado, Acento cuando está encendido)
        bg_color = QColor(COLOR_ACCENT) if self.isChecked() else QColor(COLOR_BG_ELEVATED)
        p.fillPath(path, bg_color)

        # 2. Calcular la posición de la bolita (Thumb)
        thumb_radius = self.height() / 2 - 3
        x_min = 3
        x_max = self.width() - (thumb_radius * 2) - 3
        
        # Mover la bolita basado en la posición de la animación (0.0 a 1.0)
        thumb_x = x_min + (x_max - x_min) * self._position
        thumb_rect = QRectF(thumb_x, 3, thumb_radius * 2, thumb_radius * 2)

        # Dibujar la bolita blanca
        p.setBrush(Qt.GlobalColor.white)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(thumb_rect)

        # 3. Dibujar el ícono SVG dentro de la bolita (si existe)
        pix = self.pix_on if self.isChecked() else self.pix_off
        if pix and not pix.isNull():
            icon_rect = pix.rect()
            # Centrar el ícono dentro de la bolita
            icon_rect.moveCenter(thumb_rect.center().toPoint())
            p.drawPixmap(icon_rect, pix)

        p.end()