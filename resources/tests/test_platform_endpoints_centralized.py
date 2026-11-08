# resources\\tests\\test_platform_endpoints_centralized.py

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2] / "backend"
CONFIG_DIR = BACKEND / "config"
API_HOSTS = ("api.kick.com", "id.kick.com", "id.twitch.tv", "api.twitch.tv", "pusher.com/app")


def test_platform_api_hosts_are_only_defined_in_backend_config():
    offenders = []
    for path in BACKEND.rglob("*.py"):
        if CONFIG_DIR in path.parents:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        offenders += [f"{path.relative_to(BACKEND)}: {host}" for host in API_HOSTS if host in text]
    assert not offenders, f"Endpoints fuera de backend/config: {offenders}"
