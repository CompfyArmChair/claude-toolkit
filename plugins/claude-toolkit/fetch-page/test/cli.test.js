import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { runCli as runScript } from './helpers/run-cli.js';

// Spawned as `node <package-dir>` - the folder-entry form every consumer
// uses - so package.json main-field resolution stays covered on every run.
const CLI_DIR = path.resolve(fileURLToPath(new URL('..', import.meta.url)));

const ARTICLE_SENTINEL = 'Deterministic pipelines beat vibes.';
const ARTICLE_HTML = `<!doctype html>
<html><head><title>Generic Article</title></head><body>
<nav><a href="/">Home</a> <a href="/about">About</a></nav>
<article>
<h1>Generic Article</h1>
<p>${'Plain readable article text. '.repeat(10)}</p>
<p>${ARTICLE_SENTINEL} See <a href="/next-page">the next page</a> for more.</p>
<p>${'More plain readable article text. '.repeat(10)}</p>
</article>
</body></html>`;

const PLAIN_TEXT = 'export type Shape = Record<string, number>; // List<string> survives raw\n'.repeat(5);

// Legacy-charset fixtures (Important I1): a real accented French sentence,
// long enough to clear the thin-content threshold once decoded correctly.
const LATIN1_TITLE = 'Café';
const LATIN1_PARAGRAPH = 'Résumé naïve coût élève. '.repeat(10);
const LATIN1_HTML = `<!doctype html>
<html><head><title>${LATIN1_TITLE}</title></head><body>
<article><h1>${LATIN1_TITLE}</h1><p>${LATIN1_PARAGRAPH}</p></article>
</body></html>`;
const META_CHARSET_HTML = `<!doctype html>
<html><head><meta charset="iso-8859-1"><title>${LATIN1_TITLE}</title></head><body>
<article><h1>${LATIN1_TITLE}</h1><p>${LATIN1_PARAGRAPH}</p></article>
</body></html>`;

const PNG_HEADER_BYTES = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00, 0x00, 0x0d]);

let server;
let base;

before(async () => {
  server = http.createServer((req, res) => {
    switch (req.url) {
      case '/article':
        res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
        return res.end(ARTICLE_HTML);
      case '/redirect':
        res.writeHead(302, { location: '/article' });
        return res.end();
      case '/thin':
        res.writeHead(200, { 'content-type': 'text/html' });
        return res.end('<html><head><title>Thin</title></head><body><p>tiny</p></body></html>');
      case '/blocked':
        res.writeHead(403, { 'content-type': 'text/html' });
        return res.end('<html><head><title>Blocked</title></head><body>no</body></html>');
      case '/plain.txt':
        res.writeHead(200, { 'content-type': 'text/plain' });
        return res.end(PLAIN_TEXT);
      case '/doc.pdf':
        res.writeHead(200, { 'content-type': 'application/pdf' });
        return res.end(Buffer.from('%PDF-1.4\n%fetch-page-test-fixture\n'));
      case '/latin1.html':
        res.writeHead(200, { 'content-type': 'text/html; charset=iso-8859-1' });
        return res.end(Buffer.from(LATIN1_HTML, 'latin1'));
      case '/meta-charset.html':
        res.writeHead(200, { 'content-type': 'text/html' });
        return res.end(Buffer.from(META_CHARSET_HTML, 'latin1'));
      case '/image.png':
        res.writeHead(200, { 'content-type': 'image/png' });
        return res.end(PNG_HEADER_BYTES);
      default:
        res.writeHead(404, { 'content-type': 'text/html' });
        return res.end('<html><body>not found</body></html>');
    }
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  base = `http://127.0.0.1:${server.address().port}`;
});

after(() => {
  server.closeAllConnections?.();
  server.close();
});

// Every invocation runs in a fresh non-git tmp dir, so project root = cwd
// and deposits are isolated per test. `t` is the test's TestContext (M8):
// registering cleanup here means every caller gets it for free.
function runCli(t, args) {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), 'fetch-page-cli-'));
  t.after(() => fs.rmSync(cwd, { recursive: true, force: true }));
  return run(cwd, args).then((result) => ({ cwd, ...result }));
}

// Layers the "exactly one JSON line" assertion and parsing on top of the
// shared low-level spawn helper (test/helpers/run-cli.js), which just runs
// the child process and hands back the raw result.
function run(cwd, args) {
  return runScript(CLI_DIR, args, cwd).then(({ code, stdout, stderr }) => {
    const lines = stdout.split('\n').filter((l) => l.length > 0);
    assert.equal(lines.length, 1, `stdout must be exactly one JSON line, got: ${JSON.stringify(stdout)}`);
    return { exit: code, json: JSON.parse(lines[0]), stdout, stderr };
  });
}

