import fs from 'node:fs';
import path from 'node:path';

export const SLUG_MAX_LENGTH = 60;
export const EXCLUDE_ENTRY = '.claude/web-deposits/';

// Human-readable hint only: deposit identity is the frontmatter url,
// uniqueness comes from the collision suffix (spec section 4.3).
export function deriveSlug(url) {
  const u = new URL(url);
  const host = u.hostname.replace(/^www\./, '');
  const raw = `${host}${u.pathname}`.toLowerCase();
  const kebab = raw.replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  const cut = kebab.slice(0, SLUG_MAX_LENGTH).replace(/-+$/, '');
  return cut || 'page';
}

export function resolveProjectRoot(startDir) {
  let dir = path.resolve(startDir);
  while (true) {
    if (fs.existsSync(path.join(dir, '.git'))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) return path.resolve(startDir);
    dir = parent;
  }
}

export function depositDir(projectRoot) {
  return path.join(projectRoot, '.claude', 'web-deposits');
}

// Allocation IS creation: open with 'wx' atomically reserves the name, so
// two concurrent sessions can never select the same file (spec section 4.3
// uniqueness). The caller overwrites the empty reservation with content.
export function createDepositFile(dir, date, slug, ext) {
  const base = `${date}-${slug}`;
  // Terminates: each EEXIST bumps n and retries with the next suffix; any
  // other error escapes immediately instead of looping. Deliberately
  // uncapped - a real collision run is at most a handful of concurrent
  // sessions fetching the same URL on the same day.
  for (let n = 1; ; n += 1) {
    const candidate = path.join(dir, n === 1 ? `${base}.${ext}` : `${base}-${n}.${ext}`);
    try {
      fs.closeSync(fs.openSync(candidate, 'wx'));
      return candidate;
    } catch (err) {
      if (err.code !== 'EEXIST') throw err;
    }
  }
}

function yamlString(value) {
  // Collapse embedded CR/LF before escaping: page-derived text (the title)
  // could otherwise inject a bare --- that ends the frontmatter fence
  // early, or an extra unquoted line, for a regex or eyeball reader.
  const collapsed = String(value ?? '').replace(/[\r\n]+/g, ' ');
  return `"${collapsed.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
}

export function renderFrontmatter(meta) {
  const lines = ['---'];
  for (const key of ['url', 'finalUrl', 'fetchedAt', 'httpStatus', 'tier', 'title', 'format']) {
    const value = meta[key];
    lines.push(`${key}: ${typeof value === 'number' ? value : yamlString(value)}`);
  }
  lines.push('---');
  return lines.join('\n') + '\n';
}

// In a linked worktree .git is a file "gitdir: <path>"; the shared exclude
// file lives under the common dir that <gitdir>/commondir points at.
function resolveGitCommonDir(projectRoot, dotGit) {
  if (fs.statSync(dotGit).isDirectory()) return dotGit;
  const match = fs.readFileSync(dotGit, 'utf8').match(/^gitdir:\s*(.+?)\s*$/m);
  if (!match) return null;
  const gitDir = path.resolve(projectRoot, match[1]);
  const commonDirFile = path.join(gitDir, 'commondir');
  if (fs.existsSync(commonDirFile)) {
    return path.resolve(gitDir, fs.readFileSync(commonDirFile, 'utf8').trim());
  }
  return gitDir;
}

export function ensureGitExclude(projectRoot) {
  const dotGit = path.join(projectRoot, '.git');
  if (!fs.existsSync(dotGit)) return false;
  const commonDir = resolveGitCommonDir(projectRoot, dotGit);
  if (!commonDir) return false;
  const infoDir = path.join(commonDir, 'info');
  const excludeFile = path.join(infoDir, 'exclude');
  const existing = fs.existsSync(excludeFile) ? fs.readFileSync(excludeFile, 'utf8') : '';
  if (existing.split(/\r?\n/).includes(EXCLUDE_ENTRY)) return false;
  fs.mkdirSync(infoDir, { recursive: true });
  const glue = existing.length > 0 && !existing.endsWith('\n') ? '\n' : '';
  fs.appendFileSync(excludeFile, `${glue}${EXCLUDE_ENTRY}\n`);
  return true;
}
