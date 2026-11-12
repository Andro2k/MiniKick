# frontend\dialogs\webhook_dialog.py

from typing import Callable
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QGridLayout, QLineEdit, QVBoxLayout, QHBoxLayout, QWidget
from .base_dialog import ModernModal
from frontend.widgets import (
    ModernButton, ModernSwitch, NoWheelComboBox,
    create_labeled_field, create_switch_field, create_text_label, create_error_label,
)
from frontend.common import Size

_PRESETS = ("discord", "generic")


class WebhookEndpointDialog(ModernModal):
    test_requested = Signal(object)

    def __init__(
        self,
        i18n,
        event_types=(),
        platforms=(),
        url_validator: Callable[[str], str | None] | None = None,
        existing=None,
        parent=None,
    ):
        self.i18n = i18n
        self._url_validator = url_validator
        self._existing = existing
        self._event_types = tuple(event_types)
        self._platforms = tuple(platforms)
        title_key = "webhooks.dialog.title_edit" if existing else "webhooks.dialog.title_new"
        super().__init__(
            title=self.i18n.get(title_key),
            icon_path="webhooks-filled.svg",
            width=580,
            subtitle=self.i18n.get("webhooks.dialog.subtitle"),
            parent=parent,
        )
        self._setup_ui()
        if existing:
            self._load_existing(existing)
        self._on_preset_changed()
        self._update_state()

    def _setup_ui(self):
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText(self.i18n.get("webhooks.dialog.name_placeholder"))
        self.txt_name.textChanged.connect(self._update_state)
        name_field, _ = create_labeled_field(self.i18n.get("webhooks.dialog.name_label"), self.txt_name, parent=self)
        self.content_layout.addLayout(name_field)

        self.cmb_preset = NoWheelComboBox()
        for preset in _PRESETS:
            self.cmb_preset.addItem(self.i18n.get(f"webhooks.presets.{preset}"), preset)
        self.cmb_preset.currentIndexChanged.connect(self._on_preset_changed)
        preset_field, _ = create_labeled_field(self.i18n.get("webhooks.dialog.preset_label"), self.cmb_preset, parent=self)
        self.content_layout.addLayout(preset_field)

        self.txt_url = QLineEdit()
        self.txt_url.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_url.setPlaceholderText(self.i18n.get("webhooks.dialog.url_placeholder"))
        self.txt_url.textChanged.connect(self._on_url_changed)
        url_field, _ = create_labeled_field(self.i18n.get("webhooks.dialog.url_label"), self.txt_url, parent=self)
        self.content_layout.addLayout(url_field)

        self.lbl_url_error = create_error_label(self)
        self.content_layout.addWidget(self.lbl_url_error)
        self.lbl_http_warning = create_text_label(self.i18n.get("webhooks.dialog.http_warning"), role="caption", parent=self)
        self.lbl_http_warning.setProperty("state", "warning")
        self.lbl_http_warning.hide()
        self.content_layout.addWidget(self.lbl_http_warning)

        self.txt_secret = QLineEdit()
        self.txt_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_secret.setPlaceholderText(self.i18n.get("webhooks.dialog.secret_placeholder"))
        secret_field, _ = create_labeled_field(self.i18n.get("webhooks.dialog.secret_label"), self.txt_secret, parent=self)
        self.secret_box = QWidget()
        secret_layout = QVBoxLayout(self.secret_box)
        secret_layout.setContentsMargins(*Size.Margin.MRG_NON)
        secret_layout.setSpacing(Size.SPACING_XS)
        secret_layout.addLayout(secret_field)
        secret_layout.addWidget(create_text_label(self.i18n.get("webhooks.dialog.secret_desc"), role="caption", parent=self))
        self.content_layout.addWidget(self.secret_box)

        self.switch_reveal = ModernSwitch()
        self.switch_reveal.toggled.connect(self._toggle_reveal)
        reveal_box, _ = create_switch_field(self.switch_reveal, self.i18n.get("webhooks.dialog.show_secrets"), spacing=Size.SPACING_MD)
        self.content_layout.addLayout(reveal_box)

        self.content_layout.addWidget(create_text_label(self.i18n.get("webhooks.dialog.events_label"), role="h2", parent=self))
        events_grid = QGridLayout()
        events_grid.setSpacing(Size.SPACING_SM)
        self.event_checks: dict[str, QCheckBox] = {}
        for index, event_type in enumerate(self._event_types):
            check = QCheckBox(self.i18n.get(f"webhooks.events.{event_type}"))
            check.toggled.connect(self._update_state)
            self.event_checks[event_type] = check
            events_grid.addWidget(check, index // 2, index % 2)
        self.content_layout.addLayout(events_grid)
        self.content_layout.addWidget(create_text_label(self.i18n.get("webhooks.dialog.chat_warning"), role="caption", parent=self))

        self.content_layout.addWidget(create_text_label(self.i18n.get("webhooks.dialog.platforms_label"), role="h2", parent=self))
        platforms_row = QHBoxLayout()
        platforms_row.setSpacing(Size.SPACING_LG)
        self.platform_switches: dict[str, ModernSwitch] = {}
        for platform in self._platforms:
            switch = ModernSwitch()
            switch.setChecked(True)
            switch.toggled.connect(self._update_state)
            self.platform_switches[platform] = switch
            box, _ = create_switch_field(switch, self.i18n.get(f"webhooks.platforms.{platform}"), spacing=Size.SPACING_SM)
            platforms_row.addLayout(box)
        platforms_row.addStretch()
        self.content_layout.addLayout(platforms_row)

        self.btn_test = ModernButton(self.i18n.get("webhooks.dialog.btn_test"), role="action_outlined")
        self.btn_test.clicked.connect(self._request_test)
        self.lbl_ping = create_text_label("", role="caption", parent=self)
        self.lbl_ping.hide()
        test_row = QHBoxLayout()
        test_row.setSpacing(Size.SPACING_MD)
        test_row.addWidget(self.btn_test)
        test_row.addWidget(self.lbl_ping, stretch=1)
        self.content_layout.addLayout(test_row)

        self.btn_cancel = ModernButton(self.i18n.get("common.buttons.cancel"), role="action_outlined")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save = ModernButton(self.i18n.get("webhooks.dialog.btn_save"))
        self.btn_save.clicked.connect(self._on_save_clicked)
        self.add_action_buttons(self.btn_cancel, self.btn_save)

    def _load_existing(self, endpoint):
        self.txt_name.setText(endpoint.name)
        index = self.cmb_preset.findData(endpoint.formatter)
        self.cmb_preset.setCurrentIndex(max(0, index))
        self.txt_url.setText(endpoint.target_url)
        self.txt_secret.setText(endpoint.hmac_secret)
        for event_type, check in self.event_checks.items():
            check.setChecked(event_type in endpoint.events)
        for platform, switch in self.platform_switches.items():
            switch.setChecked(platform in endpoint.platforms)

    def _preset(self) -> str:
        return self.cmb_preset.currentData() or "generic"

    def _on_preset_changed(self, *_):
        self.secret_box.setVisible(self._preset() == "generic")

    def _on_url_changed(self, text: str):
        self.lbl_url_error.hide()
        self.lbl_http_warning.setVisible(text.strip().lower().startswith("http://"))
        self._update_state()

    def _toggle_reveal(self, revealed: bool):
        mode = QLineEdit.EchoMode.Normal if revealed else QLineEdit.EchoMode.Password
        self.txt_url.setEchoMode(mode)
        self.txt_secret.setEchoMode(mode)

    def _update_state(self, *_):
        has_url = bool(self.txt_url.text().strip())
        self.btn_test.setEnabled(has_url)
        self.btn_save.setEnabled(
            bool(self.txt_name.text().strip())
            and has_url
            and any(c.isChecked() for c in self.event_checks.values())
            and any(s.isChecked() for s in self.platform_switches.values())
        )

    def _url_error(self) -> str | None:
        if not self._url_validator:
            return None
        code = self._url_validator(self.txt_url.text())
        if not code:
            return None
        self.lbl_url_error.setText(self.i18n.get(f"webhooks.dialog.err_{code}"))
        self.lbl_url_error.show()
        return code

    def _request_test(self):
        if self._url_error():
            return
        self.btn_test.setEnabled(False)
        self.lbl_ping.setText(self.i18n.get("webhooks.dialog.ping_sending"))
        self.lbl_ping.setProperty("state", "info")
        self._repolish(self.lbl_ping)
        self.lbl_ping.show()
        self.test_requested.emit(self.get_data())

    def set_ping_result(self, result):
        if result.ok:
            text = self.i18n.get("webhooks.dialog.ping_ok").replace("{status}", str(result.status_code)).replace("{ms}", str(result.latency_ms))
            state = "success"
        else:
            text = self.i18n.get("webhooks.dialog.ping_fail").replace("{error}", result.error or "-")
            state = "error"
        self.lbl_ping.setText(text)
        self.lbl_ping.setProperty("state", state)
        self._repolish(self.lbl_ping)
        self.lbl_ping.show()
        self._update_state()

    @staticmethod
    def _repolish(widget: QWidget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _on_save_clicked(self):
        if not self._url_error():
            self.accept()

    def get_data(self) -> dict:
        preset = self._preset()
        return {
            "name": self.txt_name.text().strip(),
            "formatter": preset,
            "target_url": self.txt_url.text().strip(),
            "hmac_secret": self.txt_secret.text().strip() if preset == "generic" else "",
            "events": [e for e, c in self.event_checks.items() if c.isChecked()],
            "platforms": [p for p, s in self.platform_switches.items() if s.isChecked()],
        }
