import { test } from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const pluginDir = path.resolve(here, '..', '..', 'plugins', 'claude-toolkit');
const toPosix = (p) => p.split(path.sep).join('/');

test('inject-web-doctrine: SessionStart additionalContext fully rendered', () => {
  const r = spawnSync(process.execPath, [path.join(pluginDir, 'hooks', 'inject-web-doctrine.mjs')], {
    input: '{}',
    encoding: 'utf8',
  });
  assert.equal(r.status, 0);
  const lines = r.stdout.trim().split('\n');
  assert.equal(lines.length, 1, 'exactly one JSON line');
  const out = JSON.parse(lines[0]).hookSpecificOutput;
  assert.equal(out.hookEventName, 'SessionStart');
  const ctx = out.additionalContext;
  const launcher = toPosix(path.join(pluginDir, 'fetch-page', 'bin', 'fetch-page.js'));
  assert.ok(ctx.includes(`node "${launcher}" <url>`), 'rendered launcher invocation present');
  assert.ok(!ctx.includes('{{'), 'no unrendered placeholders');
  assert.ok(ctx.includes('https://github.com/CompfyArmChair/claude-toolkit/blob/master/docs/superpowers/specs/2026-08-08-webfetch-ban-raw-fetch-pipeline-design.md'), 'spec pointer rendered');
  assert.ok(ctx.includes('`claude-toolkit:page-courier`'), 'doctrine must teach the namespaced courier id');
  assert.ok(ctx.includes('HELPER'), 'courier spawn contract present');
  assert.ok(!ctx.includes('~/.claude') && !ctx.includes('C:/Users/marti'), 'no machine-bound paths');
});
