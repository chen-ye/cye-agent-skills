# Modern Web Idioms & Discarded Patterns (2023-2026)

This document maps legacy web development patterns to their modern, native
equivalents.

## JavaScript

### 1. Array Updates

- **Legacy:** Mutating in-place or manual copying with spread.
  ```javascript
  const sorted = [...arr].sort();
  const updated = [...arr];
  updated[i] = val;
  ```
- **Modern:** Use immutable change methods.
  ```javascript
  const sorted = arr.toSorted();
  const updated = arr.with(i, val);
  ```

### 2. Data Grouping

- **Legacy:** Using `reduce()` or Lodash.
  ```javascript
  const groups = items.reduce((acc, item) => {
    (acc[item.type] ??= []).push(item);
    return acc;
  }, {});
  ```
- **Modern:** Use native `groupBy`.
  ```javascript
  const groups = Object.groupBy(items, (item) => item.type);
  ```

### 3. Set Operations

- **Legacy:** Manual filtering or libraries.
  ```javascript
  const intersect = new Set([...setA].filter((x) => setB.has(x)));
  ```
- **Modern:** Native Set methods.
  ```javascript
  const intersect = setA.intersection(setB);
  ```

### 4. Promise Construction

- **Legacy:** Extracting resolve/reject from executor.
  ```javascript
  let resolve, reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  ```
- **Modern:** Use `Promise.withResolvers()`.
  ```javascript
  const { promise, resolve, reject } = Promise.withResolvers();
  ```

### 5. Base64 Conversion

- **Legacy:** Using `atob()`/`btoa()` (string-based) or manual buffer logic.
- **Modern:** `Uint8Array` methods.
  ```javascript
  const base64 = uint8Array.toBase64();
  const bytes = Uint8Array.fromBase64(base64String);
  ```

## CSS

### 1. Conditional Parent Styling

- **Legacy:** Adding classes via JavaScript.
  ```javascript
  if (input.checked) card.classList.add("selected");
  ```
- **Modern:** The `:has()` selector.
  ```css
  .card:has(input:checked) {
    border-color: blue;
  }
  ```

### 2. Modals and Overlays

- **Legacy:** Custom `<div>` with heavy JS for focus trapping and z-index.
- **Modern:** `<dialog>` for modals and `popover` for tooltips/menus.

### 3. Responsive Components

- **Legacy:** Media queries (`@media`).
- **Modern:** Container queries (`@container`). This allows components to be
  reused in different layout contexts (sidebar vs main) without breaking.

### 4. Color Derivation

- **Legacy:** Preprocessor functions like `darken()`.
- **Modern:** `color-mix()` and Relative Color Syntax.
  ```css
  background: color-mix(in srgb, var(--brand), white 20%);
  ```