test('generic HTML article: OK, markdown deposit under cwd, absolute links, no content on stdout', async (t) => {
  const { cwd, exit, json, stdout, stderr } = await runCli(t, [`${base}/article`]);
  assert.equal(json.verdict, 'OK');
  assert.equal(exit, 0);
  assert.equal(json.format, 'markdown');
  assert.ok(!stdout.includes(ARTICLE_SENTINEL), 'page content leaked to stdout');
  assert.equal(stderr, '', `a successful fetch must produce no stderr output, got: ${stderr}`);
  assert.equal(path.dirname(fs.realpathSync(json.path)), path.join(fs.realpathSync(cwd), '.claude', 'web-deposits'));
  const deposit = fs.readFileSync(json.path, 'utf8');
  assert.ok(deposit.startsWith('---\n'), 'frontmatter missing');
  assert.ok(deposit.includes('tier: "script"'));
  assert.ok(deposit.includes(ARTICLE_SENTINEL));
  assert.ok(deposit.includes(`](${base}/next-page)`), 'content links must be absolute');
  // M1: lines counts newlines (the wc -l convention), same as
  // courier-append.js's appendedLines - not split('\n').length, which is
  // one high because the deposit always ends with a trailing newline.
  const newlineCount = deposit.split('\n').length - 1;
  assert.equal(json.lines, newlineCount, 'lines must count newlines, matching courier-append.js\'s convention');
  assert.ok(json.helper.endsWith('/courier-append.js'), `helper must point at courier-append.js: ${json.helper}`);
  assert.ok(!json.helper.includes('\\'), 'helper must use forward slashes');
  assert.ok(fs.existsSync(json.helper), 'helper must exist on disk');
});

test('redirect: finalUrl records the destination', async (t) => {
  const { json } = await runCli(t, [`${base}/redirect`]);
  assert.equal(json.verdict, 'OK');
  assert.equal(json.finalUrl, `${base}/article`);
});

test('thin page: ESCALATE, exit 2, stub carries the marker blockquote', async (t) => {
  const { exit, json } = await runCli(t, [`${base}/thin`]);
  assert.equal(json.verdict, 'ESCALATE');
  assert.equal(exit, 2);
  assert.ok(json.reasons.some((r) => r.startsWith('thin-content:')));
  const deposit = fs.readFileSync(json.path, 'utf8');
  assert.ok(deposit.includes('> fetch-page verdict: ESCALATE'));
  assert.ok(deposit.includes('tiny'), 'ESCALATE stub must retain the thin text that was extracted (M4)');
  assert.ok(json.helper.endsWith('/courier-append.js'), `helper must point at courier-append.js: ${json.helper}`);
  assert.ok(!json.helper.includes('\\'), 'helper must use forward slashes');
  assert.ok(fs.existsSync(json.helper), 'helper must exist on disk');
});

test('HTTP 403: ESCALATE with http-403 among the reasons', async (t) => {
  const { exit, json } = await runCli(t, [`${base}/blocked`]);
  assert.equal(json.verdict, 'ESCALATE');
  assert.equal(exit, 2);
  assert.ok(json.reasons.includes('http-403'));
});

test('text/plain: verbatim text deposit, angle brackets survive', async (t) => {
  const { exit, json } = await runCli(t, [`${base}/plain.txt`]);
  assert.equal(json.verdict, 'OK');
  assert.equal(exit, 0);
  assert.equal(json.format, 'text');
  const deposit = fs.readFileSync(json.path, 'utf8');
  assert.ok(deposit.includes('format: "text"'));
  assert.ok(deposit.includes('Record<string, number>'), 'angle-bracket content was eaten');
});

test('pdf: raw-bytes passthrough to a .pdf deposit', async (t) => {
  const { exit, json } = await runCli(t, [`${base}/doc.pdf`]);
  assert.equal(json.verdict, 'OK');
  assert.equal(exit, 0);
  assert.equal(json.format, 'pdf');
  assert.equal(json.lines, 0);
  assert.ok(json.path.endsWith('.pdf'));
  assert.equal(fs.readFileSync(json.path).subarray(0, 4).toString(), '%PDF');
  assert.ok(json.helper.endsWith('/courier-append.js'), `helper must point at courier-append.js: ${json.helper}`);
  assert.ok(!json.helper.includes('\\'), 'helper must use forward slashes');
  assert.ok(fs.existsSync(json.helper), 'helper must exist on disk');
});

