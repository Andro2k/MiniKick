# Walkthrough WT-1.5.0_12: Application Window Icon & Web Favicon Registration

## Summary
Fixed default Python executable icon issue in Windows Taskbar by registering a custom AppUserModelID, and added an SVG favicon to the OAuth login web page (`auth.html`).

## Key Changes

### 1. Windows Taskbar Icon ([main.py](file:///c:/Users/TheAn/Desktop/python/Kick/main.py))
- Executed `ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("andro2k.minikick.app.1.5")` during bootstrap.
- Ensures Windows attaches the `icon.ico` set via `app.setWindowIcon()` directly to the process in Taskbar and Alt+Tab menu.

### 2. OAuth Web Favicon ([auth.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/web/auth.html))
- Added embedded Kick green SVG favicon in `<head>` for browser tab display during authentication flows.

## Big-O & Performance
- Zero performance impact. Standard OS shell API call.
