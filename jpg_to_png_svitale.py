#!/usr/bin/env python3
"""
Recursively search for JPG/JPEG under INPUT_ROOT and create PNG copies under OUTPUT_ROOT
with the same relative directory structure.

Additionally, only write every Nth PNG (default: every 5th) while still creating the
directory tree for all folders encountered.

Usage:
  python jpg_to_png_every_n.py --input /path/in --output /path/out --every 5

Notes:
- "Every 5th" is based on a deterministic ordering of discovered JPGs:
  sorted by their relative path (case-insensitive).
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, List, Set, Tuple

from PIL import Image


JPG_EXTS = {".jpg", ".jpeg"}


def iter_dirs(root: Path) -> Iterable[Path]:
    """Yield all directories under root (including root)."""
    yield root
    for p in root.rglob("*"):
        if p.is_dir():
            yield p


def find_jpegs(root: Path) -> List[Path]:
    """Find all JPEGs under root (recursively)."""
    files: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in JPG_EXTS:
            files.append(p)
    # Deterministic order so "every 5th" is repeatable
    files.sort(key=lambda x: str(x.relative_to(root)).lower())
    return files


def make_output_dirs(input_root: Path, output_root: Path) -> None:
    """Replicate the directory structure from input_root into output_root."""
    for d in iter_dirs(input_root):
        rel = d.relative_to(input_root)
        (output_root / rel).mkdir(parents=True, exist_ok=True)


def convert_jpg_to_png(src: Path, dst: Path) -> None:
    """Convert one JPG/JPEG to PNG."""
    dst.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(src) as im:
        # Handle common JPG modes safely
        if im.mode in ("P", "LA"):
            im = im.convert("RGBA")
        elif im.mode != "RGB" and im.mode != "RGBA":
            im = im.convert("RGB")

        # PNG doesn't support EXIF orientation directly; apply it if present
        try:
            exif = im.getexif()
            orientation = exif.get(274)  # 274 = Orientation
            if orientation == 3:
                im = im.rotate(180, expand=True)
            elif orientation == 6:
                im = im.rotate(270, expand=True)
            elif orientation == 8:
                im = im.rotate(90, expand=True)
        except Exception:
            pass

        im.save(dst, format="PNG", optimize=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Input root directory to scan")
    ap.add_argument("--output", required=True, help="Output root directory for PNGs")
    ap.add_argument("--every", type=int, default=5, help="Write every Nth PNG (default 5)")
    ap.add_argument("--start", type=int, default=5,
                    help="Which index to start on (1-based). Default 5 means 5th,10th,15th,...")
    ap.add_argument("--dry-run", action="store_true", help="Print what would happen without writing files")
    args = ap.parse_args()

    input_root = Path(args.input).expanduser().resolve()
    output_root = Path(args.output).expanduser().resolve()

    if not input_root.exists() or not input_root.is_dir():
        raise SystemExit(f"Input root does not exist or is not a directory: {input_root}")

    if args.every <= 0:
        raise SystemExit("--every must be > 0")
    if args.start <= 0:
        raise SystemExit("--start must be > 0")

    # 1) Build duplicate directory structure (ignore file types)
    if args.dry_run:
        print(f"[DRY RUN] Would replicate directory tree from:\n  {input_root}\ninto:\n  {output_root}")
    else:
        make_output_dirs(input_root, output_root)

    # 2) Find all JPEGs
    jpegs = find_jpegs(input_root)
    if not jpegs:
        print("No JPG/JPEG files found.")
        return

    # 3) Convert only every Nth (based on sorted list order)
    # Use 1-based indexing for user clarity.
    converted = 0
    skipped = 0

    for idx_1based, src in enumerate(jpegs, start=1):
        take = (idx_1based >= args.start) and ((idx_1based - args.start) % args.every == 0)
        rel = src.relative_to(input_root)
        dst = (output_root / rel).with_suffix(".png")

        if take:
            if args.dry_run:
                print(f"[DRY RUN] CONVERT {idx_1based}: {src} -> {dst}")
            else:
                try:
                    convert_jpg_to_png(src, dst)
                    converted += 1
                except Exception as e:
                    print(f"ERROR converting {src}: {e}")
        else:
            skipped += 1
            if args.dry_run:
                print(f"[DRY RUN] SKIP    {idx_1based}: {src}")

    print(f"Done. Found {len(jpegs)} JPEGs. Converted {converted}. Skipped {skipped}.")


if __name__ == "__main__":
    main()