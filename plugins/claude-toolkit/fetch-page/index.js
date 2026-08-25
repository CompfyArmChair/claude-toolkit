#!/usr/bin/env node
import fs from 'node:fs';
import { fetchUrl } from './src/fetch.js';
import { extractReadable } from './src/extract.js';
import { classify } from './src/verdict.js';
import {
  deriveSlug, resolveProjectRoot, depositDir, createDepositFile,
  renderFrontmatter, ensureGitExclude,
} from './src/deposit.js';

const EXIT = { OK: 0, FAIL: 1, ESCALATE: 2 };

// The single stdout line is the entire interface; page content never
// appears on stdout under any verdict (spec section 4.2). Set exitCode and
// let the event loop drain naturally instead of calling process.exit():
// calling process.exit() immediately after a fetch() made with
// AbortSignal.timeout() can trip a libuv assertion on Windows
// (Assertion failed: !(handle->flags & UV_HANDLE_CLOSING)) if the timer
// handle hasn't settled yet.
function emit(result, code) {
  process.stdout.write(JSON.stringify(result) + '\n');
  process.exitCode = code;
}

function fail(url, reason) {
  emit({ verdict: 'FAIL', path: null, url, reasons: [reason] }, EXIT.FAIL);
}

// ONLY the filesystem calls that actually produce the deposit live in this
// try (mkdirSync, createDepositFile, writeFileSync): project-root
// resolution, slug derivation, extraction, classification and frontmatter
// rendering all ran before this is called, so a real extraction bug can
// never be mislabelled as a filesystem error. A permissions error, a full
// disk, or .claude occupied by a file all converge on the same one-JSON-line
// deposit:<code> FAIL (spec section 5). ensureGitExclude is bookkeeping, not
// the deposit itself, so it is carved out as best-effort (M2): its failure
// is reported to buildResult as `excludeFailed` rather than vetoing the
// write - the deposit still lands even if the .git/info/exclude entry does
// not.
function writeDepositAndEmit(location, content, url, buildResult) {
  const { dir, projectRoot, date, slug, ext } = location;
  let depositPath;
  let excludeFailed = false;
  try {
    fs.mkdirSync(dir, { recursive: true });
    try { ensureGitExclude(projectRoot); } catch { excludeFailed = true; }
    depositPath = createDepositFile(dir, date, slug, ext);
    fs.writeFileSync(depositPath, content);
  } catch (err) {
    if (depositPath) {
      // createDepositFile already reserved the path before writeFileSync
      // failed - remove the empty reservation best-effort so a failed
      // write never leaves an orphan deposit behind. A second failure here
      // must not mask the original error.
      try { fs.rmSync(depositPath, { force: true }); } catch { /* best-effort */ }
    }
    return fail(url, `deposit:${err.code ?? err.name}`);
  }
  const result = buildResult(depositPath, excludeFailed);
  return emit(result, EXIT[result.verdict]);
}

async function main() {
  const rawUrl = process.argv[2];
  if (!rawUrl) return fail(null, 'invalid-url:missing-argument');

  let url;
  try {
    url = new URL(rawUrl);
    if (url.protocol !== 'http:' && url.protocol !== 'https:') throw new Error('not http(s)');
  } catch {
    return fail(rawUrl, 'invalid-url');
  }

  let response;
  try {
    response = await fetchUrl(url.href);
  } catch (err) {
    return fail(url.href, err.name === 'TimeoutError' ? 'timeout' : `network:${err.cause?.code ?? err.name}`);
  }

  // A content type we cannot deposit meaningfully fails honestly before any
  // deposit-side work - no directory, no file. Silently decoding a binary
  // as text would deposit a wall of U+FFFD under verdict OK instead.
  if (response.body.kind === 'unsupported') {
    return fail(url.href, `unsupported-content-type:${response.body.mediaType}`);
  }

  const projectRoot = resolveProjectRoot(process.cwd());
  const dir = depositDir(projectRoot);
  const fetchedAt = new Date().toISOString();
  const date = fetchedAt.slice(0, 10);
  const slug = deriveSlug(response.finalUrl || url.href);

  if (response.body.kind === 'pdf') {
    return writeDepositAndEmit({ dir, projectRoot, date, slug, ext: 'pdf' }, response.body.bytes, url.href,
      (depositPath, excludeFailed) => ({
        verdict: 'OK', path: depositPath, url: url.href, finalUrl: response.finalUrl,
        status: response.status, title: '', bytes: response.body.bytes.length, lines: 0,
        format: 'pdf', reasons: excludeFailed ? ['git-exclude-failed'] : [],
      }));
  }

  // text bypasses Defuddle: non-HTML text is already in its final readable
  // form, and HTML-parsing raw source would corrupt it.
  const extracted = response.body.kind === 'html'
    ? { ...(await extractReadable(response.body.text, response.finalUrl || url.href)), format: 'markdown' }
    : { markdown: response.body.text, title: '', format: 'text', error: null };
  const { verdict, reasons } = classify({
    httpStatus: response.status, title: extracted.title, markdown: extracted.markdown,
  });
  // A real extraction bug must never be indistinguishable from a bot
  // wall: classify() already routes an extraction failure to ESCALATE via
  // thin-content (empty markdown), so this only adds a diagnostic entry -
  // the verdict itself is unchanged.
  if (extracted.error) reasons.push(`extract-error:${extracted.error.name}`);

  const frontmatter = renderFrontmatter({
    url: url.href, finalUrl: response.finalUrl, fetchedAt,
    httpStatus: response.status, tier: 'script', title: extracted.title, format: extracted.format,
  });
  const stubNote = verdict === 'ESCALATE'
    ? `> fetch-page verdict: ESCALATE (${reasons.join(', ')}). The tier-1 extraction below is suspected shell/blocked output. Courier content, if any, is appended after it.\n\n`
    : '';
  const contents = frontmatter + stubNote + extracted.markdown + '\n';

  return writeDepositAndEmit({ dir, projectRoot, date, slug, ext: 'md' }, contents, url.href,
    (depositPath, excludeFailed) => ({
      verdict, path: depositPath, url: url.href, finalUrl: response.finalUrl,
      status: response.status, title: extracted.title,
      // lines counts newlines (the wc -l convention, M1) - not
      // split('\n').length, which is one high because contents always ends
      // with a trailing newline. Same convention as courier-append.js.
      bytes: Buffer.byteLength(contents, 'utf8'), lines: contents.split('\n').length - 1,
      format: extracted.format,
      reasons: excludeFailed ? [...reasons, 'git-exclude-failed'] : reasons,
    }));
}

try {
  await main();
} catch (err) {
  // Anything unanticipated (M6) must still respect the one-JSON-line
  // contract: the full diagnosis goes to stderr, off the contract channel,
  // and a structured FAIL line still reaches stdout. `internal:` is
  // unmistakably distinct from `deposit:` / `network:` / `invalid-url`, so
  // an unrelated bug is never laundered into a false diagnosis.
  process.stderr.write(`${err?.stack ?? err}\n`);
  emit({ verdict: 'FAIL', path: null, url: process.argv[2] ?? null, reasons: [`internal:${err?.name ?? 'Error'}`] }, EXIT.FAIL);
}
