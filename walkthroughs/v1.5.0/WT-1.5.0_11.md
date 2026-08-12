# Walkthrough WT-1.5.0_11: Enlarged Illustration Sizing for LogView & AlreadyRunningDialog

## Summary
Increased the minimum/maximum bounds and reduced the container size offsets for `LogView` and `AlreadyRunningDialog` so their illustrations expand to match the visual scale of other main views.

## Key Changes

### 1. Log View ([log_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/log_view.py))
- `min_size`: `160`
- `max_size`: `320`
- `size_offset`: `240`

### 2. Already Running Dialog ([already_running_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/already_running_dialog.py))
- Dialog height extended to `400px`.
- `min_size`: `160`, `max_size`: `320`, `size_offset`: `180`.
- Implemented `showEvent()` to trigger dynamic sizing calculation on dialog open.

## Big-O & Performance
- Zero impact. Layout calculations remain $O(1)$.
