---
name: investigate-paseo
description: This skill should be used when the user asks to "investigate paseo", "investigate_paseo", "check paseo source", "how does paseo implement", "diagnose paseo behavior", "look up paseo docs", "query paseo docs", "debug paseo provider or workspace", "inspect paseo daemon status", "analyze paseo architecture", or inspect Paseo daemon, CLI, client, protocol, and provider internals.
version: 0.1.0
---

# Investigating Paseo Source Code, Runtime & Documentation

This skill provides procedures, CLI diagnostic tools, path references, and investigation workflows for analyzing the Paseo local-first agent management platform, its Node.js daemon (`@getpaseo/server`), provider integrations (OMP, Claude, Codex, OpenCode, ACP), workspace isolation engine, and 109 internal and public documentation files.

---

## Overview & Installation Locations

Paseo is structured as a TypeScript monorepo combining daemon services, a multi-platform client UI, and an extensive provider abstraction layer:

1. **Active CLI Executable**:
   * Resolved path: Detected via `command -v paseo` or standard shims (e.g. `~/.local/share/mise/shims/paseo`, `/usr/local/bin/paseo`).
2. **Daemon Home & State Directory**:
   * Default: `~/.paseo/` (governed by `$PASEO_HOME`).
   * Daemon Configuration: `~/.paseo/config.json`.
   * Daemon Logs: `~/.paseo/daemon.log`.
   * Persisted Agent Sessions: `~/.paseo/agents/<agent-id>.json`.
   * Managed Worktrees: `~/.paseo/worktrees/`.
3. **HTTP & WebSocket API**:
   * Default Listen Address: `http://127.0.0.1:6767`.
   * Health Probe: `http://127.0.0.1:6767/api/health`.
4. **Authoritative Source Code Checkout**:
   * Primary Path: `~/Projects/public/paseo` (or `/home/cye/Projects/public/paseo`).
   * Upstream Repository: `https://github.com/getpaseo/paseo` (branch: `main`).
   * Structure: 11 TypeScript packages under `packages/` (e.g. `@getpaseo/server`, `@getpaseo/protocol`, `@getpaseo/cli`, `@getpaseo/app`, `@getpaseo/client`, `@getpaseo/plugin`).
5. **Documentation Repositories in Source**:
   * Internal Subsystem Docs: `~/Projects/public/paseo/docs/` (42 Markdown files).
   * Public Integrator Docs: `~/Projects/public/paseo/public-docs/` (66 Markdown files).

---

## Core Investigation Workflows

### 0. Locating the Active Paseo Runtime & Environment

To quickly identify the active binary path, version, daemon process status, configuration presence, worktrees, and source checkout, execute `scripts/find_paseo_installation.sh`:

```bash
~/.config/opencode/skills/investigate-paseo/scripts/find_paseo_installation.sh
```

To output machine-readable JSON:
```bash
~/.config/opencode/skills/investigate-paseo/scripts/find_paseo_installation.sh --json
```

---

### 1. Querying Paseo Documentation (`docs/` & `public-docs/`)

Paseo contains 109 authoritative Markdown reference files covering provider architecture, permissions, worktrees, daemon lifecycles, and plugins.

To search documentation topics or query specific sections, use `scripts/query_paseo_docs.py`:

```bash
# List all available documentation topics across internal and public docs
~/.config/opencode/skills/investigate-paseo/scripts/query_paseo_docs.py --list

# Filter topics by category (e.g. docs vs public-docs)
~/.config/opencode/skills/investigate-paseo/scripts/query_paseo_docs.py --list --cat docs

# Read a specific document in full
~/.config/opencode/skills/investigate-paseo/scripts/query_paseo_docs.py architecture.md
~/.config/opencode/skills/investigate-paseo/scripts/query_paseo_docs.py providers.md

# Search across all 109 docs for a specific concept (e.g. "set_host_tools", "worktree", "approval_policy")
~/.config/opencode/skills/investigate-paseo/scripts/query_paseo_docs.py "set_host_tools"
```

*For a complete catalog of all 109 documents, consult `references/docs_map.md`.*

---

### 2. Auditing Configuration, Daemon State & Workspaces

To audit active settings, daemon port status, active worktrees, and persisted agents:

```bash
# Print high-level configuration and runtime status audit
~/.config/opencode/skills/investigate-paseo/scripts/inspect_paseo_config.py

# List detailed persisted agent records
~/.config/opencode/skills/investigate-paseo/scripts/inspect_paseo_config.py --agents

# Dump full resolved state as JSON
~/.config/opencode/skills/investigate-paseo/scripts/inspect_paseo_config.py --json
```

