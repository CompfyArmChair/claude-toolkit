import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { runCli as runScript } from './helpers/run-cli.js';
import { renderFrontmatter } from '../src/deposit.js';

const SCRIPT_PATH = fileURLToPath(new URL('../courier-append.js', import.meta.url));

// `t` is the test's TestContext (M8): registering cleanup here means every
// caller gets it removed at the end of its test for free.
function tmpdir(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'courier-append-test-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return dir;
}

// Every case asserts exactly one stdout line: the CLI's whole interface is
// one JSON line, same invariant as index.js.
function run(t, args) {
  return runScript(SCRIPT_PATH, args, tmpdir(t)).then(({ code, stdout, stderr }) => {
    const lines = stdout.split('\n').filter((l) => l.length > 0);
    assert.equal(lines.length, 1, `stdout must be exactly one JSON line, got: ${JSON.stringify(stdout)}`);
    return { exit: code, json: JSON.parse(lines[0]), stdout, stderr };
  });
}

// Builds a deposit the way index.js does: renderFrontmatter + a body
// containing a raw-text angle-bracket type and a blank line, so the append
// path is exercised against realistic content, not a toy fixture.
function buildDeposit(dir, { tier = 'script' } = {}) {
  const frontmatter = renderFrontmatter({
    url: 'https://example.com/x', finalUrl: 'https://example.com/x',
    fetchedAt: '2026-08-08T12:00:00.000Z', httpStatus: 200, tier,
    title: 'Example', format: 'markdown',
  });
  const body = 'First line of body.\n\nSecond paragraph with a List<string> and a backslash \\ in it.\n';
  const depositPath = path.join(dir, 'deposit.md');
  fs.writeFileSync(depositPath, frontmatter + body, 'utf8');
  return depositPath;
}

test('happy path: tier flips, separator + staging text appended verbatim, staging deleted', async (t) => {
  const dir = tmpdir(t);
  const depositPath = buildDeposit(dir);
  const originalBytes = fs.readFileSync(depositPath);

  const stagingText = 'Line with a backslash \\ and <tags> and non-ASCII: Résumé\nSecond staging line.\n';
  const stagingPath = path.join(dir, 'deposit.md.courier.txt');
  fs.writeFileSync(stagingPath, stagingText, 'utf8');

  const { exit, json } = await run(t, [depositPath, stagingPath]);
  assert.equal(exit, 0);
  assert.equal(json.verdict, 'OK');
  assert.equal(json.path, depositPath);
  assert.equal(typeof json.appendedBytes, 'number');
  assert.equal(typeof json.appendedLines, 'number');
  assert.ok(json.appendedBytes > 0);
  assert.ok(json.appendedLines > 0);
  assert.deepEqual(json.reasons, []);
  // I1: the append is the commit point; staging removal is a best-effort
  // epilogue reported back rather than assumed.
  assert.equal(json.stagingRemoved, true);
  // M11: the deposit is written via tmp-then-rename; no stale .tmp may
  // survive a successful append.
  assert.ok(!fs.existsSync(`${depositPath}.tmp`), 'no .tmp file must survive a successful append');

  const newBytes = fs.readFileSync(depositPath);
  const expectedPrefix = Buffer.from(
    originalBytes.toString('utf8').replace('tier: "script"', 'tier: "courier"'),
    'utf8',
  );
  // The bytes up to the separator must equal the original file with ONLY
  // the tier line changed - compare buffers, not trimmed strings.
  assert.deepEqual(newBytes.subarray(0, expectedPrefix.length), expectedPrefix);

  const newText = newBytes.toString('utf8');
  const afterPrefix = newText.slice(expectedPrefix.length);
  const separatorMatch = afterPrefix.match(
    /^\n<!-- page-courier: content below fetched via Chrome at (\d{4}-\d{2}-\d{2}T[^ ]+) -->\n/,
  );
  assert.ok(separatorMatch, `separator line missing or malformed: ${JSON.stringify(afterPrefix.slice(0, 200))}`);
  assert.ok(!Number.isNaN(Date.parse(separatorMatch[1])), 'separator timestamp must be a valid ISO-8601 date');

  const afterSeparator = afterPrefix.slice(separatorMatch[0].length);
  assert.equal(afterSeparator, stagingText, 'staging text must follow the separator verbatim');

  assert.ok(!fs.existsSync(stagingPath), 'staging file must be deleted after a successful append');
});

test('.pdf deposit: not-a-markdown-deposit, both files untouched', async (t) => {
  const dir = tmpdir(t);
  const depositPath = path.join(dir, 'deposit.pdf');
  const depositBytes = Buffer.from('%PDF-1.4\nraw bytes\n');
  fs.writeFileSync(depositPath, depositBytes);
  const stagingPath = path.join(dir, 'deposit.pdf.courier.txt');
  fs.writeFileSync(stagingPath, 'some staged text\n', 'utf8');

  const { exit, json } = await run(t, [depositPath, stagingPath]);
  assert.equal(exit, 1);
  assert.equal(json.verdict, 'FAIL');
  assert.deepEqual(json.reasons, ['not-a-markdown-deposit']);

  assert.deepEqual(fs.readFileSync(depositPath), depositBytes);
  assert.ok(fs.existsSync(stagingPath), 'staging file must survive a rejected append');
});

test('deposit already tier: courier: no-script-tier, both files unchanged', async (t) => {
  const dir = tmpdir(t);
  const depositPath = buildDeposit(dir, { tier: 'courier' });
  const originalBytes = fs.readFileSync(depositPath);
  const stagingPath = path.join(dir, 'deposit.md.courier.txt');
  const stagingText = 'more staged text\n';
  fs.writeFileSync(stagingPath, stagingText, 'utf8');

  const { exit, json } = await run(t, [depositPath, stagingPath]);
  assert.equal(exit, 1);
  assert.equal(json.verdict, 'FAIL');
  assert.deepEqual(json.reasons, ['no-script-tier']);

  assert.deepEqual(fs.readFileSync(depositPath), originalBytes);
  assert.equal(fs.readFileSync(stagingPath, 'utf8'), stagingText);
});

test('missing staging file: staging-not-found', async (t) => {
  const dir = tmpdir(t);
  const depositPath = buildDeposit(dir);
  const originalBytes = fs.readFileSync(depositPath);
  const stagingPath = path.join(dir, 'does-not-exist.courier.txt');

  const { exit, json } = await run(t, [depositPath, stagingPath]);
  assert.equal(exit, 1);
  assert.equal(json.verdict, 'FAIL');
  assert.deepEqual(json.reasons, ['staging-not-found']);
  assert.deepEqual(fs.readFileSync(depositPath), originalBytes);
});

test('empty (whitespace-only) staging: empty-staging, both files unchanged', async (t) => {
  const dir = tmpdir(t);
  const depositPath = buildDeposit(dir);
  const originalBytes = fs.readFileSync(depositPath);
  const stagingPath = path.join(dir, 'deposit.md.courier.txt');
  fs.writeFileSync(stagingPath, '   \n\t\n  ', 'utf8');

  const { exit, json } = await run(t, [depositPath, stagingPath]);
  assert.equal(exit, 1);
  assert.equal(json.verdict, 'FAIL');
  assert.deepEqual(json.reasons, ['empty-staging']);
  assert.deepEqual(fs.readFileSync(depositPath), originalBytes);
  assert.ok(fs.existsSync(stagingPath));
});

test('no arguments: missing-argument, path null', async (t) => {
  const { exit, json } = await run(t, []);
  assert.equal(exit, 1);
  assert.deepEqual(json, { verdict: 'FAIL', path: null, reasons: ['missing-argument'] });
});
