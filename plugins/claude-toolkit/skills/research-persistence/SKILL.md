---
name: research-persistence
description: 'Use when you are a standalone research agent delivering a synthesized research report and your spawn prompt does NOT include a "DEPOSIT: <path>" parameter — defines how to persist the full report to docs/research/ and reply with a digest plus the file path. Not a trigger to start research; it governs how research output is delivered.'
---

# Research Persistence Protocol

You are a standalone research agent. Your full findings are persisted to the project's `docs/research/` folder; your reply to the dispatching agent is a digest plus the file path.

## When this applies

Your spawn prompt does **not** include a `DEPOSIT: <path>` parameter. If it does, the `research-deposit` protocol governs delivery instead — do not write to `docs/research/`. The two delivery modes are mutually exclusive.

## Protocol

1. Conduct your research per your methodology skill.
2. Write your **full report** — complete with all sources, access dates, and supporting excerpts — to `docs/research/YYYY-MM-DD-<topic-slug>.md` relative to the project root, using the `Write` tool. The tool creates `docs/research/` automatically if it does not exist.
   - `YYYY-MM-DD` is today's date from your environment context.
   - `<topic-slug>` is a short kebab-case name for the research topic (e.g. `polly-retry-httpclient`).
   - If the target file already exists, choose a more specific slug — never overwrite an existing report.
3. Reply to the dispatching agent with:
   - the saved path (always), and
   - a concise digest: whether the objective is achievable, the key findings, and the caveats that would change what the caller does next.
4. Do **not** echo the full report into your reply. The report lives on disk; the caller reads it when it needs detail beyond the digest.

## If you cannot complete

If the research is blocked or only partially possible, still write what you gathered to the file, with the gaps explicitly listed under a `### Gaps` heading, and open your digest with `PARTIAL:` and a one-line reason.

## Why this matters

The report on disk is the durable, independently verifiable record — every claim traceable to a fetched source. The digest keeps the caller's context small: detail is pulled on demand, not pushed by default.
