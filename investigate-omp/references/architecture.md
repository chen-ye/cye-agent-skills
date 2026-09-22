# OMP (Oh My Pi) Runtime Architecture & Subsystems Map

This document details the internal runtime architecture, hybrid Bun/Rust execution model, tool approval subsystems, process supervision, and storage layout of OMP (`omp`).

---

## 1. High-Level Architecture & Hybrid Runtime

OMP is structured as a dual-layer, high-performance coding agent runtime combining JavaScript/TypeScript orchestration running on Bun with native Rust acceleration:

| Subsystem Layer | Technology / Binary | Role & Key Responsibilities |
| :--- | :--- | :--- |
| **CLI & Orchestrator** | Bun Standalone Executable (`/home/linuxbrew/.linuxbrew/bin/omp`) | Top-level CLI entrypoint, agent loop, prompt generation, tool dispatch, MCP protocol client, and ACP (Agent Client Protocol) server. |
| **Native Engine** | Rust N-API Addon (`@oh-my-pi/pi-natives`) | High-throughput file search, AST matching/editing, PTY process isolation, Git/Jujutsu operations, and terminal graphics. |
| **Process Supervisor** | Daemon Broker (`omp ps`, `~/.omp/run/daemons/`) | Supervises background tasks, headless browser instances, language servers, and long-running services (`hub` tool). |
| **Auth Broker & Gateway** | Credential Vault (`omp auth-broker`, `omp auth-gateway`) | Secure credential storage, token rotation, and OAuth balancing forward proxy. |
| **Documentation Virtual FS** | Embedded VFS (`omp read omp://`) | Authoritative repository of 131 internal Markdown reference documents bundled directly inside the binary. |

---

## 1.1 Upstream Source Monorepo (`can1357/oh-my-pi`)

The official source code is hosted at `https://github.com/can1357/oh-my-pi` (MIT license). The monorepo consists of:

### TypeScript Packages (`packages/`)
* **`packages/coding-agent`** (`@oh-my-pi/pi-coding-agent`): The primary CLI and orchestrator.
* **`packages/agent`** (`@oh-my-pi/pi-agent-core`): Core agent runtime and state machine.
* **`packages/ai`** (`@oh-my-pi/pi-ai`): Multi-provider LLM streaming client.
* **`packages/natives`** (`@oh-my-pi/pi-natives`): N-API JavaScript binding loader for compiled Rust addons.
* **`packages/tui`** (`@oh-my-pi/pi-tui`): Differential TUI rendering engine.
* **`packages/catalog`** (`@oh-my-pi/pi-catalog`): Model catalog database and provider registry.
* **`packages/collab-web`** (`@oh-my-pi/collab-web`): Real-time collaborative web and terminal relay client.
* **`packages/mnemopi`** (`@oh-my-pi/pi-mnemopi`): Local SQLite long-term memory engine.
* **`packages/browser-relay`** (`@oh-my-pi/browser-relay`): Chrome extension and CDP bridge.

### Rust Crates (`crates/`)
* **`crates/pi-natives`**: Aggregates all native modules into a single `cdylib` N-API addon.
* **`crates/pi-shell`**: Embedded PTY and in-process bash runtime.
* **`crates/pi-ast`**: Tree-sitter and ast-grep AST engine across 50+ languages.
* **`crates/pi-iso`**: Copy-on-write worktree isolation (APFS, btrfs, overlayfs).
* **`crates/pi-voice`**: Audio capture, Opus codec, and WebRTC streaming.
* **`crates/pi-walker`**: Parallel ignore-aware filesystem walker and scan cache.
* **`crates/pi-edit`**: Hashline patch engine with content-hash anchors and atomic application.
* **`crates/pi-builtins`**: 67 in-process command-line utilities (ls, sed, sort, jq, etc.).
* **`crates/vendor/brush-core`**: Vendored fork of the brush shell.

## 2. Native Engine: `@oh-my-pi/pi-natives`

To deliver sub-millisecond file scans and responsive TUI updates, OMP delegates performance-critical workloads to a compiled Rust Node-API addon loaded at startup from `~/.omp/natives/<version>/`:

* **`pi_natives.linux-x64-modern.node`**: AVX2/FMA-accelerated native library for modern x86-64 CPUs.
* **`pi_natives.linux-x64-baseline.node`**: Generic fallback library for older CPU microarchitectures.

### Core Primitives Implemented in Rust:
1. **Workspace Scanning & Search**:
   * Multi-threaded ripgrep-style regex search and fast globbing respecting `.gitignore` and `.ompignore`.
   * Fast file structure outline generation and diff calculation.
2. **AST Parsing & Rewriting**:
   * Tree-sitter / AST-grep integration for structural code queries (`ast_grep`) and safe AST replacements (`ast_edit`).
3. **PTY & Process Isolation**:
   * Native pseudoterminal (PTY) allocation and stream multiplexing for interactive command execution.
   * Fine-grained shell sandboxing and process group management.
