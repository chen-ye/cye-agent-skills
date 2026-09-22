# OpenCode Documentation Reference Map

The OpenCode source checkout maintains official user and developer documentation under:
`<checkout>/packages/web/src/content/docs/*.mdx` (or `<checkout>/dev/packages/web/src/content/docs/*.mdx`)

Always inspect these MDX files when determining official user-facing syntax, options, and recommended configurations.

---

## Documentation Index & Topics

| MDX File | Title | Covered Concepts & Search Keys |
| :--- | :--- | :--- |
| **`permissions.mdx`** | Permissions | Permission actions (`allow`, `ask`, `deny`), auto mode (`--auto`), object syntax, wildcards (`*`, `?`), home expansion (`~`, `$HOME`), `external_directory`, `doom_loop`, defaults. |
| **`config.mdx`** | Config | `opencode.json` / `opencode.jsonc` schema, model configuration, providers, plugins, keybindings, theme settings, options hierarchy. |
| **`tools.mdx`** | Tools | Built-in tools (`read`, `edit`, `write`, `bash`, `glob`, `grep`, `list`, `task`, `skill`), tool permission mappings, input/output schemas. |
| **`agents.mdx`** | Agents | Primary agents (`build`, `plan`), subagents (`explore`, `general`), agent frontmatter, tool access lists, permission overrides per agent. |
| **`cli.mdx`** | CLI | Command-line interface commands (`opencode`, `opencode run`, `opencode server`), CLI flags (`--auto`, `--model`, `--port`), batch modes. |
| **`custom-tools.mdx`**| Custom Tools | Defining custom JavaScript/TypeScript tools, schemas, return shapes, and integration with the tool registry. |
| **`plugins.mdx`** | Plugins | OpenCode plugin architecture, hooks (`preToolUse`, `postToolUse`, `onMessage`), lifecycle hooks, and plugin packaging. |
| **`mcp-servers.mdx`** | MCP Servers | Model Context Protocol (MCP) configuration, local/remote servers, STDIO vs. SSE/HTTP transports, auth headers. |
| **`skills.mdx`** | Agent Skills | Agent skills structure, `SKILL.md` format, progressive disclosure (`scripts/`, `references/`, `assets/`), discovery paths (`~/.config/opencode/skills`). |
| **`lsp.mdx`** | LSP Servers | Language Server Protocol integration, auto-starting language servers, diagnostics, and workspace symbol discovery. |
| **`rules.mdx`** | Rules | Custom system instructions, repository rules (`.opencode/rules`), global user rules, and instruction priority. |
| **`providers.mdx`** | Providers | Connecting model providers (Google, OpenAI, Anthropic, Bedrock, Ollama, OpenRouter, DeepSeek), API keys, and endpoint overrides. |
| **`models.mdx`** | Models | Model selection, temperature, top-p, context window limits, reasoning effort options, and cost tracking. |
| **`server.mdx`** | Server | Running headless OpenCode server, REST API endpoints, WebSocket streams, and multi-session concurrency. |
| **`acp.mdx`** | ACP Support | Agent Client Protocol specification and compatibility with editors like Zed, Cursor, or JetBrains. |
| **`tui.mdx`** | TUI | Terminal interface usage, shortcuts, session switcher, prompt modes, and visual indicators. |
| **`troubleshooting.mdx`** | Troubleshooting | Common errors, port conflicts, permission denials, LSP startup issues, and log locations. |
| **`enterprise.mdx`** | Enterprise | Enterprise policy enforcement, central permission lockdown, telemetry, and corporate proxies. |
| **`formatters.mdx`** | Formatters | Code formatting hooks (Prettier, Biome, Black, Rustfmt) triggered automatically after edits. |
| **`network.mdx`** | Network | Corporate HTTP proxies, custom TLS root certificates, and offline mode. |
| **`keybinds.mdx`** | Keybinds | Keymap customization, vim bindings, command palette shortcuts. |

---

## Multilingual Translations

The documentation directory contains localized translations in language subdirectories:
* `zh-cn/`, `zh-tw/`, `ja/`, `ko/`, `de/`, `fr/`, `es/`, `it/`, `pt-br/`, `ru/`, `tr/`, `th/`, etc.
* **Ground truth notice**: Always prefer the root English (`.mdx`) files for the most up-to-date specifications, as localized copies may lag upstream updates.
