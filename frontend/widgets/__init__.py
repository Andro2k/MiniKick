# frontend\widgets\__init__.py

from .base_view import BaseView
from .blocks import (
    ViewHeader, SettingRow, FormField, SliderRow, StatCard, 
    ModernCard, ModernScrollArea, FadingScrollArea, ExpandableSettingCard, ModernDivider,
    create_badge
)
from .controls import ModernButton, ModernSwitch, CompactSpinBox, VariableHighlighter, VariableTextEdit
from .color_picker import ModernColorPicker
from .platform_controls import PlatformSwitchGroup
from .flow_layout import FlowLayout
from .scalable_illustration import ScalableIllustration
from .table import ModernTable, ModernTableCard, TableActionCell, PlatformBadgeCell
from .filter_header import FilterHeaderView
from .search_bar import UnifiedSearchBar
from .clearable_line_edit import ClearableLineEdit
from .pagination import SegmentedPagination
from .segmented_control import ModernSegmentedControl
from .no_wheel import (
    NoWheelComboBox, NoWheelSlider, NoWheelDateEdit, NoWheelTimeEdit,
    NoWheelSpinBox, NoWheelDoubleSpinBox
)
from .category_search import CategorySearchComboBox, CategorySuggestionsPopup, CategoryItemWidget
from .searchable_combo_box import SearchableComboBox, SearchableComboPopup

__all__ = [
    "BaseView",
    "ViewHeader",
    "SettingRow",
    "FormField",
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
    "ModernColorPicker",
    "PlatformSwitchGroup",
    "FlowLayout",
    "ScalableIllustration",
    "ModernTable",
    "ModernTableCard",
    "TableActionCell",
    "PlatformBadgeCell",
    "FilterHeaderView",
    "UnifiedSearchBar",
    "ClearableLineEdit",
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
    "CategoryItemWidget",
    "SearchableComboBox",
    "SearchableComboPopup"
]

