# Paseo Architecture & Subsystems Map

This document details the internal runtime architecture, monorepo packages, daemon subsystems, workspace isolation models, and storage layout of Paseo (`paseo`).

---

## 1. High-Level Architecture

Paseo is a local-first client-server system for managing, supervising, and collaborating with autonomous AI coding agents:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Mobile App    │      │       CLI       │      │   Desktop App   │
│     (Expo)      │      │   (Commander)   │      │   (Electron)    │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         │       WebSocket        │       WebSocket        │    Managed subprocess
         │       (direct or       │       (direct)         │    + WebSocket
         │        relay)          │                        │
         └────────────┬───────────┴────────────────────────┘
                      │
               ┌──────▼──────┐
               │   Daemon    │  (Node.js / @getpaseo/server)
               │ (Port 6767) │
               └──────┬──────┘
                      │
   ┌────────────┬─────┴──────┬────────────┬────────────┐
   ▼            ▼            ▼            ▼            ▼
┌──────┐    ┌───────┐    ┌───────┐    ┌────────┐   ┌───────┐
│ OMP  │    │Claude │    │ Codex │    │OpenCode│   │  ACP  │
│(RPC) │    │ (SDK) │    │(Server)│   │        │   │Agents │
└──────┘    └───────┘    └───────┘    └────────┘   └───────┘
```

### Core Tenets
1. **Local-First Execution**: Agents, credentials, and code repositories stay strictly on the local machine (or the user-managed remote server).
2. **Multi-Agent Supervision**: Single centralized control plane across multiple different agent harnesses (OMP, Claude Code, OpenAI Codex, OpenCode, ACP agents).
3. **Workspace Isolation**: Worktrees and sandboxes isolate agent operations from the user's primary working tree.
4. **Real-time Streaming**: Event-driven architecture with monotonic timeline sequencing and WebSocket subscriptions.

---

## 2. Monorepo Package Map (`packages/`)

Paseo is organized as a TypeScript monorepo containing 11 packages:

| Package | Path | Responsibility |
| :--- | :--- | :--- |
| **`@getpaseo/server`** | `packages/server/` | The core daemon. Manages agent processes, workspaces, terminals, MCP bridge, and WebSocket API. |
| **`@getpaseo/cli`** | `packages/cli/` | The `paseo` command-line tool for controlling the daemon, workspaces, scripts, and agents. |
| **`@getpaseo/protocol`** | `packages/protocol/` | Shared wire schemas, Zod validators, WebSocket event contracts, and provider manifests. |
| **`@getpaseo/client`** | `packages/client/` | Client library and `PaseoClient` SDK facade for communicating with the daemon over WebSocket. |
| **`@getpaseo/app`** | `packages/app/` | Cross-platform client UI (React Native / Expo / Web / Desktop UI renderer). |
| **`@getpaseo/desktop`** | `packages/desktop/` | Electron desktop wrapper for macOS, Linux, and Windows; auto-starts bundled daemon. |
| **`@getpaseo/plugin`** | `packages/plugin/` | Plugin development SDK, plugin runtime, and lifecycle hooks (`index.server.ts`). |
| **`@getpaseo/relay`** | `packages/relay/` | End-to-end encrypted relay transport for pairing and remote access across firewalls. |
| **`@getpaseo/highlight`** | `packages/highlight/` | High-throughput terminal and code syntax highlighting engine. |
| **`@getpaseo/expo-two-way-audio`** | `packages/expo-two-way-audio/` | Native low-latency audio streaming for voice interaction with agents. |
| **`@getpaseo/website`** | `packages/website/` | Public documentation, landing pages, and release portals (`paseo.sh`). |

---

## 3. Daemon Subsystems (`packages/server/src/server/`)

The daemon (`@getpaseo/server`) is the central orchestrator:

* **`bootstrap.ts`**: Daemon entrypoint. Sets up HTTP/WebSocket servers, loads configuration, connects relay, and initializes storage.
* **`websocket-server.ts`**: Handles client connections, the `hello` handshake, binary frame codecs, and connection heartbeats.
* **`session.ts`**: Manages per-client subscriptions, timeline projections, and live terminal attachments.
* **`agent/agent-manager.ts`**: Central state machine for agents:
  * Lifecycle operations: create, run turn, steer, abort, resume, fork, archive.
  * Timeline journal with monotonic sequence numbers (`seq`), epoch tracking, and persistence.
  * Out-of-band slash command dispatching (`tryRunOutOfBand`).
* **`agent/agent-storage.ts`**: JSON persistence store managing agent snapshots under `$PASEO_HOME/agents/<agent-id>.json`.
* **`agent/tools/`**: Shared transport-neutral tool catalog containing Paseo's native management tools (`create_agent`, `send_agent_prompt`, `create_workspace`, etc.).
* **`agent/mcp-server.ts`**: Thin adapter exposing `PaseoToolCatalog` as an MCP server for providers that only speak MCP.
* **`agent/providers/`**: Provider-specific adapters integrating external coding agent engines:
  * `omp/`: Native OMP RPC provider with `set_host_tools`, `rpc-ui` permissions, and subagent streams.
  * `claude/`: Anthropic Claude Agent SDK integration.
  * `codex-app-server-agent.ts`: OpenAI Codex app server integration.
  * `opencode-agent.ts`: OpenCode server loopback bridge.
  * `pi/`: Pi RPC provider.
  * `acp-agent.ts`: Generic and specialized Agent Client Protocol adapters (Copilot, Cursor, Kimi).
* **`directory-sync/`**: Global reconciliation tracking state changes across projects, workspaces, and agents.
* **`workspace-labels/`**: Local tag and label assignments with atomic journaled commits.
* **`schedule/`**: Cron-driven background scheduler for autonomous agent runs and periodic heartbeats.

---

## 4. Workspace & Worktree Isolation Model

Paseo decouples workspaces from agent processes:

1. **Local Isolation (`isolation: "local"`)**:
   * Runs directly in an existing project directory on disk.
2. **Worktree Isolation (`isolation: "worktree"`)**:
   * Automatically creates a git worktree under `~/.paseo/worktrees/<slug>/`.
   * Modes:
     * `branch-off`: Creates a new branch from a base branch (`--new-branch <name> --base <branch>`).
     * `checkout-branch`: Checks out an existing branch in an isolated worktree (`--branch <name>`).
     * `checkout-pr`: Checks out a GitHub/GitLab pull request (`--pr-number <n>`).
   * Cleanly de-allocated when the last workspace referencing the worktree is archived.
3. **Workspace Scripts (`paseo.json`)**:
   * Projects can declare background development services in `paseo.json` (e.g. dev servers, build watchers).
   * Paseo supervises their process lifecycle, logs, service ports, and health status.

---

## 5. Storage Layout & Filesystem Structure

All persistent state is stored under `$PASEO_HOME` (default: `~/.paseo`):

```
~/.paseo/
├── config.json               # Main daemon configuration (JSON)
├── daemon.log                # Primary daemon diagnostic logs
├── daemon.pid                # Active daemon process ID lockfile
├── agents/                   # Agent state and timeline JSON records
│   ├── <agent-id>.json       # Persisted agent metadata and conversation entries
│   └── ...
├── worktrees/                # Managed copy-on-write git worktrees
│   ├── <project-slug>--<id>/ # Isolated worktree directories
│   └── ...
├── plugins/                  # Installed local and marketplace plugins
│   └── <plugin-id>/
├── cache/                    # Provider metadata and catalog caches
└── run/                      # Sockets, IPC pipes, and temporary launch scripts
```
