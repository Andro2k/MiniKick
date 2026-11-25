# resources\tests\test_overlay_replay_state.py
"""El estado de replay de widgets se reemplaza entero: un lector nunca ve un dict a medio mutar."""

from backend.services.overlay.overlay_manager import OverlayServerManager


def test_death_replay_state_is_replaced_not_mutated():
    manager = OverlayServerManager(port=0)
    snapshot = manager._last_death_data

    manager.trigger_widget_event("death_update", {"count": 7, "label": "Muertes"})
    manager.trigger_widget_event("widget_toggle", {"widget_id": "death", "is_active": False})

    assert snapshot == {"count": 0, "is_active": True}
    assert manager._last_death_data == {"count": 7, "is_active": False, "label": "Muertes"}


def test_score_replay_state_is_replaced_not_mutated():
    manager = OverlayServerManager(port=0)
    snapshot = manager._last_score_data

    manager.trigger_widget_event("score", {"wins": 2, "losses": 1, "title": "Ranked"})
    manager.trigger_widget_event("widget_toggle", {"widget_id": "score", "is_active": False})

    assert snapshot == {"wins": 0, "losses": 0, "is_active": True}
    assert manager._last_score_data == {"wins": 2, "losses": 1, "is_active": False, "title": "Ranked"}
