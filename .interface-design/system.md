# MiniKick Interface Design System

## Direction

MiniKick is a dark streaming workbench for configuring alerts, overlays, chat,
music, and connected platforms. The interface should feel focused and
operational: controls remain easy to scan while the preview or current task
keeps visual priority.

## Product vocabulary and visual world

- **Domain:** live stream, alerts, overlay, chat, widgets, audio, platform.
- **Color world:** near-black canvas, charcoal inset surfaces, muted gray
  labels, near-white primary text, and purposeful Kick/Twitch brand accents.
- **Signature:** expandable configuration cards reveal a subtly lighter inset
  work surface, while their header icons identify sections rather than
  repeating beside every field.
- **Avoid:** icons on every property row, high-contrast borders used as
  decoration, and unrelated accent colors for structural elements.

## Tokens and surfaces

- Use `Palette` and `Size` from `frontend.common.theme`; do not introduce
  one-off color or spacing values for standard surfaces.
- Card exterior: `Palette.NEUTRAL_950` (`#101010`), `Borders.BRD_BASE`, and
  `Size.Radius.RAD_XLG`.
- Expanded `ExpandableCard` body: `Palette.NEUTRAL_900` (`#171717`) with
  matching lower corner radii. Use the shared `expandable_card_body` role in
  QSS rather than styling individual call sites.
- Keep depth border- and surface-based; avoid decorative shadows and strong
  outlines.

## Expandable cards

- Reuse the single `ExpandableCard` implementation. Specialize it through
  subclasses when behavior differs; do not copy its expansion, divider, or
  body logic.
- Keep the title and optional section icon in the header. Reserve icons for
  meaningful section identity or functional actions.
- Property rows should default to label plus control, without decorative
  icons. Preserve icons on functional controls such as browse buttons.
- Current body rhythm uses `Size.Margin.MRG_MED` (8 px) and
  `Size.SPACING_MD` (8 px); keep spacing on the shared scale.

## Hierarchy and typography

- Let the view's primary task or preview lead. Use section headings to group
  configuration and keep supporting descriptions visually secondary.
- Use the existing semantic text roles (`setting_title`, `caption`, `body`,
  headings) rather than hardcoded per-widget typography.
- Keep property labels and controls aligned consistently; use whitespace and
  surface shifts before adding separators or icons.

## Interaction

- Preserve the shared expand/collapse behavior, chevron state, and divider
  visibility in `ExpandableCard`.
- Functional controls keep their existing hover, focus, disabled, and tooltip
  behavior; visual simplification must not remove interaction cues.
