# Design System Reference

The complete catalogue behind `clean-webpage-design`. Read the section you need; don't guess
token values or component markup. The stylesheet lives in `../assets/base.css`; a working page
is `../assets/starter.html`.

## Contents
1. [Design principles](#1-design-principles)
2. [Color tokens](#2-color-tokens)
3. [Dark mode](#3-dark-mode)
4. [Typography](#4-typography)
5. [Shape, spacing, elevation](#5-shape-spacing-elevation)
6. [Component catalogue](#6-component-catalogue)
7. [Mermaid flowcharts](#7-mermaid-flowcharts)
8. [Conventions](#8-conventions)

---

## 1. Design principles

- **Token-driven, both themes at once.** Color is never a raw hex in component CSS — always a
  token or a `color-mix()` of one. Light lives on `:root`, dark re-declares the same names on
  `html.dark`. This is why a component themes correctly without per-component dark rules.
- **Restraint reads as polish.** One accent (`--primary`), one icon set, one font, lots of
  whitespace. New hues and shadows are what make a page look busy; avoid both.
- **Flat depth.** Separation comes from 1px `--border` and faint `--muted` / `color-mix` fills,
  not drop shadows. The page feels calm and modern.
- **Korean-first.** Pretendard, negative letter-spacing, comfortable line-height, and a spaced
  middle dot `·` for enumerations.

## 2. Color tokens

shadcn-style **stone** neutrals with an **indigo** accent, in `oklch(L C H)`. Light values:

| Token | Light value | Role |
|---|---|---|
| `--background` | `oklch(1 0 0)` | page background |
| `--foreground` | `oklch(0.147 0.004 49.25)` | primary text |
| `--card` | `oklch(1 0 0)` | card / panel surface |
| `--card-foreground` | `oklch(0.147 0.004 49.25)` | text on cards |
| `--primary` | `oklch(0.488 0.243 264.376)` | accent (indigo): links, active, bullets |
| `--primary-foreground` | `oklch(0.97 0.014 254.604)` | text on accent fills |
| `--secondary` | `oklch(0.967 0.001 286.375)` | subtle fill |
| `--secondary-foreground` | `oklch(0.21 0.006 285.885)` | text on secondary |
| `--muted` | `oklch(0.97 0.001 106.424)` | hover fills, soft surfaces |
| `--muted-foreground` | `oklch(0.553 0.013 58.071)` | secondary / caption text |
| `--border` | `oklch(0.923 0.003 48.717)` | all 1px borders |
| `--input` | `oklch(0.923 0.003 48.717)` | form borders |
| `--ring` | `oklch(0.709 0.01 56.259)` | focus ring |

**Using tokens:** text `color:var(--foreground)` / `var(--muted-foreground)`; surfaces
`background:var(--card)` or `var(--background)`; lines `1px solid var(--border)`. For a faint
accent wash use `color-mix(in srgb,var(--primary) 5%,var(--card))`; for an accent chip fill
`color-mix(in srgb,var(--primary) 14%,transparent)`. `oklch` keeps lightness perceptually even,
so these mixes stay legible in both themes.

**Changing the accent** (e.g. teal instead of indigo): edit only `--primary` (and
`--primary-foreground`) on `:root` and `html.dark`. Everything else is neutral and will follow.

## 3. Dark mode

Dark redefines the same token names on `html.dark` (see `base.css`). Three pieces make it work:

1. **The token swap** — already in `base.css`.
2. **Bootstrap before paint** (in `<head>`, so there's no light flash):
   ```html
   <script>(function(){try{var t=localStorage.getItem('theme');
     if(t==='dark'||(!t&&matchMedia('(prefers-color-scheme:dark)').matches))
       document.documentElement.classList.add('dark');}catch(e){}})();</script>
   ```
3. **Toggle** (a button + the `d` key):
   ```js
   var root=document.documentElement;
   function toggle(){root.classList.toggle('dark');
     try{localStorage.setItem('theme',root.classList.contains('dark')?'dark':'light');}catch(e){}}
   ```
`color-scheme:light/dark` is set per theme so native form controls and scrollbars match. Wrap all
`localStorage` access in try/catch — it throws in some embedded contexts.

## 4. Typography

**Font stack** (`base.css` body): `'Pretendard Variable','Pretendard', -apple-system,
BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR',system-ui,sans-serif`. Pretendard covers
Korean + Latin with even weight; self-host the `.woff2` (most reliable) or use the CDN `@import`
noted in `base.css`. Always keep real fallbacks so text renders before the font loads.

**Scale (px, with weight / tracking):**
- Page title `h1`: `clamp(28,4.2vw,40)` · 800 · `-.035em` · line-height 1.14
- Section heading: 22 · 800 · `-.02em`
- Card title: 15 · 700 · `-.01em`
- Lead paragraph: 15.5 · 400 · `--muted-foreground`
- Body / list text: 13 · line-height 1.55–1.62
- Labels / eyebrows: 12–13 · 600–800 · sometimes `+.04em` tracking, uppercase for Latin eyebrows
- Captions / counts: 11–12 · `--muted-foreground`, `font-variant-numeric:tabular-nums` for numbers

Body uses `letter-spacing:-.01em`; headings tighten further. Keep line-height generous (1.5–1.6)
so Korean text breathes.

## 5. Shape, spacing, elevation

- **Radius:** `--radius:0.875rem` (14px) is the base. Cards/callouts use `var(--radius)` or 16px;
  small controls `calc(var(--radius)*.7)`; pills/chips `999px`; inner chips/nodes 7–12px.
- **Borders:** always `1px solid var(--border)`. This is the primary separator.
- **Gutter:** `.wrap{max-width:72rem;margin:0 auto;padding:0 20px}` centers content.
- **Rhythm:** sections ~22–26px apart; blocks inside a card ~14px; list items 7–12px. Hero has
  generous top padding (40px).
- **Elevation:** no box-shadow. Use `--border` + a faint `--muted` or `color-mix` fill. The sticky
  nav/tab bars use a translucent background + `backdrop-filter:blur(12px)`.

## 6. Component catalogue

All classes are in `base.css`. Markup patterns:

**Nav (sticky, blurred):** `header.nav > .wrap.nav-in` with `.brand` (+ `.mark` gradient logo),
`.navlinks > .navlink(.on)`, and an `.icon-btn` theme toggle.

**Pill tabs / chips:** `.chips > .chip`. Selected chip is `.chip.on` — an **inverse fill**
(`background:var(--foreground);color:var(--background)`), the system's signature "selected" look.
Optional `<i>` icon and a `.cnt` count. The row scrolls horizontally (`.scrollbar-none` to hide
the bar). Drive selection in JS by toggling `.on` and re-rendering.

**Card:** `.card` with `.card-title` (+ icon) and `.card-meta`. Hold content blocks inside.

**Structured block** — the content rhythm of the whole design, an icon **label** + body:
```html
<div class="block">
  <span class="block-label"><i class="ri-focus-3-line"></i>문제</span>
  <div class="block-body">…</div>
</div>
```
Four canonical labels + icons: **문제** `ri-focus-3-line`, **동작 방식** `ri-flow-chart`,
**핵심 설계 · 왜 이렇게** `ri-key-2-line`, **결과** `ri-line-chart-line`. The label is tiny, bold,
`--primary`.

- **Numbered steps** (inside 동작 방식): `.steps > .step(.step-n + .step-body)`; bold the lead
  phrase with `<b>`.
- **point — why list** (핵심 설계): `.keylist > li(<b>point</b> <span class="why">— why</span>)`.
  Each item states a decision and explains the reason.
- **check list** (결과): `.checklist > li` with a ✓ marker.

**Accent callout:** `.callout` (soft primary wash + left accent bar). Inside: `.callout-tag`
(icon label), `.callout-lead` (one bold sentence), and `.callout-cols` (two columns that stack
under 640px). Good for a "how to approach this / key takeaways" summary.

**Horizontal flow:** `.flow > .flow-node` separated by `.flow-sep` (an arrow icon). Each node has
`.n` (number), `<b>` label, `<span>` note. Wraps on desktop; **stacks vertically with down-arrows
under 640px** (the separator rotates 90°). Use for a short reference pipeline; use Mermaid
(below) when you need branches/decisions.

**Figure:** `.fig > img + figcaption` — a bordered, rounded image with a muted caption. Always
give `<img onerror="this.closest('figure')?.remove()">` so a broken self-hosted image disappears
cleanly.

## 7. Mermaid flowcharts

For real flowcharts (decision diamonds, branches, a highlighted key node), use Mermaid — it
renders client-side, needs no build step, and themes with the page.

**Load** (head): `<script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"></script>`

**Render pattern:** put an empty `<pre class="mermaid">` in the DOM, then set its **textContent**
to the diagram source (never `innerHTML` — the browser would parse `<br/>` out of your source),
remove `data-processed`, initialize with the current theme, and `mermaid.run({nodes:[pre]})`.
Re-run it inside the theme toggle so the diagram re-themes. Full snippet in `starter.html`
(`renderDiagram`), including the `themeVariables` that match the token palette.

**Authoring rules that avoid syntax errors (LLMs trip on these):**
- First line `flowchart TD`. Node ids are single letters `A`,`B`,… used once to define.
- **Quote every label**: `A["제목<br/>기술 · 기술"]`, decisions `B{"질문?"}`. Line breaks are
  `<br/>` only. Put the real tech/technique on the second line — that's what makes the diagram
  worth looking at (e.g. `MCP · 지표·로그·추적`, `RAG`, `임베딩`, `지식 증류`).
- Edges `A --> B` or `A -->|예| B`. Loops back (e.g. `E -->|아니오| C`) are fine.
- Mark exactly one **key node** (the core design idea) with a dedicated class line, not inline:
  `class E key;` then end with
  `classDef key fill:#e8f5e9,stroke:#2e7d32,color:#14532d,stroke-width:1.6px;`
  (a green highlight that reads in both themes).
- Keep to ~6–9 nodes and include at least one decision that branches and rejoins.
- **Validate** before shipping: in the page console, `await mermaid.parse(src)` throws on bad
  syntax. Check every diagram this way.
- Pair the diagram with a one-line **philosophy** caption underneath (the core idea in plain
  words) — it's what makes the flow memorable.

## 8. Conventions

- **Middle-dot spacing.** Write enumerations with `·` and render them spaced as ` · ` via the
  `esp()` helper (`s.replace(/\s*·\s*/g,' · ')`). Apply it to list/label/caption text.
- **Icons:** Remixicon only (`ri-*`), ~14–18px, usually `--muted-foreground` or `--primary`.
- **Self-host images.** Blog/CDN images are frequently hotlink-blocked; download and serve them
  from your own origin (resize to ≤1000px, strip tiny/icon images). Always add the `<img onerror>`
  fallback so broken images vanish rather than showing a torn-image glyph.
- **Static-site CDN hygiene.** Load external scripts/styles only from a CDN you trust
  (jsdelivr/cdnjs here). Pin exact versions. Inline your own CSS/JS.
- **Responsive by default.** Content maxes at `72rem`; multi-column callouts and horizontal flows
  collapse to one column under 640px; wide things (tables, diagrams) scroll inside their own
  `overflow-x:auto` box — the page body never scrolls sideways.
- **Accessibility:** color is token-driven for contrast in both themes; keep focus styles
  (`--ring`); give icon-only buttons an `aria-label`.

### Quick checklist for a new page
1. Paste `base.css`; set up the head from `starter.html` (bootstrap script, font, Remixicon).
2. Build nav → hero → chips → content from the component classes.
3. Use structured blocks for content; callout for a summary; flow or Mermaid for a pipeline.
4. Verify in **both** themes (toggle with the button or `d`); fix anything that hard-codes color.
5. Self-host images; confirm nothing scrolls horizontally on mobile width.
