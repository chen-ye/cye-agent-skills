# OMP Tool Approval, Sandboxing & Security Subsystem

This document provides a comprehensive guide to OMP's security architecture, approval evaluation pipeline, bash pattern matching engine, tool interceptors, and workspace isolation boundaries.

---

## 1. The Three-Tier Tool Classification

Every built-in and extension tool declares an approval tier that determines its default execution privilege:

| Tier | Privilege Level | Built-in Tools | Risk Characteristics |
| :--- | :--- | :--- | :--- |
| **`read`** | Unrestricted Read | `read`, `grep`, `glob`, `web_search`, `lsp` | Reads filesystem state, retrieves symbols, or queries web APIs. Cannot mutate project state. |
| **`write`** | Workspace Mutation | `edit`, `write`, `ast_edit`, `todo`, `context_notes` | Mutates existing files, creates new source files, updates todos. Cannot execute arbitrary binaries. |
| **`exec`** | Arbitrary Execution | `bash`, `eval`, `browser`, `computer`, `task`, `hub` | Spawns shell processes, executes Python/JS cells, interacts with the host desktop, or launches subagents. |

*Note: Any custom tool or extension without an explicit `approval` declaration defaults safely to the `exec` tier.*

---

## 2. Approval Modes (`tools.approvalMode`)

The active approval mode defines which tiers are auto-approved without prompting the human operator:

| Mode | Auto-Approves | Prompts For | Typical Use Case |
| :--- | :--- | :--- | :--- |
| **`always-ask`** | `read` | `write`, `exec` | High-security audits, untrusted codebases, review-only sessions. |
| **`write`** *(Default)* | `read`, `write` | `exec` | Standard development workflow. Safe edits auto-apply; shell execution requires vetting. |
| **`yolo`** (`--auto-approve`) | `read`, `write`, `exec` | *None* (except `deny` rules) | Automated CI/CD pipelines, trusted workflows, batch transformations. |

---

## 3. Evaluation Resolution Pipeline

When a tool call is dispatched by the model, OMP resolves approval through the following precedence hierarchy:

```
                  ┌───────────────────────────────┐
                  │      Incoming Tool Call       │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
             Does tool or argument trigger an explicit
                tool-level DENY or safety rule?
                   ├── YES ──► [BLOCKED / REJECTED]
                   └── NO
                                 │
                                 ▼
             Does user policy (tools.approval.<tool>)
                     define an explicit override?
                   ├── allow  ──► [AUTO-APPROVED]
                   ├── deny   ──► [BLOCKED]
                   ├── prompt ──► [PROMPT USER]
                   └── none
                                 │
                                 ▼
             Is the tool 'bash' with 'bash.patterns'?
                   ├── Matches [DENY]   ──► [BLOCKED]
                   ├── Matches [ALLOW]  ──► [AUTO-APPROVED]
                   ├── Matches [PROMPT] ──► [PROMPT USER]
                   └── Fallback to active approvalMode
                                 │
                                 ▼
             Evaluate against active 'tools.approvalMode':
                   ├── Tier within auto-approved set ──► [AUTO-APPROVED]
                   └── Tier outside auto-approved set ──► [PROMPT USER]
```

---

## 4. Bash Pattern Matching Engine (`bash.patterns`)

The `bash` tool provides granular command vetting using glob patterns evaluated in top-down order in `~/.omp/agent/config.yml`:

### A. Critical Denylist Patterns
These destructive commands are blocked by default to prevent irreversible repository corruption:
```yaml
bash:
  patterns:
    - match: rm -rf *
      approval: deny
    - match: git branch* -D*
      approval: deny
    - match: git checkout* --*
      approval: deny
    - match: git clean -*f*
      approval: deny
    - match: git push* *
      approval: deny
    - match: git reset --*
      approval: deny
    - match: git stash *
      approval: deny
    - match: git worktree remove* *
      approval: deny
```

### B. Standard Allowlist Patterns
Routine read and build commands can be pre-approved for fluid tool usage:
```yaml
    - match: git status*
      approval: allow
    - match: git diff*
      approval: allow
    - match: bun test*
      approval: allow
    - match: cargo test*
      approval: allow
    - match: pytest*
      approval: allow
    - match: "*"
      approval: prompt   # Catch-all: prompt on unrecognized commands
```

---

## 5. Bash Interceptor (`bashInterceptor.enabled`)

When enabled (`bashInterceptor.enabled: true`), OMP intercepts shell commands that duplicate native tool capabilities, directing the agent toward structured, reversible tools:

* **File inspection**: Replaces `cat`, `head`, `tail`, `less`, `more` with the structured `read` tool.
* **Content search**: Replaces `grep`, `rg`, `ag` with the indexed `grep` tool.
* **File lookup**: Replaces `find`, `fd` with the fast `glob` tool.
* **In-place edits**: Replaces `sed -i`, `perl -pi`, `awk -i` with the line-anchored `edit` tool.
* **Shell redirections**: Replaces `echo >`, `cat <<EOF` with the atomic `write` tool.
* **Background daemons**: Replaces `nohup`, `&`, `dev`, `watch` commands with the supervised `hub` tool (`op: "start"`).

---

## 6. Subagent & Workspace Isolation

OMP provides defense-in-depth isolation when delegating work to subagents:

* **Task Isolation (`task.isolation.enabled: true`)**:
  * Creates a copy-on-write Git worktree clone under `~/.omp/wt/` before delegating to subagents.
  * Subagents mutate the isolated clone without affecting the primary working directory.
  * Upon successful completion, changes can be integrated as an atomic patch (`task.isolation.merge: patch`) or reviewed manually.
* **Subagent Permission Inheritance**:
  * Subagents run with their own configured tools and model roles.
  * By default, subagent LSP access is disabled (`task.enableLsp: false`) to minimize overhead.
* **Secret Redaction (`secrets.enabled: true`)**:
  * Scans tool parameters and prompt strings to redact API tokens, private keys, and credential patterns before sending context to remote AI providers.
