---
name: investigate-source
description: "This skill should be used when the user asks to \"investigate source\", \"investigate codebase\", \"inspect source code\", \"how is this implemented\", \"find implementation of tool\", \"source code investigation\", or when starting an investigation into any software package, tool, CLI, framework, or dependency. Encodes the three-tier resolution hierarchy: utilizing existing local clones first, falling back to temporary shallow clones, and strictly resorting to compiled or minified runtimes only when source is unobtainable."
version: 0.1.0
---

# Source Code Investigation Methodology

This meta-skill defines the standard operating procedure for investigating the implementation, architecture, and behavior of software systems, tools, libraries, and frameworks.

---

## The Three-Tier Resolution Hierarchy

Always resolve and examine target software using this strict precedence order:

| Tier | Strategy | Location & Method | When to Use |
| :--- | :--- | :--- | :--- |
| **Tier 1 (Preferred)** | **Existing Local Clone** | Search `~/Projects/public/`, `~/Extern/`, `~/Projects/`, cwd | Always check first. Zero latency, preserves local branches and context. |
| **Tier 2 (Fallback)** | **Ephemeral / Shallow Clone** | Clone `--depth=1` to `/tmp/source-investigations/<name>` | Use when no local clone exists, but upstream repository is public or accessible. |
| **Tier 3 (Last Resort)** | **Compiled / Minified Runtime** | Inspect debug symbols, DWARF line tables, embedded strings, `.rodata` | **STRICTLY FORBIDDEN** unless source code is completely proprietary or unobtainable. |

> **Crucial Guardrail**: Never decompile, disassemble, or reverse-engineer minified bundles or stripped binaries when human-authored source code can be cloned or read directly.

---

## Core Investigation Workflows

### 0. Automated Source Resolution (`scripts/resolve_source.sh`)

Before manually searching directories or invoking `git clone`, run `scripts/resolve_source.sh`:

```bash
# Check if a local clone exists, or identify upstream repository
~/.config/opencode/skills/investigate-source/scripts/resolve_source.sh <target-name-or-url>

# Automatically clone to /tmp/source-investigations/ if not present locally
~/.config/opencode/skills/investigate-source/scripts/resolve_source.sh <target-name-or-url> --clone-tmp

# Output machine-readable JSON for subagent pipelines
~/.config/opencode/skills/investigate-source/scripts/resolve_source.sh <target-name-or-url> --json
```

---

### 1. Tier 1: Working with Existing Local Clones

When an existing checkout is located:

1. **Verify Checkout Freshness**:
   ```bash
   git -C <path> rev-parse --abbrev-ref HEAD
   git -C <path> rev-parse --short HEAD
   git -C <path> status --porcelain
   ```
2. **Prioritize Real Files Over Guesswork**:
   * Inspect actual files on disk using `read`, `grep`, and `glob`.
   * Never speculate on file contents or extrapolate from memory without reading.
3. **Preserve Repository Integrity**:
   * Do not modify working tree state or switch branches unless explicitly requested by the user.

---

### 2. Tier 2: Fetching Ephemeral / Temporary Clones

When no local checkout exists, but an upstream repository is identified:

1. **Perform a Shallow Clone**:
   Use `--depth=1` to fetch only the latest revision without downloading full git commit histories:
   ```bash
   # Standard shallow clone into approved temporary directory
   git clone --depth=1 <upstream-url> /tmp/source-investigations/<project-name>
   ```
   For large monorepos, append `--filter=blob:none` to minimize network payload.

2. **Persistent Checkouts**:
   If the user indicates ongoing development or asked for a permanent clone, place it in `~/Projects/public/<project-name>`.

3. **Cleanup Protocol**:
   * **Ephemeral Investigation**: `/tmp/source-investigations/<project-name>` (safe temporary directory, auto-created).

---

### 3. Tier 3: Compiled Runtime Analysis (Strict Fallback)

Resort to runtime static analysis **only** when source code is completely proprietary (e.g. vendor-only distributions, closed commercial binaries) or network constraints prevent cloning.

Execute `scripts/inspect_runtime_artifacts.sh`:
```bash
# Inspect binary headers, symbol availability, and stripped status
~/.config/opencode/skills/investigate-source/scripts/inspect_runtime_artifacts.sh /path/to/binary

# Search embedded read-only strings for keywords
~/.config/opencode/skills/investigate-source/scripts/inspect_runtime_artifacts.sh /path/to/binary --query "config"
```

*For comprehensive procedures on DWARF table parsing, unstripped symbol companions, and archive unpacking, consult `references/compiled_runtime_analysis.md`.*

---

### 4. Codebase Navigation Methodology

Once source is resolved (Tier 1 or Tier 2), follow this systematic dissection sequence:

1. **Locate Root Manifest**:
   Identify package manager, monorepo workspaces, and dependencies (`package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, `CMakeLists.txt`, `Makefile`).
2. **Trace CLI / Service Entrypoint**:
   Find argument parsing and router dispatching (`src/main.rs`, `src/cli.ts`, `cmd/main.go`).
3. **Map Domain Types & Protocol Schemas**:
   Inspect core types and interfaces before reading implementation logic.
4. **Inspect Security & Permission Boundaries**:
   Identify where filesystem mutations, shell commands, or external networks are gated.
5. **Mine Test Suites**:
   Inspect unit tests (`tests/`, `spec/`, `*_test.go`) to discover negative test cases, error expectations, and input fixtures.

*For detailed guidance across languages and frameworks, consult `references/investigation_playbook.md`.*

---

## Supporting Resources

* **`references/source_resolution_ladder.md`**: Detailed breakdown of the three tiers, candidate directory trees, and clone invariants.
* **`references/investigation_playbook.md`**: Five-phase guide for rapidly navigating and understanding an unfamiliar codebase.
* **`references/compiled_runtime_analysis.md`**: Last-resort fallback guide for inspecting binary symbols, DWARF line tables, and embedded assets.
* **`scripts/resolve_source.sh`**: Automated detection and shallow cloning tool.
* **`scripts/inspect_runtime_artifacts.sh`**: Fallback utility for inspecting compiled binaries and symbol tables.
