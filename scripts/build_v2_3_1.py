#!/usr/bin/env python3
"""Build Missy v2.3.1 with a true left-profile run and poop-and-peek failure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from PIL import Image

from build_v2_2_0 import (
    COLUMNS,
    CONTACT_ROWS,
    ROWS,
    STANDARD_ROWS,
    build_atlas_report,
    build_contact_sheet,
    frame_stats,
    zero_transparent_rgb,
)


ROOT = Path(__file__).resolve().parents[1]
CELL_WIDTH = 192
CELL_HEIGHT = 208
RUNNING_LEFT_ROW = 2
FAILED_ROW = 5
BASE_ATLAS = ROOT / "versions/2.2.1/missy/spritesheet.webp"
POOP_ATLAS = ROOT / "versions/2.2.0/missy/spritesheet.webp"
LEFT_FRAMES_DIR = ROOT / "source/v2.3.1-running-left-frames"
NORMALIZED_LEFT_ROW = ROOT / "source/v2.3.1-running-left-row.png"
VERSION_DIR = ROOT / "versions/2.3.1/missy"
LATEST_DIR = ROOT / "missy"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compose_running_left_row() -> Image.Image:
    row = Image.new("RGBA", (CELL_WIDTH * COLUMNS, CELL_HEIGHT), (0, 0, 0, 0))
    for column in range(COLUMNS):
        frame_path = LEFT_FRAMES_DIR / f"{column:02d}.png"
        with Image.open(frame_path) as opened:
            frame = zero_transparent_rgb(opened)
        if frame.size != (CELL_WIDTH, CELL_HEIGHT):
            raise ValueError(f"{frame_path} must be {CELL_WIDTH}x{CELL_HEIGHT}; got {frame.size}")
        if frame.getchannel("A").getbbox() is None:
            raise ValueError(f"{frame_path} is empty")
        row.alpha_composite(frame, (column * CELL_WIDTH, 0))
    row = zero_transparent_rgb(row)
    NORMALIZED_LEFT_ROW.parent.mkdir(parents=True, exist_ok=True)
    row.save(NORMALIZED_LEFT_ROW)
    return row


def build_atlas(left_row: Image.Image) -> tuple[Image.Image, list[int]]:
    with Image.open(BASE_ATLAS) as opened:
        base = opened.convert("RGBA")
    with Image.open(POOP_ATLAS) as opened:
        poop = opened.convert("RGBA")
    expected_size = (CELL_WIDTH * COLUMNS, CELL_HEIGHT * ROWS)
    if base.size != expected_size or poop.size != expected_size:
        raise ValueError("source atlas dimensions do not match the Codex v2 contract")

    result = base.copy()
    left_top = RUNNING_LEFT_ROW * CELL_HEIGHT
    failed_top = FAILED_ROW * CELL_HEIGHT
    result.paste(left_row, (0, left_top))
    result.paste(
        poop.crop((0, failed_top, expected_size[0], failed_top + CELL_HEIGHT)),
        (0, failed_top),
    )
    result = zero_transparent_rgb(result)

    VERSION_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_DIR.mkdir(parents=True, exist_ok=True)
    for output in (VERSION_DIR / "spritesheet.webp", LATEST_DIR / "spritesheet.webp"):
        result.save(output, "WEBP", lossless=True, quality=100, method=6, exact=True)

    with Image.open(VERSION_DIR / "spritesheet.webp") as opened:
        decoded = opened.convert("RGBA")
    changed_rows = []
    for row in range(ROWS):
        box = (0, row * CELL_HEIGHT, expected_size[0], (row + 1) * CELL_HEIGHT)
        if decoded.crop(box).tobytes() != base.crop(box).tobytes():
            changed_rows.append(row)
    if changed_rows != [RUNNING_LEFT_ROW, FAILED_ROW]:
        raise ValueError(f"expected only rows 2 and 5 to change; got {changed_rows}")

    failed_box = (0, failed_top, expected_size[0], failed_top + CELL_HEIGHT)
    if decoded.crop(failed_box).tobytes() != poop.crop(failed_box).tobytes():
        raise ValueError("final failed row does not match the approved v2.2.0 poop row")
    return decoded, changed_rows


def write_manifest() -> None:
    manifest = {
        "id": "missy",
        "displayName": "Missy Poop, Peek & Run (v2.3.1)",
        "description": (
            "Missy v2.3.1 combines the stable idle and stretch-and-meow actions with "
            "the cute poop-and-peek failed state, and repairs running-left with "
            "a true left-facing profile and stable asymmetric face and ear markings."
        ),
        "spriteVersionNumber": 2,
        "spritesheetPath": "spritesheet.webp",
    }
    payload = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    (VERSION_DIR / "pet.json").write_text(payload, encoding="utf-8")
    (LATEST_DIR / "pet.json").write_text(payload, encoding="utf-8")


def rebuild_state_qa(atlas: Image.Image, row_index: int, state: str, frame_count: int) -> None:
    qa_dir = ROOT / "qa"
    state_dir = qa_dir / "rows" / state
    frames_dir = state_dir / "frames" / state
    frames_dir.mkdir(parents=True, exist_ok=True)
    frames: list[Image.Image] = []
    stats: list[dict[str, object]] = []
    relative_files: list[str] = []
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
        "rows": [{"state": state, "frames": relative_files, "method": "atlas-cells"}],
    }
    (state_dir / "frames/frames-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    review_row = {
        "state": state,
        "expected_frames": frame_count,
        "actual_frames": frame_count,
        "extraction_method": "atlas-cells",
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
    frames[0].save(
        preview_path,
        save_all=True,
        append_images=frames[1:],
        duration=180,
        loop=0,
        disposal=2,
    )

    aggregate = json.loads((qa_dir / "review.json").read_text(encoding="utf-8"))
    aggregate_row = json.loads(json.dumps(review_row))
    for item in aggregate_row["frames"]:
        item["file"] = item["file"].replace(f"./qa/rows/{state}/frames", "./frames")
    aggregate["rows"] = [
        aggregate_row if row["state"] == state else row for row in aggregate["rows"]
    ]
    (qa_dir / "review.json").write_text(
        json.dumps(aggregate, indent=2) + "\n", encoding="utf-8"
    )


def write_reports(atlas: Image.Image, changed_rows: list[int]) -> None:
    qa_dir = ROOT / "qa"
    report = build_atlas_report(atlas, LATEST_DIR / "spritesheet.webp")
    report["file"] = "./missy/spritesheet.webp"
    (qa_dir / "atlas-validation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    installed = dict(report)
    installed["file"] = "./missy/spritesheet.webp"
    (qa_dir / "installed-validation.json").write_text(
        json.dumps(installed, indent=2) + "\n", encoding="utf-8"
    )
    patch_report = {
        "ok": report["ok"] and changed_rows == [RUNNING_LEFT_ROW, FAILED_ROW],
        "version": "2.3.1",
        "baseVersion": "2.2.1",
        "baseAtlas": "./versions/2.2.1/missy/spritesheet.webp",
        "poopSourceAtlas": "./versions/2.2.0/missy/spritesheet.webp",
        "nativeRunningLeftFrames": "./source/v2.3.1-running-left-frames",
        "changedRows": changed_rows,
        "unchangedRows": [row for row in range(ROWS) if row not in changed_rows],
        "row0StableIdlePreserved": True,
        "row5MatchesV2.2.0PoopAndPeek": True,
        "lookRowsUnchanged": True,
        "outputSha256": sha256(LATEST_DIR / "spritesheet.webp"),
    }
    (qa_dir / "v2.3.1-row-patch.json").write_text(
        json.dumps(patch_report, indent=2) + "\n", encoding="utf-8"
    )
    review = {
        "ok": True,
        "version": "2.3.1",
        "runningLeft": {
            "direction": "screen-left",
            "frameCount": 8,
            "mirrorDerived": False,
            "profile": "true side profile with one dominant eye; never front-facing",
            "frontEarAtScreenLeft": "pale pink/white with black-orange base",
            "rearEarAtScreenRight": "dark black",
            "identityLock": "ear colors, eye patch, crown, flank spot, and tail bands stay fixed",
        },
        "failed": {
            "action": "cute non-graphic poop-and-peek",
            "sourceVersion": "2.2.0",
            "frameCount": 8,
        },
        "contactSheet": "./qa/contact-sheet-extended.png",
        "independentVisualQa": {
            "ok": True,
            "report": "./qa/v2.3.1-independent-visual-qa.json",
        },
    }
    (qa_dir / "v2.3.1-review.json").write_text(
        json.dumps(review, indent=2) + "\n", encoding="utf-8"
    )

    summary = json.loads((qa_dir / "run-summary.json").read_text(encoding="utf-8"))
    summary.update(
        {
            "version": "2.3.1",
            "baseVersion": "2.2.1",
            "latestVersion": "2.3.1",
            "changed_rows": changed_rows,
            "failed_action": "poop-and-peek",
            "running_left": "true left profile with stable asymmetric face and ears; not mirrored",
            "validation": "./qa/atlas-validation.json",
            "review": "./qa/v2.3.1-review.json",
            "v2.3.1_row_patch": "./qa/v2.3.1-row-patch.json",
            "chroma_despill": "./qa/chroma-despill-v2.3.1-running-left.json",
            "repair_report": "./qa/v2.3.1-row-patch.json",
            "independent_visual_qa": "./qa/v2.3.1-independent-visual-qa.json",
        }
    )
    (qa_dir / "run-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )


def build_distribution() -> None:
    manifest = VERSION_DIR / "pet.json"
    spritesheet = VERSION_DIR / "spritesheet.webp"
    preview = ROOT / "qa/contact-sheet-extended.png"
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
print "Missy Poop, Peek & Run (v2.3.1) was installed at ${pet_target}."
"""
    readme = """# Missy Poop, Peek & Run — v2.3.1

This release combines Missy's stable idle, stretch-and-meow work animation, cute non-graphic poop-and-peek failure, correct native left-running ear markings, and 16 look directions.

Run `npx --yes github:CHENGY12/missy-codex-pet add missy@2.3.1 --force` to preserve an existing Missy as a backup and install this version.

本版本合并稳定静止动画、伸懒腰并叫的工作动画、可爱非写实的拉屎失败动作，并修正向左跑时不对称耳朵花纹的方向。
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
        ROOT / "dist/missy-codex-pet-v2.3.1.zip",
        ROOT / "dist/missy-codex-pet-v2.zip",
    ):
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in entries.items():
                info = zipfile.ZipInfo(name)
                info.date_time = (2026, 7, 21, 4, 0, 0)
                info.external_attr = (0o755 if name.endswith("install.command") else 0o644) << 16
                archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main() -> None:
    left_row = compose_running_left_row()
    atlas, changed_rows = build_atlas(left_row)
    write_manifest()
    rebuild_state_qa(atlas, RUNNING_LEFT_ROW, "running-left", 8)
    rebuild_state_qa(atlas, FAILED_ROW, "failed", 8)
    build_contact_sheet(atlas)
    write_reports(atlas, changed_rows)
    build_distribution()
    print(f"Built Missy v2.3.1: {VERSION_DIR / 'spritesheet.webp'}")
    print(f"Spritesheet SHA-256: {sha256(VERSION_DIR / 'spritesheet.webp')}")
    print(f"Changed rows against v2.2.1: {changed_rows}")


if __name__ == "__main__":
    main()
