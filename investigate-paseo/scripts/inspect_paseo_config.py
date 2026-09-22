#!/usr/bin/env python3
"""
inspect_paseo_config.py - Inspects and audits active Paseo configuration, daemon status,
configured providers, and persisted agents.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

def get_paseo_home() -> Path:
    return Path(os.environ.get("PASEO_HOME", Path.home() / ".paseo"))

def read_daemon_config(paseo_home: Path) -> dict:
    cfg_file = paseo_home / "config.json"
    if cfg_file.is_file():
        try:
            return json.loads(cfg_file.read_text(encoding="utf-8"))
        except Exception as e:
            return {"_error": f"Failed to parse config.json: {e}"}
    return {}

def get_daemon_status() -> dict:
    paseo_bin = os.environ.get("PASEO_BIN", "paseo")
    try:
        raw = subprocess.check_output([paseo_bin, "daemon", "status", "--json"], stderr=subprocess.PIPE).decode("utf-8")
        return json.loads(raw)
    except Exception:
        return {}

def list_persisted_agents(paseo_home: Path, limit: int = 15) -> list[dict]:
    agents_dir = paseo_home / "agents"
    agents = []
    if not agents_dir.is_dir():
        return agents
    for p in sorted(agents_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)[:limit]:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            agents.append({
                "agentId": data.get("id", p.stem),
                "title": data.get("title", "Untitled"),
                "provider": data.get("provider", "unknown"),
                "status": data.get("status", "unknown"),
                "cwd": data.get("cwd", "unknown"),
                "updatedAt": data.get("updatedAt"),
            })
        except Exception:
            continue
    return agents

def list_worktrees(paseo_home: Path) -> list[str]:
    wt_dir = paseo_home / "worktrees"
    if not wt_dir.is_dir():
        return []
    return sorted([d.name for d in wt_dir.iterdir() if d.is_dir()])

def format_overview(paseo_home: Path, config: dict, daemon_status: dict, agents: list[dict], worktrees: list[str]) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("Paseo Configuration, Daemon & Workspace Audit")
    lines.append("=" * 80)

    # 1. Daemon & Host Info
    lines.append("\n[Daemon Status]")
    lines.append(f"  PASEO_HOME       : {paseo_home}")
    if daemon_status:
        lines.append(f"  Running State    : {daemon_status.get('status', 'running')}")
        lines.append(f"  Listen Address   : {daemon_status.get('listenAddress', daemon_status.get('host', '127.0.0.1'))}:{daemon_status.get('port', 6767)}")
        lines.append(f"  Server ID        : {daemon_status.get('serverId', 'N/A')}")
        lines.append(f"  Process PID      : {daemon_status.get('pid', 'N/A')}")
    else:
        pid_file = paseo_home / "daemon.pid"
        pid = pid_file.read_text().strip() if pid_file.is_file() else "None"
        lines.append(f"  Running State    : Unknown / Stopped (daemon.pid: {pid})")
        lines.append(f"  Default Listen   : 127.0.0.1:6767")

    # 2. Config options
    lines.append("\n[Daemon Configuration (config.json)]")
    if not config:
        lines.append("  No config.json found (using default internal settings)")
    elif "_error" in config:
        lines.append(f"  Error: {config['_error']}")
    else:
        for k, v in config.items():
            if isinstance(v, (str, int, bool)):
                lines.append(f"  {k:<18}: {v}")
            elif isinstance(v, dict):
                lines.append(f"  {k:<18}: {len(v)} configured items")

    # 3. Worktrees
    lines.append(f"\n[Managed Worktrees] ({len(worktrees)} total)")
    if worktrees:
        for wt in worktrees[:8]:
            lines.append(f"  • {wt}")
        if len(worktrees) > 8:
            lines.append(f"    ... and {len(worktrees) - 8} more")
    else:
        lines.append("  None active")

    # 4. Recent Agents
    lines.append(f"\n[Recent Persisted Agents] (Showing {len(agents)})")
    if agents:
        for a in agents:
            lines.append(f"  • [{a['agentId'][:12]}] {a['title'][:35]:<35} | {a['provider']} | {a['status']}")
            lines.append(f"    CWD: {a['cwd']}")
    else:
        lines.append("  No agent records found under ~/.paseo/agents/")

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Audit Paseo configuration and daemon state.")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
    parser.add_argument("--agents", action="store_true", help="List detailed agent records.")
    parser.add_argument("--worktrees", action="store_true", help="List all managed worktrees.")
    args = parser.parse_args()

    paseo_home = get_paseo_home()
    config = read_daemon_config(paseo_home)
    status = get_daemon_status()
    agents = list_persisted_agents(paseo_home, limit=50 if args.agents else 10)
    worktrees = list_worktrees(paseo_home)

    if args.json:
        out = {
            "paseoHome": str(paseo_home),
            "config": config,
            "daemonStatus": status,
            "worktrees": worktrees,
            "agents": agents,
        }
        print(json.dumps(out, indent=2))
        return

    print(format_overview(paseo_home, config, status, agents, worktrees))

if __name__ == "__main__":
    main()
