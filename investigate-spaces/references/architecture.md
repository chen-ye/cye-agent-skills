# Spaces Monorepo Architecture & Subsystems Map

This document details the internal Rust workspace layout, CLI command routing, Starlark evaluation engine, task runner DAG, and cache store architecture of the `spaces` codebase.

---

## 1. Monorepo Organization (`crates/`)

The Spaces codebase is organized as a unified Rust workspace (`Cargo.toml`) structured into modular crates:

| Crate | Path | Role & Key Responsibilities |
| :--- | :--- | :--- |
| **`spaces`** | `crates/spaces` | Primary binary crate and CLI entrypoint. Contains `main.rs`, `clap` argument parsing (`arguments.rs`), execution phases (`task.rs`), rule evaluator (`evaluator.rs`), task runner (`runner.rs`), checkout engine (`co.rs`), sync engine (`sync.rs`), built-in Starlark module bindings (`builtins/`), embedded prelude (`assets/prelude/`), and documentation generator (`docs.rs`). |
| **`starstd`** | `crates/starstd` | Starlark standard library extensions. Implements 20+ modules (`fs`, `process`, `sh`, `text`, `json`, `toml`, `yaml`, `sys`, `time`, `tmp`, `hash`, `string`, `args`, `signal`, `log`, etc.) providing high-performance native implementations for Starlark scripts. |
| **`spaces-utils`** | `crates/spaces-utils` | Shared core domain logic: workspace discovery and resolution (`ws.rs`), checkout schema parser (`co.rs`), store and cache manager (`store.rs`), rule metadata and input hashing (`rule.rs`), target query engine (`query.rs`), execution logging (`logs.rs`), git operations (`git.rs`), and CI annotations (`ci.rs`). |
| **`spaces-console`**| `crates/spaces-console` | Terminal user interface, spinner management, progress bars, formatting, and verbosity filtering across 8 levels (`Trace`, `Debug`, `Message`, `Info`, `App`, `Passthrough`, `Warning`, `Error`). |
| **`spaces-archiver`**| `crates/spaces-archiver` | Archive packing and unpacking supporting `tar`, `tar.gz`, `tar.bz2`, `tar.xz`, `zip`, `http_archive`, and `oras` (OCI registry artifacts). |

---

## 2. CLI Command Pipeline (`crates/spaces/src/arguments.rs`)

Command line invocation flows from `clap` subcommands into dedicated runners:

```
                          ┌────────────────────────┐
                          │     spaces <args>      │
                          └───────────┬────────────┘
                                      │
                         [Clap Subcommand Dispatch]
                                      │
     ┌──────────────┬─────────────────┼─────────────────┬──────────────┐
     │              │                 │                 │              │
     ▼              ▼                 ▼                 ▼              ▼
[Checkout/Co]    [Sync]             [Run]           [Inspect/Query]  [Docs/Tools]
 co.rs          sync.rs           runner.rs        query.rs/inspect.rs  docs.rs
 Phase::Checkout Phase::Checkout  Phase::Run       Phase::Inspect
```

### Core Commands Reference

1. **`spaces co <entry> [name]` / `spaces checkout`**:
   * Evaluates `co.spaces.toml` in the current directory or parent directories.
   * Runs checkout phase rules (`0.checkout.spaces.star`, `1.checkout.spaces.star`).
   * Clones repositories, extracts archives, copies assets, and writes `.spaces/` state.
2. **`spaces checkout-repo --url=<url> --rev=<rev> --name=<name>`**:
   * Directly clones a repository into a new workspace and evaluates its top-level `*spaces.star` files.
3. **`spaces sync`**:
   * Evaluates checkout rules in an existing workspace to update dependencies, rebasing development branches if requested.
4. **`spaces run [target] [-- extra_args]`**:
   * Evaluates `spaces.star` across the workspace in `Phase::Run`.
   * Constructs the dependency DAG, checks input file hashes against the cache, and executes out-of-date targets.
5. **`spaces inspect [target] [--details] [--json]`**:
   * Evaluates rules without executing actions; dumps rule DAG, dependencies, inputs, and outputs.
