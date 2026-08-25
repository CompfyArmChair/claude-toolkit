#!/usr/bin/env node
import fs from 'node:fs';

const SCRIPT_TIER_LINE = 'tier: "script"';
const COURIER_TIER_LINE = 'tier: "courier"';
const FRONTMATTER_RE = /^---\n([\s\S]*?)\n---\n/;

// Same convention as index.js: process.exitCode + return-based flow, one
// JSON line on stdout, page-derived text never appears on stdout.
function emit(result, code) {
  process.stdout.write(JSON.stringify(result) + '\n');
  process.exitCode = code;
}

function fail(depositPath, reason) {
  emit({ verdict: 'FAIL', path: depositPath ?? null, reasons: [reason] }, 1);
}

async function main() {
  const [depositArg, stagingArg] = process.argv.slice(2);
  if (!depositArg || !stagingArg) return fail(depositArg, 'missing-argument');

  // The PDF guard: a .pdf deposit is a raw-bytes passthrough with no
  // frontmatter and nothing to append to.
  if (!depositArg.endsWith('.md')) return fail(depositArg, 'not-a-markdown-deposit');

  try {
    if (!fs.existsSync(depositArg)) return fail(depositArg, 'deposit-not-found');

    const deposit = fs.readFileSync(depositArg, 'utf8');
    const frontmatterMatch = deposit.match(FRONTMATTER_RE);
    const tierLineCount = frontmatterMatch
      ? frontmatterMatch[1].split('\n').filter((line) => line === SCRIPT_TIER_LINE).length
      : 0;
    // A deposit already flipped to tier: "courier" is refused too - one
    // valid input state, never a silent double-append.
    if (tierLineCount !== 1) return fail(depositArg, 'no-script-tier');

    if (!fs.existsSync(stagingArg)) return fail(depositArg, 'staging-not-found');
    const staging = fs.readFileSync(stagingArg, 'utf8');
    if (staging.trim().length === 0) return fail(depositArg, 'empty-staging');

    // Targeted first-occurrence replace within the frontmatter block only
    // (already verified to contain exactly one match) - every other byte of
    // the existing deposit, including the rest of the frontmatter and the
    // whole body, is left untouched.
    const newFrontmatterBlock = frontmatterMatch[0].replace(SCRIPT_TIER_LINE, COURIER_TIER_LINE);
    const rest = deposit.slice(frontmatterMatch[0].length);

    // Staging text is written verbatim; only the termination is normalized
    // to exactly one trailing newline (trailing newline runs stripped, one
    // added back), so trailing spaces or other content stay untouched.
    const stagingBody = staging.replace(/(\r?\n)+$/, '');
    const timestamp = new Date().toISOString();
    const separator = `\n<!-- page-courier: content below fetched via Chrome at ${timestamp} -->\n`;
    const appended = separator + stagingBody + '\n';

    // The rename is the commit point (M11): write the modified deposit to a
    // sibling .tmp file, then rename it onto the deposit path. Rename is
    // atomic within a volume, so an interruption here can only ever leave
    // the .tmp file - never a truncated deposit - and a successful rename
    // leaves no .tmp behind (rename moves the name, it does not copy it).
    // If either call throws, the deposit is untouched by construction and
    // the outer catch reports the existing io:<code> failure.
    const tmpPath = `${depositArg}.tmp`;
    fs.writeFileSync(tmpPath, newFrontmatterBlock + rest + appended, 'utf8');
    fs.renameSync(tmpPath, depositArg);

    // Staging removal is a best-effort epilogue, not part of the commit
    // (I1): the append has already succeeded above, so a locked or
    // otherwise undeletable staging file must never be reported as a
    // failed append. A leftover .courier.txt is visible and harmless.
    let stagingRemoved = true;
    try {
      fs.unlinkSync(stagingArg);
    } catch {
      stagingRemoved = false;
    }

    return emit({
      verdict: 'OK',
      path: depositArg,
      appendedBytes: Buffer.byteLength(appended, 'utf8'),
      appendedLines: appended.split('\n').length - 1,
      stagingRemoved,
      reasons: [],
    }, 0);
  } catch (err) {
    return fail(depositArg, `io:${err.code ?? err.name}`);
  }
}

await main();
