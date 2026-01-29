# Skill Maintenance Instructions

This document provides instructions for an AI agent to update and maintain the
`web-features-summary` skill using the [web-features](https://www.npmjs.com/package/web-features) dataset.

## Authority Sources

The primary source of truth is the **web-features** npm package, which tracks
Baseline status across major browsers.

- **NPM Package**: [web-features](https://www.npmjs.com/package/web-features)
- **Source Repository**: [web-platform-dx/web-features](https://github.com/web-platform-dx/web-features)

## Update Protocol

To update this skill, execute the following workflow:

### 0. Preparation

- **Action**: You **MUST** activate the **Skill Development** skill before making any modifications to ensure the skill continues to follow best practices for structure, writing style, and progressive disclosure.
  ```
  activate_skill("Skill Development")
  ```

### 1. Dependency Update

- **Goal**: Fetch the latest `web-features` dataset.
- **Action**:
  1. Navigate to the scripts directory: `cd scripts`.
  2. Update the package: `npm install web-features@latest`.

### 2. Reference List Regeneration

- **Goal**: Update the comprehensive list of baseline features.
- **Action**:
  1. Run `npm run update-reference`.
  2. Verify that `references/baseline_2023_2026.md` has been updated with new entries.
  3. Ensure the file header reflects the current generation date.

### 3. High-Impact Feature Analysis

- **Goal**: Identify new major features to highlight in `SKILL.md`.
- **Action**:
  1. Run `npm run analyze-all` to see a categorized list of all modern features.
  2. Review the output for significant new features (e.g., new CSS layout primitives, major JS methods) that have recently achieved "Baseline High" or "Baseline Low" status.
  3. Compare this list against the "High-Impact Modern Features" section in `SKILL.md`.

### 4. Skill Content Refresh

- **Goal**: Keep the summary and best practices current.
- **Action**:
  1. If significantly new features are found in Step 3, add them to the "High-Impact Modern Features" section in `SKILL.md`.
  2. If new "Chrome-First" features appear in the analysis (use `node analyze_interop_chrome.js` if needed), update the "Chrome-Supported Modern Features" section.
  3. Review `references/modern_idioms.md` to see if any new features obsolete existing patterns (e.g., if a new native method replaces a common workaround).

## Prompt for Updating

Use the following prompt to initiate an update cycle:

> "Please update the web-features-summary skill. Start by reading
> `skills/web-features-summary/MAINTENANCE.md`. Activate the **Skill
> Development** skill to ensure quality standards. Run the update scripts in
> `skills/web-features-summary/scripts/` to regenerate the baseline reference
> and analyze new features. Update `SKILL.md` with any new high-impact additions
> and commit the changes."
