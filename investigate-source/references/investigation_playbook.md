# Source-Available Codebase Investigation Playbook

This playbook provides a systematic, step-by-step methodology for dissecting an unfamiliar source-available codebase quickly and accurately.

---

## Phase 1: Entrypoint & Manifest Reconnaissance

Start by identifying the language runtime, package boundaries, and entrypoints:

### 1. Inspect the Root Manifest
* **TypeScript / Node**: Inspect `package.json` for `"workspaces"`, `"scripts"`, `"dependencies"`, and `"bin"`.
* **Rust**: Inspect `Cargo.toml` for `[workspace]` members, `default-members`, and `[[bin]]` targets.
* **Go**: Inspect `go.mod` for module path and `cmd/` for binary packages.
* **Python**: Inspect `pyproject.toml` or `setup.py` for `[project.scripts]` or entrypoints.
* **Starlark / Metabuild**: Inspect `*.star`, `BUILD`, `BUCK`.

### 2. Locate the Execution Entrypoint
Trace the user command to its physical code entry:
* CLI argument parsing layer (e.g. `clap` in Rust, `commander`/`cac` in TS, `argparse`/`click` in Python, `cobra` in Go).
* Find the main dispatch router (usually `src/main.rs`, `src/cli.ts`, `src/index.ts`, `cmd/main.go`).

---

## Phase 2: Domain Interfaces & Protocol Mapping

Before reading business logic line-by-line, extract the data structures that define the system boundaries:

### 1. Types, Traits & Interfaces
* Search for core type definitions:
  * TypeScript: `src/types/`, `src/schema/`, or `interface`/`type` declarations.
  * Rust: `struct`, `enum`, `trait` definitions in `types.rs`, `schema.rs`, or `model.rs`.
  * Go: `type ... struct`, `type ... interface` in domain packages.

### 2. Message & Wire Protocols
* Identify how commands, events, or RPC payloads are serialized:
  * JSON-RPC / ACP / LSP message schemas.
  * Protocol buffers (`.proto`), GraphQL schemas, or OpenAPI specifications.

---

## Phase 3: Service Layer & Flow Tracing

Follow the execution lifecycle from input to execution:

### 1. Command Routing
* Map the CLI subcommand or API endpoint to the handling controller or service function.
* Trace option defaults, environment variable overrides, and configuration merging.

### 2. Security & Permission Gates
* Identify where file mutations, shell commands, or external network requests are authorized.
* Look for sandbox checks, path normalization, allowlists/denylists, and user-prompting gates.

### 3. State & Cache Persistence
* Locate where persistent state is written:
  * SQLite databases (`.db`), JSON/TOML state files, global cache stores (e.g., `~/.<tool>/`).
  * Check invalidation conditions, TTLs, and file locking mechanisms (`flock`, `fs_mutex`).

---

## Phase 4: Test Suite & Edge Case Mining

Test files represent the highest-trust documentation of intended behavior:

1. **Find Test Suites**:
   * Search `tests/`, `__tests__/`, `*_test.go`, `*.test.ts`, `tests/*.rs`.
2. **Discover Edge Cases**:
   * Review negative tests: look for expected error codes, permission denials, malformed inputs, and retry loops.
3. **Inspect Fixtures**:
   * Review sample input files and mock configurations in `testdata/` or `fixtures/`.

---

## Phase 5: Synthesis & Diagnostic Tools

When concluding an investigation:

1. **Synthesize Invariants**:
   * State the architectural guarantees (e.g., "External mutations require two-tier approval", "Rule digests are computed from streaming sha256 hashes").
2. **Codify Repeatable Discovery**:
   * If the tool is investigated frequently across turns, consider authoring a dedicated `investigate-<tool>` skill with scripts for CLI queries, embedded docs search, and workspace audits.
