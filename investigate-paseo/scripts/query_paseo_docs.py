#!/usr/bin/env python3
"""
query_paseo_docs.py - Fast search and retrieval tool for Paseo documentation.

Indexes both internal developer docs (docs/) and public operator docs (public-docs/)
from the local source checkout (~/Projects/public/paseo).
"""

import argparse
import os
import re
import sys
from pathlib import Path

CANDIDATE_SRC_DIRS = [
    Path(os.environ.get("PASEO_SRC_DIR", "")) if os.environ.get("PASEO_SRC_DIR") else None,
    Path.home() / "Projects" / "public" / "paseo",
    Path.home() / "Projects" / "paseo",
    Path.home() / "Extern" / "paseo",
    Path.home() / "paseo",
]

def find_paseo_source() -> Path | None:
    for candidate in CANDIDATE_SRC_DIRS:
        if candidate and candidate.is_dir() and (candidate / "package.json").is_file():
            return candidate
    return None

def collect_docs(src_root: Path, category: str = "all") -> dict[str, Path]:
    """Collects documentation files mapped by relative identifier."""
    docs = {}
    
    # 1. Internal docs/
    if category in ("all", "docs"):
        internal_dir = src_root / "docs"
        if internal_dir.is_dir():
            for p in sorted(internal_dir.glob("**/*.md")):
                key = f"docs/{p.relative_to(internal_dir)}"
                docs[key] = p

    # 2. Public public-docs/
    if category in ("all", "public-docs", "public"):
        public_dir = src_root / "public-docs"
        if public_dir.is_dir():
            for p in sorted(public_dir.glob("**/*.md")):
                key = f"public-docs/{p.relative_to(public_dir)}"
                docs[key] = p

    return docs

def extract_title(file_path: Path) -> str:
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines()[:20]:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
    except Exception:
        pass
    return file_path.stem.replace("-", " ").title()

def search_docs(docs: dict[str, Path], query: str) -> list[dict]:
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    results = []
    for rel_name, path in docs.items():
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        matches = []
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                # Context lines
                start = max(0, idx - 2)
                end = min(len(lines), idx + 2)
                context = [f"{i+1:4d}: {lines[i]}" for i in range(start, end)]
                matches.append({"line": idx, "text": line.strip(), "context": "\n".join(context)})
        if matches:
            results.append({
                "doc": rel_name,
                "title": extract_title(path),
                "path": str(path),
                "match_count": len(matches),
                "matches": matches,
            })
    return results

def main():
    parser = argparse.ArgumentParser(description="Query Paseo internal and public documentation.")
    parser.add_argument("query", nargs="?", default=None, help="Search query string or specific document name to read.")
    parser.add_argument("--list", action="store_true", help="List all available documentation files.")
    parser.add_argument("--cat", choices=["all", "docs", "public-docs"], default="all", help="Filter by doc category.")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
    args = parser.parse_args()

    src_root = find_paseo_source()
    if not src_root:
        sys.stderr.write("ERROR: Could not locate Paseo source directory.\n")
        sys.exit(1)

    docs = collect_docs(src_root, args.cat)

    if args.list:
        if args.json:
            import json
            items = [{"id": k, "title": extract_title(v), "path": str(v)} for k, v in docs.items()]
            print(json.dumps(items, indent=2))
        else:
            print(f"Paseo Documentation Catalog ({len(docs)} files in {src_root})")
            print("=" * 80)
            current_group = ""
            for k, v in docs.items():
                group = k.split("/")[0]
                if group != current_group:
                    current_group = group
                    print(f"\n[{current_group.upper()}]")
                title = extract_title(v)
                print(f"  {k:<35} : {title}")
        return

    if not args.query:
        parser.print_help()
        return

    # Check if querying a specific document directly
    target_doc = None
    query_str = args.query.strip()
    for k, v in docs.items():
        if k == query_str or k.endswith(f"/{query_str}") or k == f"docs/{query_str}" or k == f"public-docs/{query_str}":
            target_doc = v
            break
        if target_doc is None and (v.name == query_str or v.stem == query_str):
            target_doc = v

    if target_doc and target_doc.is_file():
        content = target_doc.read_text(encoding="utf-8", errors="ignore")
        if args.json:
            import json
            print(json.dumps({"doc": str(target_doc), "content": content}))
        else:
            print(f"=== Reading: {target_doc} ===")
            print(content)
        return

    # Perform full-text search
    results = search_docs(docs, query_str)
    if args.json:
        import json
        print(json.dumps(results, indent=2))
        return

    print(f"Search results for '{query_str}': {len(results)} file(s) matched\n")
    for res in results:
        print(f"[{res['doc']}] - {res['title']} ({res['match_count']} matches)")
        print(f"  Path: {res['path']}")
        for m in res['matches'][:3]:
            print(f"    Line {m['line']}: {m['text'][:100]}")
        if len(res['matches']) > 3:
            print(f"    ... and {len(res['matches']) - 3} more match(es)")
        print("-" * 60)

if __name__ == "__main__":
    main()
