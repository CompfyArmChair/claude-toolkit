import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {
  SLUG_MAX_LENGTH, EXCLUDE_ENTRY, deriveSlug, resolveProjectRoot,
  depositDir, createDepositFile, renderFrontmatter, ensureGitExclude,
} from '../src/deposit.js';

// `t` is the test's TestContext (M8): registering cleanup here means every
// caller gets it removed at the end of its test for free.
function tmpdir(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'fetch-page-test-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return dir;
}

test('deriveSlug kebab-cases host+path and strips leading www', () => {
  assert.equal(
    deriveSlug('https://www.reddit.com/r/ClaudeAI/comments/1vim8b7/'),
    'reddit-com-r-claudeai-comments-1vim8b7'
  );
});

test('deriveSlug ignores query and fragment', () => {
  assert.equal(
    deriveSlug('https://example.com/a/b?q=1#frag'),
    'example-com-a-b'
  );
});

test('deriveSlug truncates to SLUG_MAX_LENGTH with no trailing hyphen', () => {
  const slug = deriveSlug('https://example.com/' + 'very-long-segment/'.repeat(10));
  assert.ok(slug.length <= SLUG_MAX_LENGTH);
  assert.ok(!slug.endsWith('-'));
});

test('deriveSlug lowercases mixed-case URLs', () => {
  assert.equal(deriveSlug('https://Example.com/Path/To'), 'example-com-path-to');
});

test('resolveProjectRoot finds nearest ancestor with .git dir', (t) => {
  const root = tmpdir(t);
  fs.mkdirSync(path.join(root, '.git'));
  const nested = path.join(root, 'a', 'b');
  fs.mkdirSync(nested, { recursive: true });
  assert.equal(resolveProjectRoot(nested), root);
});

test('resolveProjectRoot treats a .git FILE (worktree) as a root marker', (t) => {
  const root = tmpdir(t);
  fs.writeFileSync(path.join(root, '.git'), 'gitdir: ../elsewhere/.git/worktrees/x\n');
  assert.equal(resolveProjectRoot(root), root);
});

test('resolveProjectRoot returns startDir when no .git anywhere above', (t) => {
  const dir = tmpdir(t);
  assert.equal(resolveProjectRoot(dir), path.resolve(dir));
});

test('createDepositFile reserves the name at allocation time - no content write needed', (t) => {
  // The property that closes the concurrent-session race: allocation itself
  // must claim the filename. An exists-then-return implementation hands the
  // same path to both callers here.
  const dir = tmpdir(t);
  const first = createDepositFile(dir, '2026-08-08', 'slug', 'md');
  const second = createDepositFile(dir, '2026-08-08', 'slug', 'md');
  assert.notEqual(first, second);
  assert.ok(fs.existsSync(first));
  assert.ok(fs.existsSync(second));
});

test('createDepositFile appends -2, -3 on collision', (t) => {
  const dir = tmpdir(t);
  assert.equal(path.basename(createDepositFile(dir, '2026-08-08', 'slug', 'md')), '2026-08-08-slug.md');
  assert.equal(path.basename(createDepositFile(dir, '2026-08-08', 'slug', 'md')), '2026-08-08-slug-2.md');
  assert.equal(path.basename(createDepositFile(dir, '2026-08-08', 'slug', 'md')), '2026-08-08-slug-3.md');
});

test('renderFrontmatter emits all seven fields, quoting and escaping strings', () => {
  const fm = renderFrontmatter({
    url: 'https://a.com/x', finalUrl: 'https://a.com/y', fetchedAt: '2026-08-08T12:00:00.000Z',
    httpStatus: 200, tier: 'script', title: 'He said "hi": a story', format: 'markdown',
  });
  const lines = fm.split('\n');
  assert.equal(lines[0], '---');
  assert.ok(fm.includes('url: "https://a.com/x"'));
  assert.ok(fm.includes('finalUrl: "https://a.com/y"'));
  assert.ok(fm.includes('fetchedAt: "2026-08-08T12:00:00.000Z"'));
  assert.ok(fm.includes('httpStatus: 200'));
  assert.ok(fm.includes('tier: "script"'));
  assert.ok(fm.includes('title: "He said \\"hi\\": a story"'));
  assert.ok(fm.includes('format: "markdown"'));
  assert.ok(fm.endsWith('---\n'));
});

test('renderFrontmatter collapses embedded CR/LF so page content cannot inject frontmatter lines', () => {
  // A crafted title containing raw newlines must not be able to forge a
  // bare `---` that terminates the frontmatter fence early, nor an extra
  // unquoted key: value line, for a regex or eyeball reader.
  const fm = renderFrontmatter({
    url: 'https://a.com/x', finalUrl: 'https://a.com/y', fetchedAt: '2026-08-08T12:00:00.000Z',
    httpStatus: 200, tier: 'script', title: 'A\n---\nurl: "x"\nB', format: 'markdown',
  });
  const lines = fm.trimEnd().split('\n');
  assert.equal(lines.length, 9, `expected exactly 9 lines (--- + 7 fields + ---), got: ${JSON.stringify(lines)}`);
  assert.equal(lines[0], '---');
  assert.equal(lines[8], '---');
  assert.equal(lines.filter((l) => l.startsWith('title:')).length, 1);
  assert.equal(lines.slice(1, 8).filter((l) => l === '---').length, 0, 'no line between the fences may equal ---');
});

test('ensureGitExclude appends the entry exactly once, and only in git repos', (t) => {
  const nonGit = tmpdir(t);
  assert.equal(ensureGitExclude(nonGit), false);

  const repo = tmpdir(t);
  fs.mkdirSync(path.join(repo, '.git'));
  assert.equal(ensureGitExclude(repo), true);
  assert.equal(ensureGitExclude(repo), false);
  const exclude = fs.readFileSync(path.join(repo, '.git', 'info', 'exclude'), 'utf8');
  const hits = exclude.split(/\r?\n/).filter((l) => l === EXCLUDE_ENTRY);
  assert.equal(hits.length, 1);
});

test('ensureGitExclude resolves worktree .git files to the common dir', (t) => {
  const main = tmpdir(t);
  const worktreeGitDir = path.join(main, '.git', 'worktrees', 'wt');
  fs.mkdirSync(worktreeGitDir, { recursive: true });
  fs.writeFileSync(path.join(worktreeGitDir, 'commondir'), '../..\n');

  const wt = tmpdir(t);
  fs.writeFileSync(path.join(wt, '.git'), `gitdir: ${worktreeGitDir}\n`);

  assert.equal(ensureGitExclude(wt), true);
  const exclude = fs.readFileSync(path.join(main, '.git', 'info', 'exclude'), 'utf8');
  assert.ok(exclude.split(/\r?\n/).includes(EXCLUDE_ENTRY));
});