Direct Paseo CLI diagnostic commands:
```bash
# Check daemon health and version
paseo --version
paseo daemon status --json

# List active workspaces and scripts
paseo workspace ls
paseo script ls

# Run provider diagnostics (e.g. omp, claude, codex)
paseo provider diagnostic omp --json
```

---

### 3. Investigating Agent Providers & Protocols

Paseo implements two provider patterns: **Direct** (custom `AgentSession` implementation) and **ACP** (`ACPAgentClient` base class).

1. **OMP RPC Provider (`packages/server/src/server/agent/providers/omp/`)**:
   * Launches `omp --mode rpc-ui --cwd <dir> --session <file>`.
   * Negotiates protocol v2 (`negotiate_protocol: 2`) for chunked Base64 framing up to 64 MiB.
   * Registers native in-process Paseo tools via `set_host_tools` with `loadMode: "essential"`.
   * Subscribes to subagent streams via `set_subagent_subscription("events")` and maps them in `subagent-index.ts`.
   * Intercepts out-of-band commands (`/compact`, `/autocompact`, `/steer`, `/follow-up`, `/handoff`) before LLM turn scheduling.
   * Bridges approval dialogs via `rpc-ui-permission-mapper.ts`.
2. **Claude Code Provider (`packages/server/src/server/agent/providers/claude/`)**:
   * Uses Anthropic Claude Agent SDK with `allowedTools`, `disallowedTools`, and `settings.permissions`.
3. **OpenAI Codex Provider (`packages/server/src/server/agent/providers/codex-app-server-agent.ts`)**:
   * Connects to Codex app server with sandboxed workspace writes and network proxies.
4. **Generic & Dedicated ACP Providers (`packages/server/src/server/agent/providers/acp-agent.ts`)**:
   * Connects to Copilot, Cursor, Kimi, or generic ACP agents speaking standard JSON-RPC 2.0.
   * *For comprehensive architectural diagrams and protocol flows, consult `references/providers_and_protocols.md`.*

---

### 4. Investigating Workspaces & Git Worktrees

Paseo manages isolated development environments:

1. **Review Workspace State Machine (`packages/server/src/server/workspace/`)**:
   * Inspect how worktrees are created, slugged, and de-allocated under `~/.paseo/worktrees/`.
2. **Review Workspace Scripts (`packages/server/src/server/workspace-scripts/`)**:
   * Inspect how `paseo.json` entries are parsed, spawned in supervised terminals, and monitored.
3. **Inspect Directory Synchronization (`packages/server/src/server/directory-sync/`)**:
   * Traces how monotonic sequence numbers and tombstones synchronize workspace states to clients.

---

### 5. Diagnosing Daemon Behavior & Logs

When diagnosing process launch failures, connection timeouts, or provider discrepancies:

1. **Inspect Primary Daemon Log**:
   ```bash
   tail -n 100 ~/.paseo/daemon.log
   ```
2. **Inspect Persisted Agent Transcripts**:
   ```bash
   # List recent agent sessions
   ls -lt ~/.paseo/agents/*.json | head -n 10
   ```
3. **Inspect Active Daemon Process**:
   ```bash
   cat ~/.paseo/daemon.pid && ps -p $(cat ~/.paseo/daemon.pid)
   ```

---

## Key Subsystems Reference

### `@getpaseo/server`
* **Path**: `packages/server/src/`
* **Role**: The Node.js daemon managing WebSocket connections, agent lifecycles, and tool catalogs.

### `@getpaseo/protocol`
* **Path**: `packages/protocol/src/`
* **Role**: Source of truth for all wire schemas, Zod validators, provider configs, and message envelopes.

### `@getpaseo/cli`
* **Path**: `packages/cli/src/`
* **Role**: User-facing command-line interface implemented via Commander.js.

### Native Tool Catalog (`PaseoToolCatalog`)
* **Path**: `packages/server/src/server/agent/tools/`
* **Role**: Transport-neutral definitions of Paseo management tools injected into direct providers or exposed via MCP.

---

## Supporting Resources

* **`references/architecture.md`**: Deep dive into daemon subsystems, package map, workspace isolation, and storage layout.
* **`references/providers_and_protocols.md`**: Guide to Direct vs. ACP providers, OMP RPC integration details, host tools, and out-of-band commands.
* **`references/docs_map.md`**: Categorized directory map of all 109 internal and public documentation files.
* **`scripts/find_paseo_installation.sh`**: Automated Paseo installation, daemon state, and source checkout discovery tool.
* **`scripts/query_paseo_docs.py`**: Fast search and extraction tool across all 109 documentation files.
* **`scripts/inspect_paseo_config.py`**: Daemon configuration, status, worktrees, and agent auditing tool.
