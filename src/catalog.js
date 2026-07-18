import { fileURLToPath } from "node:url";

const missyVersions = Object.freeze({
  "2.0.0": Object.freeze({
    manifestPath: fileURLToPath(
      new URL("../versions/2.0.0/missy/pet.json", import.meta.url)
    ),
    spritesheetPath: fileURLToPath(
      new URL("../versions/2.0.0/missy/spritesheet.webp", import.meta.url)
    ),
    spritesheetSha256: "ab5dee79010b4ea8703693c7e7dae94da099ae3ca1def21847ceb57abd9d94ba"
  }),
  "2.1.0": Object.freeze({
    manifestPath: fileURLToPath(
      new URL("../versions/2.1.0/missy/pet.json", import.meta.url)
    ),
    spritesheetPath: fileURLToPath(
      new URL("../versions/2.1.0/missy/spritesheet.webp", import.meta.url)
    ),
    spritesheetSha256: "f3d28d4f899c06e3fa35e20e52710619291f5e861fe0b950ea4cea01c3dd36a8"
  })
});

export const pets = Object.freeze({
  missy: Object.freeze({
    id: "missy",
    displayName: "Missy",
    latestVersion: "2.1.0",
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
    id: pet.id,
    displayName: pet.displayName,
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
