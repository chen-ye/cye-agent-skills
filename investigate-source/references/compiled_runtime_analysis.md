# Compiled Runtime & Binary Analysis Guide (Tier 3 Fallback)

This reference defines procedures for investigating compiled binaries, minified bundles, and closed-source runtimes **strictly as a last resort** when source code is not obtainable.

---

## 1. Safety & Prerequisite Verification

Before proceeding with binary or runtime static analysis:
1. Verify that source code is genuinely unobtainable (check GitHub, internal GitLab, package registries, and local workspace roots via `scripts/resolve_source.sh`).
2. If source code is obtainable, STOP and execute Tier 2 shallow clone instead.
3. Confirm that the target executable is locally present on the filesystem.

---

## 2. Symbol Extraction & Static Inspection

### A. Checking Stripped Status
```bash
file /path/to/binary
```
* If `not stripped`: Symbol tables (`.symtab`, `.strtab`) are directly readable.
* If `stripped`: Look for unstripped debug companions (e.g. `<binary>.debug`, `/usr/lib/debug/`, or `~/.local/share/<tool>/<binary>.debug`).

### B. Extracting Go / C++ / Rust Symbols (`nm`)
```bash
# List all defined functions and demangle names
nm -C --defined-only /path/to/symbol_provider | head -n 50

# Filter methods on a specific subsystem or struct
nm -C /path/to/symbol_provider | grep -i "subsystem" | head -n 20
```

### C. DWARF Line Table Analysis
Even when source code is missing, unstripped binaries with DWARF information embed original source file paths and line numbers:
```bash
readelf --debug-dump=line /path/to/symbol_provider | grep -E "(\.rs|\.go|\.cpp|\.ts)" | head -n 30
```
This reconstructs the internal package and file layout of the original source tree.

---

## 3. String & Read-Only Data (`.rodata`) Extraction

Binaries frequently embed configuration schemas, system instructions, error templates, and SQL migrations:

### A. Targeted Keyword Extraction
```bash
strings -a /path/to/binary | grep -E "(https?://|error:|warning:|config|schema)" | head -n 30
```

### B. Extracting JSON / Prompt Blocks
```bash
strings -a /path/to/binary | grep -B 2 -A 10 "You are"
```

---

## 4. Unpacking Embedded Archives & Bundles

Many modern executables are self-extracting archive envelopes:

| Format / Target | Unpacking Technique |
| :--- | :--- |
| **Python `.par` / PEX** | `unzip -q /path/to/binary.par -d /tmp/unpacked/` |
| **Electron `.asar`** | `npx @electron/asar extract app.asar /tmp/unpacked/` |
| **Java JAR / WAR** | `jar -xf /path/to/app.jar -C /tmp/unpacked/` |
| **Embedded Tar/Zip** | `tar -xf <archive> -C /tmp/unpacked/` |

---

## 5. Dynamic Process Tracing

When static analysis is insufficient to determine runtime behavior:

1. **System Call Tracing (`strace`)**:
   ```bash
   strace -f -e trace=file,process,network -o /tmp/trace.log /path/to/binary <args>
   ```
2. **Log Stream Triage**:
   ```bash
   tail -n 100 ~/.<tool>/logs/*.log
   ```
3. **SQLite State Auditing**:
   ```bash
   sqlite3 ~/.<tool>/state.db ".tables"
   ```
