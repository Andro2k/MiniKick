# resources\tests\test_alert_html_escaping.py
"""Pruebas del escape de datos del chat en el texto HTML de las alertas."""

from unittest.mock import MagicMock

from backend.models import AlertConfig, AlertEvent, AlertType
from backend.services.alerts.alerts_service import AlertService

_ATTACK = '<img src=x onerror="alert(1)">'


def _queued_payload(template: str, **event_kwargs) -> dict:
    storage = MagicMock()
    storage.get_config.return_value = AlertConfig(
        platform="kick", alert_type="follow", text_template=template
    )
    service = AlertService(storage=storage)
    service.queue = MagicMock()
    event = AlertEvent(event_id="e1", platform="kick", alert_type=AlertType.FOLLOW, **event_kwargs)

    assert service.process_event(event) is True
    return service.queue.enqueue.call_args.args[0]


def test_formatted_html_escapes_user_and_message_but_keeps_template_markup():
    payload = _queued_payload(
        '<span class="highlight">{user}</span>: {message}',
        username="x",
        display_name=_ATTACK,
        message="<b>hola</b>",
    )

    assert "<img" not in payload["formatted_html"]
    assert "&lt;img" in payload["formatted_html"]
    assert "&lt;b&gt;hola&lt;/b&gt;" in payload["formatted_html"]
    assert payload["formatted_html"].startswith('<span class="highlight">')


def test_formatted_text_stays_raw_for_tts():
    payload = _queued_payload("{user} & {message}", username="ana", message="a < b")

    assert payload["formatted_text"] == "ana & a < b"


def test_numeric_placeholders_keep_their_type_for_format_specs():
    payload = _queued_payload("{amount:,} bits", username="ana", amount=1500)

    assert payload["formatted_html"] == "1,500 bits"
