# Walkthrough - WT-1.4.9_04: Interactive i18n Manager & Audit CLI Tool

## Summary
Created a unified interactive CLI script [`tests/i18n_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/tests/i18n_manager.py) to inspect, audit, synchronize, and alphabetize internationalization files (`en.json` and `es.json`).

---

## Interactive Menu Features
1. **Auditar claves sin uso en el código**: Scans `locales/en.json` against `frontend/`, `backend/`, and `main.py` using both exact string matching and dynamic pattern matching (`i18n.get(...)`).
2. **Verificar paridad entre idiomas**: Compares key sets between `locales/en.json` and `locales/es.json` to flag missing keys in either direction.
3. **Ordenar alfabéticamente**: Recursively orders all dictionary keys in `locales/en.json` and `locales/es.json`.
4. **Limpiar claves sin uso y sincronizar**: Automatically purges dead keys and aligns both JSON files.

---

## Files Created
- [`tests/i18n_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/tests/i18n_manager.py)

---

## Verification & Usage
- Tested via `.venv\Scripts\python.exe tests/i18n_manager.py`
- Confirmed full Windows console compatibility (ASCII fallbacks for code pages without UTF-8 support).
- All 35 pytest unit tests pass cleanly (`35 passed in 8.41s`).
