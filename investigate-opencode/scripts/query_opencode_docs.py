#!/usr/bin/env python3
import argparse
import os
import re
import sys
from pathlib import Path

DEFAULT_SEARCH_PATHS = [
    os.environ.get("OPENCODE_SRC_DIR", ""),
    os.path.expanduser("~/Projects/public/opencode"),
    os.path.expanduser("~/Extern/opencode"),
    os.path.expanduser("~/opencode"),
]

def find_docs_dir() -> Path:
    for base in DEFAULT_SEARCH_PATHS:
        if not base:
            continue
        p = Path(base)
        candidate1 = p / "packages" / "web" / "src" / "content" / "docs"
        if candidate1.is_dir():
            return candidate1
        candidate2 = p / "dev" / "packages" / "web" / "src" / "content" / "docs"
        if candidate2.is_dir():
            return candidate2
        candidate3 = p / "packages" / "docs"
        if candidate3.is_dir():
            return candidate3
    sys.stderr.write("Error: Could not locate OpenCode docs directory.\n")
    sys.exit(1)

def parse_frontmatter(text: str):
    metadata = {}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            for line in fm.strip().splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    metadata[key.strip()] = val.strip().strip("\"'")
    return metadata

def list_topics(docs_dir: Path):
    print(f"Available Documentation Topics in {docs_dir}:\n")
    print(f"{'File':<25} | {'Title':<30} | {'Description'}")
    print("-" * 80)
    for mdx in sorted(docs_dir.glob("*.mdx")):
        content = mdx.read_text(encoding="utf-8", errors="ignore")
        meta = parse_frontmatter(content)
        title = meta.get("title", mdx.stem)
        desc = meta.get("description", "")
        print(f"{mdx.name:<25} | {title:<30} | {desc}")

def search_docs(docs_dir: Path, query: str, limit: int = 5):
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    matches = []

    for mdx in sorted(docs_dir.glob("*.mdx")):
        lines = mdx.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, line in enumerate(lines):
            if pattern.search(line):
                # Grab a snippet of surrounding context
                start = max(0, idx - 2)
                end = min(len(lines), idx + 3)
                snippet = "\n".join(f"{i+1:4d} | {lines[i]}" for i in range(start, end))
                matches.append((mdx.name, idx + 1, snippet))
                if len(matches) >= limit:
                    break
        if len(matches) >= limit:
            break

    if not matches:
        print(f"No matches found for query: '{query}'")
        return

    print(f"Found {len(matches)} matches in {docs_dir}:\n")
    for fname, lno, snippet in matches:
        print(f"=== {fname} (line {lno}) ===")
        print(snippet)
        print()

def main():
    parser = argparse.ArgumentParser(description="Query OpenCode official documentation MDX files.")
    parser.add_argument("query", nargs="?", help="Search term or topic keyword")
    parser.add_argument("--list", action="store_true", help="List all available doc pages and titles")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of match excerpts to display")
    args = parser.parse_args()

    docs_dir = find_docs_dir()

    if args.list or not args.query:
        list_topics(docs_dir)
    else:
        search_docs(docs_dir, args.query, limit=args.limit)

if __name__ == "__main__":
    main()
