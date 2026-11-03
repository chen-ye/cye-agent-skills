#!/usr/bin/env python3
"""
Resolve or unresolve PR review threads via GitHub GraphQL API.
Only to be executed after explicit user review and consent.

Supports GitHub.com and GitHub Enterprise Server (auto-detects hostname).

Usage:
  python resolve_thread.py THREAD_ID [THREAD_ID ...] [--unresolve] [--hostname HOST]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.parse
from typing import Any

RESOLVE_MUTATION = """\
mutation($threadId: ID!) {
  resolveReviewThread(input: { threadId: $threadId }) {
    thread {
      id
      isResolved
      resolvedBy {
        login
      }
    }
  }
}
"""

UNRESOLVE_MUTATION = """\
mutation($threadId: ID!) {
  unresolveReviewThread(input: { threadId: $threadId }) {
    thread {
      id
      isResolved
    }
  }
}
"""


def _run(cmd: list[str], stdin: str | None = None) -> str:
    p = subprocess.run(cmd, input=stdin, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout


def _run_json(cmd: list[str], stdin: str | None = None) -> dict[str, Any]:
    out = _run(cmd, stdin=stdin)
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON: {e}\nRaw:\n{out}") from e


def auto_detect_hostname() -> str:
    try:
        pr = _run_json(["gh", "pr", "view", "--json", "url"])
        url = pr.get("url", "")
        return urllib.parse.urlparse(url).netloc or "github.com"
    except Exception:
        return "github.com"


def set_thread_resolution(thread_id: str, resolve: bool, hostname: str) -> dict[str, Any]:
    mutation = RESOLVE_MUTATION if resolve else UNRESOLVE_MUTATION
    cmd = [
        "gh",
        "api",
        "--hostname",
        hostname,
        "graphql",
        "-F",
        "query=@-",
        "-F",
        f"threadId={thread_id}",
    ]
    res = _run_json(cmd, stdin=mutation)
    if "errors" in res and res["errors"]:
        raise RuntimeError(f"GraphQL error updating thread {thread_id}: {json.dumps(res['errors'])}")
    key = "resolveReviewThread" if resolve else "unresolveReviewThread"
    return res["data"][key]["thread"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve or unresolve GitHub PR review threads upon user approval.")
    parser.add_argument("threads", nargs="+", help="One or more Review Thread GraphQL IDs")
    parser.add_argument("--unresolve", action="store_true", help="Unresolve the threads instead of resolving them")
    parser.add_argument("--hostname", help="GitHub hostname (default: auto-detected)")
    args = parser.parse_args()

    hostname = args.hostname or auto_detect_hostname()

    success_count = 0
    for tid in args.threads:
        try:
            thread = set_thread_resolution(tid, not args.unresolve, hostname)
            status = "RESOLVED" if thread.get("isResolved") else "UNRESOLVED"
            by = f" by @{thread.get('resolvedBy', {}).get('login')}" if thread.get("resolvedBy") else ""
            print(f"[{status}] Thread {tid}{by}")
            success_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to update thread {tid}: {e}", file=sys.stderr)

    if success_count != len(args.threads):
        sys.exit(1)


if __name__ == "__main__":
    main()
