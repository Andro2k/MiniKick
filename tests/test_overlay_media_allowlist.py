# tests\test_overlay_media_allowlist.py

import os
import tempfile
import unittest
from types import SimpleNamespace

from backend.services.overlay.overlay_manager import OverlayServerManager
from backend.services.overlay.overlay_routes import _is_allowed_media_dir, _is_allowed_media_file


class MediaAllowlistTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = self._tmp.name
        self.downloads = os.path.join(root, "downloads")
        self.bundle = os.path.join(root, "bundle")
        os.makedirs(self.downloads)
        os.makedirs(self.bundle)
        self.reward = os.path.join(self.downloads, "reward.png")
        self.other = os.path.join(self.downloads, "secret.txt")
        self.page = os.path.join(self.bundle, "alert.html")
        for path in (self.reward, self.other, self.page):
            with open(path, "w", encoding="utf-8") as f:
                f.write("x")
        self.manager = OverlayServerManager(port=0, settings_storage=None)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_only_the_registered_file_is_served(self) -> None:
        self.manager.register_media_file(self.reward)
        self.assertTrue(_is_allowed_media_file(self.manager, self.reward))
        self.assertFalse(_is_allowed_media_file(self.manager, self.other))

    def test_registering_a_file_does_not_open_its_folder(self) -> None:
        self.manager.register_media_file(self.reward)
        self.assertFalse(_is_allowed_media_dir(self.manager, self.downloads))

    def test_traversal_to_unregistered_file_is_rejected(self) -> None:
        self.manager.register_media_file(self.reward)
        sneaky = os.path.join(self.downloads, "..", "downloads", "secret.txt")
        self.assertFalse(_is_allowed_media_file(self.manager, sneaky))

    def test_bundle_dir_is_registered_only_when_requested(self) -> None:
        self.assertFalse(_is_allowed_media_dir(self.manager, self.bundle))
        self.manager.register_media_dir(self.bundle)
        self.assertTrue(_is_allowed_media_dir(self.manager, self.bundle))
        self.assertFalse(_is_allowed_media_dir(self.manager, self.downloads))

    def test_helpers_reject_everything_without_registrations(self) -> None:
        empty = SimpleNamespace()
        self.assertFalse(_is_allowed_media_file(empty, self.reward))
        self.assertFalse(_is_allowed_media_dir(empty, self.bundle))

    def test_register_ignores_empty_and_missing_dir(self) -> None:
        self.manager.register_media_file("")
        self.manager.register_media_dir(os.path.join(self.downloads, "no-existe"))
        self.assertEqual(self.manager.allowed_media_files, set())
        self.assertEqual(self.manager.allowed_media_dirs, set())


if __name__ == "__main__":
    unittest.main()
