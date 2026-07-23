#!/usr/bin/env python3
"""Build Missy v2.3.2 with natural grooming and a clean failed row."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from PIL import Image, ImageDraw

from build_v2_2_0 import (
    COLUMNS,
    ROWS,
    build_atlas_report,
    build_contact_sheet,
    zero_transparent_rgb,
)
from build_v2_3_1 import rebuild_state_qa


ROOT = Path(__file__).resolve().parents[1]
CELL_WIDTH = 192
CELL_HEIGHT = 208
WAVING_ROW = 3
FAILED_ROW = 5
BASE_ATLAS = ROOT / "versions/2.3.1/missy/spritesheet.webp"
WAVING_SOURCE = ROOT / "source/v2.3.2-waving-grooming-row.png"
FAILED_SOURCE = ROOT / "source/v2.3.2-failed-poop-clean-row.png"
VERSION_DIR = ROOT / "versions/2.3.2/missy"
LATEST_DIR = ROOT / "missy"
QA_DIR = ROOT / "qa"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_box(row: int) -> tuple[int, int, int, int]:
    top = row * CELL_HEIGHT
    return (0, top, CELL_WIDTH * COLUMNS, top + CELL_HEIGHT)


def load_replacement(path: Path) -> Image.Image:
    with Image.open(path) as opened:
        row = zero_transparent_rgb(opened)
    expected = (CELL_WIDTH * COLUMNS, CELL_HEIGHT)
    if row.size != expected:
        raise ValueError(f"{path} must be {expected[0]}x{expected[1]}; got {row.size}")
    return row


def failed_repair_report(base_row: Image.Image, repaired_row: Image.Image) -> dict[str, object]:
    changed_by_frame: dict[str, int] = {}
    changed_outside_repair_region = 0
    for column in range(COLUMNS):
        changed = 0
        for y in range(CELL_HEIGHT):
            for local_x in range(CELL_WIDTH):
                x = column * CELL_WIDTH + local_x
                if base_row.getpixel((x, y)) == repaired_row.getpixel((x, y)):
                    continue
                changed += 1
                if column not in {1, 7} or local_x >= 24:
                    changed_outside_repair_region += 1
        changed_by_frame[str(column)] = changed

    expected = {"0": 0, "1": 109, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 158}
    ok = changed_by_frame == expected and changed_outside_repair_region == 0
    return {
        "ok": ok,
        "repair": "clear detached source-edge fragments in the left 24 pixels of failed frames 1 and 7",
        "changedPixelsByFrame": changed_by_frame,
        "expectedChangedPixelsByFrame": expected,
        "changedPixelsOutsideRepairRegion": changed_outside_repair_region,
        "poopAndPeekActionOtherwisePixelIdentical": changed_outside_repair_region == 0,
    }


def build_atlas() -> tuple[Image.Image, list[int], dict[str, object]]:
    with Image.open(BASE_ATLAS) as opened:
        base = opened.convert("RGBA")
    expected_size = (CELL_WIDTH * COLUMNS, CELL_HEIGHT * ROWS)
    if base.size != expected_size:
        raise ValueError(f"base atlas must be {expected_size}; got {base.size}")

    waving = load_replacement(WAVING_SOURCE)
    failed = load_replacement(FAILED_SOURCE)
    repair = failed_repair_report(base.crop(row_box(FAILED_ROW)), failed)
    if not repair["ok"]:
        raise ValueError(f"failed-row repair exceeded its allowed region: {repair}")

    atlas = base.copy()
    atlas.paste(waving, (0, WAVING_ROW * CELL_HEIGHT))
    atlas.paste(failed, (0, FAILED_ROW * CELL_HEIGHT))

    VERSION_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_DIR.mkdir(parents=True, exist_ok=True)
    for output in (VERSION_DIR / "spritesheet.webp", LATEST_DIR / "spritesheet.webp"):
        atlas.save(output, "WEBP", lossless=True, quality=100, method=6, exact=True)

    with Image.open(VERSION_DIR / "spritesheet.webp") as opened:
        decoded = opened.convert("RGBA")
    if decoded.tobytes() != atlas.tobytes():
        raise ValueError("lossless WebP round-trip did not preserve the assembled atlas")

    changed_rows = [
        row for row in range(ROWS)
        if decoded.crop(row_box(row)).tobytes() != base.crop(row_box(row)).tobytes()
    ]
    if changed_rows != [WAVING_ROW, FAILED_ROW]:
        raise ValueError(f"expected only rows 3 and 5 to change; got {changed_rows}")

    return decoded, changed_rows, repair


def write_manifest() -> None:
    manifest = {
        "id": "missy",
        "displayName": "Missy (v2.3.2)",
        "description": (
            "Missy is a lovable little calico cat who keeps you company and "
            "playfully interacts with you while you work."
        ),
        "spriteVersionNumber": 2,
        "spritesheetPath": "spritesheet.webp",
    }
    payload = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    (VERSION_DIR / "pet.json").write_text(payload, encoding="utf-8")
    (LATEST_DIR / "pet.json").write_text(payload, encoding="utf-8")


def build_before_after(atlas: Image.Image) -> None:
    with Image.open(BASE_ATLAS) as opened:
        base = opened.convert("RGBA")

    label_height = 28
    panel_width = CELL_WIDTH * COLUMNS

    def save_comparison(
        row: int,
        before_label: str,
        after_label: str,
        output: Path,
    ) -> None:
        comparison = Image.new(
            "RGB",
            (panel_width, 2 * (CELL_HEIGHT + label_height)),
            "#b8b8b8",
        )
        draw = ImageDraw.Draw(comparison)
        for index, (label, source) in enumerate(
            (
                (before_label, base.crop(row_box(row))),
                (after_label, atlas.crop(row_box(row))),
            )
        ):
            top = index * (CELL_HEIGHT + label_height)
            draw.rectangle((0, top, panel_width, top + label_height - 1), fill="#111111")
            draw.text((8, top + 7), label, fill="white")
            panel = Image.new("RGB", (panel_width, CELL_HEIGHT), "#b8b8b8")
            panel.paste(source, (0, 0), source)
            comparison.paste(panel, (0, top + label_height))
        comparison.save(output)

    save_comparison(
        WAVING_ROW,
        "v2.3.1 waving - before",
        "v2.3.2 waving - natural grooming",
        QA_DIR / "v2.3.2-waving-before-after.png",
    )
    save_comparison(
        FAILED_ROW,
        "v2.3.1 failed - before",
        "v2.3.2 failed - detached left-edge blocks removed",
        QA_DIR / "v2.3.2-failed-before-after.png",
    )


def write_reports(
    atlas: Image.Image,
    changed_rows: list[int],
    failed_repair: dict[str, object],
) -> None:
    report = build_atlas_report(atlas, LATEST_DIR / "spritesheet.webp")
    report["file"] = "./missy/spritesheet.webp"
    if not report["ok"]:
        raise ValueError("atlas report failed: " + "; ".join(report["errors"]))
    payload = json.dumps(report, indent=2) + "\n"
    (QA_DIR / "atlas-validation.json").write_text(payload, encoding="utf-8")
    (QA_DIR / "installed-validation.json").write_text(payload, encoding="utf-8")

    patch_report = {
        "ok": changed_rows == [WAVING_ROW, FAILED_ROW] and failed_repair["ok"],
        "version": "2.3.2",
        "baseVersion": "2.3.1",
        "baseAtlas": "./versions/2.3.1/missy/spritesheet.webp",
        "changedRows": changed_rows,
        "unchangedRows": [row for row in range(ROWS) if row not in changed_rows],
        "unchangedRowsPixelIdentical": True,
        "lookRowsUnchanged": True,
        "waving": {
            "action": "seated lick-paw-and-wash-face grooming",
            "frameCount": 4,
            "source": "./source/v2.3.2-waving-grooming-row.png",
            "edgeCleanup": "./qa/chroma-despill-v2.3.2-waving.json",
        },
        "failed": {
            "action": "cute non-graphic poop-and-peek",
            "frameCount": 8,
            **failed_repair,
        },
        "outputSha256": sha256(LATEST_DIR / "spritesheet.webp"),
    }
    (QA_DIR / "v2.3.2-row-patch.json").write_text(
        json.dumps(patch_report, indent=2) + "\n",
        encoding="utf-8",
    )

    review = {
        "ok": True,
        "version": "2.3.2",
        "waving": {
            "action": "natural seated grooming",
            "sequence": ["raise paw", "lick paw", "wash cheek and ear", "return to seated pose"],
            "frameCount": 4,
            "identityStable": True,
            "motionReadsNaturally": True,
        },
        "failed": {
            "action": "cute non-graphic poop-and-peek",
            "frameCount": 8,
            "detachedLeftEdgeBlocksRemoved": True,
            "actionOtherwiseUnchanged": True,
        },
        "otherRows": "pixel-identical to v2.3.1",
        "contactSheet": "./qa/contact-sheet-extended.png",
        "beforeAfter": {
            "waving": "./qa/v2.3.2-waving-before-after.png",
            "failed": "./qa/v2.3.2-failed-before-after.png",
        },
        "previews": {
            "waving": "./qa/previews/waving.gif",
            "failed": "./qa/previews/failed.gif",
        },
    }
    (QA_DIR / "v2.3.2-review.json").write_text(
        json.dumps(review, indent=2) + "\n",
        encoding="utf-8",
    )

    summary = json.loads((QA_DIR / "run-summary.json").read_text(encoding="utf-8"))
    summary.update(
        {
            "ok": True,
            "version": "2.3.2",
            "baseVersion": "2.3.1",
            "latestVersion": "2.3.2",
            "changed_rows": changed_rows,
            "waving_action": "natural seated lick-paw-and-wash-face grooming",
            "failed_action": "poop-and-peek with detached left-edge fragments removed",
            "validation": "./qa/atlas-validation-v2.3.2.json",
            "installed_validation": "./qa/installed-validation.json",
            "review": "./qa/v2.3.2-review.json",
            "repair_report": "./qa/v2.3.2-row-patch.json",
            "chroma_despill": "./qa/chroma-despill-v2.3.2-waving.json",
            "package": "./missy",
        }
    )
    (QA_DIR / "run-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )


def build_distribution() -> None:
    manifest = VERSION_DIR / "pet.json"
    spritesheet = VERSION_DIR / "spritesheet.webp"
    preview = QA_DIR / "contact-sheet-extended.png"
    install_script = """#!/bin/zsh
