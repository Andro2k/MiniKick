# backend\services\settings\__init__.py
"""User settings, translations and widget configuration services."""

from .settings_service import SettingsService
from .translation_service import TranslationService
from .widgets_service import WidgetService

__all__ = [
    "SettingsService",
    "TranslationService",
    "WidgetService",
]
