# Paseo Documentation Map & File Index

Paseo maintains two comprehensive documentation trees inside its repository:
1. **Internal Architecture & Subsystems Docs**: Located in `docs/` (42 Markdown files).
2. **Public User & Integrator Docs**: Located in `public-docs/` (66 Markdown files).

---

## 1. Internal Engineering Documentation (`docs/`)

Authoritative documentation on daemon internals, protocols, UX architecture, and subsystems:

| Document Path | Core Topic / Content |
| :--- | :--- |
| `docs/architecture.md` | System overview, multi-tier architecture, monorepo package breakdown, and dataflow. |
| `docs/providers.md` | Comprehensive guide on adding and implementing agent providers (Direct vs. ACP, native tools, MCP). |
| `docs/custom-providers.md` | User-defined custom provider manifests, overrides, and environment options. |
| `docs/data-model.md` | Entity schemas for projects, workspaces, agents, timeline items, and transcripts. |
| `docs/agent-lifecycle.md` | State machine for agent creation, prompt scheduling, active-turn steering, cancellation, and archiving. |
| `docs/agent-stream-performance.md` | Streaming optimizations, backpressure handling, and timeline event batching. |
| `docs/permissions.md` | Multi-tier permission model, question elicitation, and approval resolution. |
| `docs/plugins.md` | Paseo plugin system architecture, lifecycle hooks, RPC methods, and isolated sandboxes. |
| `docs/hub.md` | Hub integration for multi-agent coordination, webhooks, and headless automation. |
| `docs/timeline-sync.md` | Monotonic sequencing, epoch counters, and gap detection across WebSocket clients. |
| `docs/terminal-performance.md` | PTY stream multiplexing, chunked rendering, and scrollback memory budgeting. |
| `docs/terminal-activity.md` | Output scanning, terminal idle detection, and background command watchers. |
| `docs/service-proxy.md` | Reverse proxy and port forwarding for workspace web services and dev servers. |
| `docs/rpc-namespacing.md` | RPC method routing and API versioning across server and client SDKs. |
| `docs/protocol-validation.md` | Zod runtime schema assertions and wire validation invariants. |
| `docs/protocol-compatibility.md` | Client/server version skew handling, capability flags, and deprecation policies. |
| `docs/workspaces.md` | Workspace lifecycle, worktree directory management, and slug hashing. |
| `docs/forge-providers.md` | GitHub, GitLab, and local Git forge providers for PR and branch checkout. |
| `docs/file-observation.md` | Multi-root project file watchers and Git status change detection. |
| `docs/docker.md` | Dockerized daemon execution, container mounts, and credential sharing. |
| `docs/ad-hoc-daemon-testing.md` | Testing workflows for running temporary daemon instances in isolated test environments. |
| `docs/testing.md` | End-to-end (Playwright) and unit testing standards across packages. |
| `docs/release.md` | Multi-platform build, packaging, notarization, and distribution workflows. |

---

## 2. Public User & Integrator Documentation (`public-docs/`)

Guides for operators, developers, and users of Paseo:

| Document Path | Topic & Summary |
| :--- | :--- |
| `public-docs/index.md` | Paseo introduction, core value proposition, and quickstart overview. |
| `public-docs/cli.md` | CLI command reference (`paseo run`, `paseo workspace`, `paseo script`, `paseo daemon`). |
| `public-docs/configuration.md` | Daemon configuration (`config.json`), environment variables, and listening options. |
| `public-docs/connectivity.md` | Direct LAN, Tailscale, SSH tunnels, and encrypted relay connectivity. |
| `public-docs/workspaces.md` | Creating and managing local workspaces and isolated Git worktrees. |
| `public-docs/worktrees.md` | Deep dive on branch-off, checkout-branch, and checkout-pr worktree workflows. |
| `public-docs/supported-providers.md` | Supported agent harnesses: Claude Code, OpenAI Codex, OMP, OpenCode, Copilot, Cursor. |
| `public-docs/providers.md` | Setting up provider credentials, custom endpoints, and runtime feature toggles. |
| `public-docs/custom-providers.md` | Defining third-party agents via YAML/JSON manifests. |
| `public-docs/mcp.md` | Configuring Model Context Protocol (MCP) servers for agents. |
| `public-docs/skills.md` | Authoring, discovering, and installing skill packs for agent personas. |
| `public-docs/schedules.md` | Cron schedules for autonomous recurring agent runs. |
| `public-docs/web-ui.md` | Deploying and accessing the browser-based client interface. |
| `public-docs/voice.md` | Setting up low-latency two-way audio and voice interaction. |
| `public-docs/troubleshooting.md` | Diagnostic checklist for provider discovery, port conflicts, and daemon logs. |
| `public-docs/security.md` | Local-first threat model, permission sandboxing, and relay encryption. |

### SDK & Plugin Reference
* `public-docs/sdk/index.md`: JavaScript/TypeScript SDK guide for automating Paseo daemons.
* `public-docs/sdk/agents.md`: Managing agents and subscribing to real-time streams via SDK.
* `public-docs/sdk/workspaces.md`: Programmatic workspace and script management.
* `public-docs/plugins/index.md`: Creating local Paseo plugins to extend the UI and server.
* `public-docs/plugins/reference.md`: Full API surface for plugin hooks and UI components.
