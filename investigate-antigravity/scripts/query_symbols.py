#!/usr/bin/env python3
"""
Fast symbol searcher over unstripped Antigravity binaries (localharness.debug).
Parses .symtab directly in ~30ms without requiring GDB or external disassemblers.
"""

import argparse
import os
import re
import struct
import sys

DEFAULT_BINARY = os.path.expanduser("~/.local/share/antigravity/localharness.debug")

def parse_elf_symtab(binary_path):
    if not os.path.exists(binary_path):
        print(f"Error: binary not found at {binary_path}", file=sys.stderr)
        print("Run the extraction step or specify --binary <path>", file=sys.stderr)
        sys.exit(1)

    with open(binary_path, "rb") as f:
        elf_header = f.read(64)
        if elf_header[:4] != b"\x7fELF":
            print(f"Error: {binary_path} is not a valid ELF file", file=sys.stderr)
            sys.exit(1)

        e_shoff = struct.unpack("<Q", elf_header[40:48])[0]
        e_shentsize = struct.unpack("<H", elf_header[58:60])[0]
        e_shnum = struct.unpack("<H", elf_header[60:62])[0]
        e_shstrndx = struct.unpack("<H", elf_header[62:64])[0]

        f.seek(e_shoff)
        sections = []
        for _ in range(e_shnum):
            sec = f.read(e_shentsize)
            sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, sh_link = struct.unpack("<IIQQQQI", sec[:44])
            sections.append({"name_idx": sh_name, "size": sh_size, "offset": sh_offset, "link": sh_link})

        shstr = sections[e_shstrndx]
        f.seek(shstr["offset"])
        shstrtab = f.read(shstr["size"])
        for s in sections:
            s["name"] = shstrtab[s["name_idx"]:].split(b"\x00")[0].decode("utf-8", errors="ignore")

        symtab_sec = next((s for s in sections if s["name"] == ".symtab"), None)
        if not symtab_sec:
            print("Error: .symtab section not found (binary might be stripped)", file=sys.stderr)
            sys.exit(1)

        strtab_sec = sections[symtab_sec["link"]]

        f.seek(strtab_sec["offset"])
        strtab = f.read(strtab_sec["size"])

        f.seek(symtab_sec["offset"])
        symtab_bytes = f.read(symtab_sec["size"])

    return symtab_bytes, strtab

def main():
    parser = argparse.ArgumentParser(description="Search symbols in unstripped Antigravity localharness binary.")
    parser.add_argument("query", nargs="?", default="", help="Query regex or keyword to filter symbol names")
    parser.add_argument("--binary", default=DEFAULT_BINARY, help="Path to localharness.debug binary")
    parser.add_argument("--limit", type=int, default=50, help="Maximum symbols to display (default: 50, 0 for all)")
    parser.add_argument("--packages-only", action="store_true", help="List unique Go package paths matching query")
    parser.add_argument("--methods-only", action="store_true", help="Only show struct methods (*.Method or (*Type).Method)")
    parser.add_argument("--count", action="store_true", help="Show total match count only")

    args = parser.parse_args()

    symtab_bytes, strtab = parse_elf_symtab(args.binary)
    pattern = re.compile(args.query, re.IGNORECASE) if args.query else None

    matches = []
    packages = set()

    for i in range(0, len(symtab_bytes), 24):
        st_name = struct.unpack("<I", symtab_bytes[i:i+4])[0]
        if st_name < len(strtab):
            end = strtab.find(b"\x00", st_name)
            name = strtab[st_name:end].decode("utf-8", errors="ignore")
            if not name:
                continue

            if args.methods_only and not (".(" in name or "(*" in name):
                continue

            if pattern and not pattern.search(name):
                continue

            if args.packages_only:
                pkg = name.split(".")[0]
                packages.add(pkg)
            else:
                matches.append(name)

    if args.packages_only:
        sorted_pkgs = sorted(list(packages))
        if args.count:
            print(len(sorted_pkgs))
            return
        limit = args.limit if args.limit > 0 else len(sorted_pkgs)
        for p in sorted_pkgs[:limit]:
            print(p)
        if len(sorted_pkgs) > limit:
            print(f"... and {len(sorted_pkgs) - limit} more packages (use --limit 0 to show all)")
        return

    if args.count:
        print(len(matches))
        return

    limit = args.limit if args.limit > 0 else len(matches)
    for s in matches[:limit]:
        print(s)
    if len(matches) > limit:
        print(f"... and {len(matches) - limit} more matching symbols (use --limit 0 to show all)")

if __name__ == "__main__":
    main()
