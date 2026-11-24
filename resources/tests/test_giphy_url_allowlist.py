# resources\tests\test_giphy_url_allowlist.py
"""Pruebas de la lista de hosts permitidos para GIF directos del chat."""

import pytest

from backend.services.media.giphy_service import GiphyService, is_allowed_gif_url


@pytest.mark.parametrize("url", [
    "https://media.tenor.com/abc/cat.gif",
    "https://cdn.7tv.app/emote/xyz/4x.webp",
    "https://cdn.discordapp.com/attachments/1/2/a.gif?ex=1",
])
def test_known_hosts_over_https_are_allowed(url):
    assert GiphyService().extract_gif_url(url) == url


@pytest.mark.parametrize("url", [
    "https://evil.example/track.gif",
    "http://media.tenor.com/abc/cat.gif",
    "https://tenor.com.evil.example/a.gif",
    "https://evil.example/tenor.com/a.gif",
])
def test_unknown_hosts_and_plain_http_are_rejected(url):
    assert not is_allowed_gif_url(url)
    assert GiphyService().extract_gif_url(f"mira esto {url}") is None


def test_giphy_pages_still_resolve_to_media_url():
    svc = GiphyService()
    assert svc.extract_gif_url("https://giphy.com/gifs/funny-cat-AbC123") == "https://media.giphy.com/media/AbC123/giphy.gif"
