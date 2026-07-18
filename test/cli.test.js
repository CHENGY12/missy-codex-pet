import assert from "node:assert/strict";
import test from "node:test";
import { runCli } from "../src/cli.js";

function captureOutput() {
  const lines = [];
  return { lines, io: { log: (value) => lines.push(String(value)) } };
}

test("lists Missy", async () => {
  const { lines, io } = captureOutput();
  await runCli(["list"], io);
  assert.deepEqual(lines, ["missy\tMissy\tlatest=2.1.1\tversions=2.0.0,2.1.1"]);
});

test("prints help", async () => {
  const { lines, io } = captureOutput();
  await runCli(["--help"], io);
  assert.match(lines.join("\n"), /codex-pets add missy/);
});

test("rejects unknown commands", async () => {
  await assert.rejects(() => runCli(["nope"]), /unknown command/);
});
