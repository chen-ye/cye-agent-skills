# Sub-agent Definition Schema

Define sub-agents using Markdown files with YAML frontmatter.

## File Location

Place sub-agent definition files in the `agents/` directory of your extension.
The filename (e.g., `security-auditor.md`) determines the default slug if `name` is not provided, but explicitly setting `name` in frontmatter is required.

## Structure

```markdown
---
name: my-agent
description: specialized description
tools:
  - tool_name_1
---
System prompt content goes here...
```

## Configuration Fields (YAML Frontmatter)

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | String | **Yes** | Unique identifier (slug) for the agent. Used by the main agent to delegate tasks. |
| `description` | String | **Yes** | Concise description of the agent's expertise. Critical for the router to decide when to use this agent. |
| `kind` | String | No | Execution mode. Default: `local`. |
| `tools` | Array | No | List of tool names this agent is allowed to use. |
| `model` | String | No | Specific model to use (e.g., `gemini-2.5-pro`). Defaults to the session model. |
| `temperature` | Number | No | Sampling temperature (0.0 - 2.0). |
| `max_turns` | Number | No | Maximum conversation turns allowed (default varies). |
| `timeout_mins`| Number | No | Execution timeout in minutes. |

## System Prompt (Body)

The content after the YAML frontmatter serves as the **System Prompt**.
Use this space to:
- Define the agent's persona.
- Set strict rules and constraints.
- Provide few-shot examples.
- Outline standard operating procedures.

## Example

```markdown
---
name: security-auditor
description: Specialized in finding security vulnerabilities in code.
kind: local
tools:
  - read_file
  - search_file_content
model: gemini-2.5-pro
temperature: 0.2
---
You are a ruthless Security Auditor.
Your job is to analyze code for potential vulnerabilities.
Focus on:
1. SQL Injection
2. XSS
3. Hardcoded credentials
```
