# frontend\components\stats\kpi_card.py
"""Tarjeta KPI con valor y variación respecto al período anterior."""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout
from frontend.common import BrandColors, Palette, Size, get_pixmap_colored


class KpiCard(QFrame):
    def __init__(self, title: str, icon_name: str, vs_text: str, higher_is_better: bool = True, parent=None):
        super().__init__(parent)
        self.setProperty("role", "card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(160)
        self._vs_text = vs_text
        self._higher_is_better = higher_is_better

        layout = QVBoxLayout(self)
        layout.setContentsMargins(*Size.Margin.MRG_MED)
        layout.setSpacing(Size.SPACING_SM)

        header = QHBoxLayout()
        header.setSpacing(Size.SPACING_SM)
        icon = QLabel(self)
        icon.setPixmap(get_pixmap_colored(icon_name))
        lbl_title = QLabel(title, self)
        lbl_title.setProperty("role", "text_caption")
        header.addWidget(icon)
        header.addWidget(lbl_title)
        header.addStretch()

        self.lbl_value = QLabel("0", self)
        self.lbl_value.setProperty("role", "text_h1")
        self.lbl_delta = QLabel(self)
        self.lbl_delta.setProperty("role", "text_caption")

        layout.addLayout(header)
        layout.addWidget(self.lbl_value)
        layout.addWidget(self.lbl_delta)

    def set_values(self, current: int, previous: int) -> None:
        self.lbl_value.setText(f"{current:,}")
        if previous <= 0:
            self.lbl_delta.setText("-")
            return
        pct = (current - previous) / previous * 100
        if pct == 0:
            self.lbl_delta.setText(f"0.0% {self._vs_text}")
            return
        is_good = (pct > 0) == self._higher_is_better
        color = BrandColors.GREEN if is_good else BrandColors.RED
        arrow = "▲" if pct > 0 else "▼"
        self.lbl_delta.setText(
            f'<span style="color:{color}">{arrow} {abs(pct):.1f}%</span> '
            f'<span style="color:{Palette.NEUTRAL_500}">{self._vs_text}</span>'
        )
