import { fileURLToPath } from "node:url";

export const pets = Object.freeze({
  missy: Object.freeze({
    id: "missy",
    displayName: "Missy",
    manifestPath: fileURLToPath(new URL("../missy/pet.json", import.meta.url)),
    spritesheetPath: fileURLToPath(new URL("../missy/spritesheet.webp", import.meta.url)),
    spritesheetSha256: "ab5dee79010b4ea8703693c7e7dae94da099ae3ca1def21847ceb57abd9d94ba"
  })
});

export function getPet(petId) {
  return pets[petId] ?? null;
}

export function listPets() {
  return Object.values(pets).map(({ id, displayName }) => ({ id, displayName }));
}
