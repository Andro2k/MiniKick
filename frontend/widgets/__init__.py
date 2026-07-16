# frontend\widgets\__init__.py

from .base_view import BaseView
from .blocks import (
    ViewHeader, SettingRow, SliderRow, StatCard, 
    ModernCard, ModernScrollArea, ExpandableSettingCard
)
from .controls import ModernButton, ModernSwitch, CompactSlider
from .flow_layout import FlowLayout
from .scalable_illustration import ScalableIllustration
from .table import ModernTable, ModernTableCard

__all__ = [
    "BaseView",
    "ViewHeader",
    "SettingRow",
    "SliderRow",
    "StatCard",
    "ModernCard",
    "ModernScrollArea",
    "ExpandableSettingCard",
    "ModernButton",
    "ModernSwitch",
    "CompactSlider",
    "FlowLayout",
    "ScalableIllustration",
    "ModernTable",
    "ModernTableCard"
]
