# frontend\components\alerts\overlay_card.py

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QBoxLayout, QSizePolicy
from PySide6.QtCore import Signal, QSize, QTimer
from frontend.widgets import ModernCard, ModernButton, SettingRow
from frontend.common import Size

class AlertsOverlayCard(ModernCard):
    copy_url_requested = Signal()
    open_browser_requested = Signal()

    def __init__(self, alerts_overlay_url: str, i18n, parent=None):
        super().__init__(parent=parent, margin=Size.Margin.MRG_MED, spacing=Size.SPACING_SM)
        self.alerts_overlay_url = alerts_overlay_url
        self.i18n = i18n
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self._setup_ui()

    def _setup_ui(self):
        self.btn_copy_url = ModernButton(
            text=self.i18n.get("common.buttons.copy"),
            role="action_outlined",
            parent=self
        )
        self.btn_copy_url.clicked.connect(self._copy_overlay_url)

        overlay_row = SettingRow(
            icon_name="link-filled.svg",
            title_text=self.i18n.get("alerts.overlay_card.title"),
            desc_text=self.i18n.get("alerts.overlay_card.desc"),
            right_widget=self.btn_copy_url,
            contents_margins=Size.Margin.MRG_NON
        )
        
        self.addWidget(overlay_row)

        self.edit_overlay_url = QLineEdit(self.alerts_overlay_url, parent=self)
        self.edit_overlay_url.hide()

        self.btn_open_browser = ModernButton(
            text=self.i18n.get("alerts.overlay_card.open_btn"),
            role="action_outlined",
            icon_name="eye-filled.svg",
            icon_size=16,
            parent=self
        )
        self.btn_open_browser.hide()

        self.url_box = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.url_actions_layout = QHBoxLayout()

    def set_overlay_url(self, url: str):
        self.alerts_overlay_url = url
        self.edit_overlay_url.setText(url)

    def _copy_overlay_url(self):
        if not self.alerts_overlay_url:
            return
        original_text = self.btn_copy_url.text()
        self.btn_copy_url.setText(self.i18n.get("rewards.obs.copied"))
        self.btn_copy_url.setEnabled(False)
        QTimer.singleShot(2000, lambda: self._reset_copy_button(original_text))
        self.copy_url_requested.emit()

    def _reset_copy_button(self, original_text: str):
        self.btn_copy_url.setText(original_text)
        self.btn_copy_url.setEnabled(True)

    def set_responsive_direction(self, _direction: QBoxLayout.Direction):
        pass

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())

    def sizeHint(self) -> QSize:
        return QSize(super().sizeHint().width(), self.minimumSizeHint().height())
