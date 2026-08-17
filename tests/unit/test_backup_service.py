# tests\unit\test_backup_service.py

import json
import os
import tempfile
from backend.services.system.backup_service import BackupService

class DummySettingsStorage:
    def __init__(self, initial=None):
        self.data = initial or {}

    def get_all(self):
        return dict(self.data)

    def load_string(self, key, default=""):
        return self.data.get(key, default)

    def save_all(self, settings):
        self.data.update(settings)

class DummyRewardsStorage:
    def __init__(self, initial=None):
        self.data = initial or {}

    def load_all(self):
        return dict(self.data)

    def save_all(self, rewards):
        self.data = dict(rewards)

class DummyCommandsStorage:
    def __init__(self, initial=None):
        self.data = initial or []

    def load_all(self):
        return list(self.data)

    def save_command(self, trigger, response, is_active=True, cooldown=5, aliases="", is_regex=False, permission="everyone"):
        self.data.append({
            "trigger": trigger,
            "response": response,
            "is_active": is_active,
            "cooldown": cooldown,
            "aliases": aliases,
            "is_regex": is_regex,
            "permission": permission
        })

class DummySpamStorage:
    def __init__(self, initial=None):
        self.data = initial or {}

    def load_all(self):
        return dict(self.data)

    def save_filter(self, f_id, config):
        self.data[f_id] = config

class DummyScheduleStorage:
    def __init__(self, initial=None):
        self.data = initial or []

    def load_all(self):
        return list(self.data)

    def save(self, name, date_str, time_str, target_platform, title, kick_category_id, kick_category_name, twitch_category_id, twitch_category_name, is_active=True):
        self.data.append({
            "name": name,
            "date_str": date_str,
            "time_str": time_str,
            "target_platform": target_platform,
            "title": title,
            "kick_category_id": kick_category_id,
            "kick_category_name": kick_category_name,
            "twitch_category_id": twitch_category_id,
            "twitch_category_name": twitch_category_name,
            "is_active": is_active
        })

def test_backup_service_export_and_import_with_bytes():
    raw_png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRtest_image_bytes"
    
    settings_st = DummySettingsStorage({"tts_enabled": True, "overlay_session_token": "secret_token_123"})
    rewards_st = DummyRewardsStorage({
        "gnomo": {
            "filepath": "C:/Videos/gnomo.mp4",
            "volume": 1.0,
            "scale": 0.5,
            "thumbnail_bytes": raw_png_bytes
        }
    })
    commands_st = DummyCommandsStorage([{"trigger": "!discord", "response": "https://discord.gg/test"}])
    spam_st = DummySpamStorage({"caps": {"enabled": True, "limit": 70}})
    sched_st = DummyScheduleStorage([{"name": "Stream Pro", "date_str": "2026-08-20", "time_str": "20:00", "target_platform": "kick", "title": "Gaming Live"}])

    service = BackupService(
        settings_storage=settings_st,
        rewards_storage=rewards_st,
        commands_storage=commands_st,
        spam_storage=spam_st,
        schedule_storage=sched_st
    )

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        filepath = os.path.join(tmpdir, "backup.json")
        success = service.export_to_json(filepath)
        assert success is True
        assert os.path.exists(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "secret_token_123" not in json.dumps(data)
        assert data["settings"]["tts_enabled"] is True
        assert "thumbnail_bytes" in data["rewards"]["gnomo"]
        assert isinstance(data["rewards"]["gnomo"]["thumbnail_bytes"], str)

        new_settings_st = DummySettingsStorage({"overlay_session_token": "preserved_local_token"})
        new_rewards_st = DummyRewardsStorage()
        new_commands_st = DummyCommandsStorage()
        new_spam_st = DummySpamStorage()
        new_sched_st = DummyScheduleStorage()

        new_service = BackupService(
            settings_storage=new_settings_st,
            rewards_storage=new_rewards_st,
            commands_storage=new_commands_st,
            spam_storage=new_spam_st,
            schedule_storage=new_sched_st
        )

        import_success = new_service.import_from_json(filepath)
        assert import_success is True

        assert new_settings_st.data["tts_enabled"] is True
        assert new_settings_st.data["overlay_session_token"] == "preserved_local_token"
        
        restored_thumbnail = new_rewards_st.data["gnomo"]["thumbnail_bytes"]
        assert isinstance(restored_thumbnail, bytes)
        assert restored_thumbnail == raw_png_bytes

        assert len(new_commands_st.data) == 1
        assert new_commands_st.data[0]["trigger"] == "!discord"
        assert len(new_sched_st.data) == 1
        assert new_sched_st.data[0]["name"] == "Stream Pro"
