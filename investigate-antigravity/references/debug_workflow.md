# Antigravity Debugging & Live Tracing Workflow

This guide details procedural workflows for diagnosing Antigravity behavior, investigating crashes, tracing tool calls, and inspecting session trajectories.

---

## 1. Fast Static Inspection (Without GDB)

Use the bundled scripts in `scripts/`:

### Symbol Querying
```bash
# Query any method or struct:
~/.gemini/skills/investigate-antigravity/scripts/query_symbols.py "policyguardian" --methods-only

# Query packages matching a subsystem:
~/.gemini/skills/investigate-antigravity/scripts/query_symbols.py "browser" --packages-only

# Count symbols in a module:
~/.gemini/skills/investigate-antigravity/scripts/query_symbols.py "cortex/command" --count
```

### Prompt & Rubric Extraction
```bash
# List all extractable prompt categories:
~/.gemini/skills/investigate-antigravity/scripts/inspect_prompts.py --list

# View the exact system rubric for code vetting:
~/.gemini/skills/investigate-antigravity/scripts/inspect_prompts.py "Code Vetting"
```

---

## 2. Dynamic Live Tracing with GDB

Because `~/.local/share/antigravity/localharness.debug` has full DWARF `.debug_info` and `.debug_line` tables, GDB can set symbolic breakpoints using original Google monorepo source paths:

```bash
# Find the running harness PID
PID=$(pgrep -f "localharness")

# Attach GDB using the debug binary as the symbol source
gdb -p $PID ~/.local/share/antigravity/localharness.debug
```

### Useful Breakpoint Targets:
* **Tool Dispatch**:
  ```gdb
  (gdb) break google3/third_party/jetski/cortex/command.(*CommandRunner).Execute
  ```
* **Policy Guardian Vetting**:
  ```gdb
  (gdb) break google3/third_party/jetski/cortex/policyguardian/policyguardian.(*Guardian).Verify
  (gdb) print *toolCall
  ```
* **LLM Synchronous Vetting**:
  ```gdb
  (gdb) break google3/third_party/jetski/cortex/policyguardian/vetting.CallLLMSync
  ```

---

## 3. Kernel Tracing with eBPF / bpftrace

To trace behavior non-invasively without pausing execution:

### Trace Shell Commands Executed by Antigravity:
```bash
sudo bpftrace -e '
uprobe:/home/cye/.local/share/antigravity/localharness.debug:"google3/third_party/jetski/cortex/command.(*Sandbox).Run" {
    printf("[PID %d] Shell Command: %s\n", pid, str(arg1));
}'
```

### Trace Policy Guardian Verdicts:
```bash
sudo bpftrace -e '
uprobe:/home/cye/.local/share/antigravity/localharness.debug:"google3/third_party/jetski/cortex/policyguardian/policyguardian.(*Guardian).Verify" {
    printf("[PID %d] PolicyGuardian.Verify called\n", pid);
}'
```

---

## 4. Inspecting Session Databases & Trajectories

Antigravity stores SQLite databases for every session:
* CLI Sessions: `~/.gemini/antigravity-cli/conversations/<uuid>.db`
* ACP Sessions: `~/.gemini/antigravity-acp/conversations/<uuid>.db`
* Trajectory Summaries: `~/.gemini/antigravity-cli/conversation_summaries.db`

### Query Active Sessions:
```bash
sqlite3 ~/.gemini/antigravity-cli/conversation_summaries.db \
  "SELECT conversation_id, title, last_modified_time FROM conversation_summaries ORDER BY last_modified_time DESC LIMIT 5;"
```

### View Individual Trajectory Steps:
```bash
sqlite3 ~/.gemini/antigravity-cli/conversations/<uuid>.db \
  "SELECT step_index, step_type, status FROM steps ORDER BY step_index ASC;"
```
