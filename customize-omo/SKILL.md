---
name: customize-omo
description: This skill MUST be invoked every time there is a request to edit, configure, tune, or customize OmO (oh-my-openagent, oh-my-opencode) settings, agent models, categories, hooks, MCPs, or any file within ~/.omo/ or .omo/. Instructs the agent on the strict unified configuration format and mandates running the validation command after any changes.
---

# Customizing Oh My OpenAgent (OmO)

`oh-my-openagent` (OmO) validates its configuration strictly at load time. If an invalid or unrecognized key is placed at the wrong schema level, the entire configuration file is silently dropped, causing the system to fall back to hardcoded defaults.

---

## File Locations & Precedence

1. **User Global Layer** (lowest precedence):
   * `~/.omo/omo.jsonc` (or `~/.omo/omo.json`)
2. **Project Layer** (highest precedence):
   * `.omo/omo.jsonc` (or `.omo/omo.json`) in the project root or nearest ancestor directory.

> **CRITICAL NOTE**: Legacy files such as `~/.config/opencode/oh-my-openagent.jsonc` or `oh-my-opencode.jsonc` are migration targets only and are **NOT read at runtime** by modern OmO (v4.19+). Always edit `~/.omo/omo.jsonc`.

---

## Strict Root Schema Invariants

The root object of `omo.jsonc` is validated with `OmoConfigLayerSchema.strict()`. **Placing harness-specific keys at the root will cause the entire config to fail validation.**

### Allowed Root-Level Keys (Strict Set):
* `$schema` (Schema definition URL)
* `agents` (Shared agent model/prompt overrides)
* `categories` (Shared task delegation category overrides)
* `models` (Shared model catalog shortcuts)
* `codegraph` (CodeGraph indexing settings)
* `task` (Task engine settings)
* `teams` (Team Mode definitions)
* `memory` (Senpi memory settings object)
* `telemetry` (Telemetry object: `{ "enabled": boolean }`)
* `[opencode]` (OpenCode plugin-specific configuration block)
* `[senpi]` / `[codex]` (Harness-specific blocks)
* `profiles` (Named profile configurations)
* `_migrations` / `legacy_migrations` (Migration journal tracking)

---

## Where OpenCode Options Belong: Inside `[opencode]`

All OpenCode plugin-specific features **must be placed inside the `[opencode]` block**:

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/omo.schema.json",

  // 1. Root level: Shared Agents & Categories
  "agents": {
    "sisyphus": { "model": "google/gemini-3.7-flash" },
    "oracle": { "model": "google/gemini-3.1-pro" },
    "explore": { "model": "google/gemini-3.5-flash-lite" }
  },
  "categories": {
    "visual-engineering": { "model": "google/gemini-3.7-flash" },
    "ultrabrain": { "model": "google/gemini-3.1-pro" },
    "deep": { "model": "google/gemini-3.7-flash" },
    "quick": { "model": "google/gemini-3.5-flash-lite" }
  },

  // 2. OpenCode Harness Block: Plugin Features & Guards
  "[opencode]": {
    "sisyphus_agent": {
      "default_builder_enabled": true,  // Keeps native 'build' as OpenCode-Builder
      "replace_plan": false             // Keeps native 'plan' alongside Prometheus
    },
    "hashline_edit": true,              // Enables hash-anchored LINE#ID edits
    "model_fallback": true,             // Automatic error retry & fallback
    "disabled_agents": [],              // E.g. ["multimodal-looker"]
    "disabled_mcps": [],                // E.g. ["grep_app"]
    "disabled_tools": [],               // E.g. ["interactive_bash"]
    "disabled_hooks": [],               // E.g. ["comment-checker"]
    "disabled_skills": [],              // E.g. ["playwright"]
    "background_task": {
      "providerConcurrency": {
        "google": 2
      }
    },
    "git_master": {
      "commit_footer": false,           // Disables automated commit footers
      "include_co_authored_by": false   // Disables automated co-author trailers
    },
    "telemetry": false                  // Telemetry boolean in OpenCode block
  }
}
```

---

## MANDATORY Post-Edit Verification

After performing ANY modification to `~/.omo/omo.jsonc` or `.omo/omo.jsonc`, **you MUST immediately run the validation doctor command**:

```bash
bunx oh-my-openagent doctor --verbose
```

### Verification Criteria (Must Pass):
1. **Validation Summary**: Must show `0 failed, 0 warnings`.
2. **Issues Section**: Must be empty (no `Invalid omo config` or `Unrecognized key` errors).
3. **Model Resolution Status**:
   * Configured agents/categories MUST show **`●`** (solid circle = user override active).
   * If any model shows **`○`** (open circle = provider fallback), validation failed and the config was dropped. Fix the schema error immediately.

---

## Session Restart Policy

Remind the user that OpenCode and plugin configurations are loaded on process startup. After saving and validating configuration edits, remind the user to restart the running OpenCode server or terminal session for in-memory plugin changes to take effect.
