# Walkthrough WT-1.5.0_07: Table Item Count Display Across Views

## Summary
Updated `CommandView`, `RewardsView`, and `TimersView` to display the total number of items in their respective table card headers (e.g. `Comandos Personalizados (N)`), providing consistent visual feedback across all management tables in MiniKick.

## Key Changes

### 1. Commands View ([command_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/command_view.py))
- Dynamically updates table card header title with total command count upon rendering rows.

### 2. Rewards View ([rewards_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py))
- Dynamically updates table card header title with total linked rewards count upon populating table.

### 3. Timers View ([timers_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/timers_view.py))
- Dynamically updates table card header title with total active/inactive timers count upon populating table.

## Big-O & Architectural Impact
- **Architecture**: Reuses existing UI contracts (`lbl_title`) and i18n translation keys cleanly.
- **Performance**: $O(1)$ string formatting step during table updates.
