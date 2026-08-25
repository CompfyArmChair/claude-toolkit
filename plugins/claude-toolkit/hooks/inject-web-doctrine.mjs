#!/usr/bin/env node
// SessionStart injection of the web-research doctrine (plugin-move spec
// section 4.3) - the mechanism that replaced ~/.claude/rules/web-research.md
// at decommission. Renders web-doctrine.md with paths computed from this
// script's own location; no prose file carries a machine path.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

for await (const _ of process.stdin) { /* drain */ }

const hookDir = path.dirname(fileURLToPath(import.meta.url));
const toPosix = (p) => p.split(path.sep).join('/');

// The repo's docs/ never ships in the installed plugin cache, so the spec
// pointer is the canonical GitHub URL rather than a local path (plan
// deviation 1, approved at plan review).
const SPEC_URL = 'https://github.com/CompfyArmChair/claude-toolkit/blob/master/docs/superpowers/specs/2026-08-08-webfetch-ban-raw-fetch-pipeline-design.md';

const template = fs.readFileSync(path.join(hookDir, 'web-doctrine.md'), 'utf8');
const rendered = template
  .replaceAll('{{FETCH_PAGE}}', toPosix(path.resolve(hookDir, '..', 'fetch-page', 'bin', 'fetch-page.js')))
  .replaceAll('{{SPEC}}', SPEC_URL);

process.stdout.write(JSON.stringify({
  hookSpecificOutput: {
    hookEventName: 'SessionStart',
    additionalContext: rendered,
  },
}) + '\n');
