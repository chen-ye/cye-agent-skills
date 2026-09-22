---
name: investigate-spaces
description: This skill should be used when the user asks to "investigate spaces", "investigate_spaces", "check spaces source", "how does spaces implement", "diagnose spaces behavior", "look up spaces docs", "query spaces docs", "debug spaces rule or checkout", "inspect spaces cache or store", "analyze spaces starlark", or inspect Spaces runtime, CLI commands, crates, and documentation.
version: 0.1.0
---

# Investigating Spaces Runtime, Architecture & Starlark Documentation

This skill provides procedures, path references, diagnostic scripts, and investigation workflows for analyzing the `spaces` CLI codebase, its Rust monorepo crates, Starlark execution engine (`starlark-rust`), dependency DAG task runner, checkout store, and 336 built-in Starlark APIs.

---

## Overview & Source Checkout Locations

Spaces is a high-performance polyrepo workspace manager and metabuild task runner written in Rust:

1. **Active Executable**:
   * Standard local path: `/home/cye/.local/bin/spaces` (or `~/.local/bin/spaces`)
   * Check version: `spaces --version` or `spaces about`
2. **Primary Source Checkout**:
   * Path: `~/Projects/public/work-spaces` (or `/home/cye/Projects/public/work-spaces`)
   * Upstream Repository: `https://github.com/work-spaces/spaces` (branch: `main`)
   * Structure: Full Rust workspace containing `crates/spaces`, `crates/starstd`, `crates/spaces-utils`, `crates/spaces-console`, `crates/spaces-archiver`.
3. **Global Cache & Store Directory**:
   * Path: `~/.spaces/`
   * Stores downloaded tool archives, git object caches, and global checkout store values.
4. **Active Workspace State**:
   * Local runtime directory: `.spaces/` inside any checked-out workspace.
   * Execution logs: `.spaces/logs/latest/__<target_name>.log`
   * Per-rule digests: `.spaces/digests/`
   * Revisions & locks: `.spaces/locks.spaces.star`
5. **Authoritative Embedded Documentation**:
   * Bundled directly inside the binary; rendered via `spaces docs` covering 26 Starlark modules and 336 native functions.

Always prioritize reading the actual source code in `~/Projects/public/work-spaces` and querying `spaces docs` over guesswork.

---

## Core Investigation Workflows

### 0. Locating the Active Spaces Runtime & Checkout

To quickly identify the active binary path, version, source checkout, global store, and workspace root, execute `scripts/find_spaces_checkout.sh`:

```bash
~/.config/opencode/skills/investigate-spaces/scripts/find_spaces_checkout.sh
```

To output machine-readable JSON:
```bash
~/.config/opencode/skills/investigate-spaces/scripts/find_spaces_checkout.sh --json
```

---

### 1. Querying Embedded Starlark Documentation (`spaces docs`)

Spaces embeds complete API references for 26 Starlark modules directly inside the executable.

To search documentation topics or inspect specific function signatures, execute `scripts/query_spaces_docs.py`:

```bash
# List all 26 Starlark modules with function counts
~/.config/opencode/skills/investigate-spaces/scripts/query_spaces_docs.py --list

# View all functions and documentation for a specific module (e.g., workspace, fs, run, text)
~/.config/opencode/skills/investigate-spaces/scripts/query_spaces_docs.py --module workspace

# Inspect docstring, arguments, and returns for a specific function
~/.config/opencode/skills/investigate-spaces/scripts/query_spaces_docs.py --func load_value
~/.config/opencode/skills/investigate-spaces/scripts/query_spaces_docs.py --func text.diagnostic

# Search across all docs for a specific keyword or concept (e.g., forget-inputs, store, digest)
~/.config/opencode/skills/investigate-spaces/scripts/query_spaces_docs.py "load_value"
```

*For a complete catalog of all modules and key signatures, consult `references/starlark_modules.md`.*

---

### 2. Auditing Workspace Configuration & Checkouts (`co.spaces.toml`)

To audit the current workspace, parsed `co.spaces.toml` targets, root Starlark scripts, and recent execution logs, execute `scripts/inspect_spaces_workspace.py`:

```bash
# Inspect current directory (or specify with --dir <path>)
~/.config/opencode/skills/investigate-spaces/scripts/inspect_spaces_workspace.py

# Inspect specific workspace checkout
~/.config/opencode/skills/investigate-spaces/scripts/inspect_spaces_workspace.py --dir ~/Projects/public/work-spaces

# Output machine-readable JSON
~/.config/opencode/skills/investigate-spaces/scripts/inspect_spaces_workspace.py --json
```

Direct CLI queries:
```bash
# Query all checkout targets from co.spaces.toml
spaces query-co entries

# Query target details
spaces inspect <target-name> --details --json
```

---

### 3. Investigating Rule Evaluation & DAG Execution (`crates/spaces/src/runner.rs`)

Spaces builds an acyclic directed graph (DAG) of task rules:

1. **Inspect Rule Construction (`crates/spaces/src/rules.rs`, `crates/spaces/src/builtins/run.rs`)**:
   * Review how `run.add_exec` and `run.add_rule` define labels (`//dir:target`), command arguments, input globs, output paths, and dependencies (`deps`).
2. **Inspect Execution Phases (`crates/spaces/src/task.rs`)**:
   * `Phase::Checkout`: Active during `spaces co`, `spaces checkout-repo`, `spaces sync`.
   * `Phase::Run`: Active during `spaces run` and `spaces shell`.
   * `Phase::Inspect`: Evaluates rules without executing tasks.
