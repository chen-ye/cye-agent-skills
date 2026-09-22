#!/usr/bin/env python3
"""
resolve_source.py - Universal, tool-agnostic source code resolution and acquisition.

Encodes the Three-Tier Investigation Hierarchy for arbitrary software:
  Tier 1: Existing local clone (checked via directory name, git remote origin, or package manifest)
  Tier 2: Upstream git repository (shallow clone into temporary or designated directory)
  Tier 3: Source unavailable (fallback to compiled / binary runtime inspection)
"""

import argparse
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
    Path.home() / "Projects",
    Path.home() / "Extern",
    Path.home(),
    Path("/workspace"),
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


def get_search_roots() -> list[Path]:
    custom = os.environ.get("INVESTIGATE_SEARCH_ROOTS")
    if custom:
        roots = []
        for p in custom.split(":"):
            if p.strip():
                roots.append(Path(os.path.expanduser(p.strip())))
        return roots
    return DEFAULT_SEARCH_ROOTS


def normalize_target_name(raw_name: str) -> str:
    """Extract canonical project identifier from a name or URL."""
    s = raw_name.strip()
    if s.endswith(".git"):
        s = s[:-4]
    if "://" in s or s.startswith("git@"):
        parsed = urlparse(s if "://" in s else f"https://{s.replace('git@', '').replace(':', '/')}")
        parts = [p for p in parsed.path.split("/") if p]
        if parts:
            return parts[-1]
    if "/" in s and not s.startswith("/") and not s.startswith("."):
        return s.split("/")[-1]
    return Path(s).name


def is_valid_source_dir(dir_path: Path) -> bool:
    if not dir_path.is_dir():
        return False
    if (dir_path / ".git").exists():
        return True
    for manifest in SOURCE_MANIFESTS:
        if (dir_path / manifest).exists():
            return True
    return False


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
        remote = None
        try:
            remote = subprocess.check_output(
                ["git", "-C", str(dir_path), "config", "--get", "remote.origin.url"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            pass

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


def matches_target(dir_path: Path, target: str, norm_name: str) -> bool:
    """Generic heuristic: does this directory represent the target software?"""
    dir_name = dir_path.name.lower()
    target_clean = norm_name.lower()
    aliases = {
        target_clean,
        target_clean.replace("-", ""),
        target_clean.replace("_", "-"),
        target_clean.replace("-", "_")
    }

    # 1. Directory name match
    if dir_name in aliases:
        return True

    # 2. Git remote URL match (generic for any repo name vs folder name discrepancy)
    if (dir_path / ".git").exists():
        try:
            remote = subprocess.check_output(
                ["git", "-C", str(dir_path), "config", "--get", "remote.origin.url"],
                stderr=subprocess.DEVNULL
            ).decode().strip().lower()
            if remote:
                remote_repo = normalize_target_name(remote).lower()
                if remote_repo in aliases or target.lower() in remote:
                    return True
        except Exception:
            pass

    # 3. Manifest package name match
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


def find_existing_local_clone(target: str) -> tuple[Path | None, list[str]]:
    checked_paths = []
    norm_name = normalize_target_name(target)

    # 1. Check current working directory and ancestors
    cwd = Path.cwd().resolve()
    curr = cwd
    while curr != curr.parent:
        if matches_target(curr, target, norm_name) and is_valid_source_dir(curr):
            return curr, [str(curr)]
        curr = curr.parent

    # 2. Check search roots
    for root in get_search_roots():
        if not root.is_dir():
            continue

        # Check root/<alias> directly
        for candidate_name in [norm_name, norm_name.replace("_", "-"), norm_name.replace("-", "_")]:
            candidate = root / candidate_name
            checked_paths.append(str(candidate))
            if candidate.is_dir() and matches_target(candidate, target, norm_name) and is_valid_source_dir(candidate):
                return candidate, checked_paths

        # Scan depth 1 subdirectories in root
        try:
            for child in root.iterdir():
                if not child.is_dir() or child.name.startswith("."):
                    continue
                if matches_target(child, target, norm_name) and is_valid_source_dir(child):
                    checked_paths.append(str(child))
                    return child, checked_paths
        except PermissionError:
            continue

    return None, checked_paths


def resolve_upstream_url(target: str) -> str | None:
    """Probe if target is or resolves to a valid git repository URL."""
    s = target.strip()
    if s.startswith("http://") or s.startswith("https://") or s.startswith("git@"):
        return s

    if "/" in s and not s.startswith(".") and not s.startswith("/"):
        # e.g. "owner/repo"
        candidate_url = f"https://github.com/{s}.git"
        return candidate_url

    # Check via gh CLI if available
    if shutil.which("gh"):
        try:
            output = subprocess.check_output(
                ["gh", "repo", "view", s, "--json", "url", "-q", ".url"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            if output:
                return f"{output}.git" if not output.endswith(".git") else output
        except Exception:
            pass

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
        print(" [TIER 3] SOURCE UNAVAILABLE - RUNTIME ARTIFACT FALLBACK")
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
