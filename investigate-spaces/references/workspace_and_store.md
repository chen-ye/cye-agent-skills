# Spaces Workspace Lifecycle, Configuration & Store Guide

This guide covers the directory layout of Spaces workspaces, `co.spaces.toml` configuration syntax, the local `.spaces/` runtime state, and the global cache store in `~/.spaces/`.

---

## 1. Workspace Directory Layout

A Spaces workspace consists of root configuration files and a managed `.spaces/` runtime directory:

```
<workspace-root>/
├── co.spaces.toml               # Workspace checkout aliases & configuration
├── 0.checkout.spaces.star       # Early checkout rules (toolchains, archives)
├── 1.checkout.spaces.star       # Main checkout rules (repositories, members)
├── spaces.star                  # Primary task/build/test rules (Phase::Run)
├── <repo_member_1>/             # Cloned repository member
├── <repo_member_2>/             # Cloned repository member
└── .spaces/                     # Local workspace runtime directory
    ├── logs/
    │   ├── latest/              # Symlink to the most recent run's logs
    │   └── <run_timestamp>/     # Target-isolated execution logs (*.log)
    ├── digests/                 # Per-rule input/output fingerprints
    └── locks.spaces.star        # Lockfile pinning repo revisions
```

---

## 2. Checkout Configuration (`co.spaces.toml`)

`co.spaces.toml` defines named checkout targets and workflows, allowing fast branch setup via `spaces co <target> <workspace-name>`.

### Entry Types

#### A. Direct Repository Entry (`[<name>.Repo]`)
```toml
[spaces-dev.Repo]
url = "https://github.com/work-spaces/spaces"
rev = "main"                     # Target branch, tag, or commit
rule-name = "spaces"             # Target directory name (defaults to repo name)
new-branch = ["spaces"]          # Auto-create branch matching workspace name
clone = "Default"                # "Default" or "Blobless"
env = ["MY_VAR=value"]           # Injected environment variables
create-lock-file = false

# Store key-value pairs accessible via workspace.load_value()
[spaces-dev.Repo.store]
build_flavor = "release"
enable_telemetry = false
```

#### B. Derived Repository Entry (`[<name>.RepoDerived]`)
Inherits all configuration from a base entry, overriding specific fields:
```toml
[spaces-dev-fork.RepoDerived]
derive-from = "spaces-dev"
url = "https://github.com/my-fork/spaces"
rev = "feature-branch"
```

#### C. Multi-Repository Workflow (`[<name>.Workflow]`)
Coordinates multi-script checkout sequences:
```toml
[roas-full.Workflow]
workflow = "workflows:roas-full"
script = ["workflows/toolchains", "workflows/repos"]
new-branch = ["reliable/roas-software", "reliable/display"]
```

---

## 3. Checkout Store (`workspace.load_value`)

Spaces provides a hierarchical key-value store evaluated during checkout and available during run phases:

### Value Resolution Precedence (Highest to Lowest)
1. **Command Line Flag**: `--store=KEY=VALUE`
   * Overrides all file-defined values regardless of URL or path parameters.
2. **`co.spaces.toml`**: `store` table within `[<entry>.Repo.store]` or `[<entry>.Workflow.store]`.
   * Preserves native TOML data types (integers, booleans, strings, arrays, tables).
3. **Starlark Call**: `checkout.store_value(key, value, path = None)`
   * Set programmatically inside `0.checkout.spaces.star` or `1.checkout.spaces.star`.

### Reading Stored Values in Starlark:
```python
# Read value with fallback search across all members
val = workspace.load_value("build_flavor")

# Read value scoped to a specific repository member path
val = workspace.load_value("build_flavor", path = "spaces")

# Read all instances of a key across the entire workspace
all_entries = workspace.load_values("my_key")
```

---

## 4. Local Workspace Runtime State (`.spaces/`)

The `.spaces/` directory in the root of a workspace contains execution state, logs, and digests:

1. **`.spaces/logs/latest/`**:
   * Symlink to the most recent `spaces run` or `spaces checkout` execution.
   * Every target emits an isolated log: `__<target_mangled_name>.log`.
   * **Failure Triage**: Never guess why a rule failed. Inspect `.spaces/logs/latest/__<target>.log` to read isolated stdout/stderr.
2. **`.spaces/digests/`**:
   * Contains JSON and hash summaries when `--create-digest-reports` is enabled.
3. **Input Fingerprint Caching**:
   * Spaces records cryptographic hashes of all files matching a rule's `inputs = [glob(...)]`.
   * On subsequent runs, if inputs, environment variables, command strings, and dependencies are identical, the rule is **skipped automatically**.
   * **Cache Force Invalidation**: Pass `--forget-inputs` to force execution.

---

## 5. Global Cache Store (`~/.spaces/`)

Spaces maintains a persistent host-wide cache under `~/.spaces/` to accelerate operations across all local workspaces:

1. **Git Object Cache & Mirrors**:
   * Speeds up clones and checkouts across multiple workspaces sharing upstream repositories.
2. **Archive Cache**:
   * Downloaded archives (`http_archive`, `archive`, `oras`) are verified against sha256 checksums and cached locally.
3. **Store Management Commands**:
   * `spaces store list`: Inspect items in the global store.
   * `spaces store prune`: Remove stale or unreferenced store items.
   * `spaces store clear`: Evict entire store cache.
