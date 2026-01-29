# Custom Command Schema (`.toml`)

Define custom commands using TOML files to create shortcuts for complex prompts or actions.

## File Location

Place command definition files in the `commands/` directory of your extension.
- `commands/deploy.toml` -> `/deploy` (or `/extension:deploy`)
- `commands/gcp/deploy.toml` -> `/gcp:deploy`

## Configuration Fields

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `prompt` | String | **Yes** | The prompt to send to the model. |
| `description` | String | No | One-line description displayed in `/help`. |

## Example (`commands/deploy.toml`)

```toml
description = "Deploys the current application to production."
prompt = """
Review the current codebase for production readiness.
If all checks pass, execute the deployment script located at ./scripts/deploy.sh.
Ensure you wait for the confirmation step.
"""
```

## Variable Expansion

Custom commands support standard variable expansion in the `prompt` string:
- `${selection}`: Currently selected text in the editor (if applicable).
- `${file}`: Current open file path.
