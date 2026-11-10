# resources\tests\test_clickable_frame.py

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from frontend.components.alerts.variants_tab_bar import AlertVariantTabPill
from frontend.components.dialogs.severity_card import SeverityCard
from frontend.widgets import ClickableFrame


class _I18n:
    def get(self, key: str, default: str = "") -> str:
        return default or key


def test_severity_card_uses_shared_click_handling(qapp):
    card = SeverityCard("high", "Title", "Subtitle")
    assert isinstance(card, ClickableFrame)
    seen = []
    card.clicked.connect(seen.append)
    card.show()
    qapp.processEvents()

    QTest.mouseClick(card, Qt.MouseButton.LeftButton, pos=QPoint(5, 5))

    assert seen == ["high"]


def test_alert_variant_pill_uses_shared_click_handling(qapp):
    pill = AlertVariantTabPill("kick", "follow", "megaphone-filled", _I18n())
    assert isinstance(pill, ClickableFrame)
    seen = []
    pill.clicked.connect(seen.append)
    pill.show()
    qapp.processEvents()

    QTest.mouseClick(pill, Qt.MouseButton.LeftButton, pos=QPoint(2, 18))

    assert seen == ["follow"]
