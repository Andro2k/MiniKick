# MiniKick Audit Tools

This directory contains the project's command line audit tools. Canonical audit filenames use a scope prefix:

- `frontend_...`: scans the presentation/UI layer.
- `project_...`: scans backend and frontend, or validates a project-wide resource such as translations.
- `project_quality_suite.py`: runs the registered quality checks.

## Recommended commands

Run the fast static suite:

```powershell
python resources/tools/project_quality_suite.py --quick --verbose
```

Run the full suite, including runtime UI checks (Windows, requires PySide6):

```powershell
python resources/tools/project_quality_suite.py --verbose
```

## Audit coverage

| Canonical tool | Scope | What it checks |
|---|---|---|
| `project_architecture_boundary_auditor.py` | Backend and frontend | Layer boundaries, forbidden dependencies, and separation of responsibilities |
| `project_code_duplication_auditor.py` | Backend and frontend | Repeated statement sequences and AST clones |
| `project_dead_code_auditor.py` | Backend and frontend; selectable | Orphan Python files, unused symbols, and unused imports |
| `project_file_placement_auditor.py` | Backend and frontend | Canonical folder placement and file naming rules |
| `project_unused_parameter_auditor.py` | Backend and frontend; selectable | Unused parameters, base-class hooks, and Qt callback parameters |
| `project_translation_integrity_auditor.py` | Project translations and Python sources | Locale key parity, missing or unused keys, and placeholder parity |
| `project_icon_integrity_tool.py` | Backend, frontend, and app entry point | Missing, unused, and malformed icon assets; also supports explicit cleanup |
| `project_performance_profiler.py` | Backend and frontend | Runtime performance budgets and profiling scenarios |
| `frontend_hardcoded_text_auditor.py` | Frontend | UI strings that bypass the translation service |
| `frontend_design_token_auditor.py` | Frontend | Raw colors and style values that bypass theme tokens |
| `frontend_qss_role_state_auditor.py` | Frontend | QSS roles and states versus their widget use |
| `frontend_qt_signal_lifecycle_auditor.py` | Frontend | Signal connection patterns that can duplicate listeners or retain closures |
| `frontend_qt_window_lifecycle_auditor.py` | Frontend and bootstrap | Static parent checks plus isolated runtime checks for the visible splash and UI views; it does not launch `Application`/`MainWindowCore`, and `--static-only` cannot detect runtime-created windows |
| `frontend_layout_responsiveness_auditor.py` | Frontend | Layout flexibility, clipping, and view sizing |

There is no general backend-only suite today. Use project-wide checks for backend changes; `project_unused_parameter_auditor.py --target backend` narrows that specific analysis to the backend.

## Related checks and why they stay separate

Some checks belong to the same quality area but inspect different code constructs. The dead-code auditor checks files, symbols, and imports; the unused-parameter auditor checks function signatures and callback contracts. The translation-integrity auditor checks locale keys and placeholders; the hardcoded-text auditor finds UI literals that bypass translations. Design tokens and QSS roles likewise validate different parts of the UI theme contract. Keeping these scanners separate preserves focused reports and lets the quality suite run each independently.

## Commands that modify files

Most audit commands are read-only. `project_dead_code_auditor.py --clean-orphans` can delete source files, and `project_icon_integrity_tool.py --clean` can delete unused icon assets. Review their dry-run or report output before using cleanup options.
