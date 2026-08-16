# tests/unit/test_roles_integrity.py

import pytest
from tests.tools.role_manager import audit_codebase

def test_all_used_roles_exist_in_theme():
    report = audit_codebase()
    missing_roles = report.missing_roles
    
    if missing_roles:
        err_msg = [f"Found {len(missing_roles)} missing QSS role(s) used in frontend but not defined in theme.py:"]
        for role, occs in sorted(missing_roles.items()):
            err_msg.append(f"  • Role '{role}' used at:")
            for o in occs:
                err_msg.append(f"      - {o.file_path}:{o.line} -> {o.context}")
        pytest.fail("\n".join(err_msg))

def test_all_used_states_exist_in_theme():
    report = audit_codebase()
    missing_states = report.missing_states

    if missing_states:
        err_msg = [f"Found {len(missing_states)} missing QSS state(s) used in frontend but not defined in theme.py:"]
        for state, occs in sorted(missing_states.items()):
            err_msg.append(f"  • State '{state}' used at:")
            for o in occs:
                err_msg.append(f"      - {o.file_path}:{o.line} -> {o.context}")
        pytest.fail("\n".join(err_msg))
