# frontend\common\layout_utils.py
"""Escalera única de anchos para los layouts adaptables del frontend."""

from enum import IntEnum


class Room(IntEnum):
    """Escalones de ancho útil; cada valor es el ancho mínimo (px) del escalón.

    Se clasifica siempre el ancho del contenido (`self.width()` de la vista),
    nunca un número suelto: `Room.of(width).fits(Room.WIDE)`.
    """

    TIGHT = 0
    SNUG = 480
    ROOMY = 650
    WIDE = 950
    VAST = 1100
    HUGE = 1280

    @classmethod
    def of(cls, width: int) -> "Room":
        """Devuelve el escalón más alto cuyo mínimo cabe en `width`."""
        for step in reversed(cls):
            if width >= step:
                return step
        return cls.TIGHT

    def fits(self, step: "Room") -> bool:
        """True si este ancho alcanza al menos el escalón indicado."""
        return self >= step

    def below(self, step: "Room") -> bool:
        """True si este ancho no alcanza el escalón indicado."""
        return self < step