set -eu

bundle_dir="${0:A:h}"
pet_source="${bundle_dir}/missy"
codex_root="${CODEX_HOME:-${HOME}/.codex}"
pet_target="${codex_root}/pets/missy"

if [[ -e "${pet_target}" ]]; then
  print -u2 "A pet named missy already exists at ${pet_target}. Nothing was overwritten."
  exit 1
fi

mkdir -p "${pet_target}"
cp "${pet_source}/pet.json" "${pet_target}/pet.json"
cp "${pet_source}/spritesheet.webp" "${pet_target}/spritesheet.webp"
print "Missy (v2.3.2) was installed at ${pet_target}."
"""
    readme = """# Missy (v2.3.2)

Missy is a lovable little calico cat who keeps you company and playfully interacts with you while you work.

This release gives the `waving` state a natural lick-paw-and-wash-face grooming loop and removes detached black source-edge fragments from the `failed` poop-and-peek animation. Every other animation row is pixel-identical to v2.3.1.

Install with:

```sh
npx --yes github:CHENGY12/missy-codex-pet add missy@2.3.2 --force
```
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
        ROOT / "dist/missy-codex-pet-v2.3.2.zip",
        ROOT / "dist/missy-codex-pet-v2.zip",
    ):
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(
            output,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for name, data in entries.items():
                info = zipfile.ZipInfo(name)
                info.date_time = (2026, 7, 23, 12, 0, 0)
                info.external_attr = (0o755 if name.endswith("install.command") else 0o644) << 16
                archive.writestr(
                    info,
                    data,
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )


def main() -> None:
    atlas, changed_rows, failed_repair = build_atlas()
    write_manifest()
    rebuild_state_qa(atlas, WAVING_ROW, "waving", 4)
    rebuild_state_qa(atlas, FAILED_ROW, "failed", 8)
    build_contact_sheet(atlas)
    build_before_after(atlas)
    write_reports(atlas, changed_rows, failed_repair)
    build_distribution()
    print(f"Built Missy v2.3.2: {VERSION_DIR / 'spritesheet.webp'}")
    print(f"Spritesheet SHA-256: {sha256(VERSION_DIR / 'spritesheet.webp')}")
    print(f"Changed rows against v2.3.1: {changed_rows}")


if __name__ == "__main__":
    main()
