#!/usr/bin/env python3
"""
inspect_spaces_workspace.py - Workspace, checkout, and log inspection tool for Spaces.

Audits active workspace files (co.spaces.toml, spaces.star), checkout targets,
execution logs in .spaces/logs/latest/, and the global store cache in ~/.spaces/.
"""

import argparse
import json
import os
import sys
import tomllib
from pathlib import Path


def find_workspace_root(start_path: Path) -> Path | None:
    current = start_path.resolve()
    home = Path.home().resolve()
    while current != current.parent:
        if (current / "co.spaces.toml").is_file() or (current / "spaces.star").is_file() or (current / "0.checkout.spaces.star").is_file():
            return current
        if (current / ".spaces").is_dir() and current != home:
            return current
        current = current.parent
    return None


def parse_co_spaces_toml(co_path: Path) -> dict:
    if not co_path.is_file():
        return {}
    try:
        with open(co_path, "rb") as f:
            data = tomllib.load(f)
        return data
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to parse {co_path}: {e}\n")
        return {}


def inspect_logs(ws_root: Path) -> dict:
    logs_dir = ws_root / ".spaces" / "logs" / "latest"
    if not logs_dir.is_dir():
        return {"exists": False, "path": str(logs_dir), "files": []}

    log_files = []
    failed_logs = []
    for p in sorted(logs_dir.glob("*.log")):
        size = p.stat().st_size
        mtime = p.stat().st_mtime
        # Check if last few lines contain ERROR or FAILED
        has_error = False
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                tail_lines = f.readlines()[-20:]
                for line in tail_lines:
                    if "ERROR" in line or "FAILED" in line or "error:" in line.lower():
                        has_error = True
                        break
        except Exception:
            pass

        log_info = {
            "name": p.name,
            "path": str(p),
            "size_bytes": size,
            "has_error": has_error,
        }
        log_files.append(log_info)
        if has_error:
            failed_logs.append(log_info)

    return {
        "exists": True,
        "path": str(logs_dir),
        "total_count": len(log_files),
        "failed_count": len(failed_logs),
        "files": log_files,
        "failed": failed_logs,
    }


def inspect_global_store() -> dict:
    store_path = Path.home() / ".spaces"
    if not store_path.is_dir():
        return {"exists": False, "path": str(store_path)}

    # Count subdirectories and estimate size
    entries = []
    try:
        for item in store_path.iterdir():
            entries.append(item.name)
    except Exception:
        pass

    return {
        "exists": True,
        "path": str(store_path),
        "top_level_entries": len(entries),
        "sample_entries": entries[:10],
    }


def main():
    parser = argparse.ArgumentParser(description="Audit Spaces workspace configuration, checkouts, and logs.")
    parser.add_argument("--dir", "-d", help="Workspace directory to inspect (defaults to cwd)")
    parser.add_argument("--co", action="store_true", help="Display checkout definitions from co.spaces.toml")
    parser.add_argument("--logs", action="store_true", help="Display recent execution logs from .spaces/logs/latest/")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    start_dir = Path(args.dir) if args.dir else Path.cwd()
    ws_root = find_workspace_root(start_dir)

    co_data = {}
    starlark_files = []
    logs_data = {"exists": False}

    if ws_root:
        co_file = ws_root / "co.spaces.toml"
        if co_file.is_file():
            co_data = parse_co_spaces_toml(co_file)
        for p in ws_root.glob("*.spaces.star"):
            starlark_files.append(p.name)
        logs_data = inspect_logs(ws_root)

    store_data = inspect_global_store()

    result = {
        "is_workspace": ws_root is not None,
        "workspace_root": str(ws_root) if ws_root else None,
        "starlark_scripts": sorted(starlark_files),
        "co_spaces_toml": co_data,
        "logs": logs_data,
        "global_store": store_data,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return

    if not ws_root:
        print(f"Current directory '{start_dir}' is NOT inside a Spaces workspace.")
        print(f"Global store located at: {store_data['path']} (exists: {store_data['exists']})")
        return

    print("=" * 80)
    print(f" Spaces Workspace: {ws_root}")
    print("=" * 80)

    if starlark_files:
        print(f"\nRoot Starlark Scripts: {', '.join(sorted(starlark_files))}")

    if co_data:
        print(f"\n--- co.spaces.toml Entries ({len(co_data)}) ---")
        for key, details in co_data.items():
            entry_type = "Unknown"
            if isinstance(details, dict):
                # e.g. key is 'spaces-dev.Repo' or details has type
                print(f"  [{key}]")
                if "url" in details:
                    print(f"    url: {details['url']}")
                if "rev" in details:
                    print(f"    rev: {details['rev']}")
                if "rule-name" in details:
                    print(f"    rule-name: {details['rule-name']}")
                if "workflow" in details:
                    print(f"    workflow: {details['workflow']}")
                if "derive-from" in details:
                    print(f"    derive-from: {details['derive-from']}")
                if "store" in details:
                    print(f"    store: {details['store']}")

    if logs_data["exists"]:
        print(f"\n--- Execution Logs (.spaces/logs/latest/) ---")
        print(f"Total targets logged: {logs_data['total_count']}")
        if logs_data['failed_count'] > 0:
            print(f"WARNING: {logs_data['failed_count']} target(s) reported errors/failures:")
            for fl in logs_data['failed']:
                print(f"  - {fl['name']} ({fl['size_bytes']} bytes)")
        else:
            print("All logged targets completed without error keywords.")
    else:
        print("\nNo recent execution logs found in .spaces/logs/latest/.")

    print(f"\nGlobal Store: {store_data['path']} ({store_data.get('top_level_entries', 0)} entries)")


if __name__ == "__main__":
    main()
