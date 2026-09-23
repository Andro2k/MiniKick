# frontend\dialogs\piper_voices_dialog.py

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QMessageBox, QLineEdit,
    QButtonGroup
)
from PySide6.QtCore import Qt, Signal, Slot
from .base_dialog import ModernFramelessShell
from backend.services.chat import PiperVoiceManager, PiperVoiceDownloadWorker
from frontend.widgets import (
    ModernCard, ModernDivider, ExpandableCard, NoWheelDoubleSpinBox,
    create_col_layout, create_row_layout, ModernScrollArea
)
from frontend.common import (
    get_icon_colored, get_pixmap_colored, COLOR_NEUTRAL_400, COLOR_WHITE, COLOR_GREEN,
    SPACING_NONE, SPACING_2XS, SPACING_XS, SPACING_MD, SPACING_LG,
    MARGIN_NONE, MARGIN_2XS, MARGIN_SM, MARGIN_XL, MARGIN_H_MD, MARGIN_SETTING_ROW
)
from frontend.components.dialogs import PiperVoiceItemWidget

class PiperVoicesDialog(ModernFramelessShell):
    voices_updated = Signal()

    def __init__(self, i18n, tts_service, parent=None, manager=None, worker_class=None):
        super().__init__(width=680, parent=parent)
        self.i18n = i18n
        self.tts_service = tts_service
        if manager is None:
            if hasattr(tts_service, "voice_manager"):
                manager = tts_service.voice_manager
            elif hasattr(tts_service, "tts") and hasattr(tts_service.tts, "_providers") and "piper" in tts_service.tts._providers:
                manager = getattr(tts_service.tts._providers["piper"], "manager", None)
            if manager is None:
                try:
                    manager = PiperVoiceManager()
                    worker_class = worker_class or PiperVoiceDownloadWorker
                except ImportError:
                    pass
        self.manager = manager
        self.worker_class = worker_class
        self._active_workers: dict = {}
        self._item_widgets: dict[str, PiperVoiceItemWidget] = {}
        self._item_entries: list[tuple[PiperVoiceItemWidget, ModernDivider]] = []
        self._active_tab = "all"
        self._setup_ui()
        self._load_synthesis_params()

    def _setup_ui(self):
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(*MARGIN_XL)
        layout.setSpacing(SPACING_MD)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACING_MD)

        icon_lbl = QLabel(self)
        icon_lbl.setPixmap(get_pixmap_colored("microphone-filled.svg", COLOR_GREEN, size=24))
        header_layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(SPACING_2XS)

        lbl_title = QLabel(self.i18n.get("piper_dialog.title"), self)
        lbl_title.setProperty("role", "h2")

        lbl_subtitle = QLabel(self.i18n.get("piper_dialog.subtitle"), self)
        lbl_subtitle.setProperty("role", "caption")
        lbl_subtitle.setWordWrap(True)

        title_layout.addWidget(lbl_title)
        title_layout.addWidget(lbl_subtitle)
        header_layout.addLayout(title_layout, stretch=1)

        layout.addLayout(header_layout)

        self.synthesis_card = ExpandableCard(
            title=self.i18n.get("piper_dialog.synthesis_title"),
            desc=self.i18n.get("piper_dialog.synthesis_desc"),
            icon_name="gear-filled.svg",
            parent=self,
            switch_enabled=False
        )

        params_container = QWidget(self.synthesis_card)
        params_main_layout = create_col_layout(spacing=SPACING_MD, margins=MARGIN_SM, parent=params_container)

        params_grid = create_row_layout(spacing=SPACING_LG)

        col_length = create_col_layout(spacing=SPACING_XS)
        lbl_length = QLabel(self.i18n.get("piper_dialog.param_length_scale"), params_container)
        lbl_length.setProperty("role", "caption")
        lbl_length.setToolTip(self.i18n.get("piper_dialog.param_length_scale_desc"))
        self.spin_length = NoWheelDoubleSpinBox(params_container)
        self.spin_length.setRange(0.20, 3.00)
        self.spin_length.setSingleStep(0.05)
        self.spin_length.setDecimals(2)
        self.spin_length.setToolTip(self.i18n.get("piper_dialog.param_length_scale_desc"))
        self.spin_length.valueChanged.connect(self._on_synthesis_params_changed)
        col_length.addWidget(lbl_length)
        col_length.addWidget(self.spin_length)
        params_grid.addLayout(col_length)

        col_noise = create_col_layout(spacing=SPACING_XS)
        lbl_noise = QLabel(self.i18n.get("piper_dialog.param_noise_scale"), params_container)
        lbl_noise.setProperty("role", "caption")
        lbl_noise.setToolTip(self.i18n.get("piper_dialog.param_noise_scale_desc"))
        self.spin_noise = NoWheelDoubleSpinBox(params_container)
        self.spin_noise.setRange(0.00, 2.00)
        self.spin_noise.setSingleStep(0.05)
        self.spin_noise.setDecimals(2)
        self.spin_noise.setToolTip(self.i18n.get("piper_dialog.param_noise_scale_desc"))
        self.spin_noise.valueChanged.connect(self._on_synthesis_params_changed)
        col_noise.addWidget(lbl_noise)
        col_noise.addWidget(self.spin_noise)
        params_grid.addLayout(col_noise)

        col_noise_w = create_col_layout(spacing=SPACING_XS)
        lbl_noise_w = QLabel(self.i18n.get("piper_dialog.param_noise_w_scale"), params_container)
        lbl_noise_w.setProperty("role", "caption")
        lbl_noise_w.setToolTip(self.i18n.get("piper_dialog.param_noise_w_scale_desc"))
        self.spin_noise_w = NoWheelDoubleSpinBox(params_container)
        self.spin_noise_w.setRange(0.00, 2.00)
        self.spin_noise_w.setSingleStep(0.05)
        self.spin_noise_w.setDecimals(2)
        self.spin_noise_w.setToolTip(self.i18n.get("piper_dialog.param_noise_w_scale_desc"))
        self.spin_noise_w.valueChanged.connect(self._on_synthesis_params_changed)
        col_noise_w.addWidget(lbl_noise_w)
        col_noise_w.addWidget(self.spin_noise_w)
        params_grid.addLayout(col_noise_w)

        params_main_layout.addLayout(params_grid)

        actions_layout = QHBoxLayout()
        self.btn_import = QPushButton(self.i18n.get("piper_dialog.btn_import"), params_container)
        self.btn_import.setProperty("role", "action_outlined")
        self.btn_import.setToolTip(self.i18n.get("piper_dialog.btn_import_tooltip"))
        self.btn_import.setIcon(get_icon_colored("cloud-download-filled.svg", COLOR_WHITE, size=14))
        self.btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_import.clicked.connect(self._on_import_model_clicked)
        actions_layout.addWidget(self.btn_import)

        actions_layout.addStretch()

        self.btn_reset_synthesis = QPushButton(self.i18n.get("piper_dialog.btn_reset_synthesis"), params_container)
        self.btn_reset_synthesis.setProperty("role", "action_outlined")
        self.btn_reset_synthesis.setToolTip(self.i18n.get("piper_dialog.btn_reset_tooltip"))
        self.btn_reset_synthesis.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset_synthesis.clicked.connect(self._reset_synthesis_defaults)
        actions_layout.addWidget(self.btn_reset_synthesis)
        params_main_layout.addLayout(actions_layout)

        self.synthesis_card.add_widget(params_container)
        layout.addWidget(self.synthesis_card)

        filter_bar_layout = QHBoxLayout()
        filter_bar_layout.setSpacing(SPACING_MD)

        cat_frame = QFrame(self)
        cat_frame.setProperty("role", "segmented_control")
        cat_layout = QHBoxLayout(cat_frame)
        cat_layout.setContentsMargins(*MARGIN_2XS)
        cat_layout.setSpacing(SPACING_2XS)

        self.cat_group = QButtonGroup(self)
        self.cat_group.setExclusive(True)

        tabs = [
            ("all", self.i18n.get("piper_dialog.tab_all")),
            ("natural", self.i18n.get("piper_dialog.tab_natural")),
            ("stream", self.i18n.get("piper_dialog.tab_stream")),
            ("installed", self.i18n.get("piper_dialog.tab_installed")),
        ]

        for tab_id, tab_label in tabs:
            clean_label = tab_label.replace("&", "&&")
            btn = QPushButton(clean_label, cat_frame)
            btn.setProperty("role", "segmented_item")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(28)
            if tab_id == "all":
                btn.setChecked(True)
            btn.toggled.connect(lambda checked, tid=tab_id: self._on_tab_toggled(tid, checked))
            self.cat_group.addButton(btn)
            cat_layout.addWidget(btn)

        filter_bar_layout.addWidget(cat_frame)
        filter_bar_layout.addStretch(1)

        search_container = QFrame(self)
        search_container.setProperty("role", "searchable_combo_search_bar")
        search_container.setFixedSize(220, 32)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(*MARGIN_H_MD)
        search_layout.setSpacing(SPACING_XS)

        lbl_search_icon = QLabel(search_container)
        lbl_search_icon.setPixmap(get_pixmap_colored("search-filled.svg", COLOR_NEUTRAL_400, size=14))
        lbl_search_icon.setFixedSize(14, 14)
        search_layout.addWidget(lbl_search_icon, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.search_input = QLineEdit(search_container)
        self.search_input.setProperty("role", "searchable_combo_input")
        self.search_input.setPlaceholderText(self.i18n.get("piper_dialog.search_placeholder"))
        self.search_input.textChanged.connect(self._apply_filter)
        search_layout.addWidget(self.search_input)

        filter_bar_layout.addWidget(search_container)
        layout.addLayout(filter_bar_layout)

        scroll = ModernScrollArea(parent=self)

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(*MARGIN_NONE)
        self.scroll_layout.setSpacing(SPACING_NONE)

        self.catalog_card = ModernCard(scroll_content, margin=MARGIN_NONE, spacing=SPACING_NONE)
        self.scroll_layout.addWidget(self.catalog_card)

        self.lbl_empty_state = QLabel(self.i18n.get("piper_dialog.empty_search"), scroll_content)
        self.lbl_empty_state.setProperty("role", "caption")
        self.lbl_empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_empty_state.setContentsMargins(*MARGIN_SETTING_ROW)
        self.lbl_empty_state.hide()
        self.scroll_layout.addWidget(self.lbl_empty_state)

        self._populate_catalog()

        self.scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)

        footer_layout = QHBoxLayout()
        self.lbl_installed_count = QLabel(self)
        self.lbl_installed_count.setProperty("role", "caption")
        footer_layout.addWidget(self.lbl_installed_count, alignment=Qt.AlignmentFlag.AlignVCenter)
        footer_layout.addStretch(1)

        btn_close = QPushButton(self.i18n.get("piper_dialog.btn_close"), self)
        btn_close.setProperty("role", "action_outlined")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        footer_layout.addWidget(btn_close)

        layout.addLayout(footer_layout)
        self._update_installed_count()

    def _on_tab_toggled(self, tab_id: str, checked: bool):
        if checked:
            self._active_tab = tab_id
            self._apply_filter()

    def _apply_filter(self):
        query = self.search_input.text().strip().lower()
        active_tab = self._active_tab

        visible_count = 0
        last_visible_divider = None

        for item, divider in self._item_entries:
            meta = item.voice_meta
            cat = meta.get("category", "natural")
            is_inst = item.is_installed
            name = meta.get("name", "").lower()
            vid = meta.get("id", "").lower()
            lang = meta.get("lang", "").lower()

            if active_tab == "natural" and cat != "natural":
                item.setVisible(False)
                divider.setVisible(False)
                continue
            elif active_tab == "stream" and cat != "stream":
                item.setVisible(False)
                divider.setVisible(False)
                continue
            elif active_tab == "installed" and not is_inst:
                item.setVisible(False)
                divider.setVisible(False)
                continue

            matches_search = not query or (query in name or query in vid or query in lang)
            if not matches_search:
                item.setVisible(False)
                divider.setVisible(False)
                continue

            item.setVisible(True)
            divider.setVisible(True)
            last_visible_divider = divider
            visible_count += 1

        if last_visible_divider:
            last_visible_divider.setVisible(False)

        self.lbl_empty_state.setVisible(visible_count == 0)
        self.catalog_card.setVisible(visible_count > 0)

    def _update_installed_count(self):
        if not self.manager:
            return
        installed_list = self.manager.get_installed_voices()
        catalog_list = self.manager.get_catalog()
        template = self.i18n.get("piper_dialog.installed_count")
        text = template.replace("{installed}", str(len(installed_list))).replace("{total}", str(len(catalog_list)))
        self.lbl_installed_count.setText(text)

    def _load_synthesis_params(self):
        ls, ns, nws = 1.0, 0.667, 0.8
        if hasattr(self.tts_service, "get_settings"):
            settings = self.tts_service.get_settings()
            ls = float(settings.get("piper_length_scale", 1.0))
            ns = float(settings.get("piper_noise_scale", 0.667))
            nws = float(settings.get("piper_noise_w_scale", 0.8))
        elif hasattr(self.tts_service, "tts") and hasattr(self.tts_service.tts, "get_piper_synthesis_params"):
            ls, ns, nws = self.tts_service.tts.get_piper_synthesis_params()

        self.spin_length.blockSignals(True)
        self.spin_noise.blockSignals(True)
        self.spin_noise_w.blockSignals(True)

        self.spin_length.setValue(ls)
        self.spin_noise.setValue(ns)
        self.spin_noise_w.setValue(nws)

        self.spin_length.blockSignals(False)
        self.spin_noise.blockSignals(False)
        self.spin_noise_w.blockSignals(False)

    def _on_synthesis_params_changed(self):
        ls = self.spin_length.value()
        ns = self.spin_noise.value()
        nws = self.spin_noise_w.value()
        if hasattr(self.tts_service, "set_piper_synthesis_params"):
            self.tts_service.set_piper_synthesis_params(ls, ns, nws)
        elif hasattr(self.tts_service, "tts") and hasattr(self.tts_service.tts, "set_piper_synthesis_params"):
            self.tts_service.tts.set_piper_synthesis_params(ls, ns, nws)

    def _reset_synthesis_defaults(self):
        self.spin_length.setValue(1.00)
        self.spin_noise.setValue(0.67)
        self.spin_noise_w.setValue(0.80)
        self._on_synthesis_params_changed()

    def _populate_catalog(self):
        if not self.manager:
            return

        catalog = self.manager.get_catalog()
        catalog_ids = set()
        default_voice_id = getattr(self.manager, "DEFAULT_VOICE_ID", getattr(self.manager, "default_voice_id", "es_MX-claude-high"))

        all_metas = []
        for meta in catalog:
            catalog_ids.add(meta["id"])
            all_metas.append((meta, self.manager.is_voice_installed(meta["id"])))

        installed_all = self.manager.get_installed_voices()
        for inst_meta in installed_all:
            vid = inst_meta["id"]
            if vid not in catalog_ids:
                meta = {
                    "id": vid,
                    "name": inst_meta["name"],
                    "lang": inst_meta.get("lang", "es"),
                    "quality": inst_meta.get("quality", "custom"),
                    "category": "natural",
                    "size_mb": "Local"
                }
                all_metas.append((meta, True))

        for idx, (meta, is_inst) in enumerate(all_metas):
            voice_id = meta["id"]
            is_default = (voice_id == default_voice_id)
            item = PiperVoiceItemWidget(meta, is_inst, self.i18n, is_default=is_default, parent=self)
            item.download_requested.connect(self._start_download)
            item.delete_requested.connect(self._delete_voice)
            item.test_requested.connect(self._test_voice)
            self._item_widgets[voice_id] = item

            divider = ModernDivider(self.catalog_card)
            self.catalog_card.addWidget(item)
            self.catalog_card.addWidget(divider)
            self._item_entries.append((item, divider))

        self._apply_filter()

    def _refresh_catalog(self):
        while self.catalog_card.card_layout.count():
            item = self.catalog_card.card_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._item_widgets.clear()
        self._item_entries.clear()
        self._populate_catalog()
        self._update_installed_count()
        self._apply_filter()

    def _on_import_model_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.get("piper_dialog.import_title"),
            "",
            self.i18n.get("piper_dialog.import_filter")
        )
        if not file_path:
            return

        json_path = file_path + ".json"
        if not os.path.exists(json_path):
            json_alt = os.path.splitext(file_path)[0] + ".json"
            if os.path.exists(json_alt):
                json_path = json_alt
            else:
                QMessageBox.warning(self, self.i18n.get("piper_dialog.title"), self.i18n.get("piper_dialog.import_missing_json"))
                return

        imported = self.manager.import_local_voice(file_path, json_path)
        if imported:
            if hasattr(self.tts_service, "tts") and hasattr(self.tts_service.tts, "invalidate_voices_cache"):
                self.tts_service.tts.invalidate_voices_cache("piper")
            self.voices_updated.emit()
            self._refresh_catalog()

    @Slot(str)
    def _start_download(self, voice_id: str):
        if voice_id in self._active_workers or not self.manager:
            return

        worker_cls = self.worker_class
        if not worker_cls:
            try:
                worker_cls = PiperVoiceDownloadWorker
            except ImportError:
                return

        item = self._item_widgets.get(voice_id)
        if item:
            item.set_downloading(True, 0)

        worker = worker_cls(voice_id, self.manager, parent=self)
        worker.progress.connect(self._on_download_progress)
        worker.finished.connect(self._on_download_finished)
        self._active_workers[voice_id] = worker
        worker.start()

    @Slot(str, int, float, float)
    def _on_download_progress(self, voice_id: str, percent: int, _down_mb: float, _tot_mb: float):
        item = self._item_widgets.get(voice_id)
        if item:
            item.set_downloading(True, percent)

    @Slot(str, bool, str)
    def _on_download_finished(self, voice_id: str, success: bool, _err_msg: str):
        if voice_id in self._active_workers:
            worker = self._active_workers.pop(voice_id)
            worker.deleteLater()

        item = self._item_widgets.get(voice_id)
        if item:
            item.set_downloading(False)
            item.update_status(success)

        if success:
            if hasattr(self.tts_service, "tts") and hasattr(self.tts_service.tts, "invalidate_voices_cache"):
                self.tts_service.tts.invalidate_voices_cache("piper")
            self.voices_updated.emit()
            self._update_installed_count()
            self._apply_filter()

    @Slot(str)
    def _delete_voice(self, voice_id: str):
        item = self._item_widgets.get(voice_id)
        voice_name = voice_id
        is_custom = False
        if item:
            is_custom = item.voice_meta.get("is_custom", False) or not item._can_download()
            voice_name = item.voice_meta.get("name", voice_id)

        from frontend.dialogs import ModernConfirmDialog
        desc = self.i18n.get("piper_dialog.confirm_delete.desc").replace("{voice_name}", voice_name)
        dialog = ModernConfirmDialog(
            self.i18n,
            parent=self,
            title_text=self.i18n.get("piper_dialog.confirm_delete.title"),
            body_text=desc
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        ok = self.manager.delete_voice(voice_id)
        if ok:
            if hasattr(self.tts_service, "tts") and hasattr(self.tts_service.tts, "invalidate_voices_cache"):
                self.tts_service.tts.invalidate_voices_cache("piper")
            self.voices_updated.emit()
            if is_custom:
                self._refresh_catalog()
            else:
                if item:
                    item.update_status(False)
                self._update_installed_count()
                self._apply_filter()

    @Slot(str)
    def _test_voice(self, voice_id: str):
        self._on_synthesis_params_changed()
        sample_text = self.i18n.get("chat.status.voice_test_sample")
        if hasattr(self.tts_service, "speak"):
            self.tts_service.speak(sample_text, voice_id=voice_id)
