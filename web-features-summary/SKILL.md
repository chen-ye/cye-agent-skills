---
name: web-features-summary
description: This skill should be used when the user is performing "frontend development", working with "HTML" or "CSS", or writing "JavaScript" (including "server-side JS", "Node.js", or "JS scripting"). It provides guidance on modern web features that have recently reached cross-browser Baseline status.
version: 1.0.0
---

# Web Features Summary (Baseline 2023-2026)

This skill summarizes web platform features that achieved Baseline status (available in all major browsers: Chrome, Firefox, Safari) between January 2023 and early 2026. Use this to ensure recommended APIs are widely available without polyfills.

## High-Impact Modern Features (Quick Reference)

### JavaScript & Web APIs
- **Array & Collections:**
  - `toSorted()`, `toReversed()`, `toSpliced()`, `with()` (Immutable array updates)
  - `Object.groupBy()`, `Map.groupBy()` (Data grouping)
  - `Set` methods: `intersection()`, `union()`, `difference()`, `symmetricDifference()`
- **Async & Control Flow:**
  - `Promise.withResolvers()` (External promise resolution)
  - `Promise.try()` (Wrap sync/async functions in a Promise)
  - `AbortSignal.any()` (Combine multiple abort signals)
  - `Array.fromAsync()` (Consume async iterables)
- **Utilities:**
  - `URL.canParse()` (Safe URL validation)
  - `Intl.Segmenter` (Locale-sensitive text segmentation)
  - `Intl.DurationFormat` (Duration string formatting)
  - `RegExp.escape()` (Escape special characters in regex strings)

### CSS
- **Layout & Scoping:**
  - **Subgrid:** (`grid-template-columns: subgrid`) Align nested grids to parent tracks.
  - **Container Queries:** (`@container`) Style based on parent size, not viewport.
  - **@scope:** (`@scope (.card) to (.content)`) True style scoping without BEM/Modules.
  - **Nesting:** Native CSS nesting (similar to Sass).
- **Colors & Theming:**
  - `light-dark()`: native light/dark mode color switching.
  - `color-mix()`: Mix colors in any space (e.g., `color-mix(in srgb, red, blue)`).
  - `Relative colors`: Derive colors from others (`rgb(from var(--bg) r g b / 50%)`).
- **Typography & Math:**
  - `text-wrap: balance` (Titles) & `text-wrap: pretty` (Body text).
  - Math functions: `pow()`, `sqrt()`, `hypot()`, `log()`, `exp()`, `round()`, `mod()`, `rem()`, `abs()`, `sign()`.
- **UI & Interaction:**
  - `scrollbar-color` / `scrollbar-width` (Standardized scrollbar styling).
  - `@starting-style` (Entry animations for `display: none` elements).
  - `view-transitions` (Native page/element transitions).

### HTML & DOM
- **Interactivity:**
  - `popover` API (Native overlays/tooltips without z-index wars).
  - `<dialog>` element (now with `requestClose()` for safe closing).
  - `inert` attribute (Disable interaction for parts of the DOM).
- **Semantics & Loading:**
  - `<search>` element (Semantic wrapper for search forms).
  - `<link rel="modulepreload">` (Preload ES modules).
  - `fetchpriority` (Hint resource priority to browser).

## Procedural Guidance

### Verify Feature Availability
1. Check the feature name against the list in `references/baseline_2023_2026.md`.
2. Verify the "Baseline Status" and date.
3. Confirm support versions for Chrome, Firefox, and Safari.

### Implement Modern APIs
1. Prefer APIs with "Baseline: high" for maximum stability.
2. Use APIs with "Baseline: low" if the target audience uses evergreen browsers and the feature was released recently enough to be in current versions.
3. Provide fallbacks or polyfills for features not yet in Baseline if broad legacy support is required.

## Additional Resources

### Reference Files
- **`references/baseline_2023_2026.md`** - Comprehensive list of 100+ web features reaching Baseline status between 2023 and 2026, sorted by release date.

### Examples
- See the description field in the reference file for high-level usage context of each feature.

### Source Data
Information derived from the [web-features](https://www.npmjs.com/package/web-features) project.
