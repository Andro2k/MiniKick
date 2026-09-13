# frontend\dialogs\duplicate_alert_dialog.py

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QCheckBox, QButtonGroup, QRadioButton
)
from frontend.dialogs.base_dialog import ModernModal
from frontend.widgets import ModernButton, ModernCard
from frontend.common import SPACING_SM, SPACING_MD, MARGIN_NONE

class DuplicateAlertModal(ModernModal):
    def __init__(self, source_platform: str, source_event: str, available_events: list[tuple[str, str]], i18n, parent=None):
        title = i18n.get("alerts.dialogs.duplicate.title")
        super().__init__(
            title=title,
            icon_path="copy-duotone.svg",
            icon_role="accent_icon",
            width=480,
            resizable=False,
            dialog_key="duplicate_alert_modal",
            parent=parent
        )
        self.i18n = i18n
        self.source_platform = source_platform
        self.source_event = source_event
        self.available_events = [ev for ev in available_events if ev[0] != source_event]

        self._setup_content()

    def _setup_content(self):
        lbl_desc = QLabel(self.i18n.get("alerts.dialogs.duplicate.desc"), self)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        self.content_layout.addWidget(lbl_desc)

        source_card = ModernCard(parent=self, margin=SPACING_SM, spacing=SPACING_SM)
        src_row = QHBoxLayout()
        src_row.setContentsMargins(*MARGIN_NONE)
        src_row.setSpacing(SPACING_SM)

        lbl_src_tag = QLabel(self.i18n.get("alerts.dialogs.duplicate.source_label"), self)
        lbl_src_tag.setProperty("role", "caption")
        lbl_src_val = QLabel(self.i18n.get(f"alerts.events.{self.source_event}"), self)
        lbl_src_val.setProperty("role", "h3")

        src_row.addWidget(lbl_src_tag)
        src_row.addWidget(lbl_src_val)
        src_row.addStretch()
        source_card.addLayout(src_row)
        self.content_layout.addWidget(source_card)

        lbl_targets = QLabel(self.i18n.get("alerts.dialogs.duplicate.target_label"), self)
        lbl_targets.setProperty("role", "h3")
        self.content_layout.addWidget(lbl_targets)

        self.btn_group_target = QButtonGroup(self)
        self.radio_buttons: dict[str, QRadioButton] = {}

        self.rb_all = QRadioButton(self.i18n.get("alerts.dialogs.duplicate.target_all"), self)
        self.rb_all.setChecked(True)
        self.btn_group_target.addButton(self.rb_all)
        self.content_layout.addWidget(self.rb_all)

        for event_key, _ in self.available_events:
            ev_name = self.i18n.get(f"alerts.events.{event_key}")
            rb = QRadioButton(ev_name, self)
            self.btn_group_target.addButton(rb)
            self.radio_buttons[event_key] = rb
            self.content_layout.addWidget(rb)

        options_card = ModernCard(parent=self, margin=SPACING_SM, spacing=SPACING_SM)
        self.chk_media = QCheckBox(self.i18n.get("alerts.dialogs.duplicate.include_media"), self)
        self.chk_media.setChecked(True)
        options_card.addWidget(self.chk_media)

        self.chk_template = QCheckBox(self.i18n.get("alerts.dialogs.duplicate.include_template"), self)
        self.chk_template.setChecked(False)
        options_card.addWidget(self.chk_template)

        self.content_layout.addWidget(options_card)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(SPACING_MD)

        self.btn_cancel = ModernButton(
            text=self.i18n.get("alerts.dialogs.duplicate.btn_cancel"),
            role="action_outlined",
            parent=self
        )
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_confirm = ModernButton(
            text=self.i18n.get("alerts.dialogs.duplicate.btn_confirm"),
            role="action_accent",
            icon_name="copy-duotone.svg",
            icon_size=14,
            parent=self
        )
        self.btn_confirm.clicked.connect(self.accept)

        actions_row.addWidget(self.btn_cancel)
        actions_row.addWidget(self.btn_confirm)
        self.content_layout.addLayout(actions_row)

    def get_selection(self) -> tuple[list[str], bool, bool]:
        target_events = []
        if self.rb_all.isChecked():
            target_events = [ev[0] for ev in self.available_events]
        else:
            for ev_key, rb in self.radio_buttons.items():
                if rb.isChecked():
                    target_events = [ev_key]
                    break

        include_media = self.chk_media.isChecked()
        include_template = self.chk_template.isChecked()
        return target_events, include_media, include_template
