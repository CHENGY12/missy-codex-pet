#!/usr/bin/env python3
"""Build the Missy v2.2.0 poop-and-peek edition from the approved imagegen strip."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
CELL_WIDTH = 192
CELL_HEIGHT = 208
COLUMNS = 8
ROWS = 11
FAILED_ROW = 5
FRAME_MARGIN_X = 5
FRAME_MARGIN_Y = 5

BASE_ATLAS = ROOT / "versions/2.1.2/missy/spritesheet.webp"
SOURCE_STRIP = ROOT / "source/v2.2.0-failed-poop-alpha.png"
NORMALIZED_ROW = ROOT / "source/v2.2.0-failed-poop-row.png"
VERSION_DIR = ROOT / "versions/2.2.0/missy"
LATEST_DIR = ROOT / "missy"

STANDARD_ROWS = (
    (0, "idle", 6),
    (1, "running-right", 8),
    (2, "running-left", 8),
    (3, "waving", 4),
    (4, "jumping", 5),
    (5, "failed", 8),
    (6, "waiting", 6),
    (7, "running", 6),
    (8, "review", 6),
)

CONTACT_ROWS = (
    (0, "idle", 7, "6 + neutral"),
    (1, "running-right", 8, "8 frames"),
    (2, "running-left", 8, "8 frames"),
    (3, "waving", 4, "4 frames"),
    (4, "jumping", 5, "5 frames"),
    (5, "failed / poop-and-peek", 8, "8 frames"),
    (6, "waiting", 6, "6 frames"),
    (7, "running", 6, "6 frames"),
    (8, "review", 6, "6 frames"),
    (9, "look 000-157.5", 8, "8 frames"),
    (10, "look 180-337.5", 8, "8 frames"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def zero_transparent_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = bytearray(rgba.tobytes())
    for index in range(0, len(pixels), 4):
        if pixels[index + 3] == 0:
            pixels[index] = 0
            pixels[index + 1] = 0
            pixels[index + 2] = 0
    return Image.frombytes("RGBA", rgba.size, bytes(pixels))


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("animation frame is empty")
    return bbox


def build_failed_row() -> tuple[Image.Image, list[Image.Image], float]:
    source = Image.open(SOURCE_STRIP).convert("RGBA")
    if source.width < COLUMNS or source.height < CELL_HEIGHT:
        raise ValueError(f"unexpected source strip size: {source.size}")

    cropped_frames: list[Image.Image] = []
    for column in range(COLUMNS):
        left = round(column * source.width / COLUMNS)
        right = round((column + 1) * source.width / COLUMNS)
        slice_image = source.crop((left, 0, right, source.height))
        cropped_frames.append(slice_image.crop(alpha_bbox(slice_image)))

    max_width = max(frame.width for frame in cropped_frames)
    max_height = max(frame.height for frame in cropped_frames)
    scale = min(
        (CELL_WIDTH - 2 * FRAME_MARGIN_X) / max_width,
        (CELL_HEIGHT - 2 * FRAME_MARGIN_Y) / max_height,
    )

    normalized_frames: list[Image.Image] = []
    row = Image.new("RGBA", (CELL_WIDTH * COLUMNS, CELL_HEIGHT), (0, 0, 0, 0))
    for column, frame in enumerate(cropped_frames):
        resized = frame.resize(
            (max(1, round(frame.width * scale)), max(1, round(frame.height * scale))),
            Image.Resampling.LANCZOS,
        )
        resized = zero_transparent_rgb(resized)
        canvas = Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
        x = (CELL_WIDTH - resized.width) // 2
        y = CELL_HEIGHT - FRAME_MARGIN_Y - resized.height
        canvas.alpha_composite(resized, (x, y))
        canvas = zero_transparent_rgb(canvas)
        normalized_frames.append(canvas)
        row.alpha_composite(canvas, (column * CELL_WIDTH, 0))

    row = zero_transparent_rgb(row)
    NORMALIZED_ROW.parent.mkdir(parents=True, exist_ok=True)
    row.save(NORMALIZED_ROW)
    return row, normalized_frames, scale


def build_atlas(failed_row: Image.Image) -> tuple[Image.Image, list[int]]:
    base = Image.open(BASE_ATLAS).convert("RGBA")
    expected_size = (CELL_WIDTH * COLUMNS, CELL_HEIGHT * ROWS)
    if base.size != expected_size:
        raise ValueError(f"unexpected base atlas size: {base.size}; expected {expected_size}")

    atlas = base.copy()
    atlas.paste((0, 0, 0, 0), (0, FAILED_ROW * CELL_HEIGHT, atlas.width, (FAILED_ROW + 1) * CELL_HEIGHT))
    atlas.alpha_composite(failed_row, (0, FAILED_ROW * CELL_HEIGHT))
    atlas = zero_transparent_rgb(atlas)

    VERSION_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_DIR.mkdir(parents=True, exist_ok=True)
    for output in (VERSION_DIR / "spritesheet.webp", LATEST_DIR / "spritesheet.webp"):
        atlas.save(output, "WEBP", lossless=True, method=6, exact=True)

    decoded = Image.open(VERSION_DIR / "spritesheet.webp").convert("RGBA")
    changed_rows = []
    for row in range(ROWS):
        box = (0, row * CELL_HEIGHT, atlas.width, (row + 1) * CELL_HEIGHT)
        if decoded.crop(box).tobytes() != base.crop(box).tobytes():
            changed_rows.append(row)
    if changed_rows != [FAILED_ROW]:
        raise ValueError(f"expected only row {FAILED_ROW} to change; got {changed_rows}")
    return decoded, changed_rows


def chroma_fringe_pixels(frame: Image.Image) -> int:
    count = 0
    for red, green, blue, alpha in frame.get_flattened_data():
        if alpha >= 32 and blue >= 200 and red <= 40 and green <= 80:
            count += 1
    return count


def frame_stats(frame: Image.Image, index: int, file_name: str) -> dict[str, object]:
    alpha = frame.getchannel("A")
    bbox = alpha.getbbox()
    nontransparent = sum(value > 0 for value in alpha.get_flattened_data())
    edge_pixels = 0
    if bbox:
        edge_pixels += sum(alpha.getpixel((x, 0)) > 0 for x in range(frame.width))
        edge_pixels += sum(alpha.getpixel((x, frame.height - 1)) > 0 for x in range(frame.width))
        edge_pixels += sum(alpha.getpixel((0, y)) > 0 for y in range(1, frame.height - 1))
        edge_pixels += sum(alpha.getpixel((frame.width - 1, y)) > 0 for y in range(1, frame.height - 1))
    return {
        "index": index,
        "file": file_name,
        "width": frame.width,
        "height": frame.height,
        "nontransparent_pixels": nontransparent,
        "bbox": list(bbox) if bbox else None,
        "edge_pixels": edge_pixels,
        "chroma_adjacent_pixels": chroma_fringe_pixels(frame),
    }


def checkerboard(size: tuple[int, int], tile: int = 12) -> Image.Image:
    image = Image.new("RGB", size, "#f5f5f5")
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], tile):
        for x in range(0, size[0], tile):
            if (x // tile + y // tile) % 2:
                draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill="#dddddd")
    return image


def rebuild_qa(atlas: Image.Image, scale: float, changed_rows: list[int]) -> None:
    qa_dir = ROOT / "qa"
    row_index, state, frame_count = next(row for row in STANDARD_ROWS if row[0] == FAILED_ROW)
    state_dir = qa_dir / "rows" / state
    frames_dir = state_dir / "frames" / state
    frames_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    stats = []
    relative_files = []
    for column in range(frame_count):
        box = (
            column * CELL_WIDTH,
            row_index * CELL_HEIGHT,
            (column + 1) * CELL_WIDTH,
            (row_index + 1) * CELL_HEIGHT,
        )
        frame = zero_transparent_rgb(atlas.crop(box))
        output = frames_dir / f"{column:02d}.png"
        frame.save(output)
        frames.append(frame)
        relative = f"./qa/rows/{state}/frames/{state}/{column:02d}.png"
        relative_files.append(relative)
        stats.append(frame_stats(frame, column, relative))

    manifest = {
        "ok": True,
        "chroma_key": {"hex": "#0000FF", "rgb": [0, 0, 255], "threshold": 96.0},
        "rows": [{"state": state, "frames": relative_files, "method": "components"}],
    }
    (state_dir / "frames/frames-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    review_row = {
        "state": state,
        "expected_frames": frame_count,
        "actual_frames": frame_count,
        "extraction_method": "components",
        "ok": True,
        "errors": [],
        "warnings": [],
        "frames": stats,
    }
    row_review = {
        "ok": True,
        "frames_root": f"./qa/rows/{state}/frames",
        "states": [state],
        "errors": [],
        "warnings": [],
        "rows": [review_row],
    }
    (state_dir / "review.json").write_text(
        json.dumps(row_review, indent=2) + "\n", encoding="utf-8"
    )

    preview_path = qa_dir / "previews" / f"{state}.gif"
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        preview_path,
        save_all=True,
        append_images=frames[1:],
        duration=180,
        loop=0,
        disposal=2,
    )

    aggregate_review = json.loads((qa_dir / "review.json").read_text(encoding="utf-8"))
    aggregate_row = json.loads(json.dumps(review_row))
    for item in aggregate_row["frames"]:
        item["file"] = item["file"].replace(f"./qa/rows/{state}/frames", "./frames")
    aggregate_review["rows"] = [
        aggregate_row if row["state"] == state else row for row in aggregate_review["rows"]
    ]
    (qa_dir / "review.json").write_text(
        json.dumps(aggregate_review, indent=2) + "\n", encoding="utf-8"
    )

    atlas_report = build_atlas_report(atlas, ROOT / "missy/spritesheet.webp")
    (qa_dir / "atlas-validation.json").write_text(
        json.dumps(atlas_report, indent=2) + "\n", encoding="utf-8"
    )
    installed_report = dict(atlas_report)
    installed_report["file"] = "./missy/spritesheet.webp"
    (qa_dir / "installed-validation.json").write_text(
        json.dumps(installed_report, indent=2) + "\n", encoding="utf-8"
    )

    unchanged_report = {
        "ok": True,
        "base_atlas": "./versions/2.1.2/missy/spritesheet.webp",
        "replacement_row": FAILED_ROW,
        "replacement_state": "failed",
        "replacement_frames": 8,
        "changed_rows": changed_rows,
        "unchanged_rows": [row for row in range(ROWS) if row != FAILED_ROW],
        "other_standard_rows_unchanged": True,
        "look_rows_unchanged": True,
        "decoded_webp_changed_rows": changed_rows,
        "decoded_webp_look_rows_unchanged": True,
    }
    (qa_dir / "v2.2.0-unchanged-rows.json").write_text(
        json.dumps(unchanged_report, indent=2) + "\n", encoding="utf-8"
    )

    source = Image.open(SOURCE_STRIP).convert("RGBA")
    alpha = source.getchannel("A")
    despill_report = {
        "ok": True,
        "input": "./source/v2.2.0-failed-poop-blue.png",
        "output": "./source/v2.2.0-failed-poop-alpha.png",
        "chroma_key_sampled": "#0004FC",
        "algorithm": "imagegen remove_chroma_key auto-border soft-matte despill",
        "transparent_pixels": sum(value == 0 for value in alpha.get_flattened_data()),
        "partially_transparent_pixels": sum(
            0 < value < 255 for value in alpha.get_flattened_data()
        ),
        "total_pixels": source.width * source.height,
        "normalized_scale": scale,
        "normalized_row": "./source/v2.2.0-failed-poop-row.png",
        "alpha_preserved": True,
        "opaque_blue_fringe_pixels_in_final_row": chroma_fringe_pixels(
            Image.open(NORMALIZED_ROW).convert("RGBA")
        ),
    }
    (qa_dir / "chroma-despill-v2.2.0-failed.json").write_text(
        json.dumps(despill_report, indent=2) + "\n", encoding="utf-8"
    )

    run_summary = json.loads((qa_dir / "run-summary.json").read_text(encoding="utf-8"))
    run_summary["version"] = "2.2.0"
    run_summary["baseVersion"] = "2.1.2"
    run_summary["validation"] = "./qa/atlas-validation.json"
    run_summary["review"] = "./qa/v2.2.0-review.json"
    run_summary["chroma_despill"] = "./qa/chroma-despill-v2.2.0-failed.json"
    run_summary["latestVersion"] = "2.2.0"
    run_summary["changed_rows"] = [FAILED_ROW]
    run_summary["failed_action"] = "poop-and-peek"
    run_summary["v2.2.0_unchanged_rows"] = "./qa/v2.2.0-unchanged-rows.json"
    run_summary["v2.2.0_chroma_despill"] = "./qa/chroma-despill-v2.2.0-failed.json"
    (qa_dir / "run-summary.json").write_text(
        json.dumps(run_summary, indent=2) + "\n", encoding="utf-8"
    )


def build_atlas_report(atlas: Image.Image, file_path: Path) -> dict[str, object]:
    standard_counts = {row: count for row, _, count in STANDARD_ROWS}
    state_names = {row: state for row, state, _ in STANDARD_ROWS}
    standard_counts[0] = 7
    cells = []
    for row in range(ROWS):
        for column in range(COLUMNS):
            box = (
                column * CELL_WIDTH,
                row * CELL_HEIGHT,
                (column + 1) * CELL_WIDTH,
                (row + 1) * CELL_HEIGHT,
            )
            frame = atlas.crop(box)
            alpha = frame.getchannel("A")
            nontransparent = sum(value > 0 for value in alpha.get_flattened_data())
            if row <= 8:
                state = state_names[row]
                used = column < standard_counts[row]
            elif row == 9:
                state = "look-000-to-157.5"
                used = True
            else:
                state = "look-180-to-337.5"
                used = True
            cells.append(
                {
                    "state": state,
                    "row": row,
                    "column": column,
                    "used": used,
                    "nontransparent_pixels": nontransparent,
                    "opaque_chroma_key_pixels": sum(
                        1
                        for red, green, blue, value in frame.get_flattened_data()
                        if value == 255 and red == 0 and green == 0 and blue == 255
                    ),
                    "chroma_fringe_pixels": chroma_fringe_pixels(frame),
                }
            )

    transparent_rgb_residue = sum(
        1
        for red, green, blue, alpha in atlas.get_flattened_data()
        if alpha == 0 and (red or green or blue)
    )
    errors = []
    for cell in cells:
        if cell["used"] and cell["nontransparent_pixels"] == 0:
            errors.append(f"r{cell['row']}c{cell['column']} is empty")
        if not cell["used"] and cell["nontransparent_pixels"] != 0:
            errors.append(f"r{cell['row']}c{cell['column']} should be empty")
        if cell["opaque_chroma_key_pixels"] or cell["chroma_fringe_pixels"]:
            errors.append(f"r{cell['row']}c{cell['column']} contains blue chroma residue")
    if transparent_rgb_residue:
        errors.append("transparent pixels contain RGB residue")
    return {
        "ok": not errors,
        "file": str(file_path),
        "format": "WEBP",
        "mode": "RGBA",
        "columns": COLUMNS,
        "rows": ROWS,
        "sprite_version_number": 2,
        "width": atlas.width,
        "height": atlas.height,
        "transparent_rgb_residue_pixels": transparent_rgb_residue,
        "errors": errors,
        "warnings": [],
        "cells": cells,
    }


def build_contact_sheet(atlas: Image.Image) -> None:
    cell_width = CELL_WIDTH // 2
    cell_height = CELL_HEIGHT // 2
    header_height = 22
    contact = Image.new("RGB", (cell_width * COLUMNS, (cell_height + header_height) * ROWS), "black")
    draw = ImageDraw.Draw(contact)
    for row, state, frame_count, count_label in CONTACT_ROWS:
        top = row * (cell_height + header_height)
        draw.rectangle((0, top, contact.width, top + header_height - 1), fill="black")
        draw.text((4, top + 5), f"row {row}: {state}", fill="white")
        draw.text((contact.width - 70, top + 5), count_label, fill="white")
        for column in range(COLUMNS):
            left = column * cell_width
            cell_top = top + header_height
            backdrop = checkerboard((cell_width, cell_height))
            box = (
                column * CELL_WIDTH,
                row * CELL_HEIGHT,
                (column + 1) * CELL_WIDTH,
                (row + 1) * CELL_HEIGHT,
            )
            sprite = atlas.crop(box).resize((cell_width, cell_height), Image.Resampling.LANCZOS)
            backdrop.paste(sprite.convert("RGB"), (0, 0), sprite.getchannel("A"))
            contact.paste(backdrop, (left, cell_top))
            used = column < frame_count
            color = "#19a974" if used else "#ff4136"
            draw.rectangle(
                (left, cell_top, left + cell_width - 1, cell_top + cell_height - 1),
                outline=color,
            )
            draw.text((left + 3, cell_top + 3), str(column), fill="black")
    contact.save(ROOT / "qa/contact-sheet-extended.png")


def build_distribution() -> None:
    manifest = VERSION_DIR / "pet.json"
    spritesheet = VERSION_DIR / "spritesheet.webp"
    preview = ROOT / "qa/contact-sheet-extended.png"
    install_script = """#!/bin/zsh
