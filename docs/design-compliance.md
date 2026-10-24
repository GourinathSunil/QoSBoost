# QoSBoost UI Design Compliance Specification

This document maps every design token, visual rule, and component specification in `DESIGN.md` to its implementation within the QoSBoost frontend.

---

## 1. Color System Mapping

`DESIGN.md` strictly mandates a near-black product-focused canvas with a four-step surface ladder and a single chromatic accent (Linear lavender-blue). No atmospheric gradients, no spotlight glow, and no rainbow marketing colors.

| Token | Hex Value | `DESIGN.md` Role | QoSBoost Frontend Application | CSS Variable / Utility |
|---|---|---|---|---|
| `colors.canvas` | `#010102` | Anchor page background (pure near-black, faint blue tint) | Root app background, page wrapper, dark whitespace between lifted panels | `--color-canvas: #010102` |
| `colors.surface-1` | `#0f1011` | Level 1 lift | KPI cards, metric charts, panel containers, topology background container, flow table frame | `--color-surface-1: #0f1011` |
| `colors.surface-2` | `#141516` | Level 2 lift | Active/featured tabs, hovered cards, table header, drawer backgrounds | `--color-surface-2: #141516` |
| `colors.surface-3` | `#18191a` | Level 3 lift | Sub-navigation bars, dropdown menus, modal backgrounds, input focus fills | `--color-surface-3: #18191a` |
| `colors.surface-4` | `#191a1b` | Level 4 lift | Deepest lifted surface, tooltip popovers, elevated badges | `--color-surface-4: #191a1b` |
| `colors.hairline` | `#23252a` | Default 1px card border | 1px hairline border on all cards, dividers, table rows | `--color-hairline: #23252a` |
| `colors.hairline-strong` | `#34343a` | Stronger 1px border | Active card borders, input borders, highlighted container strokes | `--color-hairline-strong: #34343a` |
| `colors.hairline-tertiary` | `#3e3e44` | Tertiary nested borders | Nested panel dividers, inner table headers | `--color-hairline-tertiary: #3e3e44` |
| `colors.primary` | `#5e6ad2` | Single chromatic accent (lavender-blue) | Primary CTAs ("Run Demo", "Apply Policy"), brand mark, active route pill, focus ring | `--color-primary: #5e6ad2` |
| `colors.primary-hover` | `#828fff` | Lighter hover state | Primary button hover state | `--color-primary-hover: #828fff` |
| `colors.primary-focus` | `#5e69d1` | Focus-ring tint | Focused input borders, 2px focus ring outline at 50% opacity | `--color-primary-focus: #5e69d1` |
| `colors.on-primary` | `#ffffff` | Primary button text | Text inside `button-primary` | `--color-on-primary: #ffffff` |
| `colors.brand-secure` | `#7a7fad` | Muted lavender-gray | Admission control security status, secondary accent badge | `--color-brand-secure: #7a7fad` |
| `colors.ink` | `#f7f8f8` | Primary text | Headlines, KPI numerical values, active labels, primary body text | `--color-ink: #f7f8f8` |
| `colors.ink-muted` | `#d0d6e0` | Secondary text | Metric descriptions, table body text, secondary captions | `--color-ink-muted: #d0d6e0` |
| `colors.ink-subtle` | `#8a8f98` | Tertiary text | De-emphasized timestamps, table column headers, units (ms, Mbps) | `--color-ink-subtle: #8a8f98` |
| `colors.ink-tertiary` | `#62666d` | Quaternary text | Disabled states, empty state subtitles, fine footnotes | `--color-ink-tertiary: #62666d` |
| `colors.semantic-success`| `#27a644` | The ONLY semantic status color | Status pills ("Connected", "Compliant", "QoS Active", "Admitted") | `--color-semantic-success: #27a644` |
| `colors.semantic-overlay`| `#000000` | Scrim for dialogs & modal backdrops | Modal backdrop overlay at 75% opacity | `--color-semantic-overlay: #000000` |

---

## 2. Typography Mapping

Typography follows Linear's precise hierarchy: negative letter-spacing on display sizes, neutral tracking on body, positive tracking on eyebrows, and a monospace font strictly scoped to technical data (IPs, ports, packet rates).

| Token | Size | Weight | Line Height | Letter Spacing | QoSBoost UI Application |
|---|---|---|---|---|---|
| `typography.display-xl` | 80px | 600 | 1.05 | -3.0px | Hero statement on "About / How it Works" |
| `typography.display-lg` | 56px | 600 | 1.10 | -1.8px | Top-level page headers |
| `typography.display-md` | 40px | 600 | 1.15 | -1.0px | Section headers, large KPI hero digits |
| `typography.headline` | 28px | 600 | 1.20 | -0.6px | Card titles, scenario comparison outcome headlines |
| `typography.card-title` | 22px | 500 | 1.25 | -0.4px | Metric card titles, topology modal header |
| `typography.subhead` | 20px | 400 | 1.40 | -0.2px | Page intro paragraphs, scenario step summaries |
| `typography.body-lg` | 18px | 400 | 1.50 | -0.1px | Featured callouts, policy summary descriptions |
| `typography.body` | 16px | 400 | 1.50 | -0.05px | Default explanatory text, modal descriptions |
| `typography.body-sm` | 14px | 400 | 1.50 | 0 | Table cell content, form labels, card body |
| `typography.caption` | 12px | 400 | 1.40 | 0 | Chart axis labels, metadata tags, badge labels |
| `typography.button` | 14px | 500 | 1.20 | 0 | All action buttons (`button-primary`, `button-secondary`) |
| `typography.eyebrow` | 13px | 500 | 1.30 | +0.4px | Section classification tags ("QOS CONTROLLER", "TELEMETRY") |
| `typography.mono` | 13px | 400 | 1.50 | 0 | IP addresses (10.0.0.x), ports, 5-tuples, flow IDs, DSCP tags |

