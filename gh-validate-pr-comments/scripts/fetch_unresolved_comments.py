#!/usr/bin/env python3
"""
Fetch PR review threads for a reviewer to validate whether comments have been addressed.

Supports:
- Validating UNRESOLVED review threads (default)
- Auditing review threads that were NOT resolved by the original commenter (--audit or --non-author-resolved)
- Inspecting all or resolved-only review threads (--all, --resolved-only)

Supports GitHub.com and GitHub Enterprise Server (auto-detects hostname).

Usage:
  python fetch_unresolved_comments.py [--audit | --non-author-resolved | --resolved-only | --all] [--pr NUMBER] [--format {summary,json}]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
from typing import Any

QUERY = """\
query(
  $owner: String!,
  $repo: String!,
  $number: Int!,
  $threadsCursor: String
) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number
      url
      title
      state
      author { login }
      baseRefName
      headRefName

      # Inline review threads
      reviewThreads(first: 100, after: $threadsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          originalLine
          diffSide
          startLine
          resolvedBy { login }
          comments(first: 100) {
            nodes {
              id
              body
              diffHunk
              createdAt
              updatedAt
              author { login }
            }
          }
        }
      }
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


def _ensure_gh_authenticated(hostname: str | None = None) -> None:
    cmd = ["gh", "auth", "status"]
    if hostname:
        cmd += ["--hostname", hostname]
    try:
        _run(cmd)
    except RuntimeError:
        target = f" on {hostname}" if hostname else ""
        print(f"Run `gh auth login` to authenticate the GitHub CLI{target}", file=sys.stderr)
        raise


def resolve_pr_context(pr_number: int | None = None, repo: str | None = None, host: str | None = None) -> tuple[str, str, int, str]:
    """Resolve (owner, repo, pr_number, hostname)."""
    cmd = ["gh", "pr", "view"]
    if pr_number:
        cmd.append(str(pr_number))
    if repo:
        cmd += ["--repo", repo]
    cmd += ["--json", "number,headRepositoryOwner,headRepository,url"]

    pr = _run_json(cmd)
    owner = pr["headRepositoryOwner"]["login"]
    repo_name = pr["headRepository"]["name"]
    number = int(pr["number"])
    url = pr.get("url", "")
    parsed_url = urllib.parse.urlparse(url)
    hostname = host or parsed_url.netloc or "github.com"
    return owner, repo_name, number, hostname


def gh_api_graphql(
    owner: str,
    repo: str,
    number: int,
    hostname: str,
    threads_cursor: str | None = None,
) -> dict[str, Any]:
    cmd = [
        "gh",
        "api",
        "--hostname",
        hostname,
        "graphql",
        "-F",
        "query=@-",
        "-F",
        f"owner={owner}",
        "-F",
        f"repo={repo}",
        "-F",
        f"number={number}",
    ]
    if threads_cursor:
        cmd += ["-F", f"threadsCursor={threads_cursor}"]

    return _run_json(cmd, stdin=QUERY)


def annotate_thread(thread: dict[str, Any], pr_author: str | None = None) -> dict[str, Any]:
    """Attach resolution authority metadata comparing resolvedBy with the original commenter."""
    comments = (thread.get("comments") or {}).get("nodes") or []
    first_comment = comments[0] if comments else {}
    original_commenter = (first_comment.get("author") or {}).get("login")
    resolved_by = (thread.get("resolvedBy") or {}).get("login")
    is_resolved = bool(thread.get("isResolved"))

    is_resolved_by_original_commenter = bool(
        is_resolved
        and original_commenter
        and resolved_by
        and resolved_by.lower() == original_commenter.lower()
    )
    is_resolved_by_other = bool(is_resolved and not is_resolved_by_original_commenter)
    is_resolved_by_pr_author = bool(
        is_resolved
        and pr_author
        and resolved_by
        and resolved_by.lower() == pr_author.lower()
    )

    thread["originalCommenter"] = original_commenter
    thread["resolvedByLogin"] = resolved_by
    thread["isResolvedByOriginalCommenter"] = is_resolved_by_original_commenter
    thread["isResolvedByOther"] = is_resolved_by_other
    thread["isResolvedByPrAuthor"] = is_resolved_by_pr_author
    return thread


def filter_threads(threads: list[dict[str, Any]], filter_mode: str) -> list[dict[str, Any]]:
    if filter_mode == "unresolved":
        return [t for t in threads if not t.get("isResolved")]
    if filter_mode == "audit":
        return [t for t in threads if not t.get("isResolved") or t.get("isResolvedByOther")]
    if filter_mode == "non-author-resolved":
        return [t for t in threads if t.get("isResolvedByOther")]
    if filter_mode == "resolved":
        return [t for t in threads if t.get("isResolved")]
    return list(threads)


