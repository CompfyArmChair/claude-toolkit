import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, THIN_CONTENT_CHARS, BOT_BLOCK_MARKERS } from '../src/verdict.js';

const longMarkdown = 'Plain readable article text. '.repeat(50); // ~1450 chars
const veryLongMarkdown = 'Plain readable article text. '.repeat(100); // ~2900 chars

test('healthy page classifies OK with no reasons', () => {
  const r = classify({ httpStatus: 200, title: 'An Article', markdown: longMarkdown });
  assert.deepEqual(r, { verdict: 'OK', reasons: [] });
});

test('HTTP 403, 429 and 5xx escalate', () => {
  for (const status of [403, 429, 500, 503]) {
    const r = classify({ httpStatus: status, title: 'x', markdown: longMarkdown });
    assert.equal(r.verdict, 'ESCALATE');
    assert.ok(r.reasons.includes(`http-${status}`), `expected http-${status}`);
  }
});

test('404 does NOT escalate by status alone (evidence goes in metadata)', () => {
  const r = classify({ httpStatus: 404, title: 'Not Found here', markdown: longMarkdown });
  assert.equal(r.verdict, 'OK');
});

test('bot-block marker in title escalates even on HTTP 200', () => {
  const r = classify({ httpStatus: 200, title: 'Just a moment...', markdown: longMarkdown });
  assert.equal(r.verdict, 'ESCALATE');
  assert.ok(r.reasons.some((x) => x.startsWith('bot-marker:')));
});

test('bot-block marker beyond the first 2000 chars of the body still escalates', () => {
  const r = classify({
    httpStatus: 200, title: 'An Article',
    markdown: `${veryLongMarkdown}Your request blocked by our firewall.`,
  });
  assert.equal(r.verdict, 'ESCALATE');
  assert.ok(r.reasons.some((x) => x.startsWith('bot-marker:')));
});

test('thin extraction escalates with the observed char count', () => {
  const r = classify({ httpStatus: 200, title: 'Redirect', markdown: '[Click here](x) to be redirected.' });
  assert.equal(r.verdict, 'ESCALATE');
  assert.ok(r.reasons.includes('thin-content:33chars'));
});

test('reasons accumulate (blocked page is usually thin too)', () => {
  const r = classify({ httpStatus: 403, title: 'Access denied', markdown: '' });
  assert.equal(r.verdict, 'ESCALATE');
  assert.ok(r.reasons.includes('http-403'));
  assert.ok(r.reasons.some((x) => x.startsWith('bot-marker:')));
  assert.ok(r.reasons.includes('thin-content:0chars'));
});

test('threshold constant is the spec value', () => {
  assert.equal(THIN_CONTENT_CHARS, 200);
  assert.ok(BOT_BLOCK_MARKERS.length > 0);
});
