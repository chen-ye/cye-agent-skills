---
name: investigate-opencode
description: This skill should be used when the user asks to "investigate opencode", "investigate_opencode", "check opencode source", "how does opencode implement", "diagnose opencode behavior", "look up opencode docs", "search opencode codebase", "debug opencode tool or permission", "inspect opencode schema", or analyze OpenCode internals, tools, and documentation.
version: 0.1.0
---

# Investigating OpenCode Source Code & Documentation

This skill provides procedures, path references, and investigation workflows for analyzing the OpenCode codebase, its Effect-TS core services, tool implementations, permission subsystem, and official documentation.

## Overview & Source Checkout Locations

OpenCode source checkouts typically exist in standard local workspace directories:

1. **Primary Source Checkout**: `~/Projects/public/opencode` (or `/home/cye/Projects/public/opencode`)
2. **Alternative Source Checkout**: `~/Extern/opencode` (or secondary worktree/submodule checkouts)
3. **Official Documentation Source**: Located directly inside the checkout repository under:
   * **`packages/web/src/content/docs/`** (or `opencode/dev/packages/web/src/content/docs/` depending on workspace tree depth).
   * Contains the authoritative documentation MDX files for all features, configuration keys, permissions, agents, tools, plugins, and CLI commands.

Always prioritize reading the actual source files and documentation in the checkout over relying on pre-trained assumptions or guesswork.

---

## Core Investigation Workflows

### 0. Locating the Active OpenCode Checkout

To quickly identify the active checkout path, git revision, and documentation tree, execute `scripts/find_opencode_checkout.sh`:

```bash
~/.gemini/skills/investigate-opencode/scripts/find_opencode_checkout.sh
```

To output machine-readable JSON:
```bash
~/.gemini/skills/investigate-opencode/scripts/find_opencode_checkout.sh --json
```

---

### 1. Investigating Official Documentation (`packages/web/src/content/docs/`)

When determining intended user behavior, configuration schemas, or official options, consult the documentation MDX files first.

To search documentation topics or query specific sections:
```bash
# List all available documentation pages
~/.gemini/skills/investigate-opencode/scripts/query_opencode_docs.py --list

# Search docs for a specific concept (e.g., external_directory, auto mode, doom_loop)
~/.gemini/skills/investigate-opencode/scripts/query_opencode_docs.py "external_directory"
```

#### Key Documentation Files:
* **`permissions.mdx`**: Authoritative rules for `allow`, `ask`, `deny`, wildcard matching, home directory expansion (`~`), and `external_directory` semantics.
* **`config.mdx`**: Global configuration reference (`opencode.json` / `opencode.jsonc`).
* **`agents.mdx`**: Built-in agents (`build`, `plan`), subagents (`explore`, `general`), and permission overrides.
* **`tools.mdx`**: Built-in tool behaviors, schemas, and parameter specifications.
* **`plugins.mdx`**: Hook specifications (`preToolUse`, `postToolUse`) and custom plugin writing.
* **`cli.mdx`**: Command-line flags, headless execution (`opencode run`), and daemon options.

*For a full catalog of all 35+ doc pages, consult `references/docs_map.md`.*

---

### 2. Investigating Core Tool Implementations (`packages/core/src/tool/`)

OpenCode tools are implemented as Effect-TS service layers under `packages/core/src/tool/`:

1. **Read Operations (`packages/core/src/tool/read.ts`)**:
   * Inspect how file paths are resolved, paginated (`offset`, `limit`), and sanitized.
   * Observe image ingest handling and base64 normalizations.
2. **Write & Edit Operations (`packages/core/src/tool/write.ts`, `packages/core/src/tool/edit.ts`)**:
   * Inspect atomic file updates, BOM preservation (`writeTextPreservingBom`), and line ending normalization.
   * Observe how `write` creates/overwrites and `edit` performs exact substring replacements.
3. **Shell Execution (`packages/core/src/tool/bash.ts`, `packages/opencode/src/tool/shell.ts`)**:
   * Inspect command line parsing, PTY stream handling, subshell invocation, and working directory resolution.
4. **Subagent Execution (`packages/core/src/tool/task.ts`)**:
   * Inspect subagent dispatch, foreground vs. background mode execution, and session context propagation.

---

### 3. Investigating Permissions & Location Boundaries

To understand how OpenCode secures the filesystem and sandboxes actions:

1. **Inspect Location Mutation Resolution (`packages/core/src/location-mutation.ts`)**:
   * Tracks whether a file path falls inside the project workspace (`locationRoot`).
   * When an external path is targeted, produces an `ExternalDirectoryAuthorization` claim targeting `<dir>/*`.
2. **Inspect Permission Assertions (`packages/core/src/permission.ts`)**:
   * Traces how `PermissionV2.Service.assert` checks the action against user-configured rules.
3. **Inspect the Two-Tier Authorization Invariant**:
   * External file mutations require **both** `external_directory` boundary approval AND `edit` operation approval.
   * *For comprehensive architectural diagrams and security invariants, consult `references/permission_system.md`.*

---

### 4. Investigating Agent Definitions & Subagent Permissions

To diagnose agent behaviors and prompt constructions:

1. **Inspect Native Agent Definitions (`packages/opencode/src/agent/agent.ts`)**:
   * Review default prompt templates, model configurations, and tool restrictions for `build`, `plan`, and `explore`.
2. **Inspect Subagent Permission Inheritance (`packages/opencode/src/agent/subagent-permissions.ts`)**:
   * Review how permissions granted or denied in the parent session filter down to spawned subagents.

---

### 5. Verifying with Core Unit Tests (`packages/core/test/`)

When verifying subtle edge cases or expected error behaviors, examine the unit test suites:

* **`packages/core/test/tool-write.test.ts`**: Tests file creation, BOM deduplication, external path approval, and denied write handling.
* **`packages/core/test/tool-read.test.ts`**: Tests paged reads, binary file rejection, external directory reads, and image ingestion.
* **`packages/core/test/tool-edit.test.ts`**: Tests exact replacement logic, multiple-match rejections, and permission assertions.
* **`packages/core/test/permission.test.ts`**: Tests wildcard matching, glob precedence, and auto-approval logic.

---

## Key Subsystems Reference

### `@opencode-ai/core`
* **Path**: `packages/core/src/`
* **Role**: The core Effect-TS domain layer. Houses tool definitions, location resolution, and the permission assertion engine.

### `opencode` (CLI & Runtime)
* **Path**: `packages/opencode/src/`
* **Role**: Primary application binary, CLI entrypoint, agent orchestrator, and ACP server.

### `@opencode-ai/web` (Docs Site)
* **Path**: `packages/web/src/content/docs/`
* **Role**: Authoritative user-facing documentation in MDX format.

### `@opencode-ai/tui` & `@opencode-ai/app`
* **Paths**: `packages/tui/`, `packages/app/`
* **Role**: Terminal user interface and desktop application shells.

---

## Supporting Resources

* **`references/architecture.md`**: Complete monorepo package breakdown, Effect-TS services, and data flows.
* **`references/docs_map.md`**: Comprehensive directory map of all documentation pages under `packages/web/src/content/docs/`.
* **`references/permission_system.md`**: Deep dive into the two-tier permission system, boundary gates, and evaluation rules.
* **`scripts/find_opencode_checkout.sh`**: Automated checkout discovery and path resolution tool.
* **`scripts/query_opencode_docs.py`**: Fast search and extraction tool for documentation MDX files.
