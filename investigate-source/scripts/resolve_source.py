#!/usr/bin/env python3
"""
resolve_source.py - Universal, tool-agnostic source code resolution and acquisition.

Encodes the Three-Tier Investigation Hierarchy for arbitrary software:
  Tier 1: Existing local clone (checked via directory name, git remote origin, or package manifest)
  Tier 2: Upstream git repository (shallow clone into temporary or designated directory)
  Tier 3: Source unavailable (fallback to compiled / binary runtime inspection)
"""

import argparse
import configparser
from concurrent.futures import ThreadPoolExecutor
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

# Standard local development and workspace roots to search
DEFAULT_SEARCH_ROOTS = [
    Path.home() / "Projects" / "public",
    Path.home() / "Projects" / "spaces",
    Path.home() / "Projects" / "workspaces",
    Path.home() / "Projects",
    Path.home() / "Extern",
    Path.home(),
    Path("/workspace"),
    Path("/tmp/opencode"),
    Path("/tmp/source-investigations"),
]

SOURCE_MANIFESTS = [
    "package.json",
    "Cargo.toml",
    "pyproject.toml",
    "setup.py",
    "go.mod",
    "CMakeLists.txt",
    "pom.xml",
    "build.gradle",
    "WORKSPACE",
    "WORKSPACE.bazel",
]

SKIP_CONTAINER_DIRS = {
    "node_modules",
    "target",
    "build",
    "cbuild",
    "dist",
    "venv",
    "aws_venv",
    "__pycache__",
    "coverage",
    "logs",
    "packages",
}

WEB_UI_PATH_SEGMENTS = {
    "blob",
    "tree",
    "commit",
    "commits",
    "pull",
    "pulls",
    "issues",
    "releases",
    "actions",
    "-",
}


def get_search_roots() -> list[Path]:
    custom = os.environ.get("INVESTIGATE_SEARCH_ROOTS")
    if custom:
        roots = []
        for p in custom.split(":"):
            if p.strip():
                roots.append(Path(os.path.expanduser(p.strip())))
        return roots
    return DEFAULT_SEARCH_ROOTS


def parse_repo_spec(raw_name: str) -> tuple[str | None, str | None, str]:
    """Parse raw target or git URL into (host, owner, repo)."""
    s = raw_name.strip()
    if s.endswith("/"):
        s = s.rstrip("/")

    if "://" in s or s.startswith("git@"):
        if s.startswith("git@") and "://" not in s:
            host_part, _, path_part = s[4:].partition(":")
            parsed_host = host_part or None
            parts = [p for p in path_part.split("/") if p]
        else:
            parsed = urlparse(s)
            parsed_host = parsed.hostname
            parts = [p for p in parsed.path.split("/") if p]

        for idx, seg in enumerate(parts):
            if idx >= 2 and seg in WEB_UI_PATH_SEGMENTS:
                parts = parts[:idx]
                break

        if parts and parts[-1].endswith(".git"):
            parts[-1] = parts[-1][:-4]

        if len(parts) >= 2:
            return parsed_host, "/".join(parts[:-1]), parts[-1]
        if len(parts) == 1:
            return parsed_host, None, parts[0]
        return parsed_host, None, s

    if s.endswith(".git"):
        s = s[:-4]

    if "/" in s and not s.startswith("/") and not s.startswith("."):
        parts = [p for p in s.split("/") if p]
        if len(parts) >= 3 and "." in parts[0]:
            return parts[0], "/".join(parts[1:-1]), parts[-1]
        if len(parts) >= 2:
            return None, "/".join(parts[:-1]), parts[-1]

    return None, None, Path(s).name


def normalize_target_name(raw_name: str) -> str:
    """Extract canonical project identifier from a name or URL."""
    _, _, repo = parse_repo_spec(raw_name)
    return repo


def is_valid_source_dir(dir_path: Path) -> bool:
    if not dir_path.is_dir():
        return False
    if (dir_path / ".git").exists():
        return True
    for manifest in SOURCE_MANIFESTS:
        if (dir_path / manifest).exists():
            return True
    return False


