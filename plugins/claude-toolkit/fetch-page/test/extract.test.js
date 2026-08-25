import { test } from 'node:test';
import assert from 'node:assert/strict';
import { extractReadable } from '../src/extract.js';

const ARTICLE_HTML = `<!doctype html>
<html><head><title>Sample Article</title></head><body>
<article>
<h1>Sample Article</h1>
<p>${'Plain readable article text. '.repeat(10)}</p>
<p>${'More plain readable article text. '.repeat(10)}</p>
</article>
</body></html>`;

test('extractReadable: successful extraction returns non-empty markdown, error null, and restores console.error', async () => {
  const originalConsoleError = console.error;
  const result = await extractReadable(ARTICLE_HTML, 'https://example.com/x');
  assert.ok(result.markdown.length > 0, 'expected non-empty markdown from a real article extraction');
  assert.equal(result.error, null);
  assert.equal(console.error, originalConsoleError, 'console.error must be restored to the original function after extraction');
});

test('extractReadable: an injected parse failure is captured, not swallowed', async () => {
  const boom = new RangeError('boom');
  const throwingParse = async () => { throw boom; };
  const result = await extractReadable(ARTICLE_HTML, 'https://example.com/x', throwingParse);
  assert.deepEqual({ markdown: result.markdown, title: result.title }, { markdown: '', title: '' });
  assert.equal(result.error.name, 'RangeError');
});

test('extractReadable: an invalid url resolves with error set instead of rejecting', async () => {
  // new JSDOM(...) itself throws (a TypeError from its own URL validation)
  // when the url option is malformed - this must surface the same way as
  // any other extraction failure, not escape as an unhandled rejection.
  const result = await extractReadable('<p>hi</p>', 'not a url');
  assert.equal(result.markdown, '');
  assert.equal(result.error.name, 'TypeError');
});
