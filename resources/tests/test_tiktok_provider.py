# resources\tests\test_tiktok_provider.py

import asyncio
from unittest.mock import MagicMock
from backend.providers.chat.tiktok_provider import TikTokChatProvider


def test_drain_client_loop_none_or_empty():
    TikTokChatProvider._drain_client_loop(None)
    mock_empty = MagicMock()
    mock_empty._asyncio_loop = None
    TikTokChatProvider._drain_client_loop(mock_empty)

def test_drain_client_loop_invokes_clean_tasks():
    mock_client = MagicMock()
    mock_loop = MagicMock()
    mock_loop.is_closed.return_value = False
    mock_loop.is_running.return_value = False
    mock_client._asyncio_loop = mock_loop
    mock_client._clean_tasks = MagicMock()

    TikTokChatProvider._drain_client_loop(mock_client)

    mock_client._clean_tasks.assert_called_once()

def test_drain_client_loop_fallback_cancels_and_gathers_tasks():
    loop = asyncio.new_event_loop()
    try:
        async def endless_worker():
            try:
                await asyncio.sleep(100)
            except asyncio.CancelledError:
                pass

        task = loop.create_task(endless_worker())
        assert not task.done()

        mock_client = MagicMock()
        mock_client._asyncio_loop = loop
        mock_client._clean_tasks = None
        mock_client.connected = False

        TikTokChatProvider._drain_client_loop(mock_client)

        assert task.cancelled() or task.done()
        pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
        assert len(pending) == 0
    finally:
        loop.close()

def test_stop_chat_when_loop_not_running():
    provider = TikTokChatProvider()
    mock_client = MagicMock()
    mock_loop = MagicMock()
    mock_loop.is_running.return_value = False
    mock_loop.is_closed.return_value = False
    mock_client._asyncio_loop = mock_loop
    mock_client._clean_tasks = MagicMock()

    provider._client = mock_client
    provider._is_running = True
    provider.stop_chat()

    assert not provider._is_running
    mock_client._clean_tasks.assert_called_once()

def test_mark_seen_and_deduplication():
    provider = TikTokChatProvider()
    assert not provider._mark_seen("msg_1")
    assert provider._mark_seen("msg_1")
    assert not provider._mark_seen("msg_2")

def test_extract_avatar_url():
    user = MagicMock()
    user.avatar_thumb = "https://example.com/avatar.jpg"
    assert TikTokChatProvider._extract_avatar_url(user) == "https://example.com/avatar.jpg"

    user_fallback = MagicMock()
    user_fallback.avatar_thumb = None
    user_fallback.avatar_medium = None
    user_fallback.avatar_large = None
    url_holder = MagicMock()
    url_holder.url_list = ["https://example.com/url_list.jpg"]
    user_fallback.avatar_thumb = url_holder
    assert TikTokChatProvider._extract_avatar_url(user_fallback) == "https://example.com/url_list.jpg"
