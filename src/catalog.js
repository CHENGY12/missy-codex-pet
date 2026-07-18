import { fileURLToPath } from "node:url";

const missyVersions = Object.freeze({
  "2.0.0": Object.freeze({
    installId: "missy-original-v2-0-0",
    displayName: "Missy Original (v2.0.0)",
    manifestPath: fileURLToPath(
      new URL("../versions/2.0.0/missy/pet.json", import.meta.url)
    ),
    spritesheetPath: fileURLToPath(
      new URL("../versions/2.0.0/missy/spritesheet.webp", import.meta.url)
    ),
    spritesheetSha256: "ab5dee79010b4ea8703693c7e7dae94da099ae3ca1def21847ceb57abd9d94ba"
  }),
  "2.1.1": Object.freeze({
    installId: "missy",
    displayName: "Missy Stretch & Meow (v2.1.1)",
    manifestPath: fileURLToPath(
      new URL("../versions/2.1.1/missy/pet.json", import.meta.url)
    ),
    spritesheetPath: fileURLToPath(
      new URL("../versions/2.1.1/missy/spritesheet.webp", import.meta.url)
    ),
    spritesheetSha256: "3567058c430d4c4da48b2d36d4328f8efcdd8762f9632774f1d92046135f068e"
  })
});

export const pets = Object.freeze({
  missy: Object.freeze({
    id: "missy",
    displayName: "Missy",
    latestVersion: "2.1.1",
    versions: missyVersions
  })
});

export function getPet(petId, version = null) {
  const pet = pets[petId];
  if (!pet) return null;
  const selectedVersion = version || pet.latestVersion;
  const build = pet.versions[selectedVersion];
  if (!build) return null;
  return {
    id: build.installId,
    catalogId: pet.id,
    displayName: build.displayName,
    version: selectedVersion,
    latestVersion: pet.latestVersion,
    ...build
  };
}

export function getPetVersions(petId) {
  const pet = pets[petId];
  return pet ? Object.keys(pet.versions) : [];
}

export function listPets() {
  return Object.values(pets).map(({ id, displayName, latestVersion, versions }) => ({
    id,
    displayName,
    latestVersion,
    versions: Object.keys(versions)
  }));
}
