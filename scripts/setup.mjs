/**
 * One-command dependency bootstrap (task P1-01).
 *
 * Installs the JavaScript workspace dependencies, then the pinned Python
 * tooling from requirements-dev.txt. The only network access is to the package
 * registries the two package managers already use; nothing else is contacted.
 *
 * Usage: npm run setup
 */

import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = dirname(dirname(fileURLToPath(import.meta.url)));

// Windows resolves npm/python through shims, which require a shell. Every
// argument below is a literal defined in this file, never user input.
const needsShell = process.platform === "win32";

function run(command, args) {
  console.log(`\n> ${command} ${args.join(" ")}`);
  const result = spawnSync(command, args, {
    cwd: repoRoot,
    stdio: "inherit",
    shell: needsShell,
  });

  if (result.error) {
    return { ok: false, reason: result.error.message };
  }
  if (result.status !== 0) {
    return { ok: false, reason: `exit code ${result.status}` };
  }
  return { ok: true, reason: "" };
}

function findPython() {
  for (const candidate of ["python", "python3"]) {
    const probe = spawnSync(candidate, ["--version"], { shell: needsShell });
    if (!probe.error && probe.status === 0) {
      return candidate;
    }
  }
  return null;
}

function installPythonTooling() {
  const python = findPython();
  if (python === null) {
    return { ok: false, reason: "no interpreter on PATH (tried python, python3)" };
  }

  const requirements = join(repoRoot, "requirements-dev.txt");
  if (!existsSync(requirements)) {
    return { ok: false, reason: "requirements-dev.txt is missing" };
  }

  return run(python, ["-m", "pip", "install", "-r", "requirements-dev.txt"]);
}

console.log(`Bootstrapping ${repoRoot}`);

const steps = [
  ["JavaScript workspace dependencies", run("npm", ["install"])],
  ["Python tooling", installPythonTooling()],
];

console.log("\nSetup summary:");
let failed = false;
for (const [label, result] of steps) {
  const status = result.ok ? "ok  " : "FAIL";
  const detail = result.ok ? "" : ` (${result.reason})`;
  console.log(`  ${status}  ${label}${detail}`);
  if (!result.ok) {
    failed = true;
  }
}

if (failed) {
  console.error("\nSetup incomplete. Resolve the failures above, then re-run: npm run setup");
  process.exit(1);
}

console.log("\nSetup complete. Run every quality gate with: npm run check");
