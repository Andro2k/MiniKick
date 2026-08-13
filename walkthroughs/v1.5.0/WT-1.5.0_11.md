# Walkthrough - WT-1.5.0_11: Centralized Swatch Theme Stylesheet Generation

## Summary
Refactored inline QSS `setStyleSheet` calls in `rewards_dialog.py` to use a centralized helper function `get_swatch_qss` in `frontend/common/theme.py`, eliminating hardcoded CSS strings and enforcing consistent theme constants (`COLOR_NEUTRAL_700`, `RADIUS_SM`, `RADIUS_MD`).

---

## Changes Made

### 1. Theme Configuration (`frontend/common/theme.py`)
- Created `get_swatch_qss(bg_color: str, border_width: int = 1, radius: int = RADIUS_SM) -> str` using centralized tokens:
  - `COLOR_NEUTRAL_700` (`#3F3F46`) for swatch borders.
  - `RADIUS_SM` (`6px`) for preset swatches and `RADIUS_MD` (`9px`) for the main swatch button.

### 2. Dialog Component (`frontend/dialogs/rewards_dialog.py`)
- Removed hardcoded inline `setStyleSheet` strings (`f"background-color: {hex_code}; border: 1px solid #475569; border-radius: 4px;"` and `f"background-color: {hex_code}; border: 2px solid #475569; border-radius: 6px;"`).
- Replaced with `get_swatch_qss(hex_code, border_width=1, radius=RADIUS_SM)` and `get_swatch_qss(hex_code, border_width=2, radius=RADIUS_MD)`.

---

## Verification Results

### Automated Tests
- Executed unit tests using `.venv\Scripts\pytest`:
  - Result: `35 passed in 8.10s` (100% pass rate).

### Functionality Verified
- Preset color swatches and the primary color swatch button render with consistent theme borders and border radii from `theme.py`.