*Font Family Substitutes:* Cross-platform font stack using `Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif` for Display and Text, and `ui-monospace, 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace` for Linear Mono.

---

## 3. Spacing and Border Radius System

- **Base Unit:** 4px grid.
  - `spacing.xxs`: 4px (badge inner gap, tight icon spacing)
  - `spacing.xs`: 8px (input padding vertical, button padding vertical, table padding vertical)
  - `spacing.sm`: 12px (form element gap, small card margin)
  - `spacing.md`: 16px (card interior elements, grid gap)
  - `spacing.lg`: 24px (standard card interior padding, section separation)
  - `spacing.xl`: 32px (large view padding, container gutters)
  - `spacing.xxl`: 48px (major panel margins, demo runner header)
  - `spacing.section`: 96px (page section separation on About page)

- **Border Radius Scale:**
  - `rounded.xs` (4px): Small data chips, table badges, status indicators
  - `rounded.sm` (6px): Inline code badges, port tags
  - `rounded.md` (8px): All buttons (`button-primary`, `button-secondary`), form inputs, selects
  - `rounded.lg` (12px): Standard cards (KPI cards, chart containers, flow table panel)
  - `rounded.xl` (16px): Topology canvas container, Demo comparison frame
  - `rounded.pill` (9999px): Tab switchers (`pricing-tab-default`, `pricing-tab-selected`), status badges
  - `rounded.full` (9999px): Host and switch circular nodes in topology graph

---

## 4. Components Mapping

Every component in QoSBoost maps directly to a `components:` token in `DESIGN.md`:

1. **`button-primary`**:
   - Background `#5e6ad2`, text `#ffffff`, font 14px weight 500, padding `8px 14px`, border-radius `8px`.
   - Hover: `#828fff`, Pressed: `#5e69d1`.
   - Used for: "Start Demo Scenario", "Apply Policy", "Trigger Adaptation".

2. **`button-secondary`**:
   - Background `#0f1011`, border `1px solid #23252a`, text `#f7f8f8`, font 14px weight 500, padding `8px 14px`, border-radius `8px`.
   - Hover: background `#141516`, border `#34343a`.
   - Used for: "Export Report (JSON)", "Reset Metrics", "Switch to Mock Mode".

3. **`button-tertiary`**:
   - Background transparent / `#010102`, text `#f7f8f8`, hover text `#ffffff`, padding `8px 14px`.
   - Used for: "Cancel", "Clear Filters".

4. **`status-badge`**:
   - Background `#141516`, text `#d0d6e0`, border `1px solid #23252a`, border-radius `9999px`, padding `2px 8px`, font 12px weight 400.
   - Used for: Class tags (`voice`, `video`, `web`, `bulk`), Queue ID tags, Link status.

5. **`pricing-tab-default` & `pricing-tab-selected` (Segment Switcher)**:
   - Default: Background `#010102`, text `#8a8f98`, border-radius `9999px`, padding `6px 14px`.
   - Selected: Background `#141516`, text `#f7f8f8`, border `1px solid #23252a`.
   - Used for: Preset switcher (`Balanced`, `Voice-First`, `Video-Conference`), Mode switcher (`Live Network` vs `Mock Demo`).

6. **`feature-card` / `pricing-card`**:
   - Background `#0f1011`, border `1px solid #23252a`, border-radius `12px`, padding `24px`.
   - Hover: border `#34343a`, background `#141516` when interactive.
   - Top-edge highlight: subtle `border-top: 1px solid rgba(255, 255, 255, 0.05)` for a crisp pixel-rendered feel without drop shadows.
   - Used for: KPI summary blocks, Chart containers, Dynamic Bandwidth adjustment logs.

7. **`text-input` & `text-input-focused`**:
   - Background `#0f1011`, border `1px solid #23252a`, text `#f7f8f8`, border-radius `8px`, padding `8px 12px`.
   - Focus: border `1px solid #34343a`, outline `2px solid rgba(94, 105, 209, 0.5)`.
   - Used for: Bandwidth rate limit inputs, flow search filter, policy thresholds.

8. **`top-nav`**:
   - Height 56px, background `#010102`, border-bottom `1px solid #23252a`, sticky top.
   - Wordmark left (QoSBoost in weight 600 with `#5e6ad2` symbol mark), navigation items centered, system status indicator right.

---

## 5. Strict Design Rules Enforcement

1. **No atmospheric gradients or colorful ambient glows**: Charts and cards use crisp hairline borders `#23252a` and flat dark surfaces (`#0f1011`, `#141516`).
2. **Single chromatic accent**: Lavender `#5e6ad2` is the only brand accent. All secondary accents are strictly monochromatic (`#f7f8f8`, `#d0d6e0`, `#8a8f98`).
3. **No saturated neon greens or reds on marketing surfaces**: The only semantic status green is `#27a644` for connected/healthy indicators.
4. **No pill-rounded CTAs**: Buttons strictly use `8px` (`rounded.md`), never pill. Pills are exclusively reserved for segment switchers and status badges.
5. **No layout shifts during live telemetry**: Chart containers and table layouts maintain fixed dimensions and smooth data-buffer updates.
