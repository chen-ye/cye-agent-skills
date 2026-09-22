---
name: MCP Server Tester
description: This skill should be used when the user asks to "test mcp servers", "check mcp status", "verify mcp tools", "test configured mcp", or "inspect configured mcp servers". It provides a testing script that parses settings.json and checks the responsiveness of enabled MCP servers using the mcptools CLI.
version: 0.1.0
---

# MCP Server Tester

This skill provides a standardized way to test all enabled Model Context Protocol (MCP) servers configured in the user's `settings.json` file. It uses a Python script that leverages the `mcptools` CLI to ping each server and report its status and response time.

## Usage

When tasked with testing or inspecting MCP servers:

1. Ensure `mcptools` is installed (it is typically available via `npx mcptools` or globally if installed).
2. Execute the provided testing script to check the status of all non-excluded servers.

To run the test, execute the following command:

```bash
python3 ~/.gemini/skills/mcp-server-tester/scripts/test_mcp_servers.py
```

## Interpreting Results

The script outputs the status of each enabled server:
- ✅ **Working:** The server responded successfully via `mcp tools`.
- ⚠️ **Skipped:** The server configuration lacks a `command`, `url`, or `httpUrl`.
- ❓ **Responded with HTTP error:** The server is an HTTP/SSE endpoint that responded, but `mcptools` couldn't complete the handshake (e.g., 400/401/405). This usually means the server is online but expects a proper SSE connection or authentication.
- ❌ **Failed:** The server failed to start or connection was refused.
- ⏳ **Timeout:** The server took longer than 15 seconds to respond.

## Additional Resources

### Reference Files
None currently.

### Examples
None currently.

### Scripts
- **`scripts/test_mcp_servers.py`**: The main Python script that parses `~/.gemini/settings.json`, filters out excluded servers, and runs `mcp tools` against each active server to measure startup time and verify connectivity.
