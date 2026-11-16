#!/usr/bin/env python3
"""
Collect complete ground-truth artifacts for post-review reflection.

Extracts:
1. OpenCode session transcripts via `opencode session export`:
   - Organic user prompts AND synthetic user inputs dropped by compact views
     (UI card answers/notes, inline quote comments, attached PR comments)
   - Subagent review reports (<subagent ...> completion blocks)
   - Assistant recommendations and triage cards
2. Pull request review history via `gh`:
   - Inline review comments sorted chronologically with thread links
   - Review summaries and approvals
   - PR commit history and merge metadata

Works with both github.com and GitHub Enterprise Server (auto-detected from git remote).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path
from typing import Any

SKIP_SYNTHETIC_PREFIXES = (
    "<subagent",
    "<openchamber-pull-request",
    "<shell",
    "OpenChamber restarted OpenCode",
)

SUBAGENT_HEADER_RE = re.compile(
    r'^<subagent\s+([^>]*)>\n(.*?)\n</subagent>\s*$',
    re.DOTALL,
)


def run(cmd: list[str], env: dict[str, str] | None = None, cwd: str | None = None) -> str:
    proc = subprocess.run(
        cmd,
        env=env,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr.strip()}")
    return proc.stdout


def parse_remote(remote_url: str) -> tuple[str, str]:
    remote_url = remote_url.strip()
    if remote_url.startswith("git@"):
        # git@host:owner/repo.git
        host_part, path_part = remote_url.split("@", 1)[1].split(":", 1)
        host = host_part
        slug = path_part.removesuffix(".git").lstrip("/")
        return host, slug
    parsed = urllib.parse.urlparse(remote_url)
    host = parsed.hostname or "github.com"
    slug = parsed.path.removesuffix(".git").lstrip("/")
    return host, slug


def collect_session(session_id: str, out_dir: Path) -> dict[str, Any]:
    raw = run(["opencode", "session", "export", session_id])
    data = json.loads(raw)
    messages = data.get("messages", [])

    user_feedback: list[str] = []
    subagent_reports: list[str] = []
    assistant_turns: list[str] = []

    user_count = 0
    synthetic_user_count = 0
    subagent_count = 0
    assistant_count = 0

    for idx, msg in enumerate(messages):
        mtype = msg.get("type")
        mid = msg.get("id", "")
        ts = msg.get("time", {}).get("created", "")
        text = (msg.get("text") or "").strip()

        if mtype == "user":
            if not text:
                continue
            user_count += 1
            user_feedback.append(f"## [{idx}] USER id={mid} time={ts}\n\n{text}\n")
        elif mtype == "synthetic":
            if not text:
                continue
            if text.startswith("<subagent"):
                subagent_count += 1
                match = SUBAGENT_HEADER_RE.match(text)
                if match:
                    attrs, body = match.group(1), match.group(2).strip()
                    subagent_reports.append(f"## [{idx}] SUBAGENT {attrs} id={mid}\n\n{body}\n")
                else:
                    subagent_reports.append(f"## [{idx}] SUBAGENT id={mid}\n\n{text}\n")
                continue
            if any(text.startswith(prefix) for prefix in SKIP_SYNTHETIC_PREFIXES):
                continue
            synthetic_user_count += 1
            user_feedback.append(f"## [{idx}] USER-SYNTHETIC id={mid} time={ts}\n\n{text}\n")
        elif mtype == "assistant":
            parts = msg.get("content") or []
            assistant_text = "\n\n".join(
                (p.get("text") or "").strip()
                for p in parts
                if isinstance(p, dict) and p.get("type") == "text" and (p.get("text") or "").strip()
            ).strip()
            if not assistant_text:
                assistant_text = text
            if not assistant_text:
                continue
            assistant_count += 1
            assistant_turns.append(f"## [{idx}] ASSISTANT id={mid} time={ts}\n\n{assistant_text}\n")

    (out_dir / "session_user_feedback.md").write_text("\n---\n\n".join(user_feedback) + "\n")
    (out_dir / "session_subagent_reports.md").write_text("\n---\n\n".join(subagent_reports) + "\n")
    (out_dir / "session_assistant_turns.md").write_text("\n---\n\n".join(assistant_turns) + "\n")

    return {
        "session_id": session_id,
        "total_messages": len(messages),
        "user_turns": user_count,
        "synthetic_user_turns": synthetic_user_count,
        "subagent_reports": subagent_count,
        "assistant_turns": assistant_count,
        "files": [
            str(out_dir / "session_user_feedback.md"),
            str(out_dir / "session_subagent_reports.md"),
            str(out_dir / "session_assistant_turns.md"),
        ],
    }


def collect_pr(pr_number: int, repo_dir: str, out_dir: Path, host_override: str | None, repo_override: str | None) -> dict[str, Any]:
    if repo_override and host_override:
        host, slug = host_override, repo_override
    else:
        remote_url = run(["git", "-C", repo_dir, "remote", "get-url", "origin"])
        detected_host, detected_slug = parse_remote(remote_url)
        host = host_override or detected_host
        slug = repo_override or detected_slug

    env = os.environ.copy()
    if host and host != "github.com":
        env["GH_HOST"] = host

    comments = json.loads(run(["gh", "api", "--paginate", f"repos/{slug}/pulls/{pr_number}/comments"], env=env))
    reviews = json.loads(run(["gh", "api", "--paginate", f"repos/{slug}/pulls/{pr_number}/reviews"], env=env))
    issue_comments = json.loads(run(["gh", "api", "--paginate", f"repos/{slug}/issues/{pr_number}/comments"], env=env))
    commits = json.loads(run(["gh", "api", "--paginate", f"repos/{slug}/pulls/{pr_number}/commits"], env=env))
    pr_meta = json.loads(
        run(
            [
                "gh",
                "pr",
                "view",
                str(pr_number),
                "--repo",
                slug,
                "--json",
                "number,title,url,state,mergedAt,mergeCommit,author,baseRefName,headRefName",
            ],
            env=env,
        )
    )

    comments_sorted = sorted(comments, key=lambda c: c.get("created_at") or "")
    comment_lines: list[str] = []
    for c in comments_sorted:
        cid = c.get("id")
        reply_to = c.get("in_reply_to_id")
        author = (c.get("user") or {}).get("login", "unknown")
        created = c.get("created_at", "")
        path = c.get("path", "")
        line = c.get("line") or c.get("original_line") or ""
        body = (c.get("body") or "").strip()
        comment_lines.append(
            f"### comment_id={cid} reply_to={reply_to} user={author} [{created}] `{path}:{line}`\n\n{body}\n"
        )

    review_lines: list[str] = []
    for r in reviews:
        rid = r.get("id")
        author = (r.get("user") or {}).get("login", "unknown")
        state = r.get("state", "")
        submitted = r.get("submitted_at", "")
        commit_id = (r.get("commit_id") or "")[:9]
        body = (r.get("body") or "").strip()
        if not body and state == "COMMENTED":
            continue
        review_lines.append(
            f"### review_id={rid} user={author} state={state} commit={commit_id} [{submitted}]\n\n{body}\n"
        )

    issue_lines: list[str] = []
    for ic in issue_comments:
        author = (ic.get("user") or {}).get("login", "unknown")
        created = ic.get("created_at", "")
        body = (ic.get("body") or "").strip()
        issue_lines.append(f"### user={author} [{created}]\n\n{body}\n")

    commit_lines = []
    for cm in commits:
        sha = (cm.get("sha") or "")[:9]
        commit_info = cm.get("commit") or {}
        date = ((commit_info.get("author") or {}).get("date")) or ""
        subject = (commit_info.get("message") or "").splitlines()[0] if commit_info.get("message") else ""
        commit_lines.append(f"[{date}] {sha} {subject}")

    (out_dir / "pr_summary.json").write_text(json.dumps(pr_meta, indent=2) + "\n")
    (out_dir / "pr_comments.md").write_text("\n---\n\n".join(comment_lines) + "\n")
    (out_dir / "pr_reviews.md").write_text("\n---\n\n".join(review_lines + issue_lines) + "\n")
    (out_dir / "pr_commits.txt").write_text("\n".join(commit_lines) + "\n")

    return {
        "pr_number": pr_number,
        "host": host,
        "repo": slug,
        "review_comments": len(comments_sorted),
        "reviews": len(reviews),
        "issue_comments": len(issue_comments),
        "commits": len(commits),
        "files": [
            str(out_dir / "pr_summary.json"),
            str(out_dir / "pr_comments.md"),
            str(out_dir / "pr_reviews.md"),
            str(out_dir / "pr_commits.txt"),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract session feedback and PR review history for reflection.")
    parser.add_argument("--session", help="OpenCode session ID (e.g. ses_...)")
    parser.add_argument("--pr", type=int, help="GitHub pull request number")
    parser.add_argument("--repo-dir", default=".", help="Path to git repository (default: .)")
    parser.add_argument("--host", help="Optional GitHub hostname override")
    parser.add_argument("--repo", help="Optional owner/repo override")
    parser.add_argument("--out-dir", default="/tmp/opencode/review-reflect", help="Output directory")
    args = parser.parse_args()

    if not args.session and not args.pr:
        parser.error("Provide at least one of --session or --pr.")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {"out_dir": str(out_dir)}
    if args.session:
        summary["session"] = collect_session(args.session, out_dir)
    if args.pr:
        summary["pr"] = collect_pr(args.pr, args.repo_dir, out_dir, args.host, args.repo)

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
