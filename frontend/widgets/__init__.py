# frontend\widgets\__init__.py

from .block_widget import (
    ViewHeader, SectionHeader, SettingRow, SliderRow, StatCard, 
    ModernCard, ModernScrollArea, FadingScrollArea, ExpandableCard, ExpandableSettingCard, ModernDivider,
    create_badge
)
from .controls_widget import ModernButton, ModernSwitch, CompactSpinBox, VariableHighlighter, VariableTextEdit
from .color_picker import ModernColorPicker
from .flow_layout import FlowLayout
from .scalable_illustration import ScalableIllustration
from .table_widget import ModernTable, ModernTableCard, TableActionCell, PlatformBadgeCell
from .filter_header import FilterHeaderView
from .search_bar import UnifiedSearchBar
from .clearable_line_edit import ClearableLineEdit
from .pagination_widget import SegmentedPagination
from .segmented_control import ModernSegmentedControl
from .no_wheel import (
    NoWheelComboBox, NoWheelSlider, NoWheelDateEdit, NoWheelTimeEdit,
    NoWheelSpinBox, NoWheelDoubleSpinBox
)
from .category_search import CategorySearchComboBox, CategorySuggestionsPopup, CategoryItemWidget
from .searchable_combo_box import SearchableComboBox, SearchableComboPopup
from .inspector_widgets import InspectorPropertyRow
from .layout_helpers import (
    create_card_frame, create_row_layout, create_col_layout,
    create_labeled_field, create_switch_field, create_box_layout,
    create_two_column_container, create_frameless_input,
    create_text_label, create_platform_switches,
    create_error_label, sync_dual_platform_switches
)

__all__ = [
    "create_card_frame",
    "create_row_layout",
    "create_col_layout",
    "create_labeled_field",
    "create_switch_field",
    "create_box_layout",
    "create_two_column_container",
    "create_frameless_input",
    "create_text_label",
    "create_platform_switches",
    "create_error_label",
    "sync_dual_platform_switches",
    "InspectorPropertyRow",
    "BaseView",
    "ViewHeader",
    "SectionHeader",
    "SettingRow",
    "SliderRow",
    "StatCard",
    "ModernCard",
    "ModernScrollArea",
    "FadingScrollArea",
    "ExpandableCard",
    "ExpandableSettingCard",
    "ModernDivider",
    "create_badge",
    "ModernButton",
    "ModernSwitch",
    "CompactSpinBox",
    "VariableHighlighter",
    "VariableTextEdit",
    "ModernColorPicker",
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

def __getattr__(name: str):
    if name == "BaseView":
        from frontend.views.base_view import BaseView
        return BaseView
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


