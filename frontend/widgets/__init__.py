# frontend\widgets\__init__.py

from .base_view import BaseView
from .blocks import (
    ViewHeader, SettingRow, SliderRow, StatCard, 
    ModernCard, ModernScrollArea, FadingScrollArea, ExpandableSettingCard, ModernDivider,
    create_badge
)
from .controls import ModernButton, ModernSwitch, CompactSpinBox, VariableHighlighter, VariableTextEdit
from .flow_layout import FlowLayout
from .scalable_illustration import ScalableIllustration
from .table import ModernTable, ModernTableCard, TableActionCell
from .filter_header import FilterHeaderView
from .search_bar import UnifiedSearchBar
from .pagination import SegmentedPagination
from .segmented_control import ModernSegmentedControl
from .no_wheel import (
    NoWheelComboBox, NoWheelSlider, NoWheelDateEdit, NoWheelTimeEdit,
    NoWheelSpinBox, NoWheelDoubleSpinBox
)
from .category_search import CategorySearchComboBox, CategorySuggestionsPopup, CategoryItemWidget

__all__ = [
    "BaseView",
    "ViewHeader",
    "SettingRow",
    "SliderRow",
    "StatCard",
    "ModernCard",
    "ModernScrollArea",
    "FadingScrollArea",
    "ExpandableSettingCard",
    "ModernDivider",
    "create_badge",
    "ModernButton",
    "ModernSwitch",
    "CompactSpinBox",
    "VariableHighlighter",
    "VariableTextEdit",
    "FlowLayout",
    "ScalableIllustration",
    "ModernTable",
    "ModernTableCard",
    "TableActionCell",
    "FilterHeaderView",
    "UnifiedSearchBar",
    "SegmentedPagination",
    "ModernSegmentedControl",
    "NoWheelComboBox",
    "NoWheelSlider",
    "NoWheelDateEdit",
    "NoWheelTimeEdit",
    "NoWheelSpinBox",
    "NoWheelDoubleSpinBox",
    "CategorySearchComboBox",
    "CategorySuggestionsPopup",
    "CategoryItemWidget"
]