6. **`spaces query search <keyword>` / `spaces query deps <target>`**:
   * Performs graph queries on targets, dependencies, and reverse dependencies.
   * **Note**: `query search` prints least relevant matches first (top) and most relevant last (bottom).
7. **`spaces shell [--sandbox]`**:
   * Spawns an interactive subshell initialized with the exact environment variables, tool paths, and sysroot configured by the workspace.
8. **`spaces docs`**:
   * Dumps authoritative documentation for all 26 Starlark built-in and `starstd` modules.

---

## 3. Evaluation Lifecycle & Execution Phases

Spaces evaluates Starlark scripts in distinct phases governed by `task::Phase` (`crates/spaces/src/task.rs`):

### Phase 1: `Checkout` Phase
* **Triggered by**: `spaces co`, `spaces checkout`, `spaces checkout-repo`, `spaces sync`.
* **Available Modules**: `checkout.*` (`repo`, `archive`, `http_archive`, `oras`, `asset`, `store_value`), `workspace.*`, `starstd.*`.
* **Forbidden**: `run.add_exec`, `run.add_rule` cannot register execution targets in this phase.
* **Output**: Populated workspace tree on disk, configured dev branches, and local `.spaces/` metadata.

### Phase 2: `Run` Phase
* **Triggered by**: `spaces run`, `spaces shell`.
* **Available Modules**: `run.*` (`add_exec`, `add_rule`, `add_archive`), `workspace.*`, `starstd.*`.
* **Forbidden**: `checkout.repo`, `checkout.archive` cannot mutate checkout members in this phase.
* **Output**: Target dependency DAG compiled in `runner.rs`, task executions, and target logs in `.spaces/logs/latest/`.

### Phase 3: `Inspect` Phase
* **Triggered by**: `spaces inspect`, `spaces query`.
* **Behavior**: Evaluates Starlark scripts to build rule definitions without invoking execution binaries.

---

## 4. Starlark Evaluator & Prelude System

1. **Interpreter**: Powered by `starlark-rust` (Meta's Rust implementation of Starlark).
2. **Global Prelude (`@star/prelude`)**:
   * Embedded in the binary via `include_dir!("$CARGO_MANIFEST_DIR/src/assets/prelude")`.
   * Contains helper Starlark scripts: `rules/run.star`, `rules/checkout.star`, `rules/deps.star`, `rules/env.star`, `rules/glob.star`, `rules/sandbox.star`, `rules/ws.star`, `info.star`, `semver.star`.
3. **Builtin Module Injection (`crates/spaces/src/builtins/`)**:
   * Injects native Rust structures into the Starlark global environment:
     * `workspace`: Workspace paths, environment access, checkout store keys.
     * `checkout`: Workspace member checkout constructors.
     * `run`: Target and rule constructors.
     * `info`: CI detection, OS, architecture, workspace name.
     * `semver`: SemVer parsing and requirement matching.
     * `rlog`: Rule-level structured logging.
4. **Standard Library Injection (`crates/starstd/`)**:
   * Exposes 20+ namespaces (`fs`, `process`, `sh`, `text`, `json`, `toml`, `yaml`, `sys`, `time`, `tmp`, `string`, `hash`, `args`, `signal`).

---

## 5. Dependency Graph & Task Runner (`runner.rs`)

1. **DAG Construction**:
   * Each `run.add_exec` or `run.add_rule` specifies target labels (`//path/to:rule_name`) and `deps = [...]`.
   * `runner.rs` constructs an acyclic directed graph and performs topological sorting.
2. **Caching & Input Fingerprinting**:
   * Rules declare `inputs = [glob(...)]` and `outputs = [...]`.
   * Files matching `inputs` are hashed using streaming cryptographic digests.
   * If the input hash, environment variables, command arguments, and dependencies match the recorded state in `.spaces/`, the rule is **skipped (cached)**.
3. **Cache Bypass (`--forget-inputs`)**:
   * Passing `--forget-inputs` ignores recorded input fingerprints and forces target re-execution.
4. **Log Isolation**:
   * Output from each rule is captured in isolation to `.spaces/logs/latest/__<target_mangled_name>.log`.
