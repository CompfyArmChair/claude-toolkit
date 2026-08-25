import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { needsInstall, npmSpawnConfig, installFailLine } from '../bin/launcher-core.js';

test('needsInstall: true without node_modules, false with it', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'fp-launcher-'));
  assert.equal(needsInstall(dir), true);
  fs.mkdirSync(path.join(dir, 'node_modules'));
  assert.equal(needsInstall(dir), false);
});

test('installFailLine: standard one-JSON-line FAIL with install:<code>', () => {
  assert.deepEqual(JSON.parse(installFailLine('https://x.test/', 3)),
    { verdict: 'FAIL', path: null, url: 'https://x.test/', reasons: ['install:3'] });
  assert.deepEqual(JSON.parse(installFailLine(null, 'ENOENT')),
    { verdict: 'FAIL', path: null, url: null, reasons: ['install:ENOENT'] });
});

test('npmSpawnConfig: shell only on win32 (.cmd cannot spawn shell-less on modern Node)', () => {
  assert.deepEqual(npmSpawnConfig('win32'), { command: 'npm', options: { shell: true } });
  assert.deepEqual(npmSpawnConfig('linux'), { command: 'npm', options: { shell: false } });
  assert.deepEqual(npmSpawnConfig('darwin'), { command: 'npm', options: { shell: false } });
});

test('launcher forwards argv and exit code to index.js (deps present: no install branch)', () => {
  const bin = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'bin', 'fetch-page.js');
  const r = spawnSync(process.execPath, [bin], { encoding: 'utf8' });
  assert.equal(r.status, 1);
  const lines = r.stdout.trim().split('\n');
  assert.equal(lines.length, 1, `stdout must be exactly one JSON line, got: ${JSON.stringify(r.stdout)}`);
  assert.deepEqual(JSON.parse(lines[0]),
    { verdict: 'FAIL', path: null, url: null, reasons: ['invalid-url:missing-argument'] });
});
