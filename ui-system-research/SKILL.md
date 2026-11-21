---
name: ui-system-research
description: This skill should be used when the user asks to "research a UI system", "find source comps", "build a Figma study board", "create a UI moodboard", "study [product] UI", "teardown this interface", or shares a UI screenshot and wants verified design provenance, high-resolution source assets, and a composite Figma or FigJam study board.
---

# UI System Research & Composite Study Board

Research a product or design system's real UI lineage—identifying software versions, credited designers/agencies, typography, color tokens, rendering pipeline, and verified source comps—and synthesize the findings into an editable composite UI study and visual moodboard in Figma or FigJam.

## Core Invariants

1. **Identify exact lineage before collecting comps.** When given a screenshot or product name, inspect specific visual cues (navigation rails, tab pills, typeface cuts, rendering style, hardware chrome) to pinpoint the exact software version, hardware generation, or redesign era. Never conflate an earlier launch UI with a later incremental update.
2. **Verify every visual asset before citing or placing it.** Download candidate images to `/tmp/opencode/<slug>-study/` and inspect them directly with `read`. Never include unseen URLs, unverified archive neighbors, or misattributed fan concepts. Distinguish explicitly between:
   - **1:1 flat exports** (clean screen frames from design systems, agency stylebooks, or Behance/Dribbble)
   - **First-party studio/press photos** (hardware bezels, editorial photography)
   - **Community concepts or recreations** (speculative third-party explorations)
3. **Ask which board to target—suggest a new page in `Gooeymood` by default.** Before mutating Figma, confirm the destination board unless the user already supplied a target URL and `node-id`. Suggest creating a new page in `Gooeymood` (`https://www.figma.com/board/T9UIqsH9UE6SPQaW1Va3eD/Gooeymood`) as the recommended default.
4. **Build semantic layers, never flat screenshot deliverables.** Zone 01 must reconstruct the target UI as editable Auto-Layout frames, editable text nodes, and crisp `createNodeFromSvg` icons/illustrations. Treat raw reference photos as moodboard evidence in the gallery zones, not as the composite UI study itself.
5. **Tag shared-workspace artifacts with `[AI]`.** Prefix the created page name, section headings, card titles, and AI-authored sticky notes with `[AI]` so collaborators can separate generated synthesis from human notes.

---

## Workflow

### Phase 1: Target Classification & Multi-Lane Research

1. **Inspect any supplied reference image.** Document observable layout regions, widget names, typeface characteristics, color roles, icon rails, and shader/illustration treatment.
2. **Dispatch parallel `librarian` research lanes** (one message, disjoint territories) instead of running inline search loops. Consult `references/research-playbook.md` for exact query patterns across:
   - **Lane A — First-Party & Engineering:** Official product/release blogs, press/media kits, release notes, PDF owner's guides/manuals (often yield UI diagrams and release dates), conference talks (Config, Unreal Fest, WWDC, I/O), and patents.
   - **Lane B — Design Showcases & Component Archives:** Behance, Dribbble, Layers.to, Figma Community, 60fps.design, Mobbin, and curated archives (`tools.cosmos.cosmos_search` / `cosmos_search_clusters` when Cosmos MCP is available).
   - **Lane C — Credits, Agencies & Designer Portfolios:** External studios, type foundries, creative directors, motion/3D leads, and individual staff designers whose personal portfolios often host uncropped flat comps, SVGs, and motion clips omitted from official press releases.
3. **Bypass automated fetch blocks via `agent-browser --headed`.** Behance, Dribbble shot pages, Figma Community, and some editorial showcases return `HTTP 403` or empty DOMs to `webfetch`. Open an isolated `--session` with `--headed`, extract full-resolution asset URLs (e.g., Behance `/project_modules/source/` lossless PNGs, un-clamped Sanity/Imgix/Cloudinary URLs, Adobe CCV / Vimeo / Gumlet stills), and close the browser session when finished.
4. **Extract and inspect assets locally.** Save candidates under `/tmp/opencode/<slug>-study/`, render vector/motion specimens when needed (`rsvg-convert`, `ffmpeg`), and inspect every candidate visually with `read`.

---

### Phase 2: Confirm Target Board & Page (`Gooeymood` Default)

If the user has **not** already specified an exact Figma/FigJam file URL and page/node target, ask before creating Figma nodes.

Use OpenChamber's interactive choice (`openchamber_render` with `ui` + `awaitAnswer` when allowing conditions/custom notes, or `question` for a quick selection) with these options:

1. **New page in `Gooeymood` (Recommended)** — Creates a new `[AI] <Product> UI Study` page inside `https://www.figma.com/board/T9UIqsH9UE6SPQaW1Va3eD/Gooeymood` (fileKey `T9UIqsH9UE6SPQaW1Va3eD`).
2. **Existing page in `Gooeymood`** — Target a specified page or `node-id` inside `Gooeymood` (inspect existing top-level sections first and position away from existing content).
3. **Different Figma Design or FigJam file** — User provides another `figma.com/board/...` or `figma.com/design/...` URL, or requests `create_new_file`.

---

