# backend\models\__init__.py
"""Modelos de datos del backend."""

from .alerts_models import AlertType, AlertEvent, AlertConfig

__all__ = [
    "AlertType",
    "AlertEvent",
    "AlertConfig",
]
