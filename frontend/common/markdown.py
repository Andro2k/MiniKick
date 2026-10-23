# frontend\common\markdown.py

import re
from functools import lru_cache
from frontend.common.theme import Palette, Semantic, BrandColors, Padding, Size

_RE_LATEX_O     = re.compile(r'\$\\mathcal\{O\}\((.*?)\)\$')
_RE_LATEX_MATH  = re.compile(r'\$(.*?)\$')
_RE_FILE_LINKS  = re.compile(r'\[([^\]]+)\]\((?:file:///[^\)]+|[a-zA-Z0-9_\-/\\\.]+\.(?:py|json|md|html))\)')
_RE_HTTP_LINKS  = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')
_RE_INLINE_CODE = re.compile(r'`([^`]+)`')
_RE_BOLD        = re.compile(r'\*\*([^\*]+)\*\*')
_RE_ITALIC      = re.compile(r'(?<!\*)\*([^\*]+)\*(?!\*)')
_RE_CALLOUT     = re.compile(r'^>\s*\[!(NOTE|IMPORTANT|WARNING|TIP|CAUTION)\]', re.IGNORECASE)
_RE_TABLE_DIV   = re.compile(r'^[\s\-:]+$')
_NERD_FONT_FAMILY = "'GoogleSansCode Nerd Font', 'GoogleSansCode NF', Consolas, monospace"
_CALLOUT_STYLES = {
    'NOTE': (BrandColors.BLUE, Semantic.CALLOUT_NOTE_LIGHT, '\udb80\udefc', 'Note', Semantic.BLUE_GLOW),
    'IMPORTANT': (BrandColors.PURPLE, BrandColors.PURPLE_LIGHT, '\udb80\udf61', 'Important', Semantic.PURPLE_GLOW),
    'WARNING': (BrandColors.AMBER, Semantic.CALLOUT_WARNING_LIGHT, '\uf40c', 'Warning', Semantic.AMBER_GLOW),
    'TIP': (BrandColors.GREEN, Semantic.CALLOUT_TIP_LIGHT, '\udb81\udee8', 'Tip', Semantic.GREEN_GLOW),
    'CAUTION': (BrandColors.RED, Semantic.CALLOUT_CAUTION_LIGHT, '\udb80\udc29', 'Caution', Semantic.RED_GLOW)
}
_CODE_SPAN = f'<code style="font-family: {_NERD_FONT_FAMILY}; background-color: {Palette.NEUTRAL_900}; color: {Semantic.CODE_LINK}; padding: {Padding.PAD_COMP}; border-radius: 4px; font-size: 11px;">\\1</code>'
_CODE_INLINE_SPAN = f'<code style="font-family: {_NERD_FONT_FAMILY}; background-color: {Palette.NEUTRAL_900}; color: {Palette.NEUTRAL_200}; padding: {Padding.PAD_COMP}; border-radius: 4px; font-size: 11px;">\\1</code>'


def _render_callout(callout_type: str, lines: list[str]) -> str:
    border_color, title_color, icon, label, background_color = _CALLOUT_STYLES[callout_type]
    icon_span = f'<span style="font-family: {_NERD_FONT_FAMILY}; font-size: 13px;">{icon}</span>'
    body = "<br/>".join(lines)
    return (
        f'<div style="border-left: 3px solid {border_color}; background-color: {background_color}; padding: {Padding.PAD_CALL}; margin: 12px 0; border-radius: 0 6px 6px 0;">'
        f'<div style="color: {title_color}; font-weight: bold; margin-bottom: 6px; font-size: 13px;">{icon_span} {label}</div>'
        f'<div style="color: {Palette.NEUTRAL_200}; font-size: 13px; line-height: 1.5;">{body}</div>'
        f'</div>'
    )


def _render_table(rows: list[list[str]]) -> str:
    output = ['<table style="border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 12px;">']
    for row_index, row in enumerate(rows):
        is_header = row_index == 0
        background = Palette.NEUTRAL_900 if is_header else Palette.NEUTRAL_950
        cell_tag = 'th' if is_header else 'td'
        cell_color = Palette.NEUTRAL_400 if is_header else Palette.NEUTRAL_200
        weight = "font-weight: bold;" if is_header else ""
        output.append(f'<tr style="background-color: {background};">')
        for cell in row:
            output.append(
                f'<{cell_tag} style="border: 1px solid {Palette.NEUTRAL_900}; padding: {Padding.PAD_CORE}; color: {cell_color}; text-align: left; {weight}">{cell}</{cell_tag}>'
            )
        output.append('</tr>')
    output.append('</table>')
    return "\n".join(output)


