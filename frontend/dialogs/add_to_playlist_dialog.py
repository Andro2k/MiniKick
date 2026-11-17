# frontend\dialogs\add_to_playlist_dialog.py
"""Modal para agregar la canción actual a una playlist existente o nueva."""

from PySide6.QtWidgets import QButtonGroup, QComboBox, QLineEdit, QRadioButton
from frontend.dialogs.base_dialog import ModernModal


class AddToPlaylistModal(ModernModal):
    def __init__(self, playlists: list[dict], i18n, parent=None):
        super().__init__(
            title=i18n.get("music.playlists.dialog.title"),
            icon_path="music.svg",
            icon_role="accent_icon",
            width=440,
            resizable=False,
            dialog_key="add_to_playlist_modal",
            parent=parent,
        )
        self.i18n = i18n
        self._setup_content(playlists)

    def _setup_content(self, playlists: list[dict]):
        self.rb_existing = QRadioButton(self.i18n.get("music.playlists.dialog.existing"), self)
        self.cmb_playlists = QComboBox(self)
        for playlist in playlists:
            self.cmb_playlists.addItem(playlist["name"], playlist["id"])

        self.rb_new = QRadioButton(self.i18n.get("music.playlists.dialog.new"), self)
        self.txt_name = QLineEdit(self)
        self.txt_name.setPlaceholderText(self.i18n.get("music.playlists.dialog.name_placeholder"))

        group = QButtonGroup(self)
        group.addButton(self.rb_existing)
        group.addButton(self.rb_new)

        self.rb_existing.setEnabled(bool(playlists))
        (self.rb_existing if playlists else self.rb_new).setChecked(True)

        for widget in (self.rb_existing, self.cmb_playlists, self.rb_new, self.txt_name):
            self.content_layout.addWidget(widget)

        _, self.btn_cancel, self.btn_confirm = self.create_action_row(
            cancel_text=self.i18n.get("common.buttons.cancel"),
            confirm_text=self.i18n.get("music.playlists.dialog.confirm"),
            confirm_icon="plus.svg",
        )
        self.rb_new.toggled.connect(self._sync_state)
        self.txt_name.textChanged.connect(self._sync_state)
        self._sync_state()

    def _sync_state(self, *_):
        is_new = self.rb_new.isChecked()
        self.cmb_playlists.setEnabled(not is_new and self.cmb_playlists.count() > 0)
        self.txt_name.setEnabled(is_new)
        self.btn_confirm.setEnabled(not is_new or bool(self.txt_name.text().strip()))

    def get_selection(self) -> tuple[int | None, str]:
        if self.rb_new.isChecked():
            return None, self.txt_name.text().strip()
        return self.cmb_playlists.currentData(), ""
