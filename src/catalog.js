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
  }),
  "2.1.2": Object.freeze({
    installId: "missy",
    displayName: "Missy Stretch & Meow (v2.1.2)",
    manifestPath: fileURLToPath(
      new URL("../versions/2.1.2/missy/pet.json", import.meta.url)
    ),
    spritesheetPath: fileURLToPath(
      new URL("../versions/2.1.2/missy/spritesheet.webp", import.meta.url)
    ),
    spritesheetSha256: "ab290c365020889bac82ab6b287e0a6d34e31216e94c9a31486a906e08cdbe53"
  }),
  "2.2.0": Object.freeze({
    installId: "missy",
    displayName: "Missy Poop & Peek (v2.2.0)",
    manifestPath: fileURLToPath(
      new URL("../versions/2.2.0/missy/pet.json", import.meta.url)
    ),
    spritesheetPath: fileURLToPath(
      new URL("../versions/2.2.0/missy/spritesheet.webp", import.meta.url)
    ),
    spritesheetSha256: "b56654d8b0001c426dfea6f4834363dc6bfbb12a1132bd6daae957de8172006e"
  }),
  "2.2.1": Object.freeze({
    installId: "missy",
    displayName: "Missy Stretch & Meow (v2.2.1)",
    manifestPath: fileURLToPath(
      new URL("../versions/2.2.1/missy/pet.json", import.meta.url)
    ),
    spritesheetPath: fileURLToPath(
      new URL("../versions/2.2.1/missy/spritesheet.webp", import.meta.url)
    ),
    spritesheetSha256: "96b46f6cedba898630e0900e0c7f34f2a9c2caaef75ad087fd14912cc3c4b342"
  })
});

export const pets = Object.freeze({
  missy: Object.freeze({
    id: "missy",
    displayName: "Missy",
    latestVersion: "2.2.1",
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
