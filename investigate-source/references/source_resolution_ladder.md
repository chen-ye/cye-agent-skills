# Source Resolution Ladder & Acquisition Protocol

This document establishes the mandatory three-tier resolution hierarchy for investigating software systems, tools, libraries, and frameworks.

---

## The Three-Tier Investigation Hierarchy

```
  ┌─────────────────────────────────────────────────────────────┐
  │  TIER 1: Existing Local Source Clones                      │
  │  • Search ~/Projects/public, ~/Extern, ~/Projects, cwd      │
  │  • Inspect git branch, commit, and working tree             │
  │  • Preferred tier: Zero network overhead, zero latency      │
  └──────────────────────────────┬──────────────────────────────┘
                                 │ Not found locally
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  TIER 2: Ephemeral / Shallow Upstream Clones                │
  │  • Resolve upstream git URL via gh, registry, or docs       │
  │  • Shallow clone: git clone --depth=1 --filter=blob:none    │
  │  • Target: /tmp/source-investigations/<name>                │
  │  • Or persistent: ~/Projects/public/<name> if requested     │
  └──────────────────────────────┬──────────────────────────────┘
                                 │ Source genuinely unobtainable
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  TIER 3: Compiled / Minified Runtime Inspection (LAST RESORT)│
  │  • PERMITTED ONLY IF SOURCE IS PROPRIETARY OR UNAVAILABLE    │
  │  • Inspect debug symbols (nm, objdump, DWARF line tables)   │
  │  • Unpack bundled archives (.asar, .par, .whl, .jar)        │
  │  • Extract embedded prompts and strings from .rodata        │
  └─────────────────────────────────────────────────────────────┘
```

---

## 1. Tier 1: Existing Local Clones (Priority 1)

Before performing any network requests or cloning operations, search for an existing checkout on the local filesystem.

### Standard Search Roots
The agent must verify candidate locations in order:
1. **Current Workspace & Ancestors**: The active project directory and any parent workspaces.
2. **Primary Public Checkouts**: `~/Projects/public/<target>` (or `/home/cye/Projects/public/<target>`).
3. **Workspace Checkouts**: `~/Projects/<target>`, `~/Projects/workspaces/<target>`.
4. **External/Submodule Clones**: `~/Extern/<target>`.
5. **Home Directory**: `~/<target>`.
6. **Container/Host Roots**: `/workspace/<target>`.

### Verification Heuristics
A candidate directory is confirmed as a valid source checkout if it contains either:
* A `.git` repository folder.
* A standard package or build manifest:
  * TypeScript/Node: `package.json`
  * Rust: `Cargo.toml`
  * Python: `pyproject.toml`, `setup.py`
  * Go: `go.mod`
  * C/C++: `CMakeLists.txt`
  * Starlark / Metabuild: `*.star`, `BUILD`, `BUCK`
  * Java: `pom.xml`, `build.gradle`
  * Bazel: `WORKSPACE`, `WORKSPACE.bazel`, `MODULE.bazel`

### Freshness & Revision Check
When an existing clone is found:
```bash
git -C <path> rev-parse --abbrev-ref HEAD
git -C <path> rev-parse --short HEAD
git -C <path> status --porcelain
```
Always note whether the local branch matches upstream or carries local modifications.

---

## 2. Tier 2: Shallow / Ephemeral Upstream Clones (Priority 2)

If no local clone exists, obtain the source directly from upstream using high-speed shallow cloning.

### Upstream Discovery Heuristics
1. **GitHub CLI**: `gh repo view <org/repo> --json url`
2. **NPM Registry**: `npm view <package> repository.url`
3. **PyPI API**: Query `https://pypi.org/pypi/<package>/json` for `project_urls.Source` or `project_urls.Homepage`.
4. **Crates.io**: Query `https://crates.io/api/v1/crates/<crate>` for `repository`.
5. **Git remote probing**: Verify reachable heads via `git ls-remote --heads <url>`.

### Recommended Shallow Clone Commands
Do not download full git history unless historical bisecting is explicitly required.

#### Blobless Shallow Clone (Fastest for Large Monorepos):
```bash
git clone --depth=1 --filter=blob:none <upstream-url> /tmp/source-investigations/<project-name>
```

#### Standard Shallow Clone:
```bash
git clone --depth=1 <upstream-url> /tmp/source-investigations/<project-name>
```

### Destination Conventions:
* **Ephemeral Investigation**: `/tmp/source-investigations/<project-name>` (safe temporary workdir, pre-approved for execution).
* **Permanent Local Tool**: `~/Projects/public/<project-name>` (if user requested permanent local installation or tracking).

---

## 3. Tier 3: Compiled Runtime Analysis (Strict Last Resort)

### The Anti-Premature Decompilation Invariant
> **CRITICAL RULE**: Never disassemble, decompile, or deobfuscate minified bundles or binaries if the source code is available or obtainable via git.

Jumping directly to binary strings, minified bundle reverse-engineering, or AST deobfuscation when the underlying source repository is accessible wastes tokens, loses human-authored comments, and introduces diagnostic hallucinations.

### When is Tier 3 Permitted?
Tier 3 is permitted **ONLY** when:
1. The software is closed-source or proprietary with no public or internal repository (e.g. commercial desktop apps, closed vendor firmware).
2. The system is operating in a network-airgapped environment where upstream git endpoints cannot be reached.
3. The question specifically concerns compiler optimizations, binary symbol stripping, or runtime packaging discrepancies between source and shipped binary.
