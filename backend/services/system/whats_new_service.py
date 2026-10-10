# backend/services/system/whats_new_service.py

import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from backend.config.version import APP_VERSION
from backend.utils.json_utils import fast_dumps, fast_loads

logger = logging.getLogger("minikick.system.whats_new")

_SECTION_DEFAULT_ICONS: Dict[str, str] = {
    "Dashboard": "element-filled.svg",
    "Chat": "dialog-filled.svg",
    "Stream Info": "calendar-days-filled.svg",
    "Comandos": "chat-square-code-filled.svg",
    "Timers": "alarm-filled.svg",
    "Music": "music-notes-filled.svg",
    "Widgets": "widget-add-filled.svg",
    "Triggers": "treasure-chest-filled.svg",
    "Alerts": "megaphone-filled.svg",
    "Settings": "gear-filled.svg",
    "Developer": "file-text-filled.svg",
}


def _resolve_feature_icon(section: str, feature: str) -> str:
    feat_lower = feature.lower()
    if "spam" in feat_lower or "seguridad" in feat_lower:
        return "shield-filled.svg"
    if "overlay" in feat_lower or "obs" in feat_lower or "red" in feat_lower:
        return "globe-filled.svg"
    if "log" in feat_lower or "registro" in feat_lower or "conexión" in feat_lower:
        return "file-text-filled.svg"
    if "bienvenida" in feat_lower or "insignia" in feat_lower:
        return "star-filled.svg"
    return _SECTION_DEFAULT_ICONS.get(section, "star-filled.svg")


def _resolve_release_notes_path(version_str: str, base_dir: Optional[Path] = None) -> Optional[Path]:
    norm_ver = version_str.strip().lstrip("vV") if version_str else ""
    if not norm_ver:
        return None

    rel_doc = Path("docs") / "walkthroughs" / f"v{norm_ver}" / f"Release_Notes_v{norm_ver}.md"

    if base_dir is not None:
        p = base_dir / rel_doc
        if p.is_file():
            return p
    if hasattr(sys, "_MEIPASS"):
        meipass_p = Path(sys._MEIPASS) / rel_doc
        if meipass_p.is_file():
            return meipass_p
    exe_dir = Path(sys.executable).resolve().parent
    exe_p = exe_dir / rel_doc
    if exe_p.is_file():
        return exe_p
    internal_p = exe_dir / "_internal" / rel_doc
    if internal_p.is_file():
        return internal_p
    repo_root = Path(__file__).resolve().parents[3]
    repo_p = repo_root / rel_doc
    if repo_p.is_file():
        return repo_p

    return None


