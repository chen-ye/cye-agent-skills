---
name: investigate-omp
description: This skill should be used when the user asks to "investigate omp", "investigate_omp", "check omp source", "how does omp implement", "diagnose omp behavior", "look up omp docs", "query omp internal docs", "debug omp config or permission", "inspect omp approval mode", "analyze omp runtime", or inspect Oh My Pi / OMP internals, tools, and documentation.
version: 0.1.0
---

# Investigating OMP (Oh My Pi) Runtime, Configuration & Documentation

This skill provides procedures, CLI diagnostic tools, path references, and investigation workflows for analyzing the OMP runtime, its hybrid Bun/Rust architecture (`pi-natives`), tool approval and sandboxing subsystem, multi-agent orchestration, and 131 built-in embedded documentation files.

---

## Overview & Installation Locations

OMP is distributed as a self-contained single-executable binary powered by Bun and accelerated by compiled Rust Node-API addons:

1. **Active Executable**:
   * Standard Homebrew path: `/home/linuxbrew/.linuxbrew/bin/omp`
   * Resolves to: `/home/linuxbrew/.linuxbrew/Cellar/omp/<version>/bin/omp`
2. **Global Agent State Directory**:
   * Default: `~/.omp/agent/` (governed by `$PI_CODING_AGENT_DIR`)
   * Configuration: `~/.omp/agent/config.yml` (and optional project-level `<cwd>/.omp/config.yml`)
   * Provider/Model Endpoints: `~/.omp/agent/models.yml`
   * Local State Databases: `agent.db` (auth/credentials), `history.db` (command history), `models.db` (model catalog cache)
   * User Extensions: `~/.omp/agent/extensions/*.ts`
3. **Native Rust Engine (`@oh-my-pi/pi-natives`)**:
   * Installed addon: `~/.omp/natives/<version>/pi_natives.linux-x64-modern.node` (or `baseline.node`)
4. **Execution Logs & Audit Trails**:
   * Process logs: `~/.omp/logs/omp.<date>.<pid>.log`
   * Tool invocation audit records: `~/.omp/logs/.omp.<pid>-audit.json`
5. **Authoritative Embedded Documentation**:
   * Bundled directly inside the executable; accessed via `omp read omp://` or `omp read omp://<path>`.
6. **Source Code Checkout**:
   * Path: `~/Projects/public/oh-my-pi`
   * Upstream Repository: `https://github.com/can1357/oh-my-pi` (branch: `main`)
   * Structure: Full Bun + Rust monorepo containing TypeScript packages under `packages/` (e.g. `@oh-my-pi/pi-coding-agent`) and native Rust crates under `crates/` (e.g. `crates/pi-natives`, `crates/pi-shell`, `crates/pi-ast`).

---

## Core Investigation Workflows

### 0. Locating the Active OMP Runtime & Environment

To quickly identify the active binary path, version, configuration state, native addons, and recent logs, execute `scripts/find_omp_installation.sh`:

```bash
~/.gemini/skills/investigate-omp/scripts/find_omp_installation.sh
```

To output machine-readable JSON:
```bash
~/.gemini/skills/investigate-omp/scripts/find_omp_installation.sh --json
```

---

### 1. Querying Embedded OMP Documentation (`omp://`)

OMP embeds 131 authoritative Markdown documentation files covering every CLI command, setting, tool, native crate, and protocol.

To search documentation topics or query specific sections, use `scripts/query_omp_docs.py`:

```bash
# List all 131 available documentation topics with categories
~/.gemini/skills/investigate-omp/scripts/query_omp_docs.py --list

# Filter topics by category (e.g., tools, natives, mcp, providers)
~/.gemini/skills/investigate-omp/scripts/query_omp_docs.py --list --cat tools

# Read a specific document in full
~/.gemini/skills/investigate-omp/scripts/query_omp_docs.py approval-mode.md

# Search across all 131 docs for a specific concept (e.g., approvalMode, prewalk, direnv)
~/.gemini/skills/investigate-omp/scripts/query_omp_docs.py "approvalMode"
```

*For a categorized index of all 131 documents, consult `references/docs_map.md`.*

---

### 2. Auditing Configuration, Model Roles & Providers

To audit active settings, model role mappings (`default`, `smol`, `slow`), approval policies, and configured LLM providers:

```bash
# Print high-level configuration and security audit overview
~/.gemini/skills/investigate-omp/scripts/inspect_omp_config.py

# Inspect all bash command pattern rules (allow vs. deny vs. prompt)
~/.gemini/skills/investigate-omp/scripts/inspect_omp_config.py --bash-rules

# View configured custom providers and endpoints from models.yml
~/.gemini/skills/investigate-omp/scripts/inspect_omp_config.py --providers

# Dump full resolved settings as JSON
~/.gemini/skills/investigate-omp/scripts/inspect_omp_config.py --json
```

Direct OMP CLI commands:
```bash
# Print active agent directory path
omp config path

# Query a specific setting key
omp config get tools.approvalMode --json
omp config get modelRoles --json

# List all available models from all providers
omp models --json
```

---

### 3. Investigating Tool Approvals, Sandboxing & Bash Security

