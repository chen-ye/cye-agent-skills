# Spaces Starlark Standard Library & Builtin Modules Reference

Spaces embeds 26 Starlark modules providing 336 native functions, divided between core lifecycle builtins (`crates/spaces/src/builtins/`) and the Starlark standard library (`crates/starstd/`).

---

## 1. Built-in Lifecycle & Workspace Modules

### `workspace` (22 functions)
The `workspace` module exposes workspace-level configuration, paths, environment variables, and the checkout store:

* **`workspace.load_value(key, url = None, path = None) -> value`**:
  * Loads a stored configuration value from the checkout store.
  * **Priority Order**:
    1. CLI overrides: `--store=KEY=VALUE`
    2. `co.spaces.toml`: `[entry.Repo]` or `[entry.Workflow]` `store` table
    3. `checkout.store_value()` from Starlark scripts
* **`workspace.load_values(key) -> list[dict]`**:
  * Returns all matching values across all URLs and paths as `[{"url": ..., "path": ..., "value": ...}]`.
* **`workspace.get_absolute_path() -> string`**:
  * Returns the absolute path to the workspace root directory.
* **`workspace.get_path_to_checkout() -> string`**:
  * Returns the workspace-relative path where the calling script's repository is cloned.
* **`workspace.get_path_to_home() -> string`**:
  * Returns the path to the workspace-isolated HOME directory.
* **`workspace.get_path_to_log_file(rule) -> string`**:
  * Returns the relative path to the log file for a target rule in `.spaces/logs/latest/`.
* **`workspace.get_env_var(var_name) -> string`**:
  * Gets an environment variable set in the workspace context.
* **`workspace.is_env_var_set(var_name) -> bool`** / **`workspace.is_env_var_set_to(var_name, val) -> bool`**:
  * Checks environment variable existence or specific equality.
* **`workspace.get_digest() -> string`** / **`workspace.get_short_digest() -> string`**:
  * Computes the reproducible workspace state digest.

### `checkout` (27 functions)
Available during `Phase::Checkout` (`0.checkout.spaces.star`, `1.checkout.spaces.star`, `spaces co`):

* **`checkout.add_repo(options)`**:
  * Checks out a git repository to the given directory name at the specified revision/branch/tag.
* **`checkout.add_archive(options)`** / **`checkout.add_platform_archive(options)`**:
  * Downloads and unpacks an archive into the workspace.
* **`checkout.add_oras_archive(options)`**:
  * Pulls an OCI registry artifact via ORAS.
* **`checkout.add_asset(options)`**:
  * Copies an asset file or configuration into the workspace. Also supports `checkout.add_soft_link_asset()`, `checkout.add_hard_link_asset()`, and `checkout.add_which_asset()`.
* **`checkout.store_value(key, value, path = None)`**:
  * Writes a value into the workspace checkout store accessible by `workspace.load_value()`.

### `run` (7 functions)
Available during `Phase::Run` (`spaces.star`, `spaces run`):

* **`run.add_exec(name, command, args = [], deps = [], inputs = [], outputs = [], env = {}, ...)`**:
  * Registers a command execution rule with explicit inputs and dependency labels.
* **`run.add_target(name, ...)`** / **`run.add(...)`**:
  * Registers a custom task rule with input glob tracking.
* **`run.add_archive(name, rule_name, archive = {...})`**:
  * Configures an output archive packaging task.
* **`run.add_from_clone(...)`**:
  * Dynamically inherits and evaluates rules defined in a cloned member.
* **`run.abort(message)`**:
  * Aborts rule execution with an error banner.

### `info` (19 functions)
* **`info.is_ci() -> bool`**: Returns whether the workspace is executing in a CI runner.
* **`info.get_workspace_name() -> string`**: Returns the current workspace name.
* **`info.get_os() -> string`**: Returns host OS (`linux`, `macos`, `windows`).
* **`info.get_arch() -> string`**: Returns host architecture (`x86_64`, `aarch64`).

### `semver` (19 functions)
* **`semver.parse(version_str) -> SemVer`**: Parses a SemVer string.
* **`semver.matches(version, requirement) -> bool`**: Tests version against a range expression (e.g. `^1.2.0`, `>=2.0.0`).

### `rlog` (6 functions)
* Rule-level structured logger emitting formatted logs to console and target log files.

---

## 2. Filesystem & Operating System Operations

