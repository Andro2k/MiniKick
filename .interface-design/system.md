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
