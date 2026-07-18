import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";
import { mkdtemp } from "node:fs/promises";
import { addPet, normalizePetId } from "../src/installer.js";

test("normalizes valid pet ids and rejects unsafe values", () => {
  assert.equal(normalizePetId(" missy "), "missy");
  assert.throws(() => normalizePetId("../missy"), /lowercase slug/);
  assert.throws(() => normalizePetId("Missy"), /lowercase slug/);
});

test("installs the bundled v2 Missy package", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "missy-install-"));
  const result = await addPet({ petId: "missy", codexDirectory: root });

  assert.equal(result.changed, true);
  const manifest = JSON.parse(await readFile(path.join(result.installPath, "pet.json"), "utf8"));
  assert.equal(manifest.id, "missy");
  assert.equal(manifest.spriteVersionNumber, 2);
  assert.ok((await readFile(path.join(result.installPath, "spritesheet.webp"))).length > 2_000_000);
  assert.equal(result.version, "2.1.1");
  assert.equal(result.displayName, "Missy Stretch & Meow (v2.1.1)");
});

test("installs the preserved Missy v2.0.0 package on request", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "missy-v2-0-"));
  const result = await addPet({
    petId: "missy",
    version: "2.0.0",
    codexDirectory: root
  });

  assert.equal(result.version, "2.0.0");
  assert.equal(result.id, "missy-original-v2-0-0");
  assert.equal(result.displayName, "Missy Original (v2.0.0)");
  assert.equal(result.changed, true);
  assert.ok((await readFile(path.join(result.installPath, "spritesheet.webp"))).length > 2_000_000);
});

test("rejects unknown Missy versions with the available choices", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "missy-version-missing-"));
  await assert.rejects(
    () => addPet({ petId: "missy", version: "9.9.9", codexDirectory: root }),
    /available versions: 2\.0\.0, 2\.1\.1/
  );
});

test("installs the original and latest editions side by side", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "missy-side-by-side-"));
  const original = await addPet({ petId: "missy", version: "2.0.0", codexDirectory: root });
  const latest = await addPet({ petId: "missy", version: "2.1.1", codexDirectory: root });

  assert.notEqual(original.installPath, latest.installPath);
  const originalManifest = JSON.parse(await readFile(path.join(original.installPath, "pet.json"), "utf8"));
  const latestManifest = JSON.parse(await readFile(path.join(latest.installPath, "pet.json"), "utf8"));
  assert.equal(originalManifest.displayName, "Missy Original (v2.0.0)");
  assert.equal(latestManifest.displayName, "Missy Stretch & Meow (v2.1.1)");
});

test("treats the exact published package as already installed", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "missy-current-"));
  await addPet({ petId: "missy", codexDirectory: root });
  const result = await addPet({ petId: "missy", codexDirectory: root });

  assert.equal(result.changed, false);
  assert.equal(result.backupPath, null);
});

test("refuses to overwrite a different existing pet without --force", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "missy-conflict-"));
  const target = path.join(root, "pets", "missy");
  await addPet({ petId: "missy", codexDirectory: root });
  await writeFile(path.join(target, "pet.json"), "{}\n");

  await assert.rejects(
    () => addPet({ petId: "missy", codexDirectory: root }),
    /already exists and differs/
  );
});

test("--force preserves a conflicting install as a backup", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "missy-force-"));
  const target = path.join(root, "pets", "missy");
  await addPet({ petId: "missy", codexDirectory: root });
  await writeFile(path.join(target, "pet.json"), "{\"custom\":true}\n");

  const result = await addPet({ petId: "missy", codexDirectory: root, force: true });

  assert.equal(result.changed, true);
  assert.ok(result.backupPath);
  assert.equal(await readFile(path.join(result.backupPath, "pet.json"), "utf8"), "{\"custom\":true}\n");
  const manifest = JSON.parse(await readFile(path.join(target, "pet.json"), "utf8"));
  assert.equal(manifest.spriteVersionNumber, 2);
});
