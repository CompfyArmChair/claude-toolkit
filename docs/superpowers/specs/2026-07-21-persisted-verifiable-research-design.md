# Persisted, Independently Verifiable Research Reports — Design

**Date:** 2026-07-21
**Status:** Approved

## Problem

The standalone researcher agents (`dependency-researcher`, `community-researcher`)
return their cited report as their reply and persist nothing. Once the calling
session ends, the research — and the evidence trail behind it — is gone. The
methodology skills require inline citations, but nothing enforces that a cited
source was actually read, actually supports the claim, or can be checked later
without re-running the research.

## Goals

1. Standalone researchers persist every research report to `docs/research/` in
   the project they are working in, creating the folder if absent.
2. All sources are provided with enough metadata that every claim is
   independently verifiable from the sources — without re-fetching, and
   detectably if a source has since changed.
3. The calling agent's context stays small: the reply is a digest plus the
   saved path, not the full report.

## Non-goals

- Changing the `or-*` researchers' delivery. They keep the `research-deposit`
  protocol (caller-chosen `DEPOSIT: <path>`). They inherit the strengthened
  citation standard automatically because the methodology skills are shared.
- Any hook, command, or test-harness changes.

## Design

The plugin's research architecture is a methodology × delivery matrix:
methodology skills say *how to research*; delivery skills say *how to deliver*.
`research-deposit` is the delivery skill for orchestrator teammates. This
design adds the missing standalone delivery skill and hardens the shared
methodologies.

### 1. New skill: `research-persistence`

`plugins/claude-toolkit/skills/research-persistence/SKILL.md`

Governs delivery for standalone (non-deposit) research runs:

- After synthesizing the report per the methodology skill, write the **full
  report** to `docs/research/YYYY-MM-DD-<topic-slug>.md` relative to the
  project root. The Write tool creates `docs/research/` automatically if it
  does not exist.
- Date comes from the session's environment context ("Today's date"). The slug
  is a short kebab-case topic name; if the target file already exists, choose a
  more specific slug rather than overwriting.
- Reply to the dispatching agent with a **concise digest** — key findings,
  caveats, whether the objective is achievable — **plus the saved path**.
  Never echo the full report into the reply.
- If research is blocked or only partially possible, still write what was
  gathered with gaps explicitly noted, and say so in the digest.
- **Guard clause:** if the spawn prompt contains `DEPOSIT: <path>`, the
  `research-deposit` protocol governs delivery instead — do not write to
  `docs/research/`. The two delivery skills are mutually exclusive.

### 2. Verifiability hardening in both methodology skills

`dependency-research-methodology` and `community-research-methodology` gain the
same four requirements:

- **Fetched-only citing.** A source may be cited only if its content was
  actually retrieved (WebFetch page content, Context7 query result). Search
  result snippets and titles are leads, not sources.
- **Verification metadata per source.** Every source entry carries: title,
  URL (or Context7 library id), access date, source type, and a short verbatim
  excerpt that supports the claims citing it. A reader can verify claims
  without re-fetching and can detect drift if they do.
- **Inference labeling.** Statements with no supporting source must be
  explicitly labeled as inference, clearly distinguished from sourced claims.
- **Claim-by-claim self-check (new final step).** Before delivering, walk each
  inline citation and confirm the cited excerpt actually supports the claim.
  Fix the mapping or relabel the claim as inference.

The "What NOT To Do" lists gain matching entries (e.g. "Do NOT cite a source
you did not fetch").

### 3. Standalone agent updates

`agents/dependency-researcher.md` and `agents/community-researcher.md`:

- Add `Write` to `tools:`.
- Add `research-persistence` to `skills:` frontmatter.
- Add an in-body `Skill('claude-toolkit:research-persistence')` call — the
  load-bearing path in teammate mode, mirroring the existing methodology call
  and the or-* agents' deposit call.
- No `SendMessage` is added, so the orchestrator spawn-protocol's wrap rule for
  these agents ("wrap unless the agent has both Write and SendMessage") is
  unaffected.

### 4. Release mechanics

- Version bump 1.5.5 → 1.6.0 in
  `plugins/claude-toolkit/.claude-plugin/plugin.json` and **both**
  `.claude-plugin/marketplace.json` fields (`metadata.version`,
  `plugins[0].version`).
- `claude plugin validate --strict` green at both levels (marketplace root and
  plugin dir).

## Error handling

- Blocked/partial research still persists (with gaps noted) — the disk
  artifact is the record of what was and was not established.
- Filename collision resolves by choosing a more specific slug, never by
  overwriting.
- A `DEPOSIT:` parameter always wins over persistence — no double delivery.

## Testing / verification

Agent and skill markdown has no automated test harness in this repo.
Verification is `claude plugin validate --strict` at both levels, plus a manual
read-through that the four changed/new markdown files are internally consistent
(frontmatter tools/skills match body instructions).
