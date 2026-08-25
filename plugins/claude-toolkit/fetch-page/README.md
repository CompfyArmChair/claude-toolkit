# fetch-page

Tier-1 raw fetch for the WebFetch-ban pipeline: GET a URL, extract readable
content, write it to a project-local deposit file, and print exactly one
JSON line describing the result. It never prints page content, and it never
synthesizes an answer.

Rationale, the full pipeline (tier 2, the courier), and the hook that
enforces this substitute for WebFetch all live in the spec:
`~/.claude/docs/superpowers/specs/2026-08-08-webfetch-ban-raw-fetch-pipeline-design.md`.

## Install

```
npm ci
```

in this directory. This is a prerequisite, not an optional step: without
`node_modules` present, running either entry point below fails at module
load with an `ERR_MODULE_NOT_FOUND` stack printed to stderr and **no JSON
line at all** on stdout - the FAIL exit code with a shape no consumer of
this CLI is prepared for. A plugin packaging this script must run `npm ci`
here as part of its own install step.

## Entry points

### `node <this-directory> <url>`

Fetches `<url>`, extracts readable content (or passes it through verbatim
for PDF and raw-text content types), classifies a verdict, and writes a
deposit file. Prints one JSON line on stdout; page content never appears on
stdout under any verdict.

- `OK` / `ESCALATE`: `{verdict, path, url, finalUrl, status, title, bytes, lines, format, reasons}`
- `FAIL`: `{verdict, path: null, url, reasons}` only - no `finalUrl`/`status`/etc.

### `node courier-append.js <deposit> <staging>`

Used by the `page-courier` agent (tier 2) to append browser-extracted text
to an existing markdown deposit. Flips the deposit's frontmatter `tier` from
`script` to `courier`, appends the staging file's text after a timestamped
separator, and prints one JSON line.

- success: `{ok: true, path, appendedBytes, appendedLines, stagingRemoved}`
- failure: `{ok: false, path, reason}`

## Exit codes

| Entry point | Code | Meaning |
|---|---|---|
| `index.js` | 0 | `OK` |
| `index.js` | 1 | `FAIL` |
| `index.js` | 2 | `ESCALATE` |
| `courier-append.js` | 0 | `ok: true` |
| `courier-append.js` | 1 | `ok: false` |

## The one-JSON-line rule

Every invocation of either entry point prints **exactly one** JSON line to
stdout and nothing else - this is the entire interface, and the reason a
caller can always `JSON.parse` the first (only) line of stdout. All
diagnostic detail (stack traces, library warnings) goes to stderr instead,
off the contract channel. Page or deposit content is never written to
stdout under any verdict or outcome.

## The deposit

A deposit lives at `<projectRoot>/.claude/web-deposits/YYYY-MM-DD-<slug>.md`
(project root = nearest ancestor of the current directory containing
`.git`, else the current directory; `-2`, `-3`, ... on a same-day
same-slug collision). It is YAML frontmatter (`url`, `finalUrl`,
`fetchedAt`, `httpStatus`, `tier: script|courier`, `title`, `format:
markdown|pdf|text`) followed by the verbatim extracted content. PDF
deposits are the exception: raw bytes with no frontmatter, since a PDF's
own format has no room for a text header.
