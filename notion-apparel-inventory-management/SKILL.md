---
name: Notion Apparel Inventory Management
description: This skill should be used when the user asks to "add gear to the inventory", "update the bike apparel database", "add [item name] to Notion", or manage the Bike & Outdoor Apparel Inventory. It provides the exact database IDs, property schemas, and research workflows required to accurately populate gear specifications.
version: 0.1.0
---

# Notion Apparel Inventory Management

This skill provides the standard operating procedure for adding or updating items in the "Bike & Outdoor Apparel Inventory" Notion database.

## Database Information

*   **Database URL:** `https://www.notion.so/e077daa093764343a745cad58393d8a2`
*   **Data Source ID:** `90f3af9a-084d-412e-a5c7-f0ced1816a13`

## Workflow

To add or update an item in the inventory, follow these steps:

1.  **Extract Primary Product Details:** Information should be sourced in the following priority order to ensure accuracy:
    1.  **PDPs:** Current official Product Detail Pages.
    2.  **Archived PDPs:** If the current PDP is dead or points to a newer generation, attempt to find an archived version via the Wayback Machine using the CDX API (https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server).
        To discover the URL for an old PDP, use the following approach:
        1. Query the CDX API for snapshots in the year of the product introduction (after the product went on sale). You can source the introduction year from reviews, your own knowledge, or ask the user for the purchase date.
           * **Use `run_shell_command` with `curl`** (e.g., `curl -s '...'`) because `web_fetch` may abort on these API endpoints.
           * **Search by URL Prefix:** It is often most effective to search using a wildcard `*` at the end of a known path prefix to find specific product IDs.
           * Example to find a specific product from 2020-2023: `curl -s "http://web.archive.org/cdx/search/cdx?url=https://www.rapha.cc/us/en_US/shop/mens-pro-team-training-jersey/product/*&output=json&limit=10&from=2020&to=2023"`
           * Example to find a product catalog page (if you don't know the product prefix): `curl -s "http://web.archive.org/cdx/search/cdx?url=https://www.rapha.cc/us/en/shop/jerseys&from=2021&to=2021&output=json&fl=timestamp,original,statuscode&filter=statuscode:200&limit=5"`
        2. The response will be a JSON array of snapshots. Construct the Wayback URL for the most appropriate snapshot using the format: `http://web.archive.org/web/[timestamp]/[original_url]`.
        3. Browse this snapshot via `web_fetch`. If it's a catalog page, search the page for the specific product, locate the URL for its PDP, and then check the CDX API again for snapshots of that specific PDP URL. If it's the PDP, extract product details directly.
    3.  **Reviews (established sites):** e.g., CyclingWeekly, road.cc.
    4.  **Reviews (social media/blogs):** e.g., Reddit, personal blogs.
    
    *Research must be thorough and accurate. Be aware that details can vary significantly by model year/generation. Always confirm the search result describes the exact product being added.*

2.  **Conduct Supplemental Research:** You MUST use `google_web_search` to find independent reviews and secondary information if the PDP is insufficient. This is critical for determining real-world fit (e.g., "runs small", "race cut"), practical temperature ranges, and intended usage (e.g., is it good for bikepacking?).
3.  **Populate Properties Exhaustively:**
    *   **Usage & Conditions:** Be highly comprehensive when selecting options for these multi-select fields. Do not just pick one; select all that apply based on your research (e.g., a cargo bib might be tagged for Road, Gravel, Touring, Bikepacking, Commuting, and Ultra Cycling).
    *   **Fit:** Translate brand-specific fits into the database's options (e.g., a "Race Cut" translates to "Road tight").
    *   **Care Instructions:** Synthesize washing instructions clearly.
    *   **Notes:** Write a concise summary of key features, unique materials (e.g., Pertex Shield, specific chamois pads), and fit advice.
4.  **Execute the Change:** Use `notion-create-pages` (for new items) or `notion-update-page` (for existing items) using the Data Source ID as the parent.
5.  **Report to User:** Provide a clear summary of the added/updated details and explicitly list the data sources used to gather the information.
