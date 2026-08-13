# tests\test_kick_rewards.py

from unittest.mock import MagicMock
from backend.providers.chat.kick_client import KickAPIClient

def test_kick_api_client_create_channel_reward():
    auth_provider = MagicMock()
    auth_provider.get_tokens.return_value = {"access_token": "fake_token"}
    
    client = KickAPIClient(auth_provider=auth_provider)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "id": "01HXXXXXX",
            "title": "Super Alert",
            "cost": 500,
            "description": "Explosive sound",
            "background_color": "#00e701",
            "is_enabled": True,
            "is_user_input_required": False,
            "should_redemptions_skip_request_queue": True
        },
        "message": "Reward created"
    }
    
    client.scraper = MagicMock()
    client.scraper.request.return_value = mock_response

    resp = client.create_channel_reward(
        title="Super Alert",
        cost=500,
        description="Explosive sound",
        background_color="#00e701",
        is_user_input_required=False,
        should_redemptions_skip_request_queue=True
    )

    assert resp["data"]["title"] == "Super Alert"
    assert resp["data"]["cost"] == 500
    assert resp["data"]["should_redemptions_skip_request_queue"] is True
    client.scraper.request.assert_called_once()

def test_kick_api_client_update_channel_reward():
    auth_provider = MagicMock()
    auth_provider.get_tokens.return_value = {"access_token": "fake_token"}
    
    client = KickAPIClient(auth_provider=auth_provider)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "id": "01HXXXXXX",
            "title": "Super Alert Updated",
            "cost": 1000,
            "description": "New description",
            "background_color": "#00F0FF",
            "is_user_input_required": True
        },
        "message": "Reward updated"
    }
    
    client.scraper = MagicMock()
    client.scraper.request.return_value = mock_response

    payload = {
        "title": "Super Alert Updated",
        "cost": 1000,
        "description": "New description",
        "background_color": "#00F0FF",
        "is_user_input_required": True
    }
    resp = client.update_channel_reward("01HXXXXXX", payload)

    assert resp["data"]["title"] == "Super Alert Updated"
    assert resp["data"]["cost"] == 1000
    client.scraper.request.assert_called_once()
