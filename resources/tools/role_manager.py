# resources\tools\role_manager.py

from importlib import import_module as _import_module
from pathlib import Path as _Path
import sys as _sys

_project_root = _Path(__file__).resolve().parents[2]
if str(_project_root) not in _sys.path:
    _sys.path.insert(0, str(_project_root))

_canonical = _import_module("resources.tools.frontend_qss_role_state_auditor")
for _name, _value in vars(_canonical).items():
    if not _name.startswith("__"):
        globals()[_name] = _value

if __name__ == "__main__":
    raise SystemExit(_canonical.main())
