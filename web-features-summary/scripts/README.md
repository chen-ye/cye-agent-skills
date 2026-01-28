# Skill Maintenance Scripts

These scripts are used to update the `web-features-summary` skill with the latest data from the [web-features](https://www.npmjs.com/package/web-features) project.

## How to Update

1.  **Navigate to this directory:**
    ```bash
    cd scripts
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Update the Reference List:**
    Run the generation script to overwrite the existing reference file with new data.
    ```bash
    npm run update-reference
    ```
    *This updates `../references/baseline_2023_2026.md`.*

4.  **Analyze for New High-Impact Features:**
    Run the analysis script to see if any new "major" features (like new Array methods or CSS features) have been released.
    ```bash
    npm run analyze
    ```
    *Review the output. If you see important new features, manually update the "High-Impact Modern Features" section in `../SKILL.md`.*

5.  **Comprehensive Analysis:**
    Run the full analysis script to see all modern features grouped by category (CSS, HTML, JS, API), useful for identifying high-impact items missed by the keyword filter.
    ```bash
    npm run analyze-all
    ```
