# resources\tests\test_commands_sanitization.py

import os
import tempfile
import pytest
from backend.utils.command_utils import sanitize_command_trigger, validate_trigger_prefix, is_complete_valid_trigger
from backend.database.database_manager import DatabaseManager
from backend.database.commands_storage import SQLiteCommandsStorage
from backend.services.chat.commands_service import CommandService


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_name=path)
    yield db
    try:
        db.close_all_connections()
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

def test_sanitize_command_trigger():
    assert sanitize_command_trigger("!categoria 1") == "!categoria_1"
    assert sanitize_command_trigger("!mi comando especial") == "!mi_comando_especial"
    assert sanitize_command_trigger("!multiple   spaces") == "!multiple_spaces"
    assert sanitize_command_trigger("!Categoria") == "!categoria"
    assert sanitize_command_trigger("!COMMAND") == "!command"
    assert sanitize_command_trigger("categoria 1") == "!categoria_1"
    assert sanitize_command_trigger("test") == "!test"
    assert sanitize_command_trigger("!test-command") == "!test-command"
    assert sanitize_command_trigger("!test_command") == "!test_command"
    assert sanitize_command_trigger("!test__command") == "!test_command"
    assert sanitize_command_trigger("!test!@#$%^&*()cmd") == "!testcmd"
    assert sanitize_command_trigger("") == ""
    assert sanitize_command_trigger("   ") == ""

def test_validate_trigger_prefix():
    assert validate_trigger_prefix("") is True
    assert validate_trigger_prefix("!") is True
    assert validate_trigger_prefix("!categoria") is True
    assert validate_trigger_prefix("!categoria_1") is True
    assert validate_trigger_prefix("!categoria-1") is True
    assert validate_trigger_prefix("!categoria 1") is False
    assert validate_trigger_prefix("!Categoria") is False
    assert validate_trigger_prefix("categoria") is False
    assert validate_trigger_prefix("!cat@#$") is False

def test_is_complete_valid_trigger():
    assert is_complete_valid_trigger("") is False
    assert is_complete_valid_trigger("!") is False
    assert is_complete_valid_trigger("!c") is True
    assert is_complete_valid_trigger("!categoria_1") is True
    assert is_complete_valid_trigger("!categoria 1") is False

def test_sqlite_commands_storage_update_trigger(temp_db):
    storage = SQLiteCommandsStorage(temp_db)
    
    storage.save_command(
        trigger="!antiguo comando",
        response="Respuesta de prueba",
        is_active=True,
        cooldown=5,
        aliases="",
        is_regex=False
    )
    
    cmd_before = storage.get_command_by_trigger("!antiguo comando")
    assert cmd_before is not None
    assert cmd_before["trigger"] == "!antiguo comando"

    success = storage.update_command_trigger("!antiguo comando", "!antiguo_comando")
    assert success is True

    assert storage.get_command_by_trigger("!antiguo comando") is None
    cmd_after = storage.get_command_by_trigger("!antiguo_comando")
    assert cmd_after is not None
    assert cmd_after["trigger"] == "!antiguo_comando"
    assert cmd_after["response"] == "Respuesta de prueba"

def test_command_service_legacy_migration(temp_db):
    storage = SQLiteCommandsStorage(temp_db)
    
    storage.save_command(
        trigger="!Categoria 1",
        response="Respuesta categoria",
        is_active=True,
        cooldown=5,
        aliases="",
        is_regex=False
    )
    
    service = CommandService(storage)
    
    migrated_cmd = service.get_command_by_trigger("!categoria_1")
    assert migrated_cmd is not None
    assert migrated_cmd["trigger"] == "!categoria_1"
    assert migrated_cmd["response"] == "Respuesta categoria"

    all_cmds = service.get_all_commands()
    triggers = [c["trigger"] for c in all_cmds]
    assert "!categoria_1" in triggers
    assert "!Categoria 1" not in triggers

def test_command_service_save_command_auto_sanitizes(temp_db):
    storage = SQLiteCommandsStorage(temp_db)
    service = CommandService(storage)

    service.save_command(
        trigger="!Nuevo Comando 123",
        response="Test response",
        is_active=True,
        cooldown=10,
        aliases="",
        is_regex=False,
        permission="everyone"
    )

    cmd = service.get_command_by_trigger("!nuevo_comando_123")
    assert cmd is not None
    assert cmd["trigger"] == "!nuevo_comando_123"
