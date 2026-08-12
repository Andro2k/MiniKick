# Walkthrough WT-1.5.0_06: Position & Volume Columns in Rewards Table

## Summary
Added **Posición** and **Volumen (%)** columns to the rewards table in `RewardsView`, updating all locale files (`locales/es.json`, `locales/en.json`) and expanding the table layout to 5 structured columns.

## Key Changes

### 1. Internationalization ([locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json), [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) & [default_en_locale.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/default_en_locale.py))
- Added `col_pos`, `col_volume`, and `pos_random` keys to `rewards.table` dictionary in all locale JSON and python fallback files.

### 2. Rewards View ([rewards_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py))
- Expanded table headers to 5 columns: `Recompensa`, `Archivo`, `Posición`, `Volumen`, `Acciones`.
- Configured column 2 (**Posición**) to display `X: {x}, Y: {y}` or `Aleatorio` when random positioning is enabled.
- Configured column 3 (**Volumen**) to display formatted audio percentage (e.g. `100%`, `80%`).
- Shifted action cell buttons (Play, Edit, Delete) to column 4 with fixed 140px width.

## Big-O & Architectural Impact
- **Architecture**: Maintains Separation of Responsibilities; presentation formats coordinates and percentage without altering backend storage.
- **Performance**: $O(n)$ row iteration during table population pass.
