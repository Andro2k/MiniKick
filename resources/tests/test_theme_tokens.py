# resources\tests\test_theme_tokens.py

from frontend.common import theme as theme_module

_COLOR_CLASSES = ("Palette", "Semantic", "BrandColors", "MockupPalette", "BadgeTheme", "SwitchTheme")


def test_theme_color_constants_are_never_duplicated_across_classes():
    seen = {}
    for class_name in _COLOR_CLASSES:
        for attr, value in vars(getattr(theme_module, class_name)).items():
            if attr.startswith("__") or not isinstance(value, str) or not value.startswith("#"):
                continue
            key = value.upper()
            assert key not in seen, f"{class_name}.{attr} repeats {seen[key]} ({value})"
            seen[key] = f"{class_name}.{attr}"


def test_size_owns_radius_and_margin_without_module_level_copies():
    assert not hasattr(theme_module, "Radius")
    assert not hasattr(theme_module, "Margin")
    assert theme_module.Size.Radius.RAD_MED == 8
    assert theme_module.Size.Margin.MRG_NON == (0, 0, 0, 0)
