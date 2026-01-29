# Gemini Extension Manifest Schema (`gemini-extension.json`)

The `gemini-extension.json` file must reside at the root of the extension
directory.

## Fields

| Field             | Type   | Required | Description                                                                       |
| :---------------- | :----- | :------- | :-------------------------------------------------------------------------------- |
| `name`            | String | **Yes**  | The unique identifier for the extension. Use kebab-case (e.g., `gemini-ntfy`).    |
| `displayName`     | String | No       | A human-readable name for the extension.                                          |
| `version`         | String | **Yes**  | Semantic version string (e.g., `1.0.0`).                                          |
| `description`     | String | No       | A brief description of what the extension does.                                   |
| `author`          | String | No       | The name of the extension author.                                                 |
| `license`         | String | No       | The license type (e.g., `MIT`, `Apache-2.0`).                                     |
| `repository`      | Object | No       | Repository information.                                                           |
| `repository.type` | String | No       | usually `git`.                                                                    |
| `repository.url`  | String | No       | The URL of the git repository.                                                    |
| `mcpServers`      | Object | No       | Map of MCP server names to their configuration (command, args, etc.).             |
| `contextFileName` | String | No       | Name of the file to load as context (default: `GEMINI.md`).                       |
| `excludeTools`    | Array  | No       | List of tool names to exclude (e.g., `["run_shell_command"]`).                    |
| `hooks`           | String | No       | **(Legacy)** Path to hooks file. The CLI automatically mimics `hooks/hooks.json`. |
| `dependencies`    | Object | No       | Map of system dependencies and their version requirements.                        |
| `settings`        | Array  | No       | Array of configuration settings exposed to the user.                              |

## Settings Schema

The `settings` array defines configuration options that the user can set via
`gemini extensions config`. These are exposed to the extension as environment
variables.

| Field         | Type    | Required | Description                                                                            |
| :------------ | :------ | :------- | :------------------------------------------------------------------------------------- |
| `name`        | String  | **Yes**  | Human-readable name of the setting (e.g., "API Key").                                  |
| `description` | String  | **Yes**  | Help text explaining the setting.                                                      |
| `envVar`      | String  | **Yes**  | The environment variable key where this value will be stored (e.g., `MY_EXT_API_KEY`). |
| `type`        | String  | No       | Data type (default `string`, `boolean`, `number`).                                     |
| `default`     | Any     | No       | Default value if not specified by the user.                                            |
| `optional`    | Boolean | No       | Whether the setting is optional (default `false`).                                     |
| `sensitive`   | Boolean | No       | If `true`, input is obfuscated and stored in keychain.                                 |

## Dependencies

Specify required system tools. This is for documentation and pre-check purposes.

```json
"dependencies": {
  "python": ">=3.7",
  "node": ">=18.0.0",
  "docker": "*"
}
```

## Example

```json
{
  "name": "gemini-awesome-tool",
  "version": "1.0.0",
  "settings": [
    {
      "name": "API Key",
      "description": "The API key for Awesome Service.",
      "envVar": "AWESOME_API_KEY"
    }
  ],
  "hooks": "./hooks/hooks.json"
}
```
