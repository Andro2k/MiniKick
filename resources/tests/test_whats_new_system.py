# resources\tests\test_whats_new_system.py

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from PySide6.QtWidgets import QApplication
from backend.services.system.translation_service import TranslationService
from backend.services.system.updater_service import GithubUpdateProvider
from backend.services.system.whats_new_service import (
    WhatsNewService,
    _resolve_release_notes_path,
    parse_release_notes,
    parse_release_notes_content,
)
from frontend.dialogs.whats_new_dialog import WhatsNewDialog
from frontend.navigation.sidebar_component import Sidebar


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

class MockSettingsStorage:
    def __init__(self):
        self._data = {}

    def get_setting(self, key, default=None):
        return self._data.get(key, default)

    def set_setting(self, key, value):
        self._data[key] = value

    def load_string(self, key, default=None):
        return self._data.get(key, default)

    def save_string(self, key, value):
        self._data[key] = value

    def delete_key_prefix(self, prefix: str):
        to_del = [k for k in self._data if k.startswith(prefix)]
        for k in to_del:
            del self._data[k]

def test_whats_new_service_lifecycle():
    storage = MockSettingsStorage()
    storage.save_string("seen_badges_v1.5.0", '["Chat"]')

    service = WhatsNewService(storage, app_version="1.6.1")

    assert "seen_badges_v1.5.0" not in storage._data

    assert service.is_first_launch() is True
    assert service.should_show_modal() is True

    highlights = service.get_highlights()
    assert len(highlights) > 0
    assert any(h["target_section"] == "Chat" for h in highlights)

    unseen = service.get_unseen_badges()
    assert "Chat" in unseen
    assert "Widgets" in unseen

    service.mark_section_seen("Chat")
    raw_saved = storage.load_string(WhatsNewService.SETTING_STATE)
    saved_payload = json.loads(raw_saved)
    assert saved_payload["version"] == "1.6.1"
    assert "Chat" in saved_payload["seen"]

    unseen_after = service.get_unseen_badges()
    assert "Chat" not in unseen_after
    assert "Widgets" in unseen_after

    service.mark_version_seen()
    assert service.is_first_launch() is False
    assert service.should_show_modal() is False
    saved_final = json.loads(storage.load_string(WhatsNewService.SETTING_STATE))
    assert saved_final["modal_seen"] is True

def test_whats_new_service_version_reset():
    storage = MockSettingsStorage()
    storage.save_string(
        WhatsNewService.SETTING_STATE,
        json.dumps({"version": "1.6.0", "modal_seen": True, "seen": ["Chat", "Widgets"]})
    )

    service = WhatsNewService(storage, app_version="1.6.1")

    unseen = service.get_unseen_badges()
    assert "Chat" in unseen
    assert "Widgets" in unseen
    assert service.should_show_modal() is True

def test_parse_release_notes_table(tmp_path: Path):
    doc_dir = tmp_path / "docs" / "walkthroughs" / "v1.9.9"
    doc_dir.mkdir(parents=True)
    rn_file = doc_dir / "Release_Notes_v1.9.9.md"
    rn_file.write_text(
        """# Notas de la Versión — MiniKick v1.9.9

## Novedades

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Chat | Filtros Inteligentes | Moderación de chat avanzada. | Mayor tranquilidad. |
| Widgets | Contador de Subs | Meta en pantalla para OBS. | Motivación para el stream. |
| Comandos | Disparador por Audio | Ejecución por sonido. | Diversión en vivo. |
| Developer | Telemetría Local | Monitoreo de latencia OBS. | Diagnóstico preciso. |

## Mejoras
- Algo de mejoras
""",
        encoding="utf-8"
    )

    items = parse_release_notes("1.9.9", base_dir=tmp_path)
    assert len(items) == 4
    assert items[0]["target_section"] == "Chat"
    assert items[0]["title"] == "Filtros Inteligentes"
    assert items[0]["desc"] == "Moderación de chat avanzada."
    assert items[1]["target_section"] == "Widgets"
    assert items[2]["target_section"] == "Comandos"
    assert items[3]["target_section"] == "Developer"

def test_sidebar_badges_and_toggle_reactivity(qapp):
    i18n = TranslationService()
    sidebar = Sidebar(i18n, app_version="1.6.1")
    sidebar.add_tab("Chat", "dialog-filled.svg", is_active=False)
    sidebar.add_tab("Widgets", "widget-add-filled.svg", is_active=False)
    sidebar.show()

    chat_btn = [b for b in sidebar.nav_buttons if b.property("view_name") == "Chat"][0]
    assert hasattr(chat_btn, "badge_label")
    assert not chat_btn.badge_label.isVisible()

    sidebar.set_tab_badge("Chat", True)
    assert not chat_btn.badge_label.isHidden()

    sidebar.is_expanded = True
    sidebar._update_toggle_badge()
    assert sidebar.toggle_badge.isHidden()

    sidebar.is_expanded = False
    sidebar._update_toggle_badge()
    assert not sidebar.toggle_badge.isHidden()

    emitted = []
    sidebar.section_viewed.connect(lambda name: emitted.append(name))
    sidebar._on_tab_clicked(chat_btn)

    assert "Chat" in emitted
    assert chat_btn.badge_label.isHidden()
    assert sidebar.toggle_badge.isHidden()
    sidebar.deleteLater()

