# OpenCode Permission System Architecture

This guide explains OpenCode's internal permission model, boundary safety checks, authorization layers, and pattern matching.

---

## 1. Two-Tier Authorization Architecture

Every filesystem access in OpenCode passes through a two-tier gate:

```
[Tool Invocation: read/write/edit/bash]
                 │
                 ▼
       Path Location Check
        (Inside workspace?)
          ├── YES ────────────────────────┐
          └── NO                          │
               │                          │
               ▼                          │
       [1. Boundary Gate]                 │
     Check: external_directory            │
          ├── DENY ──► [BLOCK ACTION]     │
          └── ALLOW                       │
               │                          │
               └──────────┬───────────────┘
                          │
                          ▼
                 [2. Operation Gate]
       Check action: read | edit | bash
          ├── DENY ──► [BLOCK ACTION]
          └── ALLOW ──► [EXECUTE OPERATION]
```

### Key Subsystems:
* **Boundary Gate (`external_directory`)**:
  * Triggered whenever an agent touches a path outside the active workspace directory (`worktree`).
  * Generates a glob pattern representing the directory container (e.g. `/home/user/other-project/*`).
  * Does **not** distinguish between read vs. write—it purely grants permission to cross the workspace boundary into that folder.
* **Operation Gate (`read`, `edit`, `bash`)**:
  * Evaluates whether the specific operation is allowed on the target resource.
  * Note that `edit` covers all file modifications (`edit`, `write`, `patch`).
  * **Critical Invariant**: Granting `external_directory` does NOT bypass the `edit` gate. Writing to an external file requires **both** `external_directory` approval and `edit` approval.

---

## 2. Permission Actions & Configuration

Permissions are defined in `opencode.json` / `opencode.jsonc`:

```jsonc
{
  "permission": {
    "*": "ask",
    "read": {
      "*": "allow",
      "*.env": "deny",
      "*.env.*": "deny",
      "*.env.example": "allow"
    },
    "external_directory": {
      "~/Projects/shared/**": "allow",
      "~/Documents/**": "deny"
    },
    "edit": {
      "~/Projects/shared/**": "deny" // Allow reading shared project, but protect against modifications
    },
    "bash": {
      "*": "ask",
      "git *": "allow",
      "rm -rf *": "deny"
    }
  }
}
```

### Action Resolutions:
1. `"allow"`: Executes without user prompting.
2. `"ask"`: Pauses execution and prompts the user (or remote approval gate like AutoGate) for confirmation.
3. `"deny"`: Fails immediately with a permission blocked error.

---

## 3. Evaluation Semantics

* **Last Matching Rule Wins**: When an object syntax is used, patterns are evaluated from top to bottom; the last matching entry determines the action.
* **Wildcards**:
  * `*` matches zero or more characters.
  * `?` matches exactly one character.
* **Home Directory Expansion**:
  * `~` and `$HOME` expand to the current user's home directory.
  * Home expansion does not make an external directory internal—external directory approval is still required.
* **Auto Mode (`--auto`)**:
  * Started with `opencode --auto` or `opencode run --auto`.
  * Automatically converts all `"ask"` decisions into `"allow"`.
  * Does not override explicit `"deny"` rules.