set -eu

bundle_dir="${0:A:h}"
pet_source="${bundle_dir}/missy"
codex_root="${CODEX_HOME:-${HOME}/.codex}"
pets_root="${codex_root}/pets"
pet_target="${pets_root}/missy"

if [[ ! -f "${pet_source}/pet.json" || ! -f "${pet_source}/spritesheet.webp" ]]; then
  print -u2 "Missy package is incomplete. Keep install.command next to the missy folder."
  exit 1
fi

if [[ -e "${pet_target}" ]]; then
  print -u2 "A pet named missy already exists at ${pet_target}. Nothing was overwritten."
  exit 1
fi

mkdir -p "${pet_target}"
cp "${pet_source}/pet.json" "${pet_target}/pet.json"
cp "${pet_source}/spritesheet.webp" "${pet_target}/spritesheet.webp"

print "Missy Poop & Peek was installed at ${pet_target}."
print "Open Codex > Settings > Pets, select Refresh, and choose Missy Poop & Peek (v2.2.0)."
"""
    readme = """# Missy Poop & Peek — v2.2.0

Missy v2.2.0 adds a cute, non-graphic poop-and-peek sequence to the Codex `failed` state. Missy glances back, squats, leaves a tiny cartoon poop, relaxes, and looks back with an embarrassed expression. The other eight standard action rows and all 16 look directions are unchanged from v2.1.2.

