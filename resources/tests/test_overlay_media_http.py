# resources\tests\test_overlay_media_http.py
"""Pruebas HTTP reales de /user_media y /media contra el servidor de overlays."""

import base64
import http.client
import socket

import pytest

from backend.services.overlay.overlay_manager import OverlayServerManager


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def manager():
    server = OverlayServerManager(port=_free_port())
    assert server.start()
    yield server
    server.stop()


def _get(manager, url: str, headers: dict | None = None) -> tuple[int, bytes, dict]:
    conn = http.client.HTTPConnection("127.0.0.1", manager.port, timeout=5)
    conn.request("GET", url, headers=headers or {})
    resp = conn.getresponse()
    body = resp.read()
    result = (resp.status, body, dict(resp.getheaders()))
    conn.close()
    return result


def _user_media_url(manager, root, name: str) -> str:
    b64_dir = base64.urlsafe_b64encode(str(root).encode("utf-8")).decode("ascii")
    return f"/user_media/{manager.session_token}/{b64_dir}/{name}"


def test_user_media_serves_web_assets_but_not_other_files_in_the_folder(manager, tmp_path):
    (tmp_path / "alert.html").write_text("<p>ok</p>", encoding="utf-8")
    (tmp_path / "pic.png").write_bytes(b"\x89PNG")
    (tmp_path / "secret.env").write_text("TOKEN=1", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("private", encoding="utf-8")
    manager.register_media_dir(str(tmp_path))

    assert _get(manager, _user_media_url(manager, tmp_path, "alert.html"))[0] == 200
    assert _get(manager, _user_media_url(manager, tmp_path, "pic.png"))[0] == 200
    assert _get(manager, _user_media_url(manager, tmp_path, "secret.env"))[0] == 403
    assert _get(manager, _user_media_url(manager, tmp_path, "notes.txt"))[0] == 403


def test_media_suffix_range_returns_the_last_bytes_of_the_file(manager, tmp_path):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(bytes(range(256)) * 4)
    manager.register_media_file(str(clip))
    url = f"/media?path={clip}&token={manager.session_token}"

    status, body, headers = _get(manager, url, {"Range": "bytes=-100"})

    assert status == 206
    assert headers["Content-Range"] == "bytes 924-1023/1024"
    assert body == clip.read_bytes()[-100:]


def test_media_open_and_closed_ranges_keep_working(manager, tmp_path):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(bytes(range(256)) * 4)
    manager.register_media_file(str(clip))
    url = f"/media?path={clip}&token={manager.session_token}"

    assert _get(manager, url, {"Range": "bytes=10-19"})[1] == clip.read_bytes()[10:20]
    assert _get(manager, url, {"Range": "bytes=1000-"})[1] == clip.read_bytes()[1000:]