### Phase 3: Prepare Normalized Assets & Inspect Figma Environment

1. **Load required Figma skills and MCP resources first:**
   - Invoke `figma-use` and `figma-generate-design` skills.
   - For FigJam (`figma.com/board/...`), read `skill://figma/figma-use-figjam/SKILL.md` and its node-type references (`plan-board-content.md`, `create-section.md`, `create-sticky.md`, `create-shape-with-text.md`, `create-connector.md`, `create-text.md`, `create-table.md`, `create-label.md`, `figjam-colors.md`).
   - Call `tools.figma.create_session({ fileKey, description })` and reuse the returned `sessionId` across all Figma calls.
2. **Verify page creation & available fonts:**
   - **FigJam `createPage()` note:** Empirically, `figma.createPage()` works in FigJam (`editorType === "figjam"`) despite warnings in `figma-use-figjam/SKILL.md`. Create the new page cleanly when requested, then call `await figma.setCurrentPageAsync(page)` at the start of every subsequent `use_figma` call (page context resets to page 0 on each call).
   - Call `await figma.listAvailableFontsAsync()` to verify exact installed font family and style strings (e.g., `"Semi Bold"` vs `"SemiBold"`, geometric grotesks/monos matching the studied UI) before any text mutation.
3. **Prepare image assets with exact dimensions:**
   Run `scripts/figma_assets.py prepare` to normalize WebP/PNG/JPEG files, cap oversized dimensions (`<= 2200px`), optionally trim social-crop padding, and emit `manifest.json` with exact `width`/`height` values so every Figma placeholder rectangle matches its image's true aspect ratio.

---

### Phase 4: Build the 7-Zone Composite Study Board

Consult `references/board-architecture.md` for full construction recipes, palette helpers (`hex/255`), and layout proportions. Build incrementally inside **one top-level white wrapper `SECTION`** (so the entire board moves as a single unit):

- **Header & Provenance Table:** `[AI]` board title, lineage pills, synthesis thesis, 4 design-pillar cards, and a native FigJam `TABLE` mapping System Layer → Studio/Team → Credited Leads → Verified Sources.
- **Zone 01 — Editable 1:1 Composite UI Study:** Semantic reconstruction of the target screen (hardware frame if applicable, persistent chrome, Auto-Layout bento cards, editable text, `createNodeFromSvg` icons/illustrations) overlaid with numbered FigJam callout markers (`1..N`).
- **Zone 02 — Spatial & Interaction Anatomy:** Numbered cards matching Zone 01's markers, explaining visual hierarchy, signal color restraint, progressive disclosure, and ergonomic tradeoffs.
- **Zone 03 — Visual System Foundations:** Tokenized color swatches (hex, name, role), editable type ramp paired with glyph-comparison assets, and a connected `SHAPE_WITH_TEXT` + `CONNECTOR` diagram of the rendering or component pipeline.
- **Zones 04–06 — Curated Source Moodboard:** Aspect-ratio-matched image cards grouped chronologically or by provenance (Target Lineage, Agency 1:1 Flat Comps & Stylebooks, Runtime / Design Systems / Next-Gen Evolution) with color-coded provenance badges.
- **Zone 07 — Synthesis Takeaways & Critique Zone:** Grid of `[AI]` takeaway stickies alongside a generously sized empty white participatory section seeded with 2 discussion prompt stickies.

---

### Phase 5: Batch Upload Images & Run Visual Verification

1. **Create all image placeholder rectangles first**, sized strictly to `manifest.json` aspect ratios, and collect their `nodeIds`.
2. **Batch-register uploads** via `tools.figma.upload_assets({ sessionId, fileKey, currentPageId, count, nodeIds, scaleMode: "FILL" })`, then run `scripts/figma_assets.py upload` to parallel-POST every local file to its `submitUrl`.
3. **Run structural + visual audit:**
   - Execute one read-only `use_figma` audit verifying total descendants, placed `IMAGE` fills count matching the manifest, zero stray root nodes outside the wrapper section, and zero child overflows.
   - Capture `get_screenshot` for Zone 01 (composite UI), Zone 03 (foundations), primary moodboard zones, and the full wrapper section (`maxDimension: 2048-2400`).
   - Inspect every screenshot with `read`. Fix any orphaned sections, clipped/overlapping callout badges, mismatched card row heights, or misaligned right edges in one targeted `use_figma` fix script, then capture a final verification screenshot of the changed nodes.

---

## Additional Resources

### Reference Files

- **`references/research-playbook.md`** — Multi-lane reconnaissance strategy, Behance/Dribbble/Cosmos/PDF extraction tricks, `agent-browser --headed` patterns, and visual verification rules.
- **`references/board-architecture.md`** — Detailed 7-zone FigJam/Figma layout architecture, FigJam palette `hex/255` helpers, Auto-Layout + SVG composite reconstruction rules, and visual QA checklist.

### Bundled Scripts

- **`scripts/figma_assets.py`** — Deterministic image normalization (`prepare`) generating exact `WxH` manifest metadata and parallel multipart uploader (`upload`) for Figma `upload_assets` URLs.
