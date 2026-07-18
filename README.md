# Missy — Codex Pet v2

Missy is a custom animated calico-cat pet for the Codex desktop app. She is based on Missy's white, orange, and black markings, round body, large upright ears, yellow-green eyes, and thick calico tail. The latest v2.2.0 edition adds a cute, non-graphic poop-and-peek animation when a task fails.

![Missy animation sheet](qa/contact-sheet-extended.png)

## Download

[Download the latest Missy installer](https://github.com/CHENGY12/missy-codex-pet/releases/latest/download/missy-codex-pet-v2.zip)

[Install Missy Poop & Peek directly in Codex](codex://pets/install?name=Missy%20Poop%20%26%20Peek%20(v2.2.0)&imageUrl=https%3A%2F%2Fraw.githubusercontent.com%2FCHENGY12%2Fmissy-codex-pet%2Fmain%2Fmissy%2Fspritesheet.webp&description=Missy%20the%20calico%20cat&spriteVersionNumber=2)

Install from this GitHub repository with `npx`:

```sh
npx --yes github:CHENGY12/missy-codex-pet add missy
```

That command installs the latest version. You can also choose a published pet version explicitly:

```sh
# v2.2.0 — latest; cute failed-state poop-and-peek animation
npx --yes github:CHENGY12/missy-codex-pet add missy@2.2.0

# v2.1.2 — corrected blue working-animation fringe and red left-running whiskers
npx --yes github:CHENGY12/missy-codex-pet add missy@2.1.2

# v2.1.1 — previous Stretch & Meow release
npx --yes github:CHENGY12/missy-codex-pet add missy@2.1.1

# v2.0.0 — Missy Original
npx --yes github:CHENGY12/missy-codex-pet add missy@2.0.0
```

The Original edition uses a distinct pet ID and can remain in Codex beside a newer edition. The v2.1.1, v2.1.2, and v2.2.0 releases share the `missy` ID, so choosing one replaces the other; `--force` preserves the replaced copy as a backup.

Versioned ZIP downloads:

- [Missy Poop & Peek v2.2.0](https://github.com/CHENGY12/missy-codex-pet/releases/download/v2.2.0/missy-codex-pet-v2.zip)
- [Missy Stretch & Meow v2.1.2](https://github.com/CHENGY12/missy-codex-pet/releases/download/v2.1.2/missy-codex-pet-v2.zip)
- [Missy Stretch & Meow v2.1.1](https://github.com/CHENGY12/missy-codex-pet/releases/download/v2.1.1/missy-codex-pet-v2.zip)
- [Missy v2.0.0](https://github.com/CHENGY12/missy-codex-pet/releases/download/v2.0.0/missy-codex-pet-v2.zip)

The public `codex-pets` catalog command will be:

```sh
npx codex-pets add missy
```

The direct-install link requires a Codex version with the custom pet install flow enabled. The ZIP also includes a local macOS installer and bilingual instructions. No API key is required.

The installer refuses to overwrite a different existing `missy` folder. Pass `--force` to preserve the existing folder as a timestamped backup and install the selected version.

## Install from the ZIP

1. Download and unzip `missy-codex-pet-v2.zip`.
2. Double-click `install.command` on macOS.
3. Open Codex and go to **Settings > Pets**.
4. Select **Refresh**, choose **Missy**, and use `/pet` or **Wake Pet** if needed.

Manual installation is also supported: copy the included `missy` folder to `~/.codex/pets/missy`, then refresh **Settings > Pets**.

## Pet format

- Codex pet format: v2
- Atlas: `1536 × 2288` WebP
- Cell size: `192 × 208`
- Layout: 8 columns × 11 rows
- Standard animations: idle, running right, running left, waving, jumping, failed, waiting, working, and review
- Looking directions: 16 clockwise directions at 22.5-degree intervals

## Animation triggers

- `running` is Codex's active-work/loading state. Missy stretches and then visibly meows; the blue-key fringe on her whiskers has been removed.
- `failed` is Codex's task-failure state. In v2.2.0, Missy glances back, raises her tail, squats, leaves a tiny cartoon poop, relaxes, and looks back with an embarrassed expression. The sequence is deliberately cute and non-graphic, with no anatomical detail or body fluids.
- `running-right` and `running-left` are drag movement. In v2.1.2, `running-left` is derived frame by frame from the approved right-facing gait, preserving timing while removing the old purple-red whisker tint.
- The two `look` rows are valid and unchanged from v2.0.0. In the current Codex desktop renderer they respond to the Computer Use cursor event, not ordinary mouse movement, and Codex temporarily disables looking while the pet itself is being dragged. This trigger behavior is controlled by Codex rather than by `pet.json` or the sprite sheet.

## Validation

The published sprite sheet passed:

- deterministic v2 atlas validation
- transparent-edge and chroma-despill validation
- all nine standard animation-row checks
- three isolated blind direction reviews combined by strict majority
- independent final visual QA of all 16 looking directions
- v2.1.2 validation with the correct `#0000FF` chroma key and pixel comparison confirming that only row 2 changed from v2.1.1
- v2.2.0 validation against v2.1.2 confirming that only row 5 changed, so the repaired left-running row and every other standard/look row remain pixel-identical

See [`qa/`](qa/) for the retained reports, contact sheets, direction sheets, frame checks, and animation previews.

## Repository layout

```text
missy/     Install-ready pet.json and spritesheet.webp
versions/  Preserved install-ready v2.0.0 through v2.2.0 packages
bin/       npx command entry point
src/       Safe, atomic installer and bundled pet catalog
test/      Node.js installer and CLI tests
source/    Public generated identity artwork and project specification
scripts/   Reproducible v2.2.0 atlas, QA, preview, and ZIP build
qa/        Validation reports and visual QA artifacts
dist/      Shareable ZIP installer
```

Original reference photographs and local debug artifacts are intentionally excluded from this public repository.

## 中文说明

Missy 是一个适用于 Codex 桌面应用的自定义三花猫动画宠物。v2.2.0 在任务失败时加入了可爱、非写实的“回头—蹲下—留下一个小卡通便便—松气—尴尬回望”动作。安装和使用均不需要 API Key。

可直接下载最新 ZIP，解压后双击 `install.command`，然后在 Codex 的 **Settings > Pets** 中点击 **Refresh** 并选择 **Missy**。也可以手动将 `missy` 文件夹复制到 `~/.codex/pets/missy`。

命令安装默认选择最新的 v2.2.0；也可以使用 `missy@2.2.0`、`missy@2.1.2`、`missy@2.1.1` 或 `missy@2.0.0` 指定版本。v2.2.0 以 v2.1.2 为基线，只替换 `failed` 动画，因此保留向左跑胡须修复和其他所有动作。原始 v2.0.0 使用独立名称和目录，可以与最新版同时显示在 Codex 中。
