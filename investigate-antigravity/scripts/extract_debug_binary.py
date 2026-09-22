#!/usr/bin/env python3
"""
Automated extraction script for the unstripped Antigravity localharness debug binary.
Extracts 'google3/third_party/jetski_prod/localharness/localharness' from 'agy_acp_server.par'
and places it into '~/.local/share/antigravity/localharness.debug'.
"""

import argparse
import os
import shutil
import sys
import time
import zipfile

DEFAULT_PAR = os.path.expanduser("~/.local/bin/agy_acp_server.par")
DEFAULT_DEST = os.path.expanduser("~/.local/share/antigravity/localharness.debug")
INTERNAL_HARNESS_PATH = "google3/third_party/jetski_prod/localharness/localharness"

def main():
    parser = argparse.ArgumentParser(description="Extract unstripped localharness debug binary from agy_acp_server.par")
    parser.add_argument("--par", default=DEFAULT_PAR, help="Path to agy_acp_server.par")
    parser.add_argument("--dest", default=DEFAULT_DEST, help="Destination path for localharness.debug")
    parser.add_argument("--force", action="store_true", help="Overwrite existing extracted binary")

    args = parser.parse_args()

    if not os.path.exists(args.par):
        print(f"Error: PAR binary not found at {args.par}", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(args.dest) and not args.force:
        size_mb = os.path.getsize(args.dest) / (1024 * 1024)
        print(f"Debug binary already exists at {args.dest} ({size_mb:.2f} MB). Use --force to re-extract.")
        return

    os.makedirs(os.path.dirname(args.dest), exist_ok=True)

    print(f"Opening {args.par}...")
    t0 = time.time()
    try:
        with zipfile.ZipFile(args.par) as z:
            if INTERNAL_HARNESS_PATH not in z.namelist():
                print(f"Error: '{INTERNAL_HARNESS_PATH}' not found in archive.", file=sys.stderr)
                sys.exit(1)

            print(f"Extracting {INTERNAL_HARNESS_PATH} -> {args.dest}...")
            with z.open(INTERNAL_HARNESS_PATH) as src, open(args.dest, "wb") as dst:
                shutil.copyfileobj(src, dst, length=16 * 1024 * 1024)

        os.chmod(args.dest, 0o755)
        elapsed = time.time() - t0
        size_mb = os.path.getsize(args.dest) / (1024 * 1024)
        print(f"Extraction complete in {elapsed:.2f}s. Size: {size_mb:.2f} MB ({args.dest})")
    except Exception as e:
        print(f"Failed to extract debug binary: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
