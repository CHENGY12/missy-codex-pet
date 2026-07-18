#!/usr/bin/env python3
"""Rigidly register Missy's six idle frames without changing any other atlas row."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ATLAS_SIZE = (1536, 2288)
CELL_SIZE = (192, 208)
IDLE_FRAME_COUNT = 6
NEUTRAL_COLUMN = 6
UNUSED_COLUMN = 7
ROW_COUNT = 11
ALPHA_THRESHOLD = 24
SEARCH_RADIUS = 12
BODY_ROI = (0, 0, 132, 208)
MIN_EDGE_GUARD = 2


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def shifted_array(source: np.ndarray, dx: int) -> np.ndarray:
    shifted = np.zeros_like(source)
    width = source.shape[1]
    if dx >= 0:
        shifted[:, dx:] = source[:, : width - dx]
    else:
        shifted[:, : width + dx] = source[:, -dx:]
    return shifted


def registration_score(reference: np.ndarray, candidate: np.ndarray) -> float:
    x0, y0, x1, y1 = BODY_ROI
    ref = reference[y0:y1, x0:x1]
    cur = candidate[y0:y1, x0:x1]

    ref_mask = (ref[:, :, 3] > ALPHA_THRESHOLD).astype(np.int16)
    cur_mask = (cur[:, :, 3] > ALPHA_THRESHOLD).astype(np.int16)
    alpha_error = float(np.mean(np.abs(ref_mask - cur_mask)))

    ref_rgb = ref[:, :, :3].astype(np.int32) * ref[:, :, 3:4].astype(np.int32) // 255
    cur_rgb = cur[:, :, :3].astype(np.int32) * cur[:, :, 3:4].astype(np.int32) // 255
    rgb_error = float(np.mean(np.abs(ref_rgb - cur_rgb))) / 255.0
    return alpha_error + 0.35 * rgb_error


def best_horizontal_shift(reference: np.ndarray, candidate: np.ndarray) -> tuple[int, float]:
    scored = [
        (registration_score(reference, shifted_array(candidate, dx)), dx)
        for dx in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1)
    ]
    score, dx = min(scored, key=lambda item: (item[0], abs(item[1]), item[1]))
    return dx, score


def alpha_bbox(array: np.ndarray) -> list[int] | None:
    ys, xs = np.nonzero(array[:, :, 3] > 0)
    if not len(xs):
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def common_guard_offset(frames: list[np.ndarray], relative_shifts: list[int]) -> int:
    lower = -10_000
    upper = 10_000
    width = CELL_SIZE[0]
    for frame, relative_shift in zip(frames, relative_shifts, strict=True):
        bbox = alpha_bbox(frame)
        if bbox is None:
            continue
        left, _, right, _ = bbox
        lower = max(lower, MIN_EDGE_GUARD - left - relative_shift)
        upper = min(upper, width - MIN_EDGE_GUARD - right - relative_shift)
    if lower > upper:
        raise SystemExit("idle frames cannot be registered without clipping")
    if lower <= 0 <= upper:
        return 0
    return lower if abs(lower) < abs(upper) else upper


def visible_blue_pixels(array: np.ndarray) -> int:
    rgb = array[:, :, :3].astype(np.int16)
    alpha = array[:, :, 3]
    return int(
        np.count_nonzero(
            (alpha > 0)
            & (rgb[:, :, 2] > rgb[:, :, 0] + 20)
            & (rgb[:, :, 2] > rgb[:, :, 1] + 20)
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-atlas", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--png-output")
    parser.add_argument("--frames-dir")
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args()

    input_path = Path(args.input_atlas).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    png_path = Path(args.png_output).expanduser().resolve() if args.png_output else None
    frames_dir = Path(args.frames_dir).expanduser().resolve() if args.frames_dir else None
    report_path = Path(args.json_out).expanduser().resolve()

    with Image.open(input_path) as opened:
        atlas = opened.convert("RGBA")
    if atlas.size != ATLAS_SIZE:
        raise SystemExit(f"expected {ATLAS_SIZE[0]}x{ATLAS_SIZE[1]} atlas, got {atlas.size}")

    width, height = CELL_SIZE
    frames = [
        np.asarray(atlas.crop((column * width, 0, (column + 1) * width, height))).copy()
        for column in range(IDLE_FRAME_COUNT)
    ]
    reference = frames[0]
    registrations = [best_horizontal_shift(reference, frame) for frame in frames]
    relative_shifts = [dx for dx, _ in registrations]
    guard_offset = common_guard_offset(frames, relative_shifts)
    applied_shifts = [dx + guard_offset for dx in relative_shifts]
    stabilized = [
        shifted_array(frame, dx) for frame, dx in zip(frames, applied_shifts, strict=True)
    ]

    residual_shifts = [best_horizontal_shift(stabilized[0], frame)[0] for frame in stabilized]
    before_bboxes = [alpha_bbox(frame) for frame in frames]
    after_bboxes = [alpha_bbox(frame) for frame in stabilized]
    clipped = any(
        bbox is not None
        and (bbox[0] < MIN_EDGE_GUARD or bbox[2] > width - MIN_EDGE_GUARD)
        for bbox in after_bboxes
    )

    result = atlas.copy()
    for column, frame in enumerate(stabilized):
        result.paste(Image.fromarray(frame, "RGBA"), (column * width, 0))
    result.paste(Image.fromarray(stabilized[0], "RGBA"), (NEUTRAL_COLUMN * width, 0))
    result.paste(Image.new("RGBA", CELL_SIZE, (0, 0, 0, 0)), (UNUSED_COLUMN * width, 0))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path, format="WEBP", lossless=True, quality=100, method=6, exact=True)
    if png_path:
        png_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(png_path)
    if frames_dir:
        frames_dir.mkdir(parents=True, exist_ok=True)
        for index, frame in enumerate(stabilized):
            Image.fromarray(frame, "RGBA").save(frames_dir / f"{index:02d}.png")

    with Image.open(output_path) as opened:
        decoded = opened.convert("RGBA")
    changed_rows: list[int] = []
    unchanged_rows: list[int] = []
    for row in range(ROW_COUNT):
        box = (0, row * height, ATLAS_SIZE[0], (row + 1) * height)
        target = changed_rows if decoded.crop(box).tobytes() != atlas.crop(box).tobytes() else unchanged_rows
        target.append(row)

    output_frames = [np.asarray(decoded.crop((i * width, 0, (i + 1) * width, height))) for i in range(6)]
    report = {
        "ok": changed_rows == [0] and not clipped and all(dx == 0 for dx in residual_shifts),
        "input_atlas": str(input_path),
        "output_atlas": str(output_path),
        "input_sha256": sha256(input_path),
        "output_sha256": sha256(output_path),
        "method": "integer-only rigid horizontal registration; no resampling or recoloring",
        "body_registration_roi": list(BODY_ROI),
        "relative_shifts": relative_shifts,
        "common_guard_offset": guard_offset,
        "applied_shifts": applied_shifts,
        "residual_shifts": residual_shifts,
        "registration_scores": [round(score, 8) for _, score in registrations],
        "before_alpha_bboxes": before_bboxes,
        "after_alpha_bboxes": after_bboxes,
        "edge_guard_pixels": MIN_EDGE_GUARD,
        "clipped": clipped,
        "changed_rows": changed_rows,
        "unchanged_rows": unchanged_rows,
        "other_rows_unchanged": unchanged_rows == list(range(1, ROW_COUNT)),
        "visible_blue_pixels_per_idle_frame": [visible_blue_pixels(frame) for frame in output_frames],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