OMP classifies tools into three tiers (`read`, `write`, `exec`) governed by `tools.approvalMode`:

1. **Review Active Policy**:
   * Inspect `tools.approvalMode` (`write`, `always-ask`, or `yolo`).
   * Inspect per-tool overrides under `tools.approval` in `config.yml`.
2. **Review Command Pattern Matching**:
   * Check destructive command blocks under `bash.patterns` (e.g. `rm -rf *`, `git branch* -D*`, `git reset --*`).
3. **Review Command Interceptor**:
   * Check whether `bashInterceptor.enabled` is active, redirecting commands like `cat`, `grep`, `find`, or `sed -i` to native tools (`read`, `grep`, `glob`, `edit`).
   * *For comprehensive architectural diagrams and security invariants, consult `references/approval_and_security.md`.*

---

### 4. Inspecting Bundled Subagents & Task Orchestration

OMP manages bundled task subagents formatted as Markdown with frontmatter:

```bash
# Unpack bundled agent templates into a temporary directory for inspection
omp agents unpack --dir /tmp/omp-agents-inspect --json

# Inspect unpacked subagent specifications:
# scout.md             - Fast read-only codebase explorer returning compressed context
# reviewer.md          - Diff reviewer for security, performance, and correctness
# security-reviewer.md - Vulnerability hunter and security audit agent
# sonic.md             - High-speed single-task executor
# task.md              - General multi-step execution subagent
```

Key task configuration keys in `config.yml`:
* `task.batch`: Enables multi-agent batch execution with `{ context, tasks[] }`.
* `task.maxConcurrency`: Controls simultaneous subagent worker limits (default: 32).
* `task.isolation.enabled`: Creates copy-on-write Git worktree clones in `~/.omp/wt/` for sandboxed subagent runs.
* `task.prewalk`: Automatically downshifts from a reasoning model to a smol model when editing begins.

---

### 5. Investigating Process Supervision, ACP & Daemons

OMP supervises background processes, language servers, browser automation, and daemon protocols:

1. **Process Supervision (`omp ps`)**:
   ```bash
   # List and inspect running daemon-supervised processes
   omp ps
   ```
2. **Browser Automation (`omp browser-relay`)**:
   * Manages headless Chromium via Puppeteer in `~/.omp/puppeteer/`.
   * Can connect to existing user Chrome windows using `omp browser-relay`.
3. **Agent Client Protocol (`omp acp`)**:
   * Runs OMP as an ACP server over stdio for IDE integration (Zed, Cursor, VS Code).
4. **Auth Broker & Gateway**:
   * `omp auth-broker`: Centralized credential vault and token manager.
   * `omp auth-gateway`: Local forward proxy for OAuth request balancing.

---

### 6. Diagnosing Runtime Behavior & Logs

When diagnosing crashes, unexpected tool behavior, or provider API errors:

1. **Inspect Process Execution Logs**:
   ```bash
   # Tail latest runtime log
   tail -n 100 ~/.omp/logs/$(ls -t ~/.omp/logs/omp.*.log | head -n 1 | xargs basename)
   ```
2. **Inspect Structured Tool Audit Trail**:
   ```bash
   # View recent tool invocations and outcomes from JSON audit log
   tail -n 50 ~/.omp/logs/$(ls -t ~/.omp/logs/.omp.*-audit.json | head -n 1 | xargs basename)
   ```
3. **Inspect Saved Session History**:
   ```bash
   # List session directories
   ls -la ~/.omp/agent/sessions/
   ```

---

## Key Subsystems Reference

### `@oh-my-pi/pi-natives`
* **Path**: `~/.omp/natives/<version>/pi_natives.linux-x64-modern.node`
* **Role**: Rust Node-API acceleration engine powering search, globbing, AST manipulation, PTY streams, and Git operations.

### Tool Approval Subsystem
* **Configuration**: `~/.omp/agent/config.yml` (`tools.approvalMode`, `tools.approval`, `bash.patterns`)
* **Role**: Enforces 3-tier security boundaries (`read`, `write`, `exec`) and sequential glob command vetting.

### Agent Orchestrator & Model Roles
* **Configuration**: `modelRoles` in `config.yml` (`default`, `smol`, `slow`, `plan`)
* **Role**: Manages multi-model routing, subagent batching, prewalk transitions, and advisor watchdog monitoring.

### Documentation VFS (`omp://`)
* **Access**: `omp read omp://<path>`
* **Role**: In-memory / virtual filesystem serving 131 authoritative Markdown documentation files directly from the binary.

---

## Supporting Resources

* **`references/architecture.md`**: Deep dive into the Bun orchestrator, Rust `pi-natives`, ACP protocol, daemons, and storage.
* **`references/docs_map.md`**: Categorized directory map of all 131 documentation files accessible via `omp read omp://`.
* **`references/approval_and_security.md`**: Security guide covering approval tiers, modes, bash pattern matcher, and isolation.
* **`scripts/find_omp_installation.sh`**: Automated OMP installation, binary resolution, and environment discovery tool.
* **`scripts/query_omp_docs.py`**: Fast search and extraction tool for the 131 embedded documentation files.
* **`scripts/inspect_omp_config.py`**: Configuration, security policy, and provider auditing tool.
