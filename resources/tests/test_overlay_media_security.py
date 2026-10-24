# resources\tests\test_overlay_media_security.py

import os
from types import SimpleNamespace
from backend.services.overlay.overlay_routes import _is_allowed_media_dir, _is_allowed_media_file, _is_within, canonical_media_path


def _manager(files=(), dirs=()):
    return SimpleNamespace(
        allowed_media_files={canonical_media_path(str(p)) for p in files},
        allowed_media_dirs={canonical_media_path(str(p)) for p in dirs},
    )

def test_is_within_is_sibling_safe(tmp_path):
    base = tmp_path / "overlays"
    base.mkdir()
    sibling = tmp_path / "overlays_x"
    sibling.mkdir()

    assert _is_within(str(base), str(base / "file.mp4"))
    assert not _is_within(str(base), str(sibling / "file.mp4"))

def test_only_the_registered_file_is_allowed(tmp_path):
    root = tmp_path / "media"
    root.mkdir()
    clip = root / "clip.mp4"
    clip.write_bytes(b"data")
    neighbor = root / "other.mp4"
    neighbor.write_bytes(b"data")

    manager = _manager(files=[clip])

    assert _is_allowed_media_file(manager, str(clip))
    assert not _is_allowed_media_file(manager, str(neighbor))
    assert not _is_allowed_media_file(manager, str(tmp_path / "win.ini"))

def test_registered_file_does_not_open_its_folder(tmp_path):
    root = tmp_path / "media"
    root.mkdir()
    clip = root / "clip.mp4"
    clip.write_bytes(b"data")

    manager = _manager(files=[clip])

    assert not _is_allowed_media_dir(manager, str(root))

def test_media_checks_without_registrations_are_closed(tmp_path):
    manager = _manager()
    assert not _is_allowed_media_file(manager, str(tmp_path))
    assert not _is_allowed_media_dir(manager, str(tmp_path))

def test_path_traversal_is_blocked(tmp_path):
    root = tmp_path / "media"
    root.mkdir()
    clip = root / "clip.mp4"
    clip.write_bytes(b"data")
    secret = tmp_path / "secret.txt"
    secret.write_text("classified", encoding="utf-8")

    manager = _manager(files=[clip], dirs=[root])
    sneaky = os.path.join(str(root), "..", "secret.txt")

    assert not _is_allowed_media_file(manager, sneaky)
    assert not _is_within(str(root), os.path.realpath(sneaky))
