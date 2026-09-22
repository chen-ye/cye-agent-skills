# Paseo Providers & Protocol Architecture

This document details how Paseo interfaces with AI coding agents across **Direct**, **RPC**, and **ACP** integration models, explaining provider capabilities, host tools, permission mappers, and out-of-band commands.

---

## 1. Provider Integration Models

Paseo supports two fundamental provider patterns:

```
                  ┌──────────────────────────────────────────────┐
                  │                 Paseo Daemon                 │
                  └───────┬──────────────────────────────┬───────┘
                          │                              │
             ┌────────────▼────────────┐    ┌────────────▼────────────┐
             │    Direct Providers     │    │      ACP Providers      │
             │ (Custom AgentSession)   │    │ (ACPAgentClient Base)   │
             └────────────┬────────────┘    └────────────┬────────────┘
                          │                              │
       ┌──────────┬───────┴───┬──────────┐               │
       ▼          ▼           ▼          ▼               ▼
    ┌─────┐   ┌───────┐   ┌───────┐  ┌───────┐      ┌─────────┐
    │ OMP │   │Claude │   │ Codex │  │Open-  │      │ Copilot │
    │(RPC)│   │ (SDK) │   │(Server│  │ Code  │      │ Cursor  │
    └─────┘   └───────┘   └───────┘  └───────┘      └─────────┘
```

### A. The Direct Integration Pattern
The provider implements Paseo's `AgentClient` and `AgentSession` interfaces from `agent-sdk-types.ts` directly. This requires managing process lifecycle, stdio streaming, permissions, and session history explicitly, but allows full utilization of the underlying engine's advanced capabilities:
* **`omp` (`providers/omp/`)**: Runs `omp --mode rpc-ui` using newline-delimited JSON RPC with protocol v2 chunking, native in-process Paseo host tools, and subagent stream subscriptions.
* **`claude` (`providers/claude/`)**: Runs in-process or subshell using the Anthropic Claude Agent SDK.
* **`codex` (`providers/codex-app-server-agent.ts`)**: Connects to the OpenAI Codex desktop app server.
* **`opencode` (`providers/opencode-agent.ts`)**: Spawns an OpenCode server with a memory loopback plugin bridge for environment/tool isolation.
* **`pi` (`providers/pi/`)**: Connects to Pi via `pi --mode rpc`.

### B. The ACP Pattern (`ACPAgentClient`)
Providers extend `ACPAgentClient` (`providers/acp-agent.ts`), which implements the standardized Agent Client Protocol (JSON-RPC over stdio). Used for:
* Built-in: `copilot` (`copilot-acp-agent.ts`), `cursor` (`cursor-acp-agent.ts`), `kimi` (`kimi-acp-agent.ts`), `kiro` (`kiro-acp-agent.ts`).
* Custom: User-configured custom providers extending `"acp"` (`generic-acp-agent.ts`).

---

## 2. Deep Dive: The OMP Provider (`providers/omp/`)

Paseo's OMP provider is one of its most sophisticated direct implementations:

### 2.1 Why RPC Mode over ACP Mode?
Paseo intentionally rejects `omp acp` in favor of `omp --mode rpc-ui` for these reasons:
1. **Native Host Tools (`set_host_tools`)**: Paseo injects its native tool catalog (`create_agent`, `send_agent_prompt`, `create_workspace`) directly into OMP with `loadMode: "essential"`. OMP calls these tools over stdio; Paseo executes them in-process and returns `host_tool_result`. ACP has no host tool injection.
2. **Subagent Stream Forwarding**: OMP task subagents (`scout`, `reviewer`, `sonic`) emit `subagent_lifecycle`, `subagent_progress`, and `subagent_event` frames. Paseo's `subagent-index.ts` maps them directly into Paseo's native multi-agent hierarchy. ACP has no subagent protocol.
3. **Mid-Turn Steering**: OMP RPC exposes `steer` and `follow_up` commands with configurable queue modes. Paseo's `steerActiveTurn` can steer an active tool loop without aborting the turn.
4. **Session Tree Branching**: OMP RPC exposes `branch(entryId)` and `get_branch_messages()`, allowing Paseo to rewind to specific tree nodes. ACP only supports coarse `forkSession`.
5. **CWD & Environment Isolation**: Each Paseo agent runs in a dedicated 1:1 `omp` process with isolated environment variables and worktrees.

### 2.2 Launch & Protocol Negotiation
When an OMP session starts (`cli-runtime.ts`):
1. Spawns: `omp --mode rpc-ui --approval-mode <mode> --cwd <dir> --session <file>`
2. Awaits the initial ready frame:
   ```json
   { "type": "ready", "protocolVersion": 1, "supportedProtocolVersions": [1, 2] }
   ```
3. Immediately negotiates protocol v2 (`protocol-session.ts`):
   ```json
   { "type": "negotiate_protocol", "protocolVersion": 2 }
   ```
   This enables chunked lossless Base64 framing up to 64 MiB (`rpc_chunk`).

### 2.3 Permission UI Mapping (`rpc-ui-permission-mapper.ts`)
Under `--mode rpc-ui`, OMP tool approvals arrive as `extension_ui_request` objects with `method: "select"`. Paseo intercepts and translates them:
* Inspects the prompt string (e.g. `"Allow tool: bash"`).
* Extracts tool arguments and formats command diffs.
* Emits a Paseo `AgentPermissionRequest` with `Approve` and `Deny` action buttons.
* Responds to OMP with an `extension_ui_response` carrying `{ value: "Approve" }` or `{ value: "Deny" }`.

---

## 3. Paseo Native Tool Catalog vs. MCP

Paseo tools are **not** implemented as MCP servers internally:
* They live in `packages/server/src/server/agent/tools/` as native TypeScript classes with typed schemas.
* **Direct Providers (OMP, Claude)**: Set `supportsNativePaseoTools: true`. Paseo passes the catalog directly via `set_host_tools` (OMP) or native SDK tool definitions (Claude).
* **MCP-Only Providers**: Set `supportsMcpServers: true`. Paseo's `mcp-server.ts` wraps the catalog into an ephemeral local HTTP endpoint (`/mcp/agents`) and injects it as an external MCP server into the agent process.

---

## 4. Slash Commands & Out-of-Band Handling

Paseo distinguishes between out-of-band control commands and LLM prompt commands:

### Out-of-Band Interception (`tryHandleOutOfBand`)
Handled immediately by Paseo without calling the model:
* **`/compact [instructions]`**: Calls `runtimeSession.compact(args)` directly; updates timeline with compaction events.
* **`/autocompact [on|off]`**: Calls `runtimeSession.setAutoCompaction(bool)`.
* **`/steer <message>`**: Calls `runtimeSession.steer(message)` to steer an in-flight tool loop.
* **`/follow-up <message>`**: Calls `runtimeSession.followUp(message)` to queue a prompt for the next turn.
* **`/handoff [instructions]`**: Calls `runtimeSession.handoff(args)` to generate handoff notes.

### Standard Forwarded Commands
All other slash commands (e.g. `/commit`, `/review`, `/my-skill`, `/mcp`):
1. Paseo sends the raw text via `runtimeSession.prompt("/command args")`.
2. OMP matches the command against its internal registry or loaded skills.
3. If local-only, OMP writes text to `command_output` and returns `agentInvoked: false`. Paseo's `noTurnScheduler` settles the turn immediately without expecting LLM streaming tokens.