def fetch_all(owner: str, repo: str, number: int, hostname: str) -> dict[str, Any]:
    review_threads: list[dict[str, Any]] = []
    threads_cursor: str | None = None
    pr_meta: dict[str, Any] | None = None

    while True:
        payload = gh_api_graphql(
            owner=owner,
            repo=repo,
            number=number,
            hostname=hostname,
            threads_cursor=threads_cursor,
        )

        if "errors" in payload and payload["errors"]:
            raise RuntimeError(f"GitHub GraphQL errors:\n{json.dumps(payload['errors'], indent=2)}")

        pr = payload["data"]["repository"]["pullRequest"]
        if pr_meta is None:
            pr_meta = {
                "number": pr["number"],
                "url": pr["url"],
                "title": pr["title"],
                "state": pr["state"],
                "author": (pr.get("author") or {}).get("login"),
                "owner": owner,
                "repo": repo,
                "hostname": hostname,
                "baseRefName": pr.get("baseRefName", "main"),
                "headRefName": pr.get("headRefName", ""),
            }

        t = pr["reviewThreads"]
        pr_author = pr_meta.get("author") if pr_meta else None
        for node in t.get("nodes") or []:
            review_threads.append(annotate_thread(node, pr_author=pr_author))

        threads_cursor = t["pageInfo"]["endCursor"] if t["pageInfo"]["hasNextPage"] else None
        if not threads_cursor:
            break

    return {
        "pull_request": pr_meta,
        "review_threads": review_threads,
    }


def get_proximal_code_snippet(path: str, target_line: int | None, window: int = 5) -> str:
    """Read a small window of code around target line from working tree."""
    if not path or not os.path.exists(path) or target_line is None or target_line <= 0:
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        start = max(0, target_line - window - 1)
        end = min(len(lines), target_line + window)
        snippet_lines = []
        for idx in range(start, end):
            line_no = idx + 1
            marker = " > " if line_no == target_line else "   "
            snippet_lines.append(f"{marker}{line_no:4d} | {lines[idx].rstrip()}")
        return "\n".join(snippet_lines)
    except Exception:
        return ""


