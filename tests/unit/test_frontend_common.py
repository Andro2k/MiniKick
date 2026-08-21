# tests\unit\test_frontend_common.py

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QPixmap

from frontend.common.paths import resource_path, get_assets_path, resolve_icon_path
from frontend.common.icons import (
    get_icon, 
    get_icon_colored, 
    get_pixmap_colored, 
    get_pixmap, 
    ICON_SIZE_MD, 
    ICON_SIZE_LG
)
from frontend.common.validators import validate_trigger_prefix
from frontend.widgets.no_wheel import NoWheelComboBox, NoWheelSlider, NoWheelDateEdit, NoWheelTimeEdit

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_paths_resolution():
    base_assets = get_assets_path()
    assert "assets" in base_assets
    
    icon_path = get_assets_path("icons")
    assert "icons" in icon_path
    
    resolved = resolve_icon_path("refresh.svg")
    assert resolved is not None
    assert resolved.endswith("refresh.svg")
    
    nonexistent = resolve_icon_path("non_existent_icon_xyz_123.svg")
    assert nonexistent is None

def test_validators():
    assert validate_trigger_prefix("") is True
    assert validate_trigger_prefix("   ") is True
    assert validate_trigger_prefix("!help") is True
    assert validate_trigger_prefix("!test 123") is True
    assert validate_trigger_prefix("help") is False
    assert validate_trigger_prefix("?help") is False

def test_icons_rendering(qapp):
    icon = get_icon("refresh.svg")
    assert isinstance(icon, QIcon)
    assert not icon.isNull()
    default_icon = get_icon_colored("refresh.svg")
    assert isinstance(default_icon, QIcon)
    assert not default_icon.isNull()
    colored_icon = get_icon_colored("refresh.svg", color_str="#2ECD70", size=24)
    assert isinstance(colored_icon, QIcon)
    assert not colored_icon.isNull()
    pixmap = get_pixmap_colored("refresh.svg")
    assert isinstance(pixmap, QPixmap)
    assert not pixmap.isNull()
    raw_pixmap = get_pixmap("refresh.svg", size=16)
    assert isinstance(raw_pixmap, QPixmap)
    assert not raw_pixmap.isNull()

from frontend import common

def test_frontend_common_package_exports():
    assert hasattr(common, "get_assets_path")
    assert hasattr(common, "resource_path")
    assert hasattr(common, "resolve_icon_path")
    assert hasattr(common, "get_icon")
    assert hasattr(common, "get_icon_colored")
    assert hasattr(common, "get_pixmap_colored")
    assert hasattr(common, "get_pixmap")
    assert hasattr(common, "create_circular_pixmap")
    assert hasattr(common, "validate_trigger_prefix")

def test_no_wheel_widgets_instantiation(qapp):
    cb = NoWheelComboBox()
    assert cb is not None
    slider = NoWheelSlider()
    assert slider is not None
    date_edit = NoWheelDateEdit()
    assert date_edit is not None
    time_edit = NoWheelTimeEdit()
    assert time_edit is not None
