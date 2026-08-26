import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const pluginDir = path.resolve(here, '..', '..', 'plugins', 'claude-toolkit');
const toPosix = (p) => p.split(path.sep).join('/');

test('deny-webfetch: unconditional deny whose teaching message is runnable', () => {
  const r = spawnSync(process.execPath, [path.join(pluginDir, 'hooks', 'deny-webfetch.mjs')], {
    input: JSON.stringify({ tool_name: 'WebFetch', tool_input: { url: 'https://example.com/', prompt: 'x' } }),
    encoding: 'utf8',
  });
  assert.equal(r.status, 0);
  const lines = r.stdout.trim().split('\n');
  assert.equal(lines.length, 1, `stdout must be exactly one JSON line, got: ${JSON.stringify(r.stdout)}`);
  const out = JSON.parse(lines[0]).hookSpecificOutput;
  assert.equal(out.hookEventName, 'PreToolUse');
  assert.equal(out.permissionDecision, 'deny');
  const reason = out.permissionDecisionReason;
  const launcher = toPosix(path.join(pluginDir, 'fetch-page', 'bin', 'fetch-page.js'));
  const doctrine = toPosix(path.join(pluginDir, 'hooks', 'web-doctrine.md'));
  assert.ok(reason.includes(`node "${launcher}" <url>`), 'must show the resolved launcher invocation');
  assert.ok(reason.includes(doctrine), 'must point at the doctrine template');
  assert.ok(fs.existsSync(launcher), 'launcher named in the message must exist');
  assert.ok(reason.includes('HELPER'), 'must teach the courier spawn contract');
  assert.ok(reason.includes('subagent_type "claude-toolkit:page-courier"'), 'must teach the namespaced courier id - the bare name silently resolves to general-purpose');
  assert.ok(!reason.includes('subagent_type "page-courier"'), 'bare subagent_type must not be taught');
  assert.ok(!reason.includes('~/.claude') && !reason.includes('C:/Users/marti'), 'no machine-bound paths');
  assert.ok([...reason].every((c) => c.charCodeAt(0) < 128), 'ASCII only');
});