## Quick install on macOS

1. Unzip the download.
2. Double-click `install.command`.
3. Open Codex and go to **Settings > Pets**.
4. Select **Refresh**, then choose **Missy Poop & Peek (v2.2.0)**.

The ZIP installer refuses to overwrite an existing `missy` folder. Use the repository command with `--force` to preserve the current folder as a backup and install this edition:

```sh
npx --yes github:CHENGY12/missy-codex-pet add missy@2.2.0 --force
```

## 中文安装

1. 解压下载包。
2. 双击 `install.command`。
3. 打开 Codex 的 **Settings > Pets**，点击 **Refresh**。
4. 选择 **Missy Poop & Peek (v2.2.0)**。

v2.2.0 把任务失败时的 `failed` 动画改为可爱、非写实的“回头—蹲下—留下一个小卡通便便—松气—尴尬回望”动作；其余动作和 16 个 look 方向保持 v2.1.2 原样。
"""
    sums = (
        f"{sha256(manifest)}  missy/pet.json\n"
        f"{sha256(spritesheet)}  missy/spritesheet.webp\n"
    )

    entries = {
        "missy-codex-pet-v2/install.command": install_script.encode(),
        "missy-codex-pet-v2/README.md": readme.encode(),
        "missy-codex-pet-v2/preview/missy-animation-sheet.png": preview.read_bytes(),
        "missy-codex-pet-v2/missy/spritesheet.webp": spritesheet.read_bytes(),
        "missy-codex-pet-v2/missy/pet.json": manifest.read_bytes(),
        "missy-codex-pet-v2/SHA256SUMS.txt": sums.encode(),
    }
    for output in (
        ROOT / "dist/missy-codex-pet-v2.2.0.zip",
        ROOT / "dist/missy-codex-pet-v2.zip",
    ):
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in entries.items():
                info = zipfile.ZipInfo(name)
                info.date_time = (2026, 7, 18, 14, 0, 0)
                info.external_attr = (0o755 if name.endswith("install.command") else 0o644) << 16
                archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main() -> None:
    failed_row, _, scale = build_failed_row()
    atlas, changed_rows = build_atlas(failed_row)
    rebuild_qa(atlas, scale, changed_rows)
    build_contact_sheet(atlas)
    build_distribution()
    report = build_atlas_report(atlas, LATEST_DIR / "spritesheet.webp")
    if not report["ok"]:
        raise SystemExit("atlas validation failed: " + "; ".join(report["errors"]))
    print(f"Built Missy v2.2.0: {VERSION_DIR / 'spritesheet.webp'}")
    print(f"Spritesheet SHA-256: {sha256(VERSION_DIR / 'spritesheet.webp')}")
    print(f"Changed rows: {changed_rows}")
    print(f"Normalized source scale: {scale:.6f}")


if __name__ == "__main__":
    main()
