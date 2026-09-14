# frontend\dialogs\import_backup_dialog.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from frontend.dialogs.base_dialog import ModernModal
from frontend.widgets import ModernButton, ModernCard
from frontend.common import (
    SPACING_XS, SPACING_SM, SPACING_MD, MARGIN_NONE, MARGIN_H_SM
)

SECTION_ORDER = [
    "settings",
    "alerts",
    "rewards",
    "commands",
    "spam_filters",
    "timers",
    "schedules",
    "widgets",
]

class ImportBackupModal(ModernModal):
    def __init__(self, backup_info: dict, i18n, parent=None):
        self.i18n = i18n
        self.backup_info = backup_info or {}
        self.section_checkboxes: dict[str, QCheckBox] = {}

        title = self.i18n.get("settings.dialogs.import_modal.title")
        super().__init__(
            title=title,
            icon_path="restart-duotone.svg",
            icon_role="accent_icon",
            width=540,
            resizable=False,
            dialog_key="import_backup_modal",
            parent=parent
        )
        self._setup_content()

    def _setup_content(self):
        lbl_desc = QLabel(self.i18n.get("settings.dialogs.import_modal.desc"), self)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        self.content_layout.addWidget(lbl_desc)

        version = self.backup_info.get("version")
        export_date = self.backup_info.get("export_date")
        if version or export_date:
            meta_card = ModernCard(parent=self, margin=SPACING_SM, spacing=SPACING_XS)
            if version:
                row_v = QHBoxLayout()
                row_v.setContentsMargins(*MARGIN_NONE)
                row_v.setSpacing(SPACING_SM)
                lbl_v_tag = QLabel(self.i18n.get("settings.dialogs.import_modal.metadata_version"), self)
                lbl_v_tag.setProperty("role", "caption")
                lbl_v_val = QLabel(str(version), self)
                lbl_v_val.setProperty("role", "body")
                lbl_v_val.setProperty("state", "white")
                row_v.addWidget(lbl_v_tag)
                row_v.addWidget(lbl_v_val)
                row_v.addStretch()
                meta_card.addLayout(row_v)

            if export_date:
                row_d = QHBoxLayout()
                row_d.setContentsMargins(*MARGIN_NONE)
                row_d.setSpacing(SPACING_SM)
                lbl_d_tag = QLabel(self.i18n.get("settings.dialogs.import_modal.metadata_date"), self)
                lbl_d_tag.setProperty("role", "caption")
                lbl_d_val = QLabel(str(export_date), self)
                lbl_d_val.setProperty("role", "body")
                row_d.addWidget(lbl_d_tag)
                row_d.addWidget(lbl_d_val)
                row_d.addStretch()
                meta_card.addLayout(row_d)

            self.content_layout.addWidget(meta_card)

        actions_bar = QHBoxLayout()
        actions_bar.setContentsMargins(*MARGIN_NONE)
        actions_bar.setSpacing(SPACING_SM)

        self.btn_select_all = ModernButton(
            text=self.i18n.get("settings.dialogs.import_modal.btn_select_all"),
            role="action_neutral_border",
            icon_name="check.svg",
            icon_size=12,
            parent=self
        )
        self.btn_deselect_all = ModernButton(
            text=self.i18n.get("settings.dialogs.import_modal.btn_deselect_all"),
            role="action_neutral_border",
            icon_name="x.svg",
            icon_size=12,
            parent=self
        )
        self.btn_select_all.clicked.connect(self._select_all)
        self.btn_deselect_all.clicked.connect(self._deselect_all)

        actions_bar.addWidget(self.btn_select_all)
        actions_bar.addWidget(self.btn_deselect_all)
        actions_bar.addStretch()
        self.content_layout.addLayout(actions_bar)

        raw_sections = self.backup_info.get("sections", {})
        ordered_keys = [k for k in SECTION_ORDER if k in raw_sections] + [
            k for k in raw_sections if k not in SECTION_ORDER
        ]

        sections_container = QWidget()
        sections_layout = QVBoxLayout(sections_container)
        sections_layout.setContentsMargins(*MARGIN_NONE)
        sections_layout.setSpacing(SPACING_SM)

        card_sections = ModernCard(parent=sections_container, margin=SPACING_SM, spacing=SPACING_SM)

        for sec_key in ordered_keys:
            sec_data = raw_sections[sec_key]
            row = QHBoxLayout()
            row.setContentsMargins(*MARGIN_NONE)
            row.setSpacing(SPACING_MD)

            chk = QCheckBox(card_sections)
            chk.setChecked(True)
            chk.setCursor(Qt.CursorShape.PointingHandCursor)
            self.section_checkboxes[sec_key] = chk
            chk.stateChanged.connect(self._on_checkbox_changed)

            info_col = QVBoxLayout()
            info_col.setContentsMargins(*MARGIN_NONE)
            info_col.setSpacing(SPACING_XS)

            title_key = f"settings.dialogs.import_modal.section_{sec_key}"
            desc_key = f"settings.dialogs.import_modal.section_{sec_key}_desc"

            lbl_title = QLabel(self.i18n.get(title_key), card_sections)
            lbl_title.setProperty("role", "h3")

            lbl_sub = QLabel(self.i18n.get(desc_key), card_sections)
            lbl_sub.setProperty("role", "caption")
            lbl_sub.setWordWrap(True)

            info_col.addWidget(lbl_title)
            info_col.addWidget(lbl_sub)

            count = sec_data.get("count", 0) if isinstance(sec_data, dict) else int(sec_data)
            suffix = self.i18n.get("settings.dialogs.import_modal.element_suffix") if count == 1 else self.i18n.get("settings.dialogs.import_modal.elements_suffix")
            count_str = f"{count} {suffix}"

            badge_frame = QFrame(card_sections)
            badge_frame.setProperty("role", "badge")
            badge_layout = QHBoxLayout(badge_frame)
            badge_layout.setContentsMargins(*MARGIN_H_SM)
            badge_layout.setSpacing(0)
            badge_lbl = QLabel(count_str, badge_frame)
            badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge_layout.addWidget(badge_lbl)

            row.addWidget(chk)
            row.addLayout(info_col, stretch=1)
            row.addWidget(badge_frame)
            card_sections.addLayout(row)

        sections_layout.addWidget(card_sections)
        sections_layout.addStretch()

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(280)
        scroll_area.setWidget(sections_container)
        self.content_layout.addWidget(scroll_area)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(SPACING_MD)

        self.btn_cancel = ModernButton(
            text=self.i18n.get("settings.dialogs.import_modal.btn_cancel"),
            role="action_neutral_border",
            parent=self
        )
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_confirm = ModernButton(
            text=self.i18n.get("settings.dialogs.import_modal.btn_confirm"),
            role="action_accent",
            icon_name="restart-duotone.svg",
            icon_size=14,
            parent=self
        )
        self.btn_confirm.clicked.connect(self.accept)

        actions_row.addWidget(self.btn_cancel)
        actions_row.addWidget(self.btn_confirm)
        self.content_layout.addLayout(actions_row)

        self._update_confirm_state()

    def _select_all(self):
        for chk in self.section_checkboxes.values():
            chk.setChecked(True)
        self._update_confirm_state()

    def _deselect_all(self):
        for chk in self.section_checkboxes.values():
            chk.setChecked(False)
        self._update_confirm_state()

    def _on_checkbox_changed(self):
        self._update_confirm_state()

    def _update_confirm_state(self):
        selected = self.get_selected_sections()
        self.btn_confirm.setEnabled(len(selected) > 0)

    def get_selected_sections(self) -> set[str]:
        return {sec for sec, chk in self.section_checkboxes.items() if chk.isChecked()}
