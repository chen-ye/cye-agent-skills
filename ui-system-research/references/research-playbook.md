# Multi-Lane UI Research Playbook

Use this playbook during Phase 1 to locate authoritative first-party assets, agency stylebooks, designer portfolios, and typography/shader documentation without polluting the parent context window.

## 1. Lineage First (Especially From Photos)

Before launching searches, inspect the reference screenshot closely:

- **Tab pills & navigation chrome:** Compare tab labels, dock positions, and top/side status bars against recent software releases rather than assuming the initial product launch UI.
- **Typography & numerals:** Note geometric vs. humanist grotesk cuts, tabular monospaced figures, and weight contrast.
- **Illustration/shader style:** Distinguish flat 2D vector wireframes, photorealistic PBR 3D, stepped cel-shading with contour ink lines, and hybrid 2.5D parallax layers.
- **Include observed labels verbatim** in search queries (for example, exact screen headers, widget titles, or unique feature names) alongside `"UI"`, `"HMI"`, `"infotainment"`, `"software update"`, and `"design system"`.

---

## 2. Parallel `librarian` Reconnaissance Lanes

Launch three disjoint `librarian` subagents (`category: "research"`) in a single turn:

### Lane A: First-Party, Release Docs & Engineering Talks
- Target official product newsrooms, engineering/design blogs, press media kits (`media.*`), and CDN hosts (Cloudinary, Sanity, Imgix, Contentful).
- Search official **PDF Owner's Guides, technical manuals, and release-note PDFs**—these often expose exact feature names, release version timestamps, and clean vector diagrams.
- Search engineering conference talks (Figma Config, Unreal Fest, WWDC, Google I/O, SIGGRAPH) and utility patents, which frequently disclose pipeline internals, shader stages, and full team credit lists.

### Lane B: Design Showcases & Archives
- Query `site:behance.net`, `site:dribbble.com`, `site:layers.to`, `site:figma.com/community`, `site:60fps.design`, `site:awwwards.com`, and `site:mobbin.com`.
- Distinguish between official/staff-designer galleries, contracted agency case studies, and student/community fan concepts.
- **Cosmos MCP check (parent or non-overlapping check):** Search `tools.cosmos.cosmos_search`, `tools.cosmos.cosmos_search_clusters`, and `tools.cosmos.cosmos_list_cluster_elements` for curated UI saves, Instagram design teardowns, and high-res CDN images.

### Lane C: Credited Agencies, Type Foundries & Staff Designers
- Search design press (The Verge, Wallpaper*, Fast Company, Core77, Designboom, Brand New, Typewolf) for external creative agencies, type foundries, and internal design/visualization directors.
- Inspect **personal portfolios** of Associate Partners, Design Directors, Motion Leads, and Technical Illustrators. Individual portfolios frequently retain raw 1:1 flat exports, font specimen SVGs, and process boards absent from corporate case studies.

---

## 3. Extracting Blocked or JS-Rendered Assets

Many design platforms block `webfetch` (`HTTP 403`) or render media solely via client-side JavaScript (Behance galleries, Dribbble shot pages, Figma Community, Unreal Engine spotlights, Exposure stories).

### Isolated `agent-browser --headed` Pattern

Use a dedicated per-task session with `--headed` so anti-bot TLS/headless checks pass:

```bash
SESSION="$(agent-browser session id --scope worktree --prefix ui-study)"
agent-browser --session "$SESSION" --headed open "<TARGET_URL>"
agent-browser --session "$SESSION" wait 2500
```

Extract all high-resolution `<img>`, `<video>`, `<iframe>`, and `.pdf` links via `eval --stdin`, scroll down once to trigger lazy-loaded Behance/Dribbble modules if needed, and always close the session when finished:

```bash
agent-browser --session "$SESSION" close
```

### Upgrading CDN URLs to Full Resolution

- **Behance:** Replace `/project_modules/1400_webp/...` or `/max_1200_webp/...` with `/project_modules/source/...` (or `/fs/...`). Verify `HTTP 200` and `content-type: image/png` via `curl -sI`; note that `.png` URLs under `1400_webp` actually return WebP bytes.
- **Sanity / Imgix:** Strip width/quality downscale query params (e.g., `?w=600&q=85...`) to fetch native resolution.
- **Cloudinary (`media.*`):** Request `w_1920,f_jpg,q_auto,c_lfill` (or `f_png`) for clean raster downloads, and check video `poster` URLs (`f_jpg,so_auto,c_limit,w_1280`).
- **Behance Adobe CCV embeds:** Fetch the embed HTML (`https://www-ccv.adobe.io/v1/player/ccv/<id>/embed?api_key=behance1`) only if allowed; note Adobe EdgeSuite CDN often blocks raw `curl` without browser headers.
- **Editorial SVGs & MP4 reels:** Render static SVGs with `rsvg-convert -w 1920 -h 1080`. Watch for SMIL `<animate>` SVGs that only show frame 0 statically—download the companion `.mp4` reel and extract representative frames with `ffmpeg -vf "fps=1/2"` instead.

---

## 4. Visual Verification & Gap Discipline

1. Download every candidate image into `/tmp/opencode/<slug>-study/` before building the Figma board.
2. Inspect candidate images using `read` to verify:
   - The image actually depicts the target product (not an unrelated "related shots" thumbnail scraped from the bottom of a showcase page).
   - Whether it is a **1:1 flat UI export**, a **press/studio photograph**, or a **speculative community mockup**.
   - Whether crops or excessive social-media whitespace borders need trimming (`--trim`) before upload.
3. If no public 1:1 flat export exists for the exact target sub-screen, state that gap explicitly in both the Figma board header/provenance notes and the final response, and reconstruct the screen cleanly in Zone 01 as editable layers.
