import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { listPets } from "./catalog.js";
import { addPet } from "./installer.js";

const helpText = `Usage:
  codex-pets add missy [--force]
  codex-pets list

Options:
  --force       Back up a different existing missy folder, then install
  -h, --help    Show this help message
  -v, --version Show the package version

Environment:
  CODEX_HOME    Override the Codex data directory (default: ~/.codex)`;

export async function runCli(args, io = console) {
  const [command, ...rest] = args;

  if (!command || command === "-h" || command === "--help") {
    io.log(helpText);
    return;
  }

  if (command === "-v" || command === "--version") {
    io.log(await packageVersion());
    return;
  }

  if (command === "list") {
    if (rest.length) throw new Error("usage: codex-pets list");
    for (const pet of listPets()) io.log(`${pet.id}\t${pet.displayName}`);
    return;
  }

  if (command === "add") {
    const { petId, force } = parseAddArguments(rest);
    const result = await addPet({ petId, force });
    if (result.changed) {
      io.log(`Installed ${result.displayName} (${result.id})`);
      io.log(result.installPath);
      if (result.backupPath) io.log(`Previous pet backed up to ${result.backupPath}`);
    } else {
      io.log(`${result.displayName} is already installed and up to date.`);
      io.log(result.installPath);
    }
    io.log("Open Codex > Settings > Pets, select Refresh, and choose Missy.");
    return;
  }

  throw new Error(`unknown command "${command}"; run codex-pets --help`);
}

function parseAddArguments(args) {
  const forceArgs = args.filter((argument) => argument === "--force");
  const positional = args.filter((argument) => argument !== "--force");
  if (positional.length !== 1 || forceArgs.length > 1) {
    throw new Error("usage: codex-pets add missy [--force]");
  }
  return { petId: positional[0], force: forceArgs.length === 1 };
}

async function packageVersion() {
  const packagePath = fileURLToPath(new URL("../package.json", import.meta.url));
  const packageJson = JSON.parse(await readFile(packagePath, "utf8"));
  return packageJson.version;
}
