#!/usr/bin/env python3
"""
Extracts embedded system prompts, security rubrics, and agent guidelines
from the unstripped Antigravity localharness binary.
"""

import argparse
import os
import re
import sys

DEFAULT_BINARY = os.path.expanduser("~/.local/share/antigravity/localharness.debug")

PROMPT_MARKERS = [
    ("Policy Guardian: Code Vetting", b"You are an expert in code analysis. What does the code do?"),
    ("Policy Guardian: Config Vetting", b"You are an expert in config file security analysis."),
    ("Policy Guardian: Anti-Circumvention (Denied Repeat)", b"You are a security equivalence analyzer."),
    ("Policy Guardian: Trajectory Monitor", b"You are a safety and security rater overseeing Jetski"),
    ("SWE Agent Workflow Instructions", b"Follow this systematic approach when building web applications:"),
    ("Code Search Guidelines", b"Use code search with the following arguments:"),
]

def main():
    parser = argparse.ArgumentParser(description="Extract embedded prompts and rubrics from Antigravity binary.")
    parser.add_argument("name", nargs="?", default="", help="Filter prompt by name or keyword")
    parser.add_argument("--binary", default=DEFAULT_BINARY, help="Path to localharness.debug binary")
    parser.add_argument("--list", action="store_true", help="List available extracted prompt categories")

    args = parser.parse_args()

    if not os.path.exists(args.binary):
        print(f"Error: binary not found at {args.binary}", file=sys.stderr)
        sys.exit(1)

    with open(args.binary, "rb") as f:
        data = f.read()

    if args.list:
        print("Available prompt categories:")
        for title, _ in PROMPT_MARKERS:
            print(f" - {title}")
        return

    found = False
    for title, marker in PROMPT_MARKERS:
        if args.name and args.name.lower() not in title.lower():
            continue

        idx = data.find(marker)
        if idx != -1:
            found = True
            # Find end of string (null byte or next section)
            end = data.find(b"\x00", idx)
            prompt_text = data[idx:end].decode("utf-8", errors="ignore")

            print("=" * 70)
            print(f"  {title}")
            print("=" * 70)
            print(prompt_text.strip())
            print("\n")

    if not found:
        print(f"No prompt found matching '{args.name}'. Use --list to see categories.", file=sys.stderr)

if __name__ == "__main__":
    main()
