#!/usr/bin/env node
// Stdlib-only lazy-install launcher (plugin-move spec D4 / section 4.1) -
// the ONLY documented entry point. fetch-page's deps (36 MB, jsdom) are
// neither committed nor bundled; this runs `npm ci` once, on first use.
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { needsInstall, npmSpawnConfig, installFailLine } from './launcher-core.js';

const pkgDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const url = process.argv[2] ?? null;

if (needsInstall(pkgDir)) {
  process.stderr.write('first run: installing fetch-page dependencies...\n');
  const { command, options } = npmSpawnConfig(process.platform);
  // npm's stdout is routed to OUR stderr (fd 2): stdout carries only the
  // one JSON line, even during install.
  const install = spawnSync(command, ['ci'], { cwd: pkgDir, stdio: ['ignore', 2, 2], ...options });
  if (install.status !== 0) {
    const code = install.status ?? install.error?.code ?? install.signal ?? 'unknown';
    process.stdout.write(installFailLine(url, code) + '\n');
    process.exit(1);
  }
}

// Windows has no execvp: spawn index.js with the original argv and forward
// its exit code verbatim.
const run = spawnSync(process.execPath, [path.join(pkgDir, 'index.js'), ...process.argv.slice(2)], { stdio: 'inherit' });
process.exit(run.status ?? 1);