def read_git_remote_url(dir_path: Path) -> str | None:
    """Read origin remote URL directly from .git/config without spawning subprocesses."""
    git_entry = dir_path / ".git"
    if not git_entry.exists():
        return None

    git_dir = git_entry
    try:
        if git_entry.is_file():
            first_line = git_entry.read_text(encoding="utf-8", errors="ignore").splitlines()[0].strip()
            if first_line.startswith("gitdir:"):
                raw_gitdir = first_line.split(":", 1)[1].strip()
                git_dir = (dir_path / raw_gitdir).resolve()
                commondir_file = git_dir / "commondir"
                if commondir_file.is_file():
                    common_rel = commondir_file.read_text(encoding="utf-8", errors="ignore").strip()
                    git_dir = (git_dir / common_rel).resolve()

        cfg_path = git_dir / "config"
        if not cfg_path.is_file():
            return None

        cp = configparser.ConfigParser(interpolation=None, strict=False)
        cp.read(cfg_path, encoding="utf-8")
        if cp.has_option('remote "origin"', "url"):
            return cp.get('remote "origin"', "url").strip()
        for section in cp.sections():
            if section.startswith("remote ") and cp.has_option(section, "url"):
                return cp.get(section, "url").strip()
    except Exception:
        pass
    return None


def get_git_info(dir_path: Path) -> dict:
    info = {"is_git": False, "branch": None, "commit": None, "remote_url": None, "dirty": False}
    if not (dir_path / ".git").exists():
        return info
    try:
        branch = subprocess.check_output(
            ["git", "-C", str(dir_path), "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        commit = subprocess.check_output(
            ["git", "-C", str(dir_path), "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        status = subprocess.check_output(
            ["git", "-C", str(dir_path), "status", "--porcelain"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        remote = read_git_remote_url(dir_path)

        info.update({
            "is_git": True,
            "branch": branch,
            "commit": commit,
            "remote_url": remote,
            "dirty": len(status) > 0
        })
    except Exception:
        pass
    return info


def matches_target(
    dir_path: Path,
    target: str,
    norm_name: str,
    req_host: str | None = None,
    req_owner: str | None = None,
) -> bool:
    """Generic heuristic: does this directory represent the target software?"""
    dir_name = dir_path.name.lower()
    target_clean = norm_name.lower()
    aliases = {
        target_clean,
        target_clean.replace("-", ""),
        target_clean.replace("_", "-"),
        target_clean.replace("-", "_")
    }

    remote = read_git_remote_url(dir_path)
    if req_host or req_owner:
        if not remote:
            return False
        rem_host, rem_owner, _ = parse_repo_spec(remote)
        if req_host and (not rem_host or req_host.lower() != rem_host.lower()):
            return False
        if req_owner and (not rem_owner or req_owner.lower() != rem_owner.lower()):
            return False

    # 1. Directory name match
    if dir_name in aliases:
        return True

    # 2. Git remote URL match (generic for any repo name vs folder name discrepancy)
    if remote:
        remote_lower = remote.lower()
        remote_repo = normalize_target_name(remote).lower()
        if remote_repo in aliases or target.lower() in remote_lower:
            return True

    # 3. Manifest package name match
    if not req_host and not req_owner:
        pkg_json = dir_path / "package.json"
        if pkg_json.is_file():
            try:
                with open(pkg_json, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                    name = data.get("name", "").lower()
                    if name == target_clean or name.endswith(f"/{target_clean}"):
                        return True
            except Exception:
                pass

        cargo_toml = dir_path / "Cargo.toml"
        if cargo_toml.is_file():
            try:
                content = cargo_toml.read_text(encoding="utf-8", errors="ignore")
                for match in re.finditer(r'name\s*=\s*["\']([^"\']+)["\']', content):
                    if match.group(1).lower() in aliases:
                        return True
            except Exception:
                pass

    return False


def _iter_subdirs(parent: Path) -> list[Path]:
    try:
        children = [
            c for c in parent.iterdir()
            if c.is_dir() and not c.name.startswith(".") and c.name not in SKIP_CONTAINER_DIRS
        ]
        # Prefer primary *-dev workspaces ahead of ticket and PR-* review worktrees
        children.sort(key=lambda p: (p.name.startswith("PR-"), not p.name.lower().endswith("-dev"), p.name.lower()))
        return children
    except PermissionError:
        return []


def find_existing_local_clone(target: str) -> tuple[Path | None, list[str]]:
    checked_paths = []
    req_host, req_owner, norm_name = parse_repo_spec(target)
    candidate_names = list(dict.fromkeys([
        norm_name,
        norm_name.replace("_", "-"),
        norm_name.replace("-", "_"),
    ]))

    def check_dir(path: Path) -> bool:
        checked_paths.append(str(path))
        return (
            path.is_dir()
            and is_valid_source_dir(path)
            and matches_target(path, target, norm_name, req_host, req_owner)
        )

    # 1. Check current working directory and ancestors
    cwd = Path.cwd().resolve()
    curr = cwd
    while curr != curr.parent:
        if is_valid_source_dir(curr) and matches_target(curr, target, norm_name, req_host, req_owner):
            return curr, [str(curr)]
        curr = curr.parent

    # 2. Check search roots (including nested non-git workspace containers)
    for root in get_search_roots():
        if not root.is_dir():
            continue

        for cname in candidate_names:
            candidate = root / cname
            if check_dir(candidate):
                return candidate, checked_paths

        for child in _iter_subdirs(root):
            if is_valid_source_dir(child) and matches_target(child, target, norm_name, req_host, req_owner):
                checked_paths.append(str(child))
                return child, checked_paths

            if (child / ".git").exists():
                if (child / ".gitmodules").exists():
                    for cname in candidate_names:
                        sub_cand = child / cname
                        if check_dir(sub_cand):
                            return sub_cand, checked_paths
                continue

            # Non-git workspace container (e.g., multi-repo / Spaces workspace)
            for cname in candidate_names:
                ws_cand = child / cname
                if check_dir(ws_cand):
                    return ws_cand, checked_paths

            for grandchild in _iter_subdirs(child):
                if is_valid_source_dir(grandchild) and matches_target(grandchild, target, norm_name, req_host, req_owner):
                    checked_paths.append(str(grandchild))
                    return grandchild, checked_paths

                if not (grandchild / ".git").exists():
                    for cname in candidate_names:
                        org_cand = grandchild / cname
                        if check_dir(org_cand):
                            return org_cand, checked_paths

    return None, checked_paths


def get_authenticated_gh_hosts() -> list[str]:
    """Return authenticated GitHub / GitHub Enterprise hosts via gh CLI."""
    if not shutil.which("gh"):
        return []
    try:
        raw = subprocess.check_output(
            ["gh", "auth", "status", "--json", "hosts"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode().strip()
        data = json.loads(raw)
        hosts = list((data.get("hosts") or {}).keys())
        # Probe github.com first when present, followed by enterprise hosts
        hosts.sort(key=lambda h: (h != "github.com", h))
        return hosts
    except Exception:
        return ["github.com"]


def _gh_repo_view_url(repo_ref: str) -> str | None:
    try:
        output = subprocess.check_output(
            ["gh", "repo", "view", repo_ref, "--json", "url", "-q", ".url"],
            stderr=subprocess.DEVNULL,
            timeout=8,
        ).decode().strip()
        if output:
            return f"{output}.git" if not output.endswith(".git") else output
    except Exception:
        pass
    return None


def resolve_upstream_url(target: str) -> str | None:
    """Probe if target is or resolves to a valid git repository URL."""
    s = target.strip()
    req_host, req_owner, repo = parse_repo_spec(s)

    if s.startswith("http://") or s.startswith("https://"):
        if req_host and req_owner:
            parsed = urlparse(s)
            base = f"{parsed.scheme}://{parsed.netloc}/{req_owner}/{repo}"
            return base if base.endswith(".git") else f"{base}.git"
        return s

    if s.startswith("git@"):
        return s

    if req_host and req_owner:
        return _gh_repo_view_url(f"{req_host}/{req_owner}/{repo}") or f"https://{req_host}/{req_owner}/{repo}.git"

    gh_hosts = get_authenticated_gh_hosts()

    if req_owner:
        if gh_hosts:
            refs = [f"{host}/{req_owner}/{repo}" for host in gh_hosts]
            with ThreadPoolExecutor(max_workers=min(4, len(refs))) as pool:
                for url in pool.map(_gh_repo_view_url, refs):
                    if url:
                        return url
            if "github.com" in gh_hosts:
                return None
        return f"https://github.com/{req_owner}/{repo}.git"

    if gh_hosts:
        url = _gh_repo_view_url(repo)
        if url:
            return url

    return None


def shallow_clone_to_tmp(upstream_url: str, project_name: str, target_dir: Path = None) -> tuple[Path, bool]:
    dest_dir = target_dir or (Path("/tmp/source-investigations") / project_name)
    if dest_dir.exists() and is_valid_source_dir(dest_dir):
        return dest_dir, True

    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    if dest_dir.exists():
        shutil.rmtree(dest_dir, ignore_errors=True)

    cmd = ["git", "clone", "--depth=1", "--filter=blob:none", upstream_url, str(dest_dir)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        # Fallback to standard shallow clone
        cmd = ["git", "clone", "--depth=1", upstream_url, str(dest_dir)]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if res.returncode == 0:
        return dest_dir, True
    return dest_dir, False


def find_system_binary(target_name: str) -> tuple[Path | None, str | None]:
    norm_name = normalize_target_name(target_name)
    bin_path = shutil.which(norm_name)
    if not bin_path:
        for candidate in [
            Path.home() / ".local" / "bin" / norm_name,
            Path("/usr/local/bin") / norm_name,
            Path("/home/linuxbrew/.linuxbrew/bin") / norm_name,
        ]:
            if candidate.is_file() and os.access(candidate, os.X_OK):
                bin_path = str(candidate)
                break
    if bin_path:
        version = None
        try:
            version = subprocess.check_output(
                [bin_path, "--version"],
                stderr=subprocess.STDOUT
            ).decode().strip().splitlines()[0]
        except Exception:
            pass
        return Path(bin_path), version
    return None, None


def main():
    parser = argparse.ArgumentParser(
        description="Resolve and locate source code checkouts following the 3-tier investigation hierarchy."
    )
    parser.add_argument("target", help="Tool name, package, repo name, or git URL (e.g. ripgrep, BurntSushi/ripgrep, uv)")
    parser.add_argument("--clone-tmp", action="store_true", help="If no local clone exists, shallow clone into /tmp/source-investigations/")
    parser.add_argument("--clone-to", help="If no local clone exists, clone into the specified directory")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    target = args.target.strip()
    norm_name = normalize_target_name(target)

    # -------------------------------------------------------------
    # Tier 1: Check existing local checkouts
    # -------------------------------------------------------------
    local_path, checked_paths = find_existing_local_clone(target)
    if local_path:
        git_info = get_git_info(local_path)
        result = {
            "tier": 1,
            "status": "found_local_clone",
            "tier_description": "Tier 1: Existing local clone discovered.",
            "target": target,
            "project_name": norm_name,
            "source_path": str(local_path),
            "git": git_info,
            "is_ephemeral": False,
            "action_recommended": f"Investigate source files directly in '{local_path}'. Do not decompile runtimes."
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("=" * 80)
            print(" [TIER 1] EXISTING LOCAL SOURCE CLONE FOUND")
            print("=" * 80)
            print(f"Project Name:   {norm_name}")
            print(f"Source Path:    {local_path}")
            if git_info["is_git"]:
                print(f"Git Revision:   {git_info['branch']} ({git_info['commit']})")
                print(f"Remote URL:     {git_info.get('remote_url', 'unknown')}")
                print(f"Tree Clean:     {not git_info['dirty']}")
            print(f"\nRecommended Action: Investigate source code directly at {local_path}.")
        return

    # -------------------------------------------------------------
    # Tier 2: Check upstream git repository & clone if requested
    # -------------------------------------------------------------
    upstream_url = resolve_upstream_url(target)
    if upstream_url:
        if args.clone_tmp or args.clone_to:
            dest = Path(args.clone_to) if args.clone_to else (Path("/tmp/source-investigations") / norm_name)
            cloned_path, success = shallow_clone_to_tmp(upstream_url, norm_name, target_dir=dest)
            if success:
                git_info = get_git_info(cloned_path)
                result = {
                    "tier": 2,
                    "status": "cloned_upstream_source",
                    "tier_description": "Tier 2: Source cloned from upstream repository.",
                    "target": target,
                    "project_name": norm_name,
                    "source_path": str(cloned_path),
                    "upstream_url": upstream_url,
                    "git": git_info,
                    "is_ephemeral": bool(not args.clone_to),
                    "action_recommended": f"Investigate fresh source files at '{cloned_path}'. Clean up when done if temporary."
                }
                if args.json:
                    print(json.dumps(result, indent=2))
                else:
                    print("=" * 80)
                    print(" [TIER 2] UPSTREAM SOURCE CLONED SUCCESSFULLY")
                    print("=" * 80)
                    print(f"Project Name:   {norm_name}")
                    print(f"Cloned Path:    {cloned_path}")
                    print(f"Upstream URL:   {upstream_url}")
                    if git_info["is_git"]:
                        print(f"Git Revision:   {git_info['branch']} ({git_info['commit']})")
                    print(f"\nRecommended Action: Investigate raw source files directly at {cloned_path}.")
                return
            else:
                sys.stderr.write(f"Warning: Failed to clone from {upstream_url}.\n")

        result = {
            "tier": 2,
            "status": "upstream_source_available",
            "tier_description": "Tier 2: Upstream source repository identified (not yet cloned).",
            "target": target,
            "project_name": norm_name,
            "source_path": None,
            "upstream_url": upstream_url,
            "action_recommended": f"Fetch shallow clone to /tmp/source-investigations/{norm_name} or specify destination with --clone-to."
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("=" * 80)
            print(" [TIER 2] UPSTREAM SOURCE REPOSITORY IDENTIFIED")
            print("=" * 80)
            print(f"Project Name:   {norm_name}")
            print(f"Upstream URL:   {upstream_url}")
            print(f"\nRecommended Action: Fetch shallow clone before investigating:")
            print(f"  git clone --depth=1 {upstream_url} /tmp/source-investigations/{norm_name}")
            print(f"Or re-run with: resolve_source.sh {target} --clone-tmp")
        return

    # -------------------------------------------------------------
    # Tier 3: Source is unavailable -> fallback to compiled runtime
    # -------------------------------------------------------------
    bin_path, bin_version = find_system_binary(target)
    result = {
        "tier": 3,
        "status": "source_unobtainable_runtime_fallback",
        "tier_description": "Tier 3: Source code is unobtainable. Fallback to compiled runtime analysis.",
        "target": target,
        "project_name": norm_name,
        "source_path": None,
        "system_binary": str(bin_path) if bin_path else None,
        "binary_version": bin_version,
        "action_recommended": "Exhausted source options. Proceed with binary static analysis, symbol tables, and strings extraction."
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=" * 80)
        print(" [TIER 1/2 EXHAUSTED -> TIER 3] SOURCE UNAVAILABLE - RUNTIME ARTIFACT FALLBACK")
        print("=" * 80)
        print(f"Project:        {norm_name}")
        print(f"Source Code:    Not found locally or via public remotes.")
        if bin_path:
            print(f"System Binary:  {bin_path}")
            print(f"Version:        {bin_version or 'unknown'}")
            print(f"\nRecommended Action: Analyze binary symbols (nm, objdump), DWARF tables, embedded assets, or daemon logs.")
        else:
            print(f"System Binary:  Not found on PATH.")
            print(f"\nRecommended Action: Verify target name or provide upstream repository URL.")


if __name__ == "__main__":
    main()
