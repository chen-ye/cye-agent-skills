# Skill Maintenance Instructions

This document provides instructions for an AI agent to update and maintain the
`gemini-extension-authoring` skill using official, evergreen documentation.

## Authority Sources

The primary source of truth is the **Gemini CLI Documentation** site. Do not
rely on a fixed list of URLs, as the documentation structure may change.

- **Documentation Root**:
  [https://geminicli.com/docs](https://geminicli.com/docs)
- **Extensions Section**:
  [https://geminicli.com/docs/extensions/](https://geminicli.com/docs/extensions/)

## Update Protocol

To update this skill, execute the following workflow:

### 0. Preparation

- **Action**: You **MUST** activate the **Skill Development** skill before making any modifications to ensure the skill continues to follow best practices for structure, writing style, and progressive disclosure.
  ```
  activate_skill("Skill Development")
  ```

### 1. Discovery and Navigation

- **Goal**: Identify all relevant pages for extensions, hooks, and
  configuration.
- **Action**:
  1. Start at `https://geminicli.com/docs/extensions/` and
     `https://geminicli.com/docs/hooks/`.
  2. Spider/browse the navigation menu to identify new or renamed pages related
     to:
     - Extension Manifests / Schema
     - Hook Events and Implementation
     - Command Line Interface / Reference
     - Publishing / Releasing
     - Security / Permissions
  3. Create a list of relevant URLs to fetch in the subsequent steps.

### 2. Schema Validation

- **Goal**: Ensure `references/extension-schema.md` matches the latest
  `gemini-extension.json` specification.
- **Action**:
  1. Fetch the discovered pages related to the extension manifest and reference.
  2. Extract the full list of supported fields for `gemini-extension.json`.
  3. Check for new fields (e.g., `permissions`, `icons`, new `repository`
     types).
  4. Verify the `settings` object schema (fields like `envVar`, `optional`,
     `default`).
  5. Update `references/extension-schema.md` with any changes.

### 3. Hook Event Synchronization

- **Goal**: Ensure `references/hooks-schema.md` lists all currently supported
  lifecycle events.
- **Action**:
  1. Fetch discovered pages related to hooks and events.
  2. List all documented event types (e.g., `BeforeTool`, `AfterModel`,
     `SessionStart`).
  3. Compare with the table in `references/hooks-schema.md`.
  4. Add any new events or deprecate old ones.
  5. Verify the JSON payload structure (stdin) for each event hasn't changed.

### 4. Best Practices Refresh

- **Goal**: Ensure `SKILL.md` advice aligns with current recommendations.
- **Action**:
  1. Fetch discovered pages related to best practices, security, and examples.
  2. Review sections on Security, Performance, and User Experience.
  3. Update the "Best Practices" section in `SKILL.md` if new guidelines emerge
     (e.g., specific warning labels, timeout recommendations).

### 5. Capabilities Synchronization

- **Goal**: Ensure documentation and schemas for MCP servers, Skills,
  Sub-agents, and Commands is up to date.
- **Action**:
  1. Check for updates to **MCP Server** configuration in
     `gemini-extension.json`.
  2. Verify **Agent Skills** structure (`skills/` directory) and discovery
     mechanisms.
  3. Verify **Sub-agents** (experimental) structure (`agents/` directory) and
     update `references/agents-schema.md`.
  4. Verify **Custom Commands** (`commands/` directory) structure and update
     `references/commands-schema.md`.
  5. Update the corresponding sections in `SKILL.md`.

### 6. Publishing Workflow Check

...

## Prompt for Updating

Use the following prompt to initiate an update cycle:

> "Please update the gemini-extension-authoring skill. Start by reading
> `skills/gemini-extension-authoring/MAINTENANCE.md`. Activate the **Skill
> Development** skill to ensure quality standards. Then, browse
> `https://geminicli.com/docs/extensions/` and related sections to discover the
> latest documentation pages. Comprehensively verify that `SKILL.md` (including
> capabilities like MCP, Skills, Agents, Commands) and the schemas in
> `references/` (extension, hooks, agents, commands) match the current official
> documentation. Report any discrepancies and fix them."
