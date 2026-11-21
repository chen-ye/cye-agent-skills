#!/usr/bin/env python3
"""Prepare UI moodboard image assets and batch-upload them to Figma upload_assets URLs."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops


SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


def trim_uniform_border(img: Image.Image, fuzz: int = 12) -> Image.Image:
    """Trim uniform border padding (e.g., white social-post margins) from an image."""
    rgb = img.convert("RGB")
    bg = Image.new("RGB", rgb.size, rgb.getpixel((0, 0)))
    diff = ImageChops.difference(rgb, bg)
    diff = ImageChops.add(diff, diff, 2.0, -fuzz)
    bbox = diff.getbbox()
    if not bbox:
        return img
    return img.crop(bbox)


def normalize_image(
    src: Path,
    dst_dir: Path,
    max_dim: int,
    trim: bool,
    border_px: int,
    jpeg_quality: int,
) -> dict[str, Any]:
    with Image.open(src) as raw:
        # Handle animated GIF/WebP by taking frame 0 cleanly
        if getattr(raw, "is_animated", False):
            raw.seek(0)
        has_alpha = raw.mode in ("RGBA", "LA") or (
            raw.mode == "P" and "transparency" in raw.info
        )
        img = raw.convert("RGBA" if has_alpha else "RGB")

        if trim:
            img = trim_uniform_border(img)
            if border_px > 0:
                bg_col = (255, 255, 255, 255) if has_alpha else (255, 255, 255)
                padded = Image.new(
                    img.mode,
                    (img.width + border_px * 2, img.height + border_px * 2),
                    bg_col,
                )
                padded.paste(img, (border_px, border_px))
                img = padded

        if max(img.width, img.height) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        stem = src.stem
        use_png = has_alpha or src.suffix.lower() == ".png"
        ext = ".png" if use_png else ".jpg"
        dst = dst_dir / f"{stem}{ext}"

        if use_png:
            img.save(dst, format="PNG", optimize=True)
            fmt = "PNG"
        else:
            img.convert("RGB").save(dst, format="JPEG", quality=jpeg_quality, optimize=True)
            fmt = "JPEG"

        return {
            "key": stem,
            "source": str(src),
            "path": str(dst),
            "width": img.width,
            "height": img.height,
            "aspectRatio": round(img.width / img.height, 4),
            "format": fmt,
            "bytes": dst.stat().st_size,
        }


def cmd_prepare(args: argparse.Namespace) -> int:
    in_dir = Path(args.input_dir).expanduser().resolve()
    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    trim_keys = set(args.trim_keys or [])
    files = sorted(
        p for p in in_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
    )
    if not files:
        print(f"No supported image files found in {in_dir}", file=sys.stderr)
        return 1

    manifest: list[dict[str, Any]] = []
    for p in files:
        do_trim = args.trim_all or (p.stem in trim_keys)
        info = normalize_image(
            p,
            out_dir,
            max_dim=args.max_dim,
            trim=do_trim,
            border_px=args.border,
            jpeg_quality=args.quality,
        )
        manifest.append(info)
        print(
            f"{info['key']:36s} {info['width']:>5d}x{info['height']:<5d} "
            f"{info['format']:4s} {info['bytes'] // 1024:>5d} KB"
        )

    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else out_dir / "manifest.json"
    manifest_path.write_text(json.dumps({"assets": manifest}, indent=2) + "\n")
    print(f"Wrote manifest ({len(manifest)} assets) -> {manifest_path}")
    return 0


def upload_one(item: dict[str, str]) -> dict[str, Any]:
    path = item["path"]
    url = item["submitUrl"]
    node_id = item.get("nodeId") or item.get("targetNodeId", "")
    if not os.path.isfile(path):
        return {"nodeId": node_id, "path": path, "ok": False, "error": "file not found"}

    proc = subprocess.run(
        ["curl", "-sS", "-f", "-X", "POST", "-F", f"file=@{path}", url],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return {
            "nodeId": node_id,
            "path": path,
            "ok": False,
            "returncode": proc.returncode,
            "stderr": proc.stderr.strip(),
            "stdout": proc.stdout.strip(),
        }
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"raw": proc.stdout.strip()}
    return {"nodeId": node_id, "path": path, "ok": True, "response": payload}


def cmd_upload(args: argparse.Namespace) -> int:
    mapping_path = Path(args.mapping_json).expanduser().resolve()
    data = json.loads(mapping_path.read_text())
    items = data if isinstance(data, list) else data.get("uploads", [])
    if not items:
        print("Mapping JSON contains no upload items", file=sys.stderr)
        return 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(upload_one, items))

    failed = [r for r in results if not r["ok"]]
    summary = {
        "total": len(results),
        "succeeded": len(results) - len(failed),
        "failed": len(failed),
        "results": results,
    }
    print(json.dumps(summary, indent=2))
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize moodboard images with exact dimension metadata and upload to Figma."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_prep = sub.add_parser("prepare", help="Normalize images and emit manifest.json with WxH dimensions.")
    p_prep.add_argument("input_dir", help="Directory containing raw downloaded images.")
    p_prep.add_argument("output_dir", help="Directory to write normalized PNG/JPEG files.")
    p_prep.add_argument("--max-dim", type=int, default=2200, help="Maximum pixel edge length (default: 2200).")
    p_prep.add_argument("--quality", type=int, default=90, help="JPEG quality 1-100 (default: 90).")
    p_prep.add_argument("--trim-all", action="store_true", help="Auto-trim uniform outer margins on all images.")
    p_prep.add_argument("--trim-keys", nargs="*", help="Only auto-trim images whose filename stems match these keys.")
    p_prep.add_argument("--border", type=int, default=24, help="White padding added after trimming (default: 24px).")
    p_prep.add_argument("--manifest", help="Optional custom output path for manifest.json.")
    p_prep.set_defaults(func=cmd_prepare)

    p_up = sub.add_parser("upload", help="Parallel POST images to Figma upload_assets submitUrls.")
    p_up.add_argument("mapping_json", help="JSON array (or {uploads: [...]}) of {nodeId, path, submitUrl}.")
    p_up.add_argument("--workers", type=int, default=8, help="Concurrent upload workers (default: 8).")
    p_up.set_defaults(func=cmd_upload)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