def parse_release_notes_content(content: str) -> List[Dict[str, str]]:
    if not content or not content.strip():
        return []

    match = re.search(r"##\s+Novedades\s*\n(.*?)(?=\n##\s+|\Z)", content, re.DOTALL | re.IGNORECASE)
    if not match:
        return []

    section_text = match.group(1)
    lines = [line.strip() for line in section_text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return []

    header_cols = [c.strip().lower() for c in lines[0].strip("|").split("|")]
    has_section_col = any("secci" in c or "módu" in c or "modu" in c for c in header_cols)

    highlights: List[Dict[str, str]] = []
    for line in lines[2:]:
        cols = [c.strip() for c in line.strip("|").split("|")]
        if not cols or not cols[0]:
            continue

        if has_section_col and len(cols) >= 3:
            target_sec = cols[0].strip()
            feature = cols[1].strip()
            desc = cols[2].strip()
        elif len(cols) >= 2:
            target_sec = "Dashboard"
            feature = cols[0].strip()
            desc = cols[1].strip()
        else:
            continue

        icon = _resolve_feature_icon(target_sec, feature)
        highlights.append({
            "icon": icon,
            "title": feature,
            "desc": desc,
            "target_section": target_sec,
        })

    return highlights


def parse_release_notes(version_str: str, base_dir: Optional[Path] = None) -> List[Dict[str, str]]:
    norm_ver = version_str.strip().lstrip("vV") if version_str else ""
    if not norm_ver:
        return []

    rn_path = _resolve_release_notes_path(norm_ver, base_dir)
    if not rn_path or not rn_path.is_file():
        logger.debug("[WhatsNew] Release notes not found for v%s", norm_ver)
        return []

    try:
        content = rn_path.read_text(encoding="utf-8")
        return parse_release_notes_content(content)
    except Exception as e:
        logger.error("[WhatsNew] Failed to read release notes at %s: %s", rn_path, e)
        return []


class WhatsNewService:
    SETTING_STATE = "whats_new_state"
    SETTING_LEGACY_BADGES_PREFIX = "seen_badges_v"

    def __init__(
        self,
        settings_storage: Any,
        app_version: str = APP_VERSION,
        base_dir: Optional[Path] = None,
    ):
        self.settings_storage = settings_storage
        self.raw_app_version = app_version or APP_VERSION
        self.app_version = self._normalize_version(self.raw_app_version)
        self.base_dir = base_dir
        self._parsed_highlights = parse_release_notes(self.app_version, self.base_dir)

        state = self._load_state()
        if not self._parsed_highlights:
            if state.get("version") == self.app_version and state.get("highlights"):
                self._parsed_highlights = state.get("highlights", [])
        elif self._parsed_highlights and not state.get("highlights"):
            state["highlights"] = self._parsed_highlights
            self._save_state(state)

        self._purge_legacy_keys()

    @staticmethod
    def _normalize_version(ver: str) -> str:
        return ver.strip().lstrip("vV") if ver else ""

    def _purge_legacy_keys(self) -> None:
        if hasattr(self.settings_storage, "delete_key_prefix"):
            try:
                self.settings_storage.delete_key_prefix(self.SETTING_LEGACY_BADGES_PREFIX)
            except Exception as e:
                logger.debug("[WhatsNew] Purge legacy keys error: %s", e)

    def _get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        if hasattr(self.settings_storage, "load_string"):
            return self.settings_storage.load_string(key, default)
        if hasattr(self.settings_storage, "get_setting"):
            return self.settings_storage.get_setting(key, default)
        return default

    def _set_setting(self, key: str, value: str) -> None:
        if hasattr(self.settings_storage, "save_string"):
            self.settings_storage.save_string(key, value)
        elif hasattr(self.settings_storage, "set_setting"):
            self.settings_storage.set_setting(key, value)

    def _load_state(self) -> Dict[str, Any]:
        raw = self._get_setting(self.SETTING_STATE, None)
        if raw is None:
            legacy_badges = self._get_setting("seen_feature_badges", None)
            legacy_version = self._get_setting("last_seen_app_version", None)
            if legacy_badges is not None or legacy_version is not None:
                seen_list = []
                if legacy_badges:
                    try:
                        data = fast_loads(legacy_badges)
                        if isinstance(data, dict):
                            seen_list = data.get("seen", [])
                        elif isinstance(data, list):
                            seen_list = data
                    except Exception:
                        pass
                migrated_ver = self._normalize_version(legacy_version) if legacy_version else self.app_version
                state = {
                    "version": migrated_ver,
                    "modal_seen": bool(legacy_version and migrated_ver == self.app_version),
                    "seen": seen_list,
                }
                self._save_state(state)
                return state
            return {}
        try:
            data = fast_loads(raw)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {}

    def _save_state(self, state: Dict[str, Any]) -> None:
        try:
            self._set_setting(self.SETTING_STATE, fast_dumps(state))
        except Exception as e:
            logger.error("[WhatsNew] Failed to save state: %s", e)

    def is_first_launch(self) -> bool:
        state = self._load_state()
        return not bool(state.get("version"))

    def should_show_modal(self) -> bool:
        state = self._load_state()
        stored_ver = self._normalize_version(state.get("version", ""))
        if not stored_ver:
            return True
        if stored_ver != self.app_version:
            return True
        return not state.get("modal_seen", False)

    def get_all_highlights(self) -> List[Dict[str, str]]:
        if self._parsed_highlights:
            return list(self._parsed_highlights)
        return []

    def get_highlights(self) -> List[Dict[str, str]]:
        return self.get_all_highlights()

    def set_highlights(self, highlights: List[Dict[str, str]]) -> None:
        if highlights:
            self._parsed_highlights = list(highlights)
            state = self._load_state()
            state["version"] = self.app_version
            state["highlights"] = self._parsed_highlights
            self._save_state(state)

    def load_highlights_from_content(self, content: str) -> List[Dict[str, str]]:
        highlights = parse_release_notes_content(content)
        if highlights:
            self.set_highlights(highlights)
        return highlights

    def get_unseen_badges(self) -> Set[str]:
        seen = self._get_seen_badges()
        all_highlights = self.get_all_highlights()
        target_sections = {h["target_section"] for h in all_highlights if "target_section" in h}
        return target_sections - seen

    def mark_section_seen(self, section_name: str) -> None:
        state = self._load_state()
        stored_ver = self._normalize_version(state.get("version", ""))
        if stored_ver != self.app_version:
            seen = [section_name]
            modal_seen = False
        else:
            seen = list(state.get("seen", []))
            if section_name not in seen:
                seen.append(section_name)
            modal_seen = state.get("modal_seen", False)
        state["version"] = self.app_version
        state["modal_seen"] = modal_seen
        state["seen"] = sorted(seen)
        if self._parsed_highlights and "highlights" not in state:
            state["highlights"] = self._parsed_highlights
        self._save_state(state)

    def mark_version_seen(self) -> None:
        state = self._load_state()
        stored_ver = self._normalize_version(state.get("version", ""))
        if stored_ver != self.app_version:
            seen = []
        else:
            seen = state.get("seen", [])
        state["version"] = self.app_version
        state["modal_seen"] = True
        state["seen"] = seen
        if self._parsed_highlights and "highlights" not in state:
            state["highlights"] = self._parsed_highlights
        self._save_state(state)

    def _get_seen_badges(self) -> Set[str]:
        state = self._load_state()
        stored_ver = self._normalize_version(state.get("version", ""))
        if stored_ver != self.app_version:
            return set()
        return set(state.get("seen", []))
