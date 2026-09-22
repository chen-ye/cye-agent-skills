#!/usr/bin/env python3
"""
query_omp_docs.py - High-speed search and retrieval tool for OMP embedded documentation.

Leverages OMP's built-in virtual documentation provider ('omp read omp://<path>')
with local disk caching in ~/.cache/omp_docs/ for sub-millisecond full-text searches.
"""

import argparse
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CACHE_DIR = Path(os.environ.get("OMP_DOCS_CACHE", Path.home() / ".cache" / "omp_docs"))

CANDIDATE_DOCS_DIRS = [
    Path(os.environ.get("OMP_SRC_DIR", "")) / "docs" if os.environ.get("OMP_SRC_DIR") else None,
    Path.home() / "Projects" / "public" / "oh-my-pi" / "docs",
    Path.home() / "Extern" / "oh-my-pi" / "docs",
    Path.home() / "oh-my-pi" / "docs",
]

def find_source_docs_dir() -> Path | None:
    for candidate in CANDIDATE_DOCS_DIRS:
        if candidate and candidate.is_dir():
            return candidate
    return None


def get_omp_bin() -> str:
    omp_bin = os.environ.get("OMP_BIN")
    if omp_bin and os.path.isfile(omp_bin) and os.access(omp_bin, os.X_OK):
        return omp_bin
    for candidate in ["/home/linuxbrew/.linuxbrew/bin/omp", "/usr/local/bin/omp", str(Path.home() / ".local/bin/omp")]:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return "omp"

def fetch_doc_list(omp_bin: str) -> list[str]:
    src_docs = find_source_docs_dir()
    if src_docs:
        docs = []
        for p in sorted(src_docs.glob("**/*.md")):
            docs.append(str(p.relative_to(src_docs)))
        return docs

    list_cache = CACHE_DIR / "_doc_list.txt"

    list_cache = CACHE_DIR / "_doc_list.txt"
    if list_cache.is_file():
        return [line.strip() for line in list_cache.read_text(encoding="utf-8").splitlines() if line.strip()]

    try:
        raw = subprocess.check_output([omp_bin, "read", "omp://"], stderr=subprocess.PIPE).decode("utf-8", errors="ignore")
        docs = sorted(re.findall(r'\[.*?\]\(omp://(.*?)\)', raw))
        if docs:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            list_cache.write_text("\n".join(docs) + "\n", encoding="utf-8")
        return docs
    except Exception as e:
        sys.stderr.write(f"Error fetching doc list from {omp_bin}: {e}\n")
        return []

def read_single_doc(omp_bin: str, doc_name: str) -> str:
    if not doc_name.endswith(".md"):
        doc_name += ".md"

    src_docs = find_source_docs_dir()
    if src_docs:
        target = src_docs / doc_name
        if target.is_file():
            return target.read_text(encoding="utf-8", errors="ignore")

    cached_file = CACHE_DIR / doc_name

    if not doc_name.endswith(".md"):
        doc_name += ".md"

    cached_file = CACHE_DIR / doc_name
    if cached_file.is_file():
        return cached_file.read_text(encoding="utf-8", errors="ignore")

    try:
        content = subprocess.check_output([omp_bin, "read", f"omp://{doc_name}"], stderr=subprocess.PIPE).decode("utf-8", errors="ignore")
        if content.strip():
            cached_file.parent.mkdir(parents=True, exist_ok=True)
            cached_file.write_text(content, encoding="utf-8")
        return content
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error reading doc omp://{doc_name}: {e.stderr.decode(errors='ignore')}\n")
        return ""

def sync_all_docs(omp_bin: str, doc_list: list[str]):
    print(f"Syncing {len(doc_list)} documentation files to {CACHE_DIR}...")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _sync(doc):
        dest = CACHE_DIR / doc
        if dest.is_file():
            return doc, True
        try:
            content = subprocess.check_output([omp_bin, "read", f"omp://{doc}"], stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            return doc, True
        except Exception:
            return doc, False

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(_sync, doc_list))
    success = sum(1 for _, ok in results if ok)
    print(f"Successfully cached {success}/{len(doc_list)} docs.")