### `fs` (38 functions)
High-performance native filesystem operations:
* `fs.read_file_to_string(path) -> string`: Reads file content as UTF-8.
* `fs.write_string_to_file(path, content) -> NoneType`: Writes string content to a file.
* `fs.write_string_atomic(path, content) -> NoneType`: Atomically writes file to disk.
* `fs.read_bytes(path) -> list[int]` / `fs.write_bytes(path, bytes) -> NoneType`: Binary I/O.
* `fs.exists(path) -> bool` / `fs.is_file(path) -> bool` / `fs.is_directory(path) -> bool`: Path checks.
* `fs.read_directory(path) -> list[string]`: Lists directory contents.
* `fs.mkdir(path, recursive = True) -> NoneType`: Creates directories.
* `fs.copy(src, dest) -> NoneType` / `fs.move(src, dest) -> NoneType` / `fs.remove(path) -> NoneType`: Mutation helpers.
* `fs.walk_directory(path, ...) -> list[string]`: Recursive directory traverser.
* `fs.read_json_to_dict(path)` / `fs.write_json_from_dict(path, dict)`: High-speed JSON file bridge.
* `fs.read_toml_to_dict(path)` / `fs.write_toml_from_dict(path, dict)`: High-speed TOML file bridge.
* `fs.read_yaml_to_dict(path)` / `fs.write_yaml_from_dict(path, dict)`: High-speed YAML file bridge.

### `path` (19 functions)
* `path.join(*parts) -> string`: Joins path segments.
* `path.split(path) -> tuple`: Splits path into directory and file.
* `path.dirname(path) -> string` / `path.basename(path) -> string` / `path.extension(path) -> string`.
* `path.is_absolute(path) -> bool` / `path.canonicalize(path) -> string`.

### `tmp` (5 functions)
* `tmp.file(suffix = "") -> string`: Creates a tracked temporary file.
* `tmp.dir(prefix = "") -> string`: Creates a tracked temporary directory.
* `tmp.dir_keep(prefix = "") -> string`: Creates a persistent temporary directory.
* `tmp.cleanup(path) -> NoneType` / `tmp.cleanup_all() -> NoneType`.

### `sys` (11 functions)
* `sys.os() -> string` (`linux`, `macos`, `windows`).
* `sys.arch() -> string` (`x86_64`, `aarch64`).
* `sys.cpu_count() -> int` / `sys.total_memory_bytes() -> int`.
* `sys.user_home() -> string` / `sys.username() -> string` / `sys.hostname() -> string`.
* `sys.exit(code) -> int`: Terminates Starlark execution with exit code.

---

## 3. Process Execution & Shell Control

### `process` (18 functions) & `sh` (4 functions)
* **`process.run(options) -> ProcessResult`**:
  * Executes a process directly without shell overhead.
  * Options: `{"command": ..., "args": [...], "cwd": ..., "env": {...}, "capture_stdout": True, "capture_stderr": True}`.
* **`sh.run(cmd, cwd = None, env = {}) -> ShResult`**:
  * Executes a command line through `/bin/sh` or system shell.
* **`sh.quote(arg) -> string`**: Shell-escapes strings.

### `signal` (9 functions)
* `signal.trap(name, handler) -> NoneType`: Registers signal trap for `SIGINT`, `SIGTERM`.
* `signal.wait(timeout_ms = None)`: Awaits queued signal.
* `signal.clear() -> NoneType`: Clears all traps.

---

## 4. Structured Data & Diagnostics

### `text` (18 functions)
Advanced text analysis and diagnostic formatter:
* **`text.grep({"path": ..., "pattern": ..., "max": ...}) -> list[dict]`**:
  * Regex grep returning structured line numbers and named capture groups.
* **`text.diagnostic({"file": ..., "line": ..., "message": ..., "severity": "error"}) -> dict`**:
  * Constructs a structured diagnostic object.
* **`text.render_diagnostics(diagnostics, format = "human") -> string`**:
  * Renders diagnostics in `human`, `github` (workflow annotations), `json`, or `sarif` format.
* **`text.scan_lines(content, callback) -> list`**: High-speed line scanning.
* **`text.head(path, n)` / `text.tail(path, n)` / `text.line_count(path)`**.

### `json` (7 functions)
* `json.encode(val) -> string` / `json.decode(s) -> val` / `json.try_decode(s, default = None)`.

### `toml` (5 functions) & `yaml` (5 functions)
* `toml.string_to_dict(s) -> dict` / `toml.to_string(dict) -> string` / `toml.try_string_to_dict(s, default = None)`.
* `yaml.string_to_dict(s) -> dict` / `yaml.to_string(dict) -> string` / `yaml.try_string_to_dict(s, default = None)`.

---

## 5. Script Utilities & Time

### `args` (6 functions)
Parses trailing command line arguments in `.exec.star` scripts (`#!/usr/bin/env spaces`).

### `time` (15 functions)
* `time.now() -> tuple` / `time.unix() -> int` / `time.unix_ms() -> int` / `time.iso8601() -> string`.
* `time.sleep(ns)` / `time.sleep_ms(ms)` / `time.sleep_seconds(s)`.
* `time.timer() -> int` / `time.timer_elapsed_ms(id) -> int`: High-resolution execution profiling.

### `hash` (18 functions)
* `hash.sha256(s) -> string` / `hash.sha256_file(path) -> string` / `hash.md5(s) -> string`.
