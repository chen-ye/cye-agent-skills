# Hooks Configuration Schema (`hooks.json`)

Hooks are defined in a JSON file (typically `hooks/hooks.json`) referenced by the `gemini-extension.json` manifest.

## Structure

The root object contains a `hooks` property, which maps **Event Names** to arrays of **Hook Definitions**.

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

| Event Name | Trigger Moment |
| :--- | :--- |
| `AfterAgent` | Runs after the agent loop completes a task. |
| `Notification` | Runs when the agent emits a notification (e.g., waiting for input, error). |
| `BeforeTool` | Runs before a tool is executed. |
| `AfterTool` | Runs after a tool has executed. |
| `BeforeModel` | Runs before a prompt is sent to the LLM. |
| `AfterModel` | Runs after a response is received from the LLM. |
| `SessionStart` | Runs when a new session begins. |

## Hook Definition

| Field | Type | Description |
| :--- | :--- | :--- |
| `matcher` | String | A glob pattern or regex to match against the event context (e.g., tool name). Use `*` to match everything. |
| `hooks` | Array | A list of hook actions to execute. |

## Hook Action

| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | String | Unique identifier for this specific hook action. |
| `type` | String | Must be `command`. |
| `command` | String | The shell command to execute. |
| `timeout` | Number | Execution timeout in milliseconds (default: 300000). |

## Variable Expansion

In the `command` string, you can use `${extensionPath}`. This variable is resolved at runtime to the absolute path of the extension's root directory. This is critical for referencing scripts included in your extension.

**Example:**
`"${extensionPath}/hooks/myscript.py"`

## Data Flow

Hooks communicate via standard input (stdin) and standard output (stdout).
*   **Input**: JSON object containing event details (e.g., `hook_event_name`, `prompt`, `response`, `tool_name`, `tool_args`).
*   **Output**: JSON object (optional) to modify behavior or provide feedback.
