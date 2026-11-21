---
name: tooling-friction
description: This skill should be used when tooling, CLI, MCP server, or extension friction is noticed during a session, or when the user asks to "capture tooling pain points", "audit session friction", "file tool friction", "fix this tool's UX", or "triage tooling issues". Spins off a subagent to audit session pain points, presents a terse briefing for user approval, and routes approved items to owned-tool handoff sessions or support skills and wrapper tooling.
---

# Tooling Friction Audit & Remediation

Capture, verify, and remediate friction in CLIs, MCP servers, IDE/browser extensions, and helper scripts encountered during a working session without derailing the main task's context window.

## Core Invariants

1. **Delegate the audit; keep the child `sessionID`.** Spin off a dedicated subagent to review raw session friction and inspect tool sources, then resume that same `sessionID` after user approval so investigation context is not rebuilt from scratch.
2. **Gate on user approval between briefing and remediation.** Never dispatch handoff sessions, edit external repos, or author support skills until the user reviews and approves the terse pain-point briefing.
3. **Pass concrete evidence to the subagent.** Subagents start with fresh context and cannot read the parent turn history unless provided. Supply exact tool names, commands, raw error payloads, file paths, and workarounds used (or pass the parent session ID / trace artifact path so the child can inspect `session.messages` via `tools.openchamber`).
4. **Verify before attributing.** Require the subagent to verify suspect file paths, schemas, or CLI flags in the workspace before recommending a fix. Distinguish verified defects from unverified hypotheses.

---

## Workflow

### Stage 1: Spin Off Friction Audit Subagent

Trigger Stage 1 as soon as notable or recurring tooling friction occurs (schema mismatches, misleading error messages, opaque session state, auth/env footguns, missing read/write bridges, or brittle CLI flags) or when the user asks to capture session pain points.

Dispatch a subagent (`subagent` tool) with `agent: "general"` and `category: "research"` (so the child can read files, inspect `tools.openchamber`, and run non-mutating checks) using this contract:

1. **Scope & inputs:** Provide a chronological list of the friction events from the current session (commands run, MCP tool calls, exact error JSON/strings, manual workarounds required, and any `~/.local/share/opencode/tool-output/` files or parent `sessionId`).
2. **Audit instructions:**
   - Extract and deduplicate concrete pain points (group symptoms sharing one root cause).
   - Inspect `tools.openchamber({ action: "projects.list" })` (and local checkouts when available) to classify each affected tool as **Owned** (local repo or extension registered in OpenChamber / user-maintained) vs. **External / Hard-to-Fix** (third-party SaaS, closed-source binary, upstream-gated API, or disproportionately costly to patch directly).
   - For owned tools, locate the exact file/symbol or schema line responsible when cheaply verifiable; otherwise mark as unverified suspicion.
   - Do **not** mutate files, create sessions, or write skills during Stage 1.
3. **Output constraint:** Return a **terse briefing** — short, high-signal bullets or a compact table (tool, ownership, symptom + exact error/repro, severity). Omit narrative filler.

Record the returned child `sessionID`.

### Stage 2: Present Terse Briefing for User Review

Relay the subagent's findings to the user as a **terse briefing** for review and approval before planning or executing fixes:

- Keep each pain point to 1–2 lines: **Tool** (Owned vs. External), **Issue + Evidence**, **Impact**.
- Pair summary counts with a compact table or stacked cards (use `openchamber_render` with `ui` + `awaitAnswer` when the user needs to select a subset of items or add conditions, or ask directly in chat for simple go/no-go approval).
- Stop and wait for the user's decision.

### Stage 3: Resume Subagent for Remediation Proposals

Once the user approves the briefing (in full or for specific items), resume the **same** child `sessionID` (`subagent({ sessionID, ... })`) with the user's approved item list and any conditions.

Instruct the subagent to produce concrete remediation steps split across two tracks:

#### Track A: Owned Tooling (Direct Fix via Session Handoff)

Apply Track A when the user owns the tool, MCP server, or extension (matched via `projects.list` or local source checkout).

For each approved owned-tool item, instruct the subagent to:
1. Check `tools.openchamber({ action: "session.list", parameters: { directory: "<project-dir>", all: true } })` to see whether an active matching session already exists or a fresh session should be created.
2. Draft the exact handoff payload for `tools.openchamber({ action: "session.create" | "session.send" })`:
   - **Target:** `projectId` / `directory` (use `agent: "orchestrator"` when the profile's default agent is unavailable).
   - **Title:** concise 3–5 word label.
   - **Prompt:** concise context of what workflow hit the bug, numbered pain points with exact error strings, verified `path:line` anchors, and expected behavior or tests to add.

#### Track B: Unowned or High-Friction-to-Fix Tooling (Support Skills & Wrapper Tooling)

Apply Track B when the tool is third-party, upstream-gated (e.g., vendor API permissions/schema), or more expensive to patch upstream than to guard locally.

For each approved external/hard-to-fix item, instruct the subagent to propose one or more of:
1. **Support Skill:** Create or update a dedicated skill (for personal skill repos, write `<skill-repo>/<skill-name>/SKILL.md` and register globally via `npx skills add <skill-repo> -g -s <skill-name> -y`) encoding:
   - Exact working invocation patterns, required env vars, and flag workarounds.
   - Known broken parameters/endpoints to avoid (with exact error signatures).
   - Auth/redaction boundaries and safety invariants.
2. **Support Script / Wrapper Tool:** Propose a small, deterministic helper script (for example, an auth-header extractor, preflight checker, or payload resizer/normalizer) when prose instructions alone cannot prevent the failure.
3. **Upstream Bug Report Draft (Optional):** Draft a minimal reproduction snippet if filing an upstream issue is worthwhile.

### Stage 4: Execute Approved Remediations

Review the subagent's Track A and Track B proposals, confirm execution if the user has not already authorized the specific targets, and execute:

- **Track A:** Dispatch each approved handoff via `tools.openchamber({ action: "session.create" | "session.send" })` (without `returnResult: true` unless the main session needs to block on the child session's outcome).
- **Track B:** Author the approved support skill or helper script, verify any scripts/commands run cleanly, and link new skills through the skills CLI lockfile (`npx skills add <source> -g -s <name> -y`).

Report the dispatched session IDs, created/updated files, and verified checks clearly to the user.
