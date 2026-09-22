# OpenCode Monorepo Architecture & Subsystems Map

This document details the internal package layout, Effect-TS service layers, tool execution architecture, and runtime boundaries of the OpenCode monorepo.

---

## 1. Monorepo Organization (`packages/`)

OpenCode is organized as a Turborepo/Bun monorepo with strict package boundaries:

| Package | Path | Role & Key Responsibilities |
| :--- | :--- | :--- |
| **`@opencode-ai/core`** | `packages/core` | Core domain engine. Implements Effect-TS services for tool definitions, file mutations, path resolution, and permission assertions. |
| **`opencode`** | `packages/opencode` | Main binary and CLI runtime. Implements agent definitions (`build`, `plan`, `explore`), subagent permissions, ACP server, and shell tools. |
| **`@opencode-ai/web`** | `packages/web` | Official website and documentation site (`src/content/docs/*.mdx`). Primary source of truth for user-facing features and configs. |
| **`@opencode-ai/tui`** | `packages/tui` | Terminal User Interface (TUI) built with terminal components, interactive permission popovers, and status bars. |
| **`@opencode-ai/app`** | `packages/app` | Desktop application frontend, multi-language i18n dictionaries (`src/i18n/*.ts`), and workspace manager. |
| **`@opencode-ai/server`**| `packages/server` | Standalone HTTP / WebSocket server daemon managing sessions, runs, and PTY processes. |
| **`@opencode-ai/sdk`** | `packages/sdk` | Client SDK and OpenAPI schema (`openapi.json`). |
| **`@opencode-ai/protocol`**| `packages/protocol`| JSON-RPC and wire protocol schemas shared across client/server boundaries. |
| **`@opencode-ai/schema`**| `packages/schema` | JSON schema generator for `config.json` (`https://opencode.ai/config.json`). |

---

## 2. Core Subsystems (`packages/core/src/`)

### A. Location & Path Boundary Resolution (`location-mutation.ts`, `location.ts`)
* **`Location.Service`**: Tracks the active workspace directory (the `worktree` or current directory where OpenCode was initialized).
* **`LocationMutation.Service`**: Resolves file and directory targets:
  * **Relative paths**: Must resolve within the active location; relative traversal outside the workspace triggers `relative_escape`.
  * **External absolute paths**: Identified when canonical path does not reside within the workspace root. Triggers `externalDirectory: { action: "external_directory", resource: "<canonical-dir>/*", save: "<canonical-dir>/*" }`.
  * **Crucial Rule**: Boundary resolution does not approve or execute the action—it only produces the required authorization claims.

### B. Tool Execution Framework (`tool/`)
Tools are defined as Effect layers registered in `ToolRegistry.Service`:
* **`read.ts`**: Paged file reader and image ingest. Asserts `external_directory` if external, then asserts `action: "read"`.
* **`write.ts`**: Full file overwrite and file creation. Asserts `external_directory` if external, then asserts `action: "edit"`.
* **`edit.ts`**: Exact text replacement. Checks non-empty replacement, resolves target, asserts `external_directory` if external, then asserts `action: "edit"`.
* **`bash.ts`**: Shell command execution. Asserts `external_directory` if `workdir` is external, parses command lines, and asserts `action: "bash"`.
* **`grep.ts` & `glob.ts`**: Fast AST/regex content search and pattern matching.
* **`patch.ts`**: Unified patch hunk applicator.
* **`task.ts` & `skill.ts`**: Subagent spawning and custom skill invocation.

### C. Permission Engine (`permission.ts`)
* **`PermissionV2.Service`**:
  * Evaluates permission assertions: `assert({ action, resources, save, sessionID, agent, source })`.
  * Evaluates rules matching `allow`, `ask`, or `deny`.
  * Supports wildcard glob patterns (`*`, `?`) and `$HOME`/`~` home expansion.

---

## 3. Runtime & Agent System (`packages/opencode/src/`)

### A. Agent Definitions (`src/agent/agent.ts`)
* **`build`**: Default primary agent. Has full access to tools subject to user permissions.
* **`plan`**: Planning mode agent. Allows `question` and `plan_exit`; explicitly sets `edit: { "*": "deny" }`.
* **`explore`**: Fast exploration subagent. Sets `* : deny`, but explicitly allows `read`, `grep`, `glob`, `list`, `bash`, `webfetch`, `websearch`, and `external_directory`.
* **`general`**: Multi-step worker subagent for parallel research.

### B. Subagent Permission Filtering (`src/agent/subagent-permissions.ts`)
Subagents inherit permissions from their parent session. If the parent session explicitly denies an action or grants `external_directory`, those constraints flow down according to subagent inheritance rules.

### C. External Directory Safety Guard (`src/tool/external-directory.ts`)
* Implements `assertExternalDirectoryEffect(ctx, target, options)`.
* Checks if `target` is contained in `InstanceState.context`.
* If external, generates glob `<parent-dir>/*` and prompts via `ctx.ask({ permission: "external_directory", patterns: [glob], always: [glob] })`.

---

## 4. Specifications & Architecture Documents (`specs/v2/`)

* **`specs/v2/session.md`**: Specification of the session lifecycle, message structures, tool calls, and state transitions.
* **`specs/v2/schema-changelog.md`**: Historical evolution of schemas, config keys, and deprecated flags.