def _render_block(line: str) -> str:
    if line.startswith('# '):
        return f'<h1 style="color: {Palette.NEUTRAL_050}; font-size: 18px; font-weight: bold; border-bottom: 1px solid {Palette.NEUTRAL_900}; padding-bottom: {Size.SPACING_SM}px; margin: 16px 0 10px 0;">{line[2:]}</h1>'
    if line.startswith('## '):
        return f'<h2 style="color: {Palette.NEUTRAL_050}; font-size: 16px; font-weight: bold; border-bottom: 1px solid {Palette.NEUTRAL_900}; padding-bottom: {Size.SPACING_XXS}px; margin: 14px 0 8px 0;">{line[3:]}</h2>'
    if line.startswith('### '):
        return f'<h3 style="color: {Palette.NEUTRAL_200}; font-size: 14px; font-weight: bold; margin: 10px 0 6px 0;">{line[4:]}</h3>'
    if line in ('---', '***'):
        return f'<hr style="border: none; border-top: 1px solid {Palette.NEUTRAL_900}; margin: 14px 0;" />'
    if line.startswith(('- ', '* ')):
        return f'<div style="color: {Palette.NEUTRAL_200}; font-size: 13px; margin: 4px 0 4px 16px; line-height: 1.5;">• {line[2:]}</div>'
    if line.startswith(('• ', '◦ ')):
        return f'<div style="color: {Palette.NEUTRAL_200}; font-size: 13px; margin: 4px 0 4px 16px; line-height: 1.5;">{line}</div>'
    return f'<p style="color: {Palette.NEUTRAL_200}; font-size: 13px; margin: 6px 0; line-height: 1.5;">{line}</p>'


@lru_cache(maxsize=16)
def markdown_to_github_html(md: str) -> str:
    if not md:
        return ""

    text = _RE_LATEX_O.sub(f'<span style="font-family: {_NERD_FONT_FAMILY}; color: {Semantic.LATEX_MATH}; font-weight: bold;">O(\\1)</span>', md)
    text = _RE_LATEX_MATH.sub(f'<span style="font-family: {_NERD_FONT_FAMILY}; color: {Semantic.LATEX_MATH};">\\1</span>', text)
    text = _RE_FILE_LINKS.sub(_CODE_SPAN, text)
    text = _RE_HTTP_LINKS.sub(rf'<a href="\2" style="color: {Semantic.CODE_LINK}; text-decoration: underline;">\1</a>', text)
    text = _RE_INLINE_CODE.sub(_CODE_INLINE_SPAN, text)
    text = _RE_BOLD.sub(r'<b>\1</b>', text)
    text = _RE_ITALIC.sub(r'<i>\1</i>', text)

    lines = text.splitlines()
    html_out = []

    in_table = False
    table_rows = []

    in_callout = False
    callout_type = ''
    callout_lines = []

    def flush_callout():
        nonlocal in_callout, callout_type, callout_lines
        if in_callout and callout_type in _CALLOUT_STYLES:
            html_out.append(_render_callout(callout_type, callout_lines))
        in_callout = False
        callout_type = ''
        callout_lines = []

    def flush_table():
        nonlocal in_table, table_rows
        if in_table and table_rows:
            html_out.append(_render_table(table_rows))
        in_table = False
        table_rows = []

    for line in lines:
        stripped = line.strip()

        callout_match = _RE_CALLOUT.match(stripped)
        if callout_match:
            flush_table()
            flush_callout()
            in_callout = True
            callout_type = callout_match.group(1).upper()
            continue

        if in_callout:
            if stripped.startswith('>'):
                callout_lines.append(stripped.lstrip('>').strip())
                continue
            flush_callout()

        if stripped.startswith('|') and stripped.endswith('|'):
            flush_callout()
            cols = [c.strip() for c in stripped.strip('|').split('|')]
            if all(_RE_TABLE_DIV.match(c) for c in cols):
                continue
            in_table = True
            table_rows.append(cols)
            continue
        elif in_table:
            flush_table()

        if not stripped:
            continue

        html_out.append(_render_block(stripped))

    flush_callout()
    flush_table()

    body = "\n".join(html_out)
    return (
        f'<html><head><style>'
        f'body {{ font-family: "Google Sans", "Segoe UI", sans-serif; color: {Palette.NEUTRAL_200}; font-size: 13px; }}'
        f'code {{ font-family: {_NERD_FONT_FAMILY}; }}'
        f'</style></head>'
        f'<body style="font-family: \'Google Sans\', \'Segoe UI\', sans-serif; color: {Palette.NEUTRAL_200}; background-color: transparent;">{body}</body></html>'
    )