def test_whats_new_dialog_creation_dynamic_and_i18n(qapp):
    i18n = TranslationService()
    highlights = [
        {
            "icon": "shield-filled.svg",
            "title": "Filtros Anti-Spam",
            "desc": "Configuración directa desde el chat",
            "target_section": "Chat",
        },
        {
            "icon": "globe-filled.svg",
            "title": "Servidor de Overlays",
            "desc": "Emisión ultrarrápida en OBS",
            "target_section": "Widgets",
        }
    ]
    dialog = WhatsNewDialog(
        i18n=i18n,
        highlights=highlights,
        is_first_launch=False,
        app_version="1.6.1"
    )
    assert dialog is not None
    assert dialog.title_lbl is not None
    assert len(dialog.highlights) == 2
    dialog.deleteLater()

def test_get_highlights_all_items(tmp_path):
    doc_dir = tmp_path / "docs" / "walkthroughs" / "v2.0.0"
    doc_dir.mkdir(parents=True)
    rn_file = doc_dir / "Release_Notes_v2.0.0.md"
    rn_file.write_text(
        """# Notas de la Versión — MiniKick v2.0.0

## Novedades

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Chat | Item 1 | Desc 1 | Ben 1 |
| Widgets | Item 2 | Desc 2 | Ben 2 |
| Comandos | Item 3 | Desc 3 | Ben 3 |
| Developer | Item 4 | Desc 4 | Ben 4 |
| Dashboard | Item 5 | Desc 5 | Ben 5 |
""",
        encoding="utf-8"
    )
    storage = MockSettingsStorage()
    service = WhatsNewService(storage, app_version="2.0.0", base_dir=tmp_path)
    highlights = service.get_highlights()
    assert len(highlights) == 5
    assert [h["target_section"] for h in highlights] == ["Chat", "Widgets", "Comandos", "Developer", "Dashboard"]

def test_parse_release_notes_content_pure():
    content = """# Release Notes v1.6.2
## Novedades

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Chat | Watchdog de Heartbeat | Envío proactivo de pings Pusher. | Conexión sin desconexiones silenciosas. |
| Widgets | Top Chatters Reactivo | Actualización inmediata de métricas. | Datos precisos en OBS. |

## Mejoras
- Algo de mejoras
"""
    items = parse_release_notes_content(content)
    assert len(items) == 2
    assert items[0]["title"] == "Watchdog de Heartbeat"
    assert items[0]["target_section"] == "Chat"
    assert items[0]["desc"] == "Envío proactivo de pings Pusher."
    assert items[1]["target_section"] == "Widgets"

def test_resolve_release_notes_path_with_meipass(tmp_path, monkeypatch):
    doc_dir = tmp_path / "docs" / "walkthroughs" / "v1.6.2"
    doc_dir.mkdir(parents=True)
    rn_file = doc_dir / "Release_Notes_v1.6.2.md"
    rn_file.write_text("dummy", encoding="utf-8")

    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    resolved = _resolve_release_notes_path("1.6.2")
    assert resolved is not None
    assert resolved.samefile(rn_file)

def test_whats_new_service_sqlite_highlight_caching():
    storage = MockSettingsStorage()
    cached_highlights = [
        {"icon": "star-filled.svg", "title": "Test Cached", "desc": "Desc", "target_section": "Chat"}
    ]
    storage.save_string(
        WhatsNewService.SETTING_STATE,
        json.dumps({
            "version": "9.9.9",
            "modal_seen": False,
            "seen": [],
            "highlights": cached_highlights
        })
    )

    service = WhatsNewService(storage, app_version="9.9.9", base_dir=Path("/non_existent"))
    highlights = service.get_highlights()
    assert len(highlights) == 1
    assert highlights[0]["title"] == "Test Cached"

def test_whats_new_service_load_highlights_from_content():
    storage = MockSettingsStorage()
    service = WhatsNewService(storage, app_version="9.9.9", base_dir=Path("/non_existent"))
    assert len(service.get_highlights()) == 0

    markdown = """## Novedades

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Developer | Telemetría Local | Diagnóstico en tiempo real. | Depuración ágil. |
"""
    loaded = service.load_highlights_from_content(markdown)
    assert len(loaded) == 1
    assert loaded[0]["title"] == "Telemetría Local"
    assert len(service.get_highlights()) == 1

    state = json.loads(storage.load_string(WhatsNewService.SETTING_STATE))
    assert len(state.get("highlights", [])) == 1
    assert state["highlights"][0]["title"] == "Telemetría Local"

def test_github_update_provider_fetch_release_by_tag_and_version():
    provider = GithubUpdateProvider(repo_owner="TestOwner", repo_name="TestRepo")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "tag_name": "v1.6.2",
        "name": "MiniKick v1.6.2",
        "published_at": "2026-09-30T20:00:00Z",
        "body": "## Novedades\n| Sección | Característica | Descripción | Beneficio |\n|---|---|---|---|\n| Chat | Heartbeat | Fix | Mejor |",
        "html_url": "https://github.com/TestOwner/TestRepo/releases/tag/v1.6.2",
        "author": {"login": "tester"},
        "assets": []
    }

    with patch("requests.get", return_value=mock_resp) as mock_get:
        release = provider.fetch_release_by_tag("v1.6.2")
        assert release is not None
        assert release["tag_name"] == "v1.6.2"
        assert "tester" == release["author"]
        assert "Heartbeat" in release["body"]

        ver_release = provider.fetch_release_for_version("1.6.2")
        assert ver_release is not None
        assert ver_release["tag_name"] == "v1.6.2"
