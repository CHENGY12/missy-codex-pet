# Missy — Codex Pet v2

Missy is a custom animated calico-cat pet for the Codex desktop app. She is based on Missy's white, orange, and black markings, round body, large upright ears, yellow-green eyes, and thick calico tail.

![Missy animation sheet](qa/contact-sheet-extended.png)

## Download

[Download the latest Missy installer](https://github.com/CHENGY12/missy-codex-pet/releases/latest/download/missy-codex-pet-v2.zip)

[Install Missy directly in Codex](codex://pets/install?name=Missy&imageUrl=https%3A%2F%2Fraw.githubusercontent.com%2FCHENGY12%2Fmissy-codex-pet%2Fmain%2Fmissy%2Fspritesheet.webp&description=Missy%20the%20calico%20cat&spriteVersionNumber=2)

Install from this GitHub repository with `npx`:

```sh
npx --yes github:CHENGY12/missy-codex-pet add missy
```

That command installs the latest version. You can also choose either published pet version explicitly:

```sh
# v2.1.0 — stretch and meow while Codex is working
npx --yes github:CHENGY12/missy-codex-pet add missy@2.1.0

# v2.0.0 — original working animation
npx --yes github:CHENGY12/missy-codex-pet add missy@2.0.0
```

If another Missy version is already installed, append `--force`. The installer first preserves the current folder as a timestamped backup, then switches versions.

Versioned ZIP downloads:

- [Missy v2.1.0](https://github.com/CHENGY12/missy-codex-pet/releases/download/v2.1.0/missy-codex-pet-v2.zip)
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

- `running` is Codex's active-work/loading state. In v2.1.0, Missy stretches and then visibly meows.
- `running-right` and `running-left` are drag movement and were not changed.
- The two `look` rows are valid and unchanged from v2.0.0. In the current Codex desktop renderer they respond to the Computer Use cursor event, not ordinary mouse movement, and Codex temporarily disables looking while the pet itself is being dragged. This trigger behavior is controlled by Codex rather than by `pet.json` or the sprite sheet.

## Validation

The published sprite sheet passed:

- deterministic v2 atlas validation
- transparent-edge and chroma-despill validation
- all nine standard animation-row checks
- three isolated blind direction reviews combined by strict majority
- independent final visual QA of all 16 looking directions
- v2.1.0 pixel comparison confirming that only row 7 changed and both look rows remained identical

See [`qa/`](qa/) for the retained reports, contact sheets, direction sheets, frame checks, and animation previews.

## Repository layout

```text
missy/     Install-ready pet.json and spritesheet.webp
versions/  Preserved install-ready v2.0.0 and v2.1.0 packages
bin/       npx command entry point
src/       Safe, atomic installer and bundled pet catalog
test/      Node.js installer and CLI tests
source/    Public generated identity artwork and project specification
qa/        Validation reports and visual QA artifacts
dist/      Shareable ZIP installer
```

Original reference photographs and local debug artifacts are intentionally excluded from this public repository.

## 中文说明

Missy 是一个适用于 Codex 桌面应用的自定义三花猫动画宠物。安装和使用均不需要 API Key。

可直接下载最新 ZIP，解压后双击 `install.command`，然后在 Codex 的 **Settings > Pets** 中点击 **Refresh** 并选择 **Missy**。也可以手动将 `missy` 文件夹复制到 `~/.codex/pets/missy`。

命令安装默认选择最新的 v2.1.0；也可以使用 `missy@2.1.0` 或 `missy@2.0.0` 指定版本。切换已有版本时加上 `--force`，安装器会先自动备份当前 Missy。