def print_summary(data: dict[str, Any], filter_mode: str = "unresolved", include_code: bool = True) -> None:
    pr = data["pull_request"]
    all_threads = data["review_threads"]
    threads = filter_threads(all_threads, filter_mode)

    total_threads = len(all_threads)
    unresolved_count = len([t for t in all_threads if not t.get("isResolved")])
    resolved_count = total_threads - unresolved_count
    resolved_by_commenter_count = len([t for t in all_threads if t.get("isResolvedByOriginalCommenter")])
    resolved_by_other_count = len([t for t in all_threads if t.get("isResolvedByOther")])

    pr_author_str = f" (author: @{pr['author']})" if pr.get("author") else ""
    print("=" * 80)
    print(f"PR Review Validation: #{pr['number']} {pr['title']}{pr_author_str}")
    print(f"URL: {pr['url']}")
    print(
        f"Review Threads: {total_threads} total "
        f"({unresolved_count} unresolved, {resolved_count} resolved "
        f"[{resolved_by_commenter_count} by original commenter, {resolved_by_other_count} by others])"
    )
    print(f"Listing: {len(threads)} thread(s) [filter={filter_mode}]")
    if filter_mode == "unresolved" and resolved_by_other_count > 0:
        print(
            f"Notice: {resolved_by_other_count} resolved thread(s) were NOT resolved by the original commenter. "
            f"Run with --audit or --non-author-resolved to audit them."
        )
    print("=" * 80)

    if not threads:
        if filter_mode == "unresolved":
            print("\n✓ No unresolved review threads on this PR.")
            if resolved_by_other_count > 0:
                print(
                    f"  ({resolved_by_other_count} thread(s) resolved by someone other than the original commenter; "
                    f"run with --audit or --non-author-resolved to verify they were sufficiently addressed.)"
                )
        elif filter_mode == "audit":
            print("\n✓ No unresolved or non-original-commenter-resolved review threads on this PR.")
        elif filter_mode == "non-author-resolved":
            print("\n✓ All resolved review threads were resolved by their original commenter.")
        else:
            print("\nNo review threads match the filter.")
        return

    for i, t in enumerate(threads, 1):
        orig_commenter = t.get("originalCommenter") or "unknown"
        resolved_by = t.get("resolvedByLogin") or "unknown"
        if not t.get("isResolved"):
            status = f"UNRESOLVED (commenter: @{orig_commenter})"
        elif t.get("isResolvedByOriginalCommenter"):
            status = f"RESOLVED by original commenter @{resolved_by}"
        else:
            resolver_role = "PR author " if t.get("isResolvedByPrAuthor") else ""
            status = (
                f"RESOLVED by {resolver_role}@{resolved_by} "
                f"(original commenter: @{orig_commenter}) "
                f"[AUDIT: NOT RESOLVED BY ORIGINAL COMMENTER]"
            )

        path = t.get("path")
        current_line = t.get("line")
        original_line = t.get("originalLine")
        line = current_line or original_line
        tid = t["id"]
        outdated = " (outdated diff)" if t.get("isOutdated") else ""
        comments = (t.get("comments") or {}).get("nodes") or []

        print(f"\n[{i}] {status}{outdated} | Thread ID: {tid}")
        if current_line and original_line and current_line != original_line:
            print(f"    File: {path}:{current_line} (original line: {original_line})")
        elif current_line is None and original_line:
            print(f"    File: {path}:{original_line} (original line at review; diff outdated)")
        else:
            print(f"    File: {path}:{line}")

        if comments:
            first = comments[0]
            first_author = (first.get("author") or {}).get("login") or "unknown"
            print(f"    Reviewer Comment by @{first_author} ({first.get('createdAt', '')}):")
            for line_text in (first.get("body") or "").strip().splitlines():
                print(f"        {line_text}")

            diff_hunk = first.get("diffHunk")
            if diff_hunk:
                print(f"    Diff Hunk at Review:")
                for dh_line in diff_hunk.strip().splitlines()[-6:]:
                    print(f"        {dh_line}")

            if len(comments) > 1:
                print(f"    Replies ({len(comments) - 1}):")
                for reply in comments[1:]:
                    reply_author = (reply.get("author") or {}).get("login") or "unknown"
                    reply_lines = (reply.get("body") or "").strip().splitlines()
                    if reply_lines:
                        print(f"        @{reply_author}: {reply_lines[0]}")
                        for r_line in reply_lines[1:]:
                            print(f"          {r_line}")
                    else:
                        print(f"        @{reply_author}:")

        if include_code and path and line:
            snippet = get_proximal_code_snippet(path, line)
            if snippet:
                print(f"    Proximal Code in Working Tree ({path}):")
                for snip_line in snippet.splitlines():
                    print(f"        {snip_line}")
            else:
                print(
                    f"    [!] Note: File '{path}' not found in current directory or target line inaccessible. "
                    f"Use Read tool to inspect."
                )
        print("-" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch PR review threads for validation by a reviewer agent.")
    parser.add_argument("--pr", type=int, help="PR number (default: auto-detected from branch)")
    parser.add_argument("--repo", help="Repository in owner/name format")
    parser.add_argument("--hostname", help="GitHub hostname (default: auto-detected)")

    filter_group = parser.add_mutually_exclusive_group()
    filter_group.add_argument(
        "--audit",
        action="store_true",
        help="Show unresolved threads AND threads resolved by someone other than the original commenter",
    )
    filter_group.add_argument(
        "--non-author-resolved",
        action="store_true",
        help="Show only resolved threads that were NOT resolved by the original commenter",
    )
    filter_group.add_argument("--all", action="store_true", help="Show all threads")
    filter_group.add_argument("--resolved-only", action="store_true", help="Show all resolved threads")

    parser.add_argument("--format", choices=["summary", "json"], default="summary", help="Output format (default: summary)")
    parser.add_argument("--no-code", action="store_true", help="Omit proximal code snippet from summary")
    args = parser.parse_args()

    if args.all:
        filter_mode = "all"
    elif args.resolved_only:
        filter_mode = "resolved"
    elif args.audit:
        filter_mode = "audit"
    elif args.non_author_resolved:
        filter_mode = "non-author-resolved"
    else:
        filter_mode = "unresolved"

    owner, repo, number, hostname = resolve_pr_context(args.pr, args.repo, args.hostname)
    _ensure_gh_authenticated(hostname)
    result = fetch_all(owner, repo, number, hostname)

    if args.format == "json":
        result["filter_mode"] = filter_mode
        result["review_threads"] = filter_threads(result["review_threads"], filter_mode)
        print(json.dumps(result, indent=2))
    else:
        print_summary(result, filter_mode=filter_mode, include_code=not args.no_code)


if __name__ == "__main__":
    main()
