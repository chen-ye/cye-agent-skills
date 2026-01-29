---
name: Gemini Extension Authoring
description: This skill should be used when the user asks to "create a gemini extension", "author a gemini extension", "package a gemini hook", "publish a gemini extension", or asks about "extension structure", "gemini-extension.json", or "hooks.json".
version: 1.0.0
---

# Gemini Extension Authoring

This skill provides expert guidance on creating, packaging, and publishing extensions for the Gemini CLI.

## Extension Structure

Gemini CLI extensions are self-contained directories that can include commands, hooks, MCP servers, and other resources.

Create the extension directory structure:

```
my-extension/
├── gemini-extension.json  (Required: Manifest)
├── README.md              (Required: Documentation)
├── LICENSE                (Required: License)
├── hooks/
│   ├── hooks.json         (Optional: Hook definitions)
│   └── my_hook.py         (Optional: Hook script)
├── commands/              (Optional: Custom commands)
└── mcp-server/            (Optional: MCP server code)
```

## Core Components

### The Manifest (`gemini-extension.json`)

The `gemini-extension.json` file is the heart of the extension. It defines metadata, configuration settings, dependencies, and entry points for hooks or MCP servers.

**Key Fields:**
*   `name`: Unique identifier (kebab-case).
*   `version`: Semantic version (e.g., "1.0.0").
*   `settings`: Configuration options exposed to the user.
*   `hooks`: Path to the hooks definition file (e.g., `./hooks/hooks.json`).
*   `dependencies`: Required system tools (e.g., `{"python": ">=3.7"}`).

See **`references/extension-schema.md`** for the full schema specification.

### Hooks Configuration (`hooks.json`)

Hooks allow extensions to intercept and modify CLI behavior. They are defined in a JSON file referenced by the manifest.

**Structure:**
*   Grouped by event name (e.g., `AfterAgent`, `BeforeTool`).
*   Uses `matcher` to filter events (e.g., `*` for all, or specific tool names).
*   Defines the `command` to execute.

**Best Practice:**
Use `${extensionPath}` in your command strings to reference files within your extension directory reliably.

```json
"command": "${extensionPath}/hooks/my_script.py"
```

See **`references/hooks-schema.md`** for detailed event types and configuration options.

## Development Workflow

### 1. Initialize the Extension

Start by creating the directory and the manifest file.

```bash
mkdir -p extensions/my-extension
touch extensions/my-extension/gemini-extension.json
```

### 2. Implement Functionality

*   **Hooks:** Write scripts (Python/Bash) to handle events. Ensure they are executable (`chmod +x`).
*   **Settings:** Define user-configurable settings in `gemini-extension.json` using the `settings` array. These map to environment variables at runtime.

### 3. Enable and Test locally

Enable the extension for your local user to test it.

Edit `extensions/extension-enablement.json` (or use the CLI if available) to include your extension path.

### 4. Configure Settings

Test the configuration workflow using the CLI:

```bash
gemini extensions config my-extension
```

## Publishing

Gemini extensions are published as Git repositories and GitHub Releases.

1.  **Git Init:** Initialize a git repo in your extension directory.
2.  **Commit:** Commit all files (ensure `.gitignore` excludes temporary files).
3.  **Tag:** Create a semantic version tag (e.g., `v1.0.0`).
4.  **Release:** Create a GitHub Release pointing to the tag.

Users install using the GitHub URL:
`gemini extensions install https://github.com/username/my-extension`

## Best Practices

*   **Environment Variables:** Use the `settings` schema to define environment variables. The CLI will handle prompting the user and setting them.
*   **Paths:** Always use `${extensionPath}` for internal file references.
*   **Dependencies:** Explicitly list system requirements (like Python, Node.js) in the `dependencies` section of the manifest and the README.
*   **Security:** Warn users about sensitive data in settings (e.g., API keys, public topics).

## Additional Resources

### Reference Files
- **`references/extension-schema.md`** - Detailed `gemini-extension.json` schema.
- **`references/hooks-schema.md`** - Detailed `hooks.json` schema and event types.

### Examples
- **`examples/gemini-extension.json`** - Complete manifest example.
- **`examples/hooks.json`** - Complete hooks configuration example.
