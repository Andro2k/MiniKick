# MiniKick Interface Design System

## Direction

MiniKick is a compact desktop control room for streamers managing live platforms, chat, alerts, music, and OBS overlays. Keep the interface focused and information-dense, with dark neutral surfaces, restrained borders, and platform/semantic colors used to communicate actions and status.

## Tokens and spacing

- Use the shared tokens in `frontend/common/theme.py` for colors, radii, typography, margins, and padding.
- Reuse an existing token when its value matches the intended spacing.
- Add a new spacing token when the same meaningful value appears in multiple places; avoid tokens for isolated exceptions.
- Keep token names semantic and compactness-oriented rather than tied to a single widget.
- Current padding tokens include `PAD_XS` (`4px 4px`), `PAD_SM` (`4px 6px`), `PAD_MD` (`6px 10px`), `PAD_LG` (`6px 14px`), `PAD_COMPACT` (`2px 6px`), `PAD_TIGHT` (`4px 8px`), `PAD_COMBO` (`6px 28px 6px 14px`), `PAD_LIST` (`4px 10px`), and `PAD_CALLOUT` (`10px 14px`).
- Reuse `Size.SPACING_*` for scalar and composed spacing values in QSS and generated HTML. The scale includes `SPACING_XXS` (`4px`) for the common 4px step.
- Use shared padding tokens in both QSS and generated Markdown HTML where the dimensions match. Markdown styles may import `Padding` from `frontend.common.theme`.
- For near-matches, prefer the nearest existing token when the visual difference is negligible (for example, `7px 10px` uses `PAD_MD`, and `5px 12px` uses `FLAT_M`). Keep distinct values as named tokens when changing them would noticeably affect a component's layout.

## Chat overlay scaling

- Treat the configured chat font size as the overlay's shared scale. Existing and newly rendered messages inherit the live `--font-size`; do not freeze it with per-message inline styles.
- Size profile elements in `em` relative to that message scale so identity remains legible when streamers tune the overlay for OBS.
- Reference proportions: vertical Dark/Light avatar `3.14em`, horizontal Dark/Light avatar `2.29em`, Minimal avatar `2.29em`; corresponding profile badges are `1.43em`, `1.14em`, and `1em`. Message badges use approximately `1.35em`.
- Keep profile image, fallback, platform badge, message badges, and message spacing on the same scale across themes and orientations. Theme-specific colors and surfaces may vary; sizing behavior should not.
- The Settings mockup must consume the selected overlay size and scale its typography, avatar, and badges together, rather than previewing a fixed-size approximation.
- Clamp externally supplied overlay sizes to the supported UI range (`10–36px`) before applying them.