def list_topics(omp_bin: str, doc_list: list[str], category_filter: str = ""):
    print(f"Available OMP Documentation Topics ({len(doc_list)} files available):\n")
    print(f"{'Document':<40} | {'Category':<20} | {'First Header / Title'}")
    print("-" * 90)

    for doc in doc_list:
        cat = "general"
        if "/" in doc:
            cat = doc.split("/")[0]
        elif "native" in doc:
            cat = "natives"
        elif "tool" in doc:
            cat = "tools"
        elif "mcp" in doc:
            cat = "mcp"
        elif "provider" in doc:
            cat = "providers"
        elif "agent" in doc:
            cat = "agents"

        if category_filter and category_filter.lower() not in cat.lower() and category_filter.lower() not in doc.lower():
            continue

        # Peek title from cache if exists
        title = doc
        cached = CACHE_DIR / doc
        if cached.is_file():
            for line in cached.read_text(encoding="utf-8", errors="ignore").splitlines()[:5]:
                if line.startswith("# "):
                    title = line.lstrip("# ").strip()
                    break

        print(f"{doc:<40} | {cat:<20} | {title}")

def search_docs(omp_bin: str, doc_list: list[str], query: str, limit: int = 5):
    # Ensure cache is populated for fast regex search across all files
    cached_count = sum(1 for d in doc_list if (CACHE_DIR / d).is_file())
    if cached_count < len(doc_list) // 2:
        print(f"Initializing local documentation cache ({cached_count}/{len(doc_list)} cached)...")
        sync_all_docs(omp_bin, doc_list)

    pattern = re.compile(re.escape(query), re.IGNORECASE)
    matches = []

    for doc in doc_list:
        p = CACHE_DIR / doc
        if not p.is_file():
            continue
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, line in enumerate(lines):
            if pattern.search(line):
                start = max(0, idx - 2)
                end = min(len(lines), idx + 3)
                snippet = "\n".join(f"{i+1:4d} | {lines[i]}" for i in range(start, end))
                matches.append((doc, idx + 1, snippet))
                if len(matches) >= limit:
                    break
        if len(matches) >= limit:
            break

    if not matches:
        print(f"No matches found for query: '{query}'")
        return

    print(f"Found {len(matches)} matches for '{query}':\n")
    for doc, lno, snippet in matches:
        print(f"=== {doc} (line {lno}) ===")
        print(snippet)
        print()

def main():
    parser = argparse.ArgumentParser(description="Query and view OMP embedded documentation.")
    parser.add_argument("query", nargs="?", help="Doc file name (e.g. approval-mode.md), search query, or topic keyword")
    parser.add_argument("--list", action="store_true", help="List all available documentation topics")
    parser.add_argument("--cat", type=str, default="", help="Filter topics list by category (e.g. tools, natives, mcp)")
    parser.add_argument("--read", type=str, default="", help="Read a specific document file in full")
    parser.add_argument("--sync", action="store_true", help="Sync/cache all documentation files locally")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of search snippets to display (default: 5)")
    args = parser.parse_args()

    omp_bin = get_omp_bin()
    doc_list = fetch_doc_list(omp_bin)
    if not doc_list:
        sys.stderr.write("Failed to retrieve document list from OMP.\n")
        sys.exit(1)

    if args.sync:
        sync_all_docs(omp_bin, doc_list)
        return

    if args.list:
        list_topics(omp_bin, doc_list, category_filter=args.cat)
        return

    target_doc = args.read or args.query

    if not target_doc:
        list_topics(omp_bin, doc_list, category_filter=args.cat)
        return

    # Check if target_doc matches an exact doc or close doc name
    normalized = target_doc if target_doc.endswith(".md") else target_doc + ".md"
    exact_match = None
    for d in doc_list:
        if d.lower() == normalized.lower() or Path(d).name.lower() == normalized.lower():
            exact_match = d
            break

    if exact_match:
        content = read_single_doc(omp_bin, exact_match)
        if content:
            print(content)
        return

    # If args.read was explicitly specified and not found
    if args.read:
        sys.stderr.write(f"Error: Document '{args.read}' not found in OMP documentation.\n")
        sys.exit(1)

    # Otherwise perform full-text search
    search_docs(omp_bin, doc_list, args.query, limit=args.limit)

if __name__ == "__main__":
    main()
