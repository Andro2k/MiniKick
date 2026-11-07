from frontend.common import markdown_to_github_html
from frontend.dialogs.release_notes_dialog import ReleaseNotesDialog


class _Translations:
    def get(self, key: str) -> str:
        return key


def test_github_release_markdown_renders_gfm_features(qapp):
    markdown = """## Novedades

| Cambio | Beneficio |
|---|---|
| **Chat** | `nuevo comando` |

- Primera mejora
- Segunda mejora

```python
print("MiniKick")
```

[Ver release](https://github.com/Andro2k/MiniKick/releases)
"""

    rendered = markdown_to_github_html(markdown)

    assert "<h2" in rendered
    assert "<table" in rendered
    assert "<ul" in rendered
    assert "<pre" in rendered
    assert 'href="https://github.com/Andro2k/MiniKick/releases"' in rendered
    assert "color: #F4F4F4" in rendered


def test_github_release_markdown_handles_empty_body():
    assert markdown_to_github_html("") == ""


def test_release_dialog_displays_original_github_body_as_markdown(qapp):
    dialog = ReleaseNotesDialog(_Translations())
    try:
        dialog._on_release_fetched({
            "name": "v1.6.7",
            "published_at": "2026-11-07T12:00:00Z",
            "author": "MiniKick",
            "html_url": "https://github.com/Andro2k/MiniKick/releases/tag/v1.6.7",
            "body": "## Release original\n\n| Idioma | Texto |\n|---|---|\n| Español | Publicado en GitHub |",
        })

        rendered = dialog.txt_content.toHtml()
        assert "Release original" in rendered
        assert "Publicado en GitHub" in rendered
        assert "<table" in rendered
    finally:
        dialog.close()
