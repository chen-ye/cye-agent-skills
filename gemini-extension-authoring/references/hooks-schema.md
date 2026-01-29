# Hooks Configuration Schema (`hooks.json`)

Hooks are defined in a JSON file (typically `hooks/hooks.json`) referenced by
the `gemini-extension.json` manifest.

## Structure

The root object contains a `hooks` property, which maps **Event Names** to
arrays of **Hook Definitions**.

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "pattern",
        "hooks": [ ... ]
      }
    ]
  }
}
```

## Event Names

| Event Name            | Trigger Moment                                                             |
| :-------------------- | :------------------------------------------------------------------------- |
| `SessionStart`        | Runs when a new session begins.                                            |
| `SessionEnd`          | Runs when a session ends.                                                  |
| `BeforeAgent`         | Runs before the agent loop starts a task.                                  |
| `AfterAgent`          | Runs after the agent loop completes a task.                                |
| `Notification`        | Runs when the agent emits a notification (e.g., waiting for input, error). |
| `BeforeToolSelection` | Runs before the agent selects a tool.                                      |
| `BeforeTool`          | Runs before a tool is executed.                                            |
| `AfterTool`           | Runs after a tool has executed.                                            |
| `BeforeModel`         | Runs before a prompt is sent to the LLM.                                   |
| `AfterModel`          | Runs after a response is received from the LLM.                            |
| `PreCompress`         | Runs before context compression.                                           |

## Hook Definition

| Field     | Type   | Description                                                                                                                           |
| :-------- | :----- | :------------------------------------------------------------------------------------------------------------------------------------ |
| `matcher` | String | Condition to trigger the hook. Regex for tools (e.g., `write_.*`), Exact String for lifecycle (e.g., `SessionStart`), or `*` for all. |
| `hooks`   | Array  | A list of hook actions to execute.                                                                                                    |

## Hook Action

| Field         | Type   | Description                                          |
| :------------ | :----- | :--------------------------------------------------- |
| `name`        | String | Unique identifier for this specific hook action.     |
| `type`        | String | Must be `command`.                                   |
| `command`     | String | The shell command to execute.                        |
| `timeout`     | Number | Execution timeout in milliseconds (default: 300000). |
| `description` | String | Description of the hook action.                      |

## Variable Expansion

In the `command` string, you can use `${extensionPath}`. This variable is
resolved at runtime to the absolute path of the extension's root directory. This
is critical for referencing scripts included in your extension.

**Example:** `"${extensionPath}/hooks/myscript.py"`

## Data Flow

Hooks communicate via standard input (stdin) and standard output (stdout).

- **Input**: JSON object containing event details (e.g., `hook_event_name`,
  `prompt`, `response`, `tool_name`, `tool_args`).
- **Output**: JSON object (optional) to modify behavior or provide feedback.

### Strict JSON Requirements (The "Golden Rule")

1. **Silence is Mandatory**: Your script must NOT print any plain text to
   stdout. Even a single `echo` before the JSON will break parsing.
2. **Pollution = Failure**: If stdout contains non-JSON text, parsing will fail.
3. **Debug via Stderr**: Use stderr for all logging (e.g., `echo "debug" >&2`).

### Exit Codes

- **0**: Success (or "allow").
- **1**: Failure (or "deny").
- **Other**: Treated as failure/error.

### Environment Variables

- `GEMINI_PROJECT_DIR`: Absolute path to project root.
- `GEMINI_SESSION_ID`: Unique session ID.
- `GEMINI_CWD`: Current working directory.
- `CLAUDE_PROJECT_DIR`: Compatibility alias.
