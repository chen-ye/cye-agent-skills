# Agent Skills

Collection of skills for AI agents.

## Skills

- **app-audit**: Analyzes installed Termux packages and Android apps to identify redundancies, categorize usage, and suggest cleanups.
- **gemini-extension-authoring**: Provide expert guidance on creating,
  packaging, and publishing extensions for the Gemini CLI.
- **web-features-summary**: Summarizes newly available web platform features
  (Baseline 2023-2026) and Chrome-specific capabilities.

## Usage

### Gemini CLI

Install a skill into your current workspace:

```bash
gemini skills install https://github.com/chen-ye/cye-agent-skills.git --path <skill-name> --scope workspace
```

### Generic Skills CLI

Install via [skills](https://github.com/vercel-labs/skills) CLI:

```bash
npx skills add https://github.com/chen-ye/cye-agent-skills -g --skill <skill-name>
```