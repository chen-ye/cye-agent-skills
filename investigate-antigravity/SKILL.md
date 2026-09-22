---
name: investigate-antigravity
description: This skill should be used when the user asks to "investigate antigravity", "diagnose antigravity behavior", "reverse engineer antigravity", "inspect localharness", "debug antigravity crash", "look up internal jetski methods", "understand policy guardian implementation", or analyze Antigravity binary symbols and internal prompts.
version: 0.1.0
---

# Investigating & Diagnosing Google Antigravity

This skill provides procedures, tools, and symbol references for investigating, diagnosing, and reverse-engineering the internal behavior of Google Antigravity, its execution harness (`jetski` / `localharness`), and the Agent Client Protocol (ACP) server.

## Overview & Binary Assets

Antigravity's runtime divides responsibilities between an outer orchestrator and an execution harness:

1. **`~/.local/bin/agy_acp_server.par`**: Outer Python/C++ executable implementing the ACP JSON-RPC server and communicating with Gemini APIs.
2. **`~/.local/bin/localharness_external`**: Production stripped Go binary executing tool calls, shell sandboxing, and diff generation.
3. **`~/.local/share/antigravity/localharness.debug`**: Extracted 987 MB unstripped Go binary containing **827,093 symbols**, full DWARF debug info (`.debug_info`, `.debug_line`), and source path line tables.

Always query `~/.local/share/antigravity/localharness.debug` directly for static analysis and debugging to avoid extracting from the archive repeatedly.

---

## Core Investigation Workflows

### 0. Binary Acquisition and Automated Setup

To acquire or re-extract the unstripped debug binary after an Antigravity update, execute `scripts/extract_debug_binary.py`:
```bash
~/.gemini/skills/investigate-antigravity/scripts/extract_debug_binary.py
```
*For the manual acquisition procedure from the upstream ACP Agent Registry, consult `references/binary_acquisition.md`.*

---

### 1. Querying Internal Symbols and Packages

To find internal structs, functions, or package boundaries, execute `scripts/query_symbols.py`:

```bash
# Search for methods on a specific subsystem (e.g., Policy Guardian)
~/.gemini/skills/investigate-antigravity/scripts/query_symbols.py "policyguardian" --methods-only

# List all Go package paths matching a keyword
~/.gemini/skills/investigate-antigravity/scripts/query_symbols.py "cortex" --packages-only

# Filter for terminal command execution methods
~/.gemini/skills/investigate-antigravity/scripts/query_symbols.py "command" --methods-only --limit 20
```

*For an overview of the 229 internal packages in the `jetski` codebase, consult `references/architecture.md`.*

---

### 2. Extracting Embedded Prompts and Safety Rubrics

Antigravity embeds its internal system instructions, security rubrics, and subagent prompts directly in the binary's read-only data sections (`.rodata`).

To extract and view these prompts, execute `scripts/inspect_prompts.py`:

```bash
# List available prompt categories
~/.gemini/skills/investigate-antigravity/scripts/inspect_prompts.py --list

# View the Policy Guardian code-vetting rubric
~/.gemini/skills/investigate-antigravity/scripts/inspect_prompts.py "Code Vetting"

# View the anti-circumvention rubric (VetDeniedRepeat)
~/.gemini/skills/investigate-antigravity/scripts/inspect_prompts.py "Anti-Circumvention"

# View the configuration downgrade rubric
~/.gemini/skills/investigate-antigravity/scripts/inspect_prompts.py "Config Vetting"
```

---

### 3. Diagnosing Runtime Behavior & Crashes

When Antigravity misbehaves, crashes, or rejects commands:

1. **Inspect Log Streams**:
   * CLI daemon log: `tail -n 100 ~/.antigravity/agy_daemon.log`
   * Active CLI session logs: `~/.gemini/antigravity-cli/log/`
   * Check for crash dumps: `ls -la ~/.gemini/antigravity-cli/crashes/`
2. **Inspect Conversation Trajectories**:
   * Open the session SQLite database:
     ```bash
     sqlite3 ~/.gemini/antigravity-cli/conversations/<session-id>.db "SELECT step_index, step_type, status FROM steps;"
     ```
3. **Trace Live Process Execution**:
   * Attach GDB or eBPF probes using `~/.local/share/antigravity/localharness.debug` as the symbol provider.
   * *For exact GDB commands, breakpoints, and bpftrace scripts, consult `references/debug_workflow.md`.*

---

## Key Subsystems Reference

### Policy Guardian
* **Path**: `google3/third_party/jetski/cortex/policyguardian/`
* **Role**: Automated safety and security supervisor developed with DeepMind (`gdm/security/agi_control/`).
* **Key Components**:
  * `deterministic_vetting_configs`: Zero-latency pre-checks (path normalization, `$PATH` hijacking, sensitive file blocks).
  * `vetting`: SafeBrowsing API queries, GitHub repo star/fork checks, dependency typosquatting checks, and data exfiltration tracking.
  * `CallLLMSync`: Synchronous Gemini Flash Lite evaluation for ambiguous actions.

### Cortex Execution Engine
* **Path**: `google3/third_party/jetski/cortex/`
* **Role**: The core agent loop and state machine.
* **Key Components**:
  * `core/contrib/variants/minisweagent`: Software engineering task agent.
  * `command/sandboxproxy`: PTY allocation, process isolation, and shell streaming.
  * `chatconverters/browser`: Chrome DevTools Protocol (CDP) client for browser automation.

---

## Supporting Resources

* **`references/binary_acquisition.md`**: Upstream ACP registry URLs, download endpoints, and manual extraction procedures.
* **`references/architecture.md`**: Complete map of internal Go packages, data structures, and binary layouts.
* **`references/debug_workflow.md`**: Step-by-step instructions for GDB live debugging, bpftrace probes, and SQLite trajectory analysis.
* **`scripts/extract_debug_binary.py`**: Automated extraction tool for `localharness.debug`.
* **`scripts/query_symbols.py`**: High-speed symbol parser querying `.symtab` in ~30ms.
* **`scripts/inspect_prompts.py`**: Embedded prompt and rubric extractor.
