#!/usr/bin/env node
// Unconditional PreToolUse deny for WebFetch. The deny reason IS the
// redirect: it teaches the raw-fetch substitute at exactly the moment it is
// needed. Node port of the retired ~/.claude PowerShell hook (plugin-move
// spec section 4.2); every path it emits is computed from its own location.
// ASCII only: the reason crosses shells and Windows code pages verbatim.
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Drain stdin (the hook payload) so the parent's pipe write never blocks;
// the deny is unconditional, so the payload content is irrelevant.
for await (const _ of process.stdin) { /* drain */ }

const hookDir = path.dirname(fileURLToPath(import.meta.url));
const toPosix = (p) => p.split(path.sep).join('/');
const launcher = toPosix(path.resolve(hookDir, '..', 'fetch-page', 'bin', 'fetch-page.js'));
const doctrine = toPosix(path.resolve(hookDir, 'web-doctrine.md'));

const reason = [
  'WebFetch is disabled here: it does not return the page - a small side-model summarises it, and that summarisation fabricates (invented citations, blended statistics). Use the raw-fetch pipeline instead:',
  `1. Run: node "${launcher}" <url>`,
  '   It deposits the page verbatim (extracted markdown, raw text, or raw PDF) under <projectRoot>/.claude/web-deposits/ and prints ONE JSON line {verdict, path, helper, ...}. Page content is never inlined - Read or Grep the deposit file at "path".',
  '2. verdict OK: Read/Grep the deposit.',
  '3. verdict ESCALATE (bot wall / JS-only shell): spawn the page-courier agent (Agent tool, subagent_type "claude-toolkit:page-courier" - the bare name does not resolve) with the URL, the deposit path, and the helper path from the JSON (spawn prompt: URL / DEPOSIT / HELPER); it fetches via real Chrome and appends the page verbatim to that same file. Verdicts are routing advice, not gates - the courier may also be used on an OK deposit that looks incomplete.',
  '4. verdict FAIL: report honestly that the fetch failed. Do NOT answer from memory as if the page had been fetched.',
  `Multi-page research: delegate to a subagent (model Sonnet or above) that runs fetch-page and reads deposits in its own context, citing deposit-path:line for every claim. See ${doctrine}.`,
].join('\n');

process.stdout.write(JSON.stringify({
  hookSpecificOutput: {
    hookEventName: 'PreToolUse',
    permissionDecision: 'deny',
    permissionDecisionReason: reason,
  },
}) + '\n');
