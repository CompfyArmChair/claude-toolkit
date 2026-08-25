// Pure parts of the lazy-install launcher, extracted for unit testing
// (plugin-move spec section 5). Stdlib-only: this module loads before any
// npm install has ever run.
import fs from 'node:fs';
import path from 'node:path';

export function needsInstall(pkgDir) {
  return !fs.existsSync(path.join(pkgDir, 'node_modules'));
}

// Node >= 18.20 / 20.12 refuses to spawn .cmd files without a shell
// (CVE-2024-27980 hardening) - on Windows the shell resolves `npm` to
// npm.cmd via PATH; POSIX spawns the npm binary directly.
export function npmSpawnConfig(platform) {
  return { command: 'npm', options: { shell: platform === 'win32' } };
}

// The one-JSON-line stdout contract holds even before install: same FAIL
// shape as index.js, reason install:<code>.
export function installFailLine(url, code) {
  return JSON.stringify({ verdict: 'FAIL', path: null, url: url ?? null, reasons: [`install:${code}`] });
}
