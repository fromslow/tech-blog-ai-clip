---
name: clean-webpage-design
description: >-
  A reusable design system for building clean, minimal content websites — the
  "fromslow / AI 클리핑" look: shadcn-style oklch color tokens with first-class
  light/dark mode, Pretendard Korean typography, pill-shaped tab/chip navigation,
  soft rounded cards, labeled "structured" content blocks (문제 → 동작 → 핵심 설계 →
  결과), accent callouts, numbered flow steps, and theme-aware Mermaid flowcharts.
  Use this whenever you build or restyle a web page, static site, landing page,
  content/feed page, docs page, dashboard, or any HTML UI and want a polished,
  consistent, Korean-friendly aesthetic with dark mode — especially when the user
  says "같은 디자인으로", "이 톤으로", "그 느낌", references this site, or asks for a
  clean / minimal / modern / shadcn-like look. Prefer this over ad-hoc CSS so the
  result is coherent, accessible, and theme-correct in both light and dark.
---

# Clean Webpage Design

A portable design system distilled from a Korean tech-blog "AI clipping" site. It gives any
static HTML page a coherent, modern look that is correct in **both light and dark mode** from
the first line. The whole system is CSS-variable driven, dependency-light (one icon font, an
optional Korean font, optional Mermaid), and friendly to Korean content.

## What you get

- **oklch token palette** (shadcn `stone`/indigo family) with a complete dark-mode swap.
- **Pretendard** typography tuned for Korean + Latin, tight letter-spacing, clear scale.
- A small component vocabulary: sticky blurred **nav**, pill **tabs/chips**, soft **cards**,
  labeled **structured blocks**, **point → why** key lists, check **result lists**, accent
  **callouts**, numbered **flow** steps, and **theme-aware Mermaid** flowcharts.
- Conventions that keep it feeling hand-made: middle-dot `·` spacing, self-hosted images,
  a one-function dark toggle, responsive by default.

## How to apply it

1. **Start from the stylesheet.** Copy [`assets/base.css`](assets/base.css) into the page (inline
   in a `<style>` or linked). It defines every token for light + dark and all component classes.
   Everything else references `var(--…)` — never hard-code a hex that should be a token, or the
   page breaks in dark mode.
2. **Set up the document head** exactly as in [`assets/starter.html`](assets/starter.html): the
   dark-mode bootstrap script (reads saved theme before paint, avoids a flash), the font, and the
   Remixicon stylesheet. Then build the page body from the component classes.
3. **Read [`references/design-system.md`](references/design-system.md)** for the full catalogue —
   exact token values, the type scale, every component's markup + rationale, the dark-toggle and
   Mermaid snippets, and the house conventions. Consult it whenever you add a component or need a
   value; don't guess tokens.

`assets/starter.html` is a complete working page (nav + tabs + hero + card + callout + flow +
Mermaid) — the fastest way to start is to copy it and replace the content.

## Non-negotiables (why the look holds together)

- **Theme via tokens, both directions.** Light is defined on `:root`; `html.dark` redefines the
  same tokens. Every color in your own CSS must be a token or a `color-mix()` of one. A single
  hard-coded color is the usual reason a page looks wrong in dark mode.
- **Restraint.** One accent (`--primary`), generous whitespace, one icon set (Remixicon), one
  font. Borders are 1px `--border`; corners use the `--radius` scale. Resist adding new hues.
- **Depth without shadows.** Elevation comes from `--border` + subtle `--muted` / `color-mix`
  fills, not drop shadows. Keep it flat and calm.
- **Korean-first typography.** Pretendard, `letter-spacing:-.01em` on body and tighter on
  headings, `line-height:1.5–1.6`. Space the middle dot as ` · ` in rendered lists (see the
  `esp()` helper in the reference) so enumerations breathe.
- **Static-site friendliness.** External scripts/styles only from a CDN you trust; **self-host
  images** (hotlinked blog/CDN images are often blocked) and let `<img onerror>` remove broken
  ones gracefully.

## When NOT to over-reach

This is a design layer, not a framework. Don't pull in a UI library, build step, or component
runtime to use it — it's plain CSS + a little vanilla JS. If a project already has its own design
system, borrow the tokens/conventions rather than overriding their styles wholesale.
