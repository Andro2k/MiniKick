# frontend\common\markdown.py

from functools import lru_cache
from PySide6.QtGui import QTextDocument
from .theme import Palette, Semantic, Padding, Size

_MARKDOWN_STYLESHEET = f"""
body {{
    color: {Palette.NEUTRAL_200};
    font-family: "Google Sans", "Segoe UI", sans-serif;
    font-size: 13px;
}}
h1, h2, h3, h4, h5, h6 {{
    color: {Palette.NEUTRAL_050};
    margin-top: 12px;
    margin-bottom: 6px;
}}
p, li {{
    line-height: 1.45;
}}
a {{
    color: {Semantic.CODE_LINK};
    text-decoration: underline;
}}
code, pre {{
    background-color: {Palette.NEUTRAL_950};
    color: {Palette.NEUTRAL_200};
    font-family: "GoogleSansCode Nerd Font", "GoogleSansCode NF", Consolas, monospace;
}}
code {{
    padding: {Padding.PAD_COMP};
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
}}
th, td {{
    border: 1px solid {Palette.NEUTRAL_750};
    padding: {Padding.PAD_CORE};
    text-align: left;
}}
th {{
    background-color: {Palette.NEUTRAL_950};
    color: {Palette.NEUTRAL_400};
}}
blockquote {{
    color: {Palette.NEUTRAL_200};
    margin-left: {Size.SPACING_MD}px;
}}
"""


@lru_cache(maxsize=16)
def markdown_to_github_html(markdown: str) -> str:
    if not markdown:
        return ""

    document = QTextDocument()
    document.setMarkdown(
        markdown,
        QTextDocument.MarkdownFeature.MarkdownDialectGitHub,
    )
    html = document.toHtml()
    return html.replace("</head>", f"<style>{_MARKDOWN_STYLESHEET}</style></head>", 1)
