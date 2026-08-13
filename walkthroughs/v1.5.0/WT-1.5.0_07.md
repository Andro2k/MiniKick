# Walkthrough - WT-1.5.0_07: Complete Reward Info Editing & Single-Row User Input Layout

## Summary
Updated `RewardsConfigWizard` to support editing **all** reward properties (Title, Points Cost, Description, Background Color, User Input Requirement, Media File, Volume, and OBS layout settings) in Edit Mode, and aligned the *"Requiere texto del espectador"* switch into a single horizontal row.

---

## Changes Made

### 1. Dialog Component (`frontend/dialogs/rewards_dialog.py`)
- **Single-Row User Input Switch**:
  - Implemented `_build_user_input_row()` using a horizontal layout (`QHBoxLayout`):
    `[ Label: "Requiere texto del espectador" ] ---- stretch ---- [ ModernSwitch ]`
  - Replaced stacked vertical layout with single-row layout across both Creation Mode and Edit Mode.

- **Full Data Editing Support in Edit Mode (`is_edit_mode`)**:
  - Added form fields to Edit Mode:
    - Reward Title (`txt_edit_title`)
    - Channel Points Cost (`spin_edit_cost`)
    - Description (`txt_edit_desc`)
    - Visual Color Picker (`_build_color_picker()`)
    - Single-row User Input switch (`chk_user_input`)
  - Updated `_load_existing_data(config)` to populate all fields (`cost`, `description`, `background_color`, `is_user_input_required`, `filepath`, `volume`, `pos_x`, `pos_y`, `scale`, `is_random_pos`).
  - Updated `get_config_data()` to export all fields in both Create Mode and Edit Mode.

---

## Verification Results

### Automated Tests
- Executed unit tests using `.venv\Scripts\pytest`:
  - Result: All test suites PASSED cleanly.

### Functionality Verified
- *"Requiere texto del espectador"* label and toggle are rendered side-by-side on a single row.
- Editing an existing reward displays all fields (Title, Cost, Description, Color Picker, User Input switch, Media path, Volume, OBS settings).
- Saving an edited reward updates and persists all fields in storage.