3. **Inspect the Task Runner (`crates/spaces/src/runner.rs`)**:
   * Evaluates dependencies topologically.
   * Compares streaming cryptographic hashes of all files in `inputs` against cached hashes.
   * Automatically skips up-to-date targets.
   * *For comprehensive architectural diagrams and DAG mechanics, consult `references/architecture.md`.*

---

### 4. Investigating Starlark Standard Library & Builtins (`crates/starstd/`)

Native modules are implemented in Rust:

1. **Filesystem & Path Operations (`crates/starstd/src/fs.rs`, `crates/starstd/src/path.rs`)**:
   * Inspect high-performance file read/write (`fs.read_file_to_string`, `fs.write_string_to_file`), path canonicalization, and directory walking (`fs.walk_directory`).
2. **Process Execution & Shell (`crates/starstd/src/process.rs`, `crates/starstd/src/sh.rs`)**:
   * Review direct process spawning (`process.run`) vs shell command lines (`sh.run`).
3. **Structured Data & Text (`crates/starstd/src/text.rs`, `crates/starstd/src/json.rs`, `toml.rs`, `yaml.rs`)**:
   * Review line streaming, regex matching (`text.grep`), diagnostic generation (`text.diagnostic`), and CI annotation rendering (`text.render_diagnostics`).
4. **Embedded Prelude (`crates/spaces/src/assets/prelude/`)**:
   * Contains the `@star/prelude` Starlark standard library scripts included directly inside the binary.

---

### 5. Diagnosing Rule Failures, Logs & Cache Invalidation

When a rule fails or behavior is unexpected:

1. **Inspect Target-Specific Execution Logs**:
   * Do not guess why a rule failed. Inspect `.spaces/logs/latest/`:
   ```bash
   # List recent logs ordered by modification time
   ls -lat .spaces/logs/latest/
   
   # Inspect the isolated stdout/stderr for a failed target
   cat .spaces/logs/latest/__<target_name>.log
   ```
2. **Force Re-execution / Invalidate Caches**:
   * If inputs have not changed but you must force execution:
   ```bash
   spaces run <target> --forget-inputs
   ```
3. **Reverse Relevance in `spaces query search`**:
   * `spaces query search <keyword>` outputs results with the **least relevant match first (top)** and the **most relevant match last (bottom)**. Always inspect search output from the bottom up.

---

### 6. Inspecting Subcommands & CLI Argument Parsing (`crates/spaces/src/arguments.rs`)

To investigate command-line flags, options, and verbosity modes:

1. **Review CLI Definition (`crates/spaces/src/arguments.rs`)**:
   * Uses `clap` to parse commands: `co`, `checkout`, `checkout-repo`, `sync`, `run`, `inspect`, `query`, `query-co`, `shell`, `docs`, `about`, `tools`, `foreach`, `logs`, `store`, `features`, `version`.
2. **Review Verbosity Levels (`Level`)**:
   * `Trace`, `Debug`, `Message`, `Info`, `App` (default), `Passthrough`, `Warning`, `Error`.
   * Pass `--verbosity=debug` and `--show-elapsed-time` to instrument performance.

---

## Key Subsystems Reference

### `spaces` (CLI & Runtime Engine)
* **Path**: `crates/spaces/`
* **Role**: Primary executable entrypoint, evaluator loop, phase dispatch, task runner, checkout engine, and Starlark builtin modules.

### `starstd` (Native Starlark Standard Library)
* **Path**: `crates/starstd/`
* **Role**: 20+ native Rust modules extending Starlark (`fs`, `process`, `sh`, `text`, `json`, `toml`, `yaml`, `sys`, `time`, `tmp`, `string`, `hash`, `args`, `signal`).

### `spaces-utils` (Core Workspace Logic)
* **Path**: `crates/spaces-utils/`
* **Role**: Workspace boundary detection (`ws.rs`), checkout configuration parsing (`co.rs`), store and cache management (`store.rs`), rule metadata (`rule.rs`), query engine (`query.rs`), execution logs (`logs.rs`), and git operations (`git.rs`).

### `spaces-console` (Terminal Output & Logging)
* **Path**: `crates/spaces-console/`
* **Role**: Console formatting, verbosity filtering, multi-progress bar coordination, and terminal spinners.

### `spaces-archiver` (Archive Drivers)
* **Path**: `crates/spaces-archiver/`
* **Role**: Pack and unpack operations for `tar`, `zip`, `http_archive`, and `oras` (OCI registry artifacts).

---

## Supporting Resources

* **`references/architecture.md`**: Complete Rust monorepo crate breakdown, evaluation lifecycle, dependency DAG, and task runner mechanics.
* **`references/starlark_modules.md`**: Authoritative reference catalog for all 26 Starlark modules (builtins and `starstd`) with function signatures and examples.
* **`references/workspace_and_store.md`**: Comprehensive guide to workspace layout, `co.spaces.toml` schemas, dev-branches, checkout store precedence (`workspace.load_value`), and `.spaces/` runtime state.
* **`scripts/find_spaces_checkout.sh`**: Automated runtime, binary, source checkout, and workspace discovery tool.
* **`scripts/query_spaces_docs.py`**: Fast search and extraction tool for `spaces docs` Starlark documentation.
* **`scripts/inspect_spaces_workspace.py`**: Workspace audit and log triage tool.
