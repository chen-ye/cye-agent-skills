# Google Antigravity Internal Architecture Map

This reference documents the internal package structures, module boundaries, and binary layouts reverse-engineered from Google Antigravity's unstripped debug binary (`localharness.debug`).

---

## 1. Binary Ecosystem & File Locations

Antigravity operates across multiple decoupled binaries:

| Path | Format | Role |
| :--- | :--- | :--- |
| `~/.local/bin/agy` | Stripped Go ELF (~201 MB) | The command-line user interface and interactive terminal TUI. |
| `~/.local/bin/agy_acp_server.par` | Hermetic Python/C++ Archive (~1.8 GB) | Implements the Agent Client Protocol (ACP v1) for editor integrations (Zed, JetBrains). Talks to Gemini over TLS. |
| `~/.local/bin/localharness_external` | Stripped Go ELF (~123 MB) | Production tool execution harness, terminal sandbox, and diff engine spawned by `agy_acp_server.par`. |
| `~/.local/share/antigravity/localharness.debug` | Unstripped Go ELF (~987 MB) | Extracted debug binary with full DWARF sections, `.symtab` (827,093 symbols), and source path line tables. |

---

## 2. Core Go Packages (`google3/third_party/jetski/`)

The Go execution core is organized into 229 internal packages under `third_party/jetski`:

### A. The Agent Planning Engine (`cortex/`)
* **`cortex/core/contrib/variants/minisweagent`**: The core software engineering task loop. Handles step generation, tool call dispatch, and completion conditions.
* **`cortex/core/contrib/variants/minimalagent`**: Headless minimal agent variant used for single-shot print prompts (`agy -p`).
* **`cortex/cascade_run_state`**: State tracker for multi-step reasoning trees, checkpointing, and branch rollbacks.
* **`cortex/accumulator`**: Token budget accumulator tracking input/output tokens and billing tiers across multi-turn sessions.
* **`cortex/artifacts/knowledge`**: Repository indexing, memory retrieval, and persistence under `~/.gemini/knowledge/`.

### B. Security & Safety (`cortex/policyguardian/`)
* **`policyguardian/deterministic_vetting_configs`**:
  * Fast synchronous checks executing in <1ms:
  * `VetFileWrite`, `VetFileDelete`, `VetReplaceFileContent`, `VetStrReplaceEditor`.
  * Enforces path normalization, sensitive path blocks (`/etc/shadow`, `~/.ssh/`), and `$PATH` hijacking prevention.
* **`policyguardian/vetting`**:
  * `CheckSafeBrowsing`: Hashes outbound URLs and checks Google SafeBrowsing API.
  * `VetGitHubRepo`: Queries GitHub API for stars, forks, and merged PRs on target repositories.
  * `VetDependency`: Validates package names against registries to prevent hallucinated dependency attacks.
  * `vetDataFlow`: Detects private data exfiltration to external networks.
  * `CallLLMSync`: Synchronous, blocking evaluation using Gemini Flash Lite.
* **`gdm/security/agi_control/agent_monitoring/jetski`**:
  * DeepMind's supervisor framework implementing `PolicyGuardianMonitor`.

### C. Execution & Sandboxing (`cortex/command/`)
* **`cortex/command/sandboxproxy`**: Manages process isolation and PTY allocation for terminal execution.
* **`cortex/command`**: Intercepts stdout/stderr streams and detects execution timeouts.
* **`cortex/command/environment`**: Manages environment variable sanitization and dynamic `export` tracking.

### D. Browser Automation via CDP (`cortex/chatconverters/browser/`)
* **`browser_pb`**: Protobuf definitions for Chrome DevTools Protocol (CDP) commands.
* Exposes coordinate translation, DOM snapshotting (`DOMSnapshot.enable`), screenshot capture, and mouse/keyboard synthetic event generation.

### E. Protocol Buffers & Wire Formats
* **`codeium_common_pb`**: Common protocol buffers for completions, code edits, and editor events.
* **`cortex_pb`**: Agent configuration (`PolicyGuardianConfig`, `CommandAssessorConfig`, `PermissionConfig`).
