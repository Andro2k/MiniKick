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


_THEME_NAMES = (
    "Palette", "Semantic", "BrandColors", "MockupPalette", "BadgeTheme",
    "SwitchTheme", "Padding", "Typography", "Size", "Borders", "Gradients",
)


def test_every_theme_token_referenced_in_the_code_exists():
    import ast
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2]
    missing = set()
    for folder in ("frontend", "backend", "bootstrap"):
        for path in (root / folder).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)):
                    continue
                owner = node.value.id
                if owner in _THEME_NAMES and not hasattr(getattr(theme_module, owner), node.attr):
                    missing.add(f"{path.relative_to(root).as_posix()}:{node.lineno} {owner}.{node.attr}")
    assert not missing, "Undefined theme tokens: " + ", ".join(sorted(missing))
