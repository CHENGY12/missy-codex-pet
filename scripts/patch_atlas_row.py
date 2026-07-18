#!/usr/bin/env python3
"""Replace one complete Codex pet atlas row and verify all other rows are unchanged."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

ATLAS_WIDTH = 1536
ATLAS_HEIGHT = 2288
ROW_HEIGHT = 208
ROW_COUNT = 11


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-atlas", required=True)
    parser.add_argument("--replacement-row", required=True)
    parser.add_argument("--row-index", required=True, type=int)
    parser.add_argument("--output", required=True)
    parser.add_argument("--png-output")
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args()

    base_path = Path(args.base_atlas).expanduser().resolve()
    row_path = Path(args.replacement_row).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    report_path = Path(args.json_out).expanduser().resolve()
    png_path = Path(args.png_output).expanduser().resolve() if args.png_output else None

    if not 0 <= args.row_index < ROW_COUNT:
        raise SystemExit(f"row index must be between 0 and {ROW_COUNT - 1}")

    with Image.open(base_path) as opened:
        base = opened.convert("RGBA")
    with Image.open(row_path) as opened:
        replacement = opened.convert("RGBA")

    if base.size != (ATLAS_WIDTH, ATLAS_HEIGHT):
        raise SystemExit(f"expected {ATLAS_WIDTH}x{ATLAS_HEIGHT} atlas, got {base.size}")
    if replacement.size != (ATLAS_WIDTH, ROW_HEIGHT):
        raise SystemExit(f"expected {ATLAS_WIDTH}x{ROW_HEIGHT} row, got {replacement.size}")

    top = args.row_index * ROW_HEIGHT
    expected = base.copy()
    expected.paste(replacement, (0, top))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    expected.save(output_path, format="WEBP", lossless=True, quality=100, method=6, exact=True)
    if png_path:
        png_path.parent.mkdir(parents=True, exist_ok=True)
        expected.save(png_path)

    with Image.open(output_path) as opened:
        decoded = opened.convert("RGBA")

    changed_rows = []
    unchanged_rows = []
    for row_index in range(ROW_COUNT):
        box = (0, row_index * ROW_HEIGHT, ATLAS_WIDTH, (row_index + 1) * ROW_HEIGHT)
        if decoded.crop(box).tobytes() == base.crop(box).tobytes():
            unchanged_rows.append(row_index)
        else:
            changed_rows.append(row_index)

    decoded_matches_expected = decoded.tobytes() == expected.tobytes()
    report = {
        "ok": decoded_matches_expected and changed_rows == [args.row_index],
        "base_atlas": str(base_path),
        "replacement_row": str(row_path),
        "output": str(output_path),
        "row_index": args.row_index,
        "changed_rows": changed_rows,
        "unchanged_rows": unchanged_rows,
        "other_rows_unchanged": unchanged_rows
        == [row for row in range(ROW_COUNT) if row != args.row_index],
        "decoded_webp_matches_expected": decoded_matches_expected,
        "output_sha256": sha256(output_path),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
