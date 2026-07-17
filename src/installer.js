import { createHash, randomUUID } from "node:crypto";
import { copyFile, mkdir, readFile, rename, rm, stat } from "node:fs/promises";
import { homedir } from "node:os";
import path from "node:path";
import { getPet } from "./catalog.js";

const petSlugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export function normalizePetId(value) {
  const petId = String(value ?? "").trim();
  if (!petSlugPattern.test(petId)) {
    throw new Error("pet id must be a lowercase slug such as missy");
  }
  return petId;
}

export function defaultCodexDirectory(environment = process.env) {
  return environment.CODEX_HOME || path.join(homedir(), ".codex");
}

export async function addPet({
  petId,
  codexDirectory = defaultCodexDirectory(),
  force = false
}) {
  const normalizedPetId = normalizePetId(petId);
  const pet = getPet(normalizedPetId);
  if (!pet) {
    throw new Error(`unknown pet "${normalizedPetId}"; run codex-pets list`);
  }

  await validateSourcePackage(pet);

  const petsDirectory = path.resolve(codexDirectory, "pets");
  const installPath = path.join(petsDirectory, pet.id);
  await mkdir(petsDirectory, { recursive: true });

  if (await pathExists(installPath)) {
    if (await matchesPublishedPet(installPath, pet)) {
      return { ...pet, installPath, changed: false, backupPath: null };
    }
    if (!force) {
      throw new Error(
        `${installPath} already exists and differs from the published Missy package; rerun with --force to preserve it as a backup and install Missy`
      );
    }
  }

  const temporaryPath = path.join(
    petsDirectory,
    `.${pet.id}.install-${process.pid}-${randomUUID().slice(0, 8)}`
  );
  let backupPath = null;

  await mkdir(temporaryPath);
  try {
    await copyFile(pet.manifestPath, path.join(temporaryPath, "pet.json"));
    await copyFile(pet.spritesheetPath, path.join(temporaryPath, "spritesheet.webp"));
    await validateInstalledPackage(temporaryPath, pet);

    if (await pathExists(installPath)) {
      backupPath = await nextBackupPath(petsDirectory, pet.id);
      await rename(installPath, backupPath);
    }

    try {
      await rename(temporaryPath, installPath);
    } catch (error) {
      if (backupPath && !(await pathExists(installPath))) {
        await rename(backupPath, installPath);
        backupPath = null;
      }
      throw error;
    }
  } catch (error) {
    await rm(temporaryPath, { recursive: true, force: true });
    throw error;
  }

  return { ...pet, installPath, changed: true, backupPath };
}

async function validateSourcePackage(pet) {
  await validateManifest(pet.manifestPath, pet.id);
  const digest = await sha256(pet.spritesheetPath);
  if (digest !== pet.spritesheetSha256) {
    throw new Error("bundled Missy spritesheet failed its SHA-256 integrity check");
  }
}

async function validateInstalledPackage(directory, pet) {
  await validateManifest(path.join(directory, "pet.json"), pet.id);
  const digest = await sha256(path.join(directory, "spritesheet.webp"));
  if (digest !== pet.spritesheetSha256) {
    throw new Error("installed Missy spritesheet failed its SHA-256 integrity check");
  }
}

async function validateManifest(manifestPath, expectedPetId) {
  let manifest;
  try {
    manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  } catch {
    throw new Error("Missy pet.json is missing or invalid");
  }

  if (manifest.id !== expectedPetId) {
    throw new Error("Missy pet.json has an unexpected id");
  }
  if (!manifest.displayName || manifest.spritesheetPath !== "spritesheet.webp") {
    throw new Error("Missy pet.json is missing required fields");
  }
  if (manifest.spriteVersionNumber !== 2) {
    throw new Error("Missy pet.json must declare spriteVersionNumber 2");
  }
}

async function matchesPublishedPet(directory, pet) {
  try {
    await validateInstalledPackage(directory, pet);
    return true;
  } catch {
    return false;
  }
}

async function sha256(filePath) {
  const bytes = await readFile(filePath);
  return createHash("sha256").update(bytes).digest("hex");
}

async function pathExists(filePath) {
  try {
    await stat(filePath);
    return true;
  } catch (error) {
    if (error?.code === "ENOENT") return false;
    throw error;
  }
}

async function nextBackupPath(petsDirectory, petId) {
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "");
  let candidate = path.join(petsDirectory, `${petId}.backup-${timestamp}`);
  let suffix = 1;
  while (await pathExists(candidate)) {
    candidate = path.join(petsDirectory, `${petId}.backup-${timestamp}-${suffix}`);
    suffix += 1;
  }
  return candidate;
}