4. **Git & VCS Primitives**:
   * Direct in-process Git operations and Jujutsu workspace tree manipulation, bypassing subshell overhead.
5. **Terminal UI & Desktop Integration**:
   * SIXEL graphics rendering, terminal diff highlighting, clipboard access, and desktop screen capture.

---

## 3. Agent & Subagent Orchestration

OMP features a flexible multi-agent architecture configured via `~/.omp/agent/config.yml`:

### A. Model Roles
* **`default`**: Primary coding and orchestrator model (e.g., `rrllm/gemini-3.8-flash:high`).
* **`smol`**: Fast, low-latency model used for scout exploration, summaries, and title generation (e.g., `rrllm/gemini-3.5-flash-lite:medium`).
* **`slow`**: Deep reasoning model for architecture planning and hard bug diagnosis (e.g., `litellm/google/gemini-3.1-pro-preview-customtools:high`).
* **`plan`**: Specialized planning model used when `--plan` or `/plan` mode is active.

### B. Bundled Task Agents (`omp agents unpack`)
OMP ships with bundled specialized subagents defined in Markdown with frontmatter:
* **`scout`**: Fast read-only codebase explorer returning compressed structured findings.
* **`reviewer`**: Code review agent checking diffs for security, performance, and correctness.
* **`security-reviewer`**: Specialized security auditor scanning for vulnerabilities.
* **`sonic`**: High-speed single-task executor.
* **`task`**: Default general-purpose subagent for delegating multi-step work units.

### C. Execution Optimizations
* **Batch Task Spawning (`task.batch: true`)**: Allows spawning multiple independent subagents in parallel with a single tool call carrying `{ context, tasks[] }`.
* **Prewalk (`--prewalk` / `task.prewalk`)**: Starts an implementation plan on a high-tier reasoning model, then automatically steps down to the `smol` role at the first edit/write.
* **Advisor Watchdog (`--advisor`)**: Runs an isolated background agent that passively reviews every turn and injects steerage notes when anomalies occur.

---

## 4. Tool System & Security Model

OMP implements a 3-tier approval hierarchy governed by `tools.approvalMode`:

### A. Approval Tiers
1. **`read`**: Read-only operations (`read`, `grep`, `glob`, `web_search`).
2. **`write`**: Workspace-modifying operations that do not execute arbitrary binaries (`edit`, `write`, `todo`).
3. **`exec`**: Arbitrary execution or broad actions (`bash`, `eval`, `browser`, `computer`, `task`).

### B. Approval Modes
* **`always-ask`**: Auto-approves `read` only; prompts for `write` and `exec`.
* **`write`** (Common Default): Auto-approves `read` and `write`; prompts for `exec` unless covered by allowlist rules.
* **`yolo`**: Auto-approves all tiers (subject to explicit deny rules).

### C. Pattern-Based Security Matching (`bash.patterns`)
The bash tool evaluates command strings against an ordered list of glob patterns in `config.yml`:
* Deny patterns (e.g. `rm -rf *`, `git push* *`, `git reset --*`) immediately block high-risk commands.
* Allow patterns grant silent auto-execution for vetted tools (e.g. `pytest*`, `cargo test*`, `bun test*`).
* Fallback `*` policy prompts the user when no explicit match exists.

---

## 5. Storage Layout & Filesystem Structure

```
~/.omp/
├── agent/
│   ├── config.yml            # Primary global configuration (YAML)
│   ├── models.yml            # Custom provider endpoints and API keys
│   ├── agent.db              # SQLite database: credentials & auth tokens
│   ├── history.db            # SQLite database: command and prompt history
│   ├── models.db             # SQLite database: cached provider model catalogs
│   ├── extensions/           # User-installed TypeScript/JavaScript extensions
│   ├── sessions/             # Session storage organized by project path
│   │   └── --path--/         # Workspace-specific JSONL session transcripts
│   └── terminal-sessions/    # Saved interactive PTY session logs
├── cache/                    # Extension and cache databases
├── logs/                     # Process execution logs (omp.<date>.<pid>.log)
│   └── .omp.<pid>-audit.json # Structured audit trail of tool invocations
├── natives/                  # Extracted native Rust Node-API addons
│   └── <version>/            # e.g., pi_natives.linux-x64-modern.node
├── plugins/                  # Installed OMP plugin packages and node_modules
└── run/
    └── daemons/              # PID files, sockets, and browser profiles for daemons
```

---

## 6. Built-in Embedded Documentation (`omp://`)

OMP embeds 131 comprehensive documentation files compiled into the executable itself:
* Accessible via `omp read omp://` (to list all files) or `omp read omp://<path>` (to read).
* Covers CLI flags, runtime internals, tool implementations, MCP integrations, provider quirks, and extensions.
* For the full index and categorical breakdown, consult `references/docs_map.md`.
