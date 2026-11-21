# Composite Study Board Architecture (FigJam & Figma)

Use this reference during Phases 3–5 to construct a cohesive, legible, non-overlapping 7-zone UI study and moodboard.

## 1. FigJam vs. Figma Design API Rules

Check `figma.editorType` first (`"figjam"` vs `"figma"`):

- **FigJam supports `figma.createPage()`.** Despite warnings in `figma-use-figjam/SKILL.md`, `figma.createPage()` executes and persists cleanly on FigJam boards. Always load the target page via `await figma.setCurrentPageAsync(page)` at the start of every `use_figma` call (context resets to page 0 between calls).
- **Available in FigJam:** `createSection`, `createAutoLayout`, `createFrame`, `createRectangle`, `createEllipse`, `createText`, `createNodeFromSvg`, `createSticky`, `createShapeWithText`, `createConnector`, `createTable`, `createCodeBlock`.
- **Not available in FigJam:** `createComponent`, `createComponentSet` (build repeated items cleanly via helper factory functions returning Auto-Layout frames instead).
- **Canonical FigJam `hex/255` palette helper:** Always convert FigJam section, sticky, shape, and connector palette colors via `hex/255` rather than rounded decimals so FigJam recognizes native swatches:

```js
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 });

const SECTION_BG = {
  white: h(0xff, 0xff, 0xff),
  lightGray: h(0xf9, 0xf9, 0xf9),
  lightGreen: h(0xeb, 0xff, 0xee),
  lightTeal: h(0xf1, 0xfe, 0xfd),
  lightBlue: h(0xf5, 0xfb, 0xff),
  lightViolet: h(0xf8, 0xf5, 0xff),
  lightOrange: h(0xff, 0xf7, 0xf0),
  lightYellow: h(0xff, 0xfb, 0xf0),
};

const STICKY_BG = {
  yellow: h(0xff, 0xe2, 0x99),
  orange: h(0xff, 0xd3, 0xa8),
  blue: h(0xa8, 0xda, 0xff),
  violet: h(0xd3, 0xbd, 0xff),
  teal: h(0xb3, 0xf4, 0xef),
  green: h(0xb3, 0xef, 0xbd),
  pink: h(0xff, 0xa8, 0xdb),
};
```

- **Important parenting pitfall:** When calling `figma.createSection()` inside a script, explicitly call `parentSection.appendChild(childSection)` before assigning local `x`/`y` coordinates; otherwise the child section remains orphaned at the page root. Clear `section.name = ""` whenever a visible H2 text header sits inside the section.

---

## 2. Seven-Zone Study Layout

Wrap the entire board inside **one white top-level `SECTION`** (`~4456–4680px` wide) with `100px` outer padding and `92–96px` vertical gaps between zones. Alternating soft FigJam section tints (`lightGray`, `lightBlue` + `lightYellow`, `lightOrange`, `lightTeal`, `lightViolet`, `lightGray`, `lightGreen`) separate sections cleanly at overview zoom.

| Zone | Layout & Width | Required Contents |
|---|---|---|
| **00 · Header & Provenance** | Full-width banner (`lightGray`) | `[AI]` title (`64–72px Bold`), lineage/stack pill badges, 2-paragraph design thesis + target version note, 4 pillar callout cards, and a native 4-column `TABLE` (Layer, Studio/Team, Credited Leads, Verified Sources) with dark `#1E1E1E` header row. |
| **01 · Editable Composite UI** | Left column (`~42%` width, `lightBlue`) | Semantic 1:1 Auto-Layout reconstruction of the studied screen: hardware bezel/chrome if applicable, active/inactive controls, Auto-Layout bento/panel cards, editable text in verified available fonts, crisp `createNodeFromSvg` icons/diagrams, and numbered FigJam callout circles (`48×48` orange `ELLIPSE` `SHAPE_WITH_TEXT`). |
| **02 · Spatial & Interaction Anatomy** | Right column (`~58%` width, `lightYellow`, same height as Zone 01) | `2×N` equal-height white cards matching the numbered callouts in Zone 01, pairing concise pattern titles with concrete UX/ergonomic rationales. |
| **03 · Visual System Foundations** | 3 equal-height white cards across full width (`lightOrange`) | **Card A:** Surface, chrome, and semantic color swatches (`#HEX`, token name, usage role). **Card B:** Editable type scale ramp + uploaded typography specimen/overlay comparisons. **Card C:** 5-step connected `SHAPE_WITH_TEXT` + `CONNECTOR` shader/architecture pipeline + visual before/after comparison. |
| **04 · Target Lineage** | 2 rows × 3–4 cards (`lightTeal`) | Chronological progression showing how the target screen evolved across software releases, pairing studio/press captures with exact release tags. |
| **05 · Agency Stylebooks & 1:1 Flat Comps** | Feature matrix + 2×2 + ultra-wide row (`lightViolet`) | Uncropped 1:1 flat design comps (Behance, Dribbble, agency stylebooks) plus driver/secondary cluster state comparisons (day, alert, night). |
| **06 · Runtime & System Evolution** | 2 rows × 4 cards (`lightGray`) | Engine/editor viewports, pure uncropped renders, design-system component sheets, and next-gen OS UI evolution. |
| **07 · Takeaways & Team Critique** | Split row (`lightGreen`) | Left: `3×2` grid of `[AI]` wide stickies (`isWideWidth = true`, `56–64px` gap). Right: generous empty white section (`[AI] Team Discussion & Reference Pulls`) pre-seeded with 2 prompt stickies and ample room for human collaborators. |

---

## 3. Card Sizing & Aspect-Ratio Discipline

1. **Match every image frame to its normalized asset dimensions.** Never crop or stretch a `16:9` flat comp into a `4:3` card. Read `width` and `height` from `scripts/figma_assets.py prepare`'s `manifest.json` and compute `imgW = Math.round(targetRowImgH * naturalW / naturalH)` so every card in a row shares identical image height while preserving each asset's exact natural aspect ratio.
2. **Equalize card heights per row.** Append all cards in a row first, read `maxH = Math.max(...cards.map(c => c.height))`, then resize each card to `maxH` with `layoutSizingVertical = "FIXED"` so rows align cleanly at the bottom edge.
3. **Unify section right margins.** After building all zones, normalize every full-width section to the same target width and resize the top-level board wrapper to `maxRight + 100` by `maxBottom + 100`.

---

## 4. Visual Audit Checklist

After uploading all images via `upload_assets` + `scripts/figma_assets.py upload`:

1. Run a structural read-back script checking:
   - Total `IMAGE` fills placed equals total manifest entries.
   - `page.children.length === 1` (zero orphaned sections or stray nodes outside the wrapper).
   - Zero child overflows (`child.x + child.width <= parent.width`, `child.y + child.height <= parent.height`).
2. Capture `get_screenshot` for Zone 01, Zone 03, main moodboard sections, and the full board wrapper (`maxDimension: 2048–2400`) and inspect them with `read`.
3. Verify callout markers in Zone 01 never obscure critical labels, verify zero clipped text or colliding card borders, fix any visual defects in one targeted `use_figma` pass, and capture one final verification screenshot of modified sections.