test('charset=iso-8859-1 header: accented characters survive, no U+FFFD', async (t) => {
  const { exit, json } = await runCli(t, [`${base}/latin1.html`]);
  assert.equal(exit, 0);
  assert.equal(json.verdict, 'OK');
  assert.equal(json.title, LATIN1_TITLE);
  const deposit = fs.readFileSync(json.path, 'utf8');
  assert.ok(deposit.includes('Résumé naïve coût élève'), 'accented text was not decoded correctly');
  assert.ok(!deposit.includes('�'), 'a legacy-encoded page must not be replaced with U+FFFD');
});

test('meta charset sniff (no charset in Content-Type header): accented characters survive', async (t) => {
  const { exit, json } = await runCli(t, [`${base}/meta-charset.html`]);
  assert.equal(exit, 0);
  assert.equal(json.verdict, 'OK');
  assert.equal(json.title, LATIN1_TITLE);
  const deposit = fs.readFileSync(json.path, 'utf8');
  assert.ok(deposit.includes('Résumé naïve coût élève'), 'accented text was not decoded correctly');
  assert.ok(!deposit.includes('�'), 'a legacy-encoded page must not be replaced with U+FFFD');
});

test('unsupported content type (image/png): honest FAIL, no deposit dir/file created', async (t) => {
  const { cwd, exit, json } = await runCli(t, [`${base}/image.png`]);
  assert.equal(exit, 1);
  assert.equal(json.verdict, 'FAIL');
  assert.equal(json.path, null);
  assert.deepEqual(json.reasons, ['unsupported-content-type:image/png']);
  assert.ok(!fs.existsSync(path.join(cwd, '.claude', 'web-deposits')), 'no deposit directory should be created');
});

test('missing argument: structured FAIL, exit 1 (also proves folder-entry resolution)', async (t) => {
  const { exit, json } = await runCli(t, []);
  assert.equal(exit, 1);
  assert.deepEqual(json, { verdict: 'FAIL', path: null, url: null, reasons: ['invalid-url:missing-argument'] });
});

test('deposit-side filesystem failure: structured FAIL, one line, exit 1', async (t) => {
  // .claude occupied by a FILE makes mkdir of the deposit dir throw - the
  // portable stand-in for permission/disk errors on the deposit path.
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), 'fetch-page-cli-'));
  t.after(() => fs.rmSync(cwd, { recursive: true, force: true }));
  fs.writeFileSync(path.join(cwd, '.claude'), 'a file where the deposit dir must go');
  const { exit, json } = await run(cwd, [`${base}/article`]);
  assert.equal(json.verdict, 'FAIL');
  assert.equal(exit, 1);
  assert.equal(json.path, null);
  assert.ok(json.reasons[0].startsWith('deposit:'), json.reasons[0]);
});

test('git-exclude bookkeeping failure: deposit still written, verdict unaffected, reason surfaced (M2)', async (t) => {
  // A .git directory whose info/ path is occupied by a FILE makes
  // ensureGitExclude's mkdirSync throw - the portable stand-in for a
  // read-only .git or an unwritable commondir. The primary artifact (the
  // deposit) must land regardless: git bookkeeping is a convenience, not
  // the deposit itself.
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), 'fetch-page-cli-'));
  t.after(() => fs.rmSync(cwd, { recursive: true, force: true }));
  fs.mkdirSync(path.join(cwd, '.git'));
  fs.writeFileSync(path.join(cwd, '.git', 'info'), 'blocking file');
  const { exit, json } = await run(cwd, [`${base}/article`]);
  assert.equal(json.verdict, 'OK');
  assert.equal(exit, 0);
  assert.ok(json.path && fs.existsSync(json.path), 'deposit must still be written');
  assert.ok(json.reasons.includes('git-exclude-failed'));
});

test('invalid URL (not a URL at all): structured FAIL, reasons ["invalid-url"] (M3)', async (t) => {
  const { exit, json } = await runCli(t, ['not a url']);
  assert.equal(exit, 1);
  assert.deepEqual(json.reasons, ['invalid-url']);
  assert.equal('helper' in json, false, 'FAIL (path null) must not carry helper');
});

test('invalid URL (non-http(s) scheme): structured FAIL, reasons ["invalid-url"] (M3)', async (t) => {
  const { exit, json } = await runCli(t, ['ftp://example.com/x']);
  assert.equal(exit, 1);
  assert.deepEqual(json.reasons, ['invalid-url']);
});

test('network error (closed port, offline and deterministic): FAIL, reasons[0] starts with "network:" (M3)', async (t) => {
  const { exit, json } = await runCli(t, ['http://127.0.0.1:49999/x']);
  assert.equal(exit, 1);
  assert.equal(json.verdict, 'FAIL');
  assert.ok(json.reasons[0].startsWith('network:'), json.reasons[0]);
});
