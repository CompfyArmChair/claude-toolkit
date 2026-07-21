# Persisted, Independently Verifiable Research Reports — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standalone researcher agents persist every research report to `docs/research/` with independently verifiable citations, and reply with a digest plus the file path.

**Architecture:** The plugin's research architecture is a methodology × delivery matrix. This plan adds the missing standalone delivery skill (`research-persistence`, sibling of `research-deposit`), hardens the two shared methodology skills with verifiability requirements (fetched-only citing, access dates, verbatim excerpts, claim-by-claim self-check), and wires the delivery skill into the two standalone researcher agents. The or-* researchers are untouched — they inherit the methodology hardening automatically.

**Tech Stack:** Claude Code plugin markdown (agents, skills), plugin/marketplace manifests. No code, no test harness — verification is `claude plugin validate --strict` plus exact-string consistency checks.

**Spec:** `docs/superpowers/specs/2026-07-21-persisted-verifiable-research-design.md`

## Global Constraints

- Work on branch `research-persistence` (already exists). Never push — the user decides.
- **Never `git add -A`** — the repo root contains untracked junk (`.clone/`). Stage explicit paths only.
- Version alignment: `plugins/claude-toolkit/.claude-plugin/plugin.json` `version`, marketplace `metadata.version`, and marketplace `plugins[0].version` must all read `1.6.0` after Task 5.
- The `research-persistence` skill and `research-deposit` skill are mutually exclusive delivery modes; a `DEPOSIT: <path>` parameter in the spawn prompt always wins.
- All file paths below are relative to the repo root `I:\Dev\claude-toolkit`.

---

### Task 1: Create the `research-persistence` skill

**Files:**
- Create: `plugins/claude-toolkit/skills/research-persistence/SKILL.md`
- Modify: `README.md` (skills list, after the `research-deposit` line)

**Interfaces:**
- Consumes: nothing.
- Produces: skill named `research-persistence`, invocable as `Skill('claude-toolkit:research-persistence')` — Task 4's agent frontmatter and body reference exactly these names.

- [ ] **Step 1: Write the skill file**

Create `plugins/claude-toolkit/skills/research-persistence/SKILL.md` with exactly this content:

```markdown
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
```

- [ ] **Step 2: Add the README entry**

In `README.md`, use Edit with:

old_string:
```
- **research-deposit** — Deposit protocol: research agents write findings to disk and reply with a minimal token
```

new_string:
```
- **research-deposit** — Deposit protocol: research agents write findings to disk and reply with a minimal token
- **research-persistence** — Standalone delivery protocol: researchers save the full report to docs/research/ and reply with a digest plus the path
```

- [ ] **Step 3: Verify skill frontmatter parses**

Run from the repo root: `claude plugin validate --strict plugins/claude-toolkit`
Expected: validation passes (no errors; the new skill is picked up).

- [ ] **Step 4: Commit**

```bash
git add plugins/claude-toolkit/skills/research-persistence/SKILL.md README.md
git commit -m "feat(skills): add research-persistence standalone delivery protocol"
```

---

### Task 2: Harden `dependency-research-methodology` for independent verifiability

**Files:**
- Modify: `plugins/claude-toolkit/skills/dependency-research-methodology/SKILL.md`

**Interfaces:**
- Consumes: nothing.
- Produces: a Step 6 titled `## Step 6: Verify Every Claim` and the inference label literal `(inference — no source)` — Task 3 uses the identical heading and label so the two methodologies stay symmetric.

All edits below are Edit-tool operations on `plugins/claude-toolkit/skills/dependency-research-methodology/SKILL.md` with exact strings.

- [ ] **Step 1: Fetched-only citing rule in Step 3**

old_string:
```
Run independent research areas in parallel where possible.
```

new_string:
```
Run independent research areas in parallel where possible.

**Only fetched content counts as a source.** A search result's title or snippet is a lead, not a source — you may cite only pages whose content you actually retrieved (WebFetch) and Context7 results you actually received. Record the access date as you fetch; the Sources list requires it.
```

- [ ] **Step 2: Verification metadata in the Sources template**

old_string:
```
### Sources
[1] [Title](URL) - Official docs
[2] [Title](URL) - Blog post, YYYY-MM
[3] Context7: [library-id] - API reference
[4] [Title](URL) - Stack Overflow
```

new_string:
```
### Sources
[1] [Title](URL) - Official docs. Accessed YYYY-MM-DD.
    > "Verbatim excerpt that supports the claims citing [1]"
[2] [Title](URL) - Blog post, YYYY-MM. Accessed YYYY-MM-DD.
    > "Verbatim excerpt that supports the claims citing [2]"
[3] Context7: [library-id] - API reference. Accessed YYYY-MM-DD.
    > "Verbatim excerpt from the returned documentation"
[4] [Title](URL) - Stack Overflow. Accessed YYYY-MM-DD.
    > "Verbatim excerpt that supports the claims citing [4]"
```

- [ ] **Step 3: Add Step 6 (claim-by-claim self-check)**

old_string:
```
# Citation Requirements
```

new_string:
```
## Step 6: Verify Every Claim

Before delivering, walk the report claim by claim:

1. For each inline citation, re-read the excerpt in the matching Sources entry. Does it actually support the claim as written? If not: fix the claim, fix the mapping, or re-fetch to find real support.
2. Any statement without a citation must be labeled inline as `(inference — no source)` — unless it merely restates the request or the report's own structure.
3. Confirm every Sources entry has a link (URL or Context7 id), an access date, and a verbatim excerpt.

Deliver only after this pass is clean.

# Citation Requirements
```

- [ ] **Step 4: Extend Citation Requirements**

old_string:
```
- **When sources conflict**, note both with citations
```

new_string:
```
- **When sources conflict**, note both with citations
- **Cite only sources you actually fetched** - search-result titles and snippets are leads, not sources
- **Every source entry carries an access date and a verbatim supporting excerpt** - claims must be verifiable without re-fetching
- **Label unsourced statements** as `(inference — no source)` - never present inference as sourced fact
```

- [ ] **Step 5: Extend What NOT To Do**

old_string:
```
- Do NOT exceed 3 follow-up cycles per research area
```

new_string:
```
- Do NOT exceed 3 follow-up cycles per research area
- Do NOT cite a source you did not actually fetch
- Do NOT present inference as sourced fact - label it `(inference — no source)`
- Do NOT deliver without the Step 6 claim-by-claim verification pass
```

- [ ] **Step 6: Verify**

Run from the repo root: `claude plugin validate --strict plugins/claude-toolkit`
Expected: validation passes.

Then confirm the file contains exactly one `## Step 6: Verify Every Claim` heading and three occurrences of `(inference — no source)` (Steps 3, 4, 5 above each added one).

- [ ] **Step 7: Commit**

```bash
git add plugins/claude-toolkit/skills/dependency-research-methodology/SKILL.md
git commit -m "feat(skills): dependency research citations must be independently verifiable"
```

---

### Task 3: Harden `community-research-methodology` for independent verifiability

**Files:**
- Modify: `plugins/claude-toolkit/skills/community-research-methodology/SKILL.md`

**Interfaces:**
- Consumes: heading `## Step 6: Verify Every Claim` and label literal `(inference — no source)` as established in Task 2 (kept textually identical for symmetry).
- Produces: nothing consumed later.

All edits below are Edit-tool operations on `plugins/claude-toolkit/skills/community-research-methodology/SKILL.md` with exact strings.

- [ ] **Step 1: Fetched-only citing rule in Step 3**

old_string:
```
- The context (when written, what scale, what domain)
```

new_string:
```
- The context (when written, what scale, what domain)

**Only fetched content counts as a source.** A search result's title or snippet is a lead, not a source — you may cite only pages whose content you actually retrieved with WebFetch. Record the access date as you fetch; the Sources list requires it.
```

- [ ] **Step 2: Verification metadata in the Sources template**

old_string:
```
### Sources
[1] [Title](URL) - Brief description of perspective/context
[2] [Title](URL) - Brief description
[3] [Title](URL) - Brief description
...
```

new_string:
```
### Sources
[1] [Title](URL) - Brief description of perspective/context. Accessed YYYY-MM-DD.
    > "Verbatim excerpt that supports the claims citing [1]"
[2] [Title](URL) - Brief description. Accessed YYYY-MM-DD.
    > "Verbatim excerpt that supports the claims citing [2]"
...
```

- [ ] **Step 3: Add Step 6 (claim-by-claim self-check)**

old_string:
```
# Source Quality Assessment
```

new_string:
```
## Step 6: Verify Every Claim

Before delivering, walk the report claim by claim:

1. For each inline citation, re-read the excerpt in the matching Sources entry. Does it actually support the claim as written? If not: fix the claim, fix the mapping, or re-fetch to find real support.
2. Any statement without a citation must be labeled inline as `(inference — no source)` — unless it merely restates the request or the report's own structure.
3. Confirm every Sources entry has a URL, an access date, and a verbatim excerpt.

Deliver only after this pass is clean.

# Source Quality Assessment
```

- [ ] **Step 4: Extend Citation Requirements**

old_string:
```
- **When sources conflict**, cite both sides
```

new_string:
```
- **When sources conflict**, cite both sides
- **Cite only sources you actually fetched** - search-result titles and snippets are leads, not sources
- **Every source entry carries an access date and a verbatim supporting excerpt** - claims must be verifiable without re-fetching
- **Label unsourced statements** as `(inference — no source)` - never present inference as sourced fact
```

- [ ] **Step 5: Extend What NOT To Do**

old_string:
```
- Do NOT present opinions as facts
```

new_string:
```
- Do NOT present opinions as facts
- Do NOT cite a source you did not actually fetch
- Do NOT present inference as sourced fact - label it `(inference — no source)`
- Do NOT deliver without the Step 6 claim-by-claim verification pass
```

- [ ] **Step 6: Verify**

Run from the repo root: `claude plugin validate --strict plugins/claude-toolkit`
Expected: validation passes.

Then confirm the file contains exactly one `## Step 6: Verify Every Claim` heading and three occurrences of `(inference — no source)`.

- [ ] **Step 7: Commit**

```bash
git add plugins/claude-toolkit/skills/community-research-methodology/SKILL.md
git commit -m "feat(skills): community research citations must be independently verifiable"
```

---

### Task 4: Wire `research-persistence` into the standalone researcher agents

**Files:**
- Modify: `plugins/claude-toolkit/agents/dependency-researcher.md` (full rewrite, content below)
- Modify: `plugins/claude-toolkit/agents/community-researcher.md` (full rewrite, content below)
- Modify: `README.md` (the two researcher agent lines)

**Interfaces:**
- Consumes: skill name `research-persistence` / `Skill('claude-toolkit:research-persistence')` from Task 1.
- Produces: nothing consumed later.

Note: neither agent gains `SendMessage`. The or-superpowers-at-scale spawn protocol wraps agents that lack `Write`+`SendMessage`; adding only `Write` keeps that wrap rule's behavior unchanged.

- [ ] **Step 1: Rewrite `plugins/claude-toolkit/agents/dependency-researcher.md`**

Replace the entire file with:

```markdown
---
name: dependency-researcher
description: Library research specialist for SDKs, frameworks, and APIs. Use whenever working with external libraries - for implementation, debugging, evaluation, or design. Reads documentation sources, saves a fully-cited report to docs/research/, and replies with a digest plus the file path.
tools: Glob, Grep, Read, WebFetch, WebSearch, mcp__context7__resolve-library-id, mcp__context7__query-docs, Write, Skill
model: opus
skills: [dependency-research-methodology, research-persistence]
---

You are a Library Research Agent. You decompose research requests into focused queries, fetch documentation from multiple sources, evaluate results, and synthesize focused reports.

Use `Skill('claude-toolkit:dependency-research-methodology')` to load the research-and-citation workflow, then execute it for the request in your prompt.

Use `Skill('claude-toolkit:research-persistence')` to deliver your findings: write the full report to `docs/research/` and reply with a concise digest plus the saved path.

> Note: `skills:` frontmatter pre-seeds these skills when this agent runs as a foreground subagent, but it is **inert when this agent runs as a teammate** (e.g. dispatched by the orchestrator). The in-body `Skill(...)` calls above are the load-bearing path in teammate mode — do not delete them as "redundant".
```

- [ ] **Step 2: Rewrite `plugins/claude-toolkit/agents/community-researcher.md`**

Replace the entire file with:

```markdown
---
name: community-researcher
description: Community knowledge specialist for design decisions and trade-offs. Use when evaluating approaches, considering alternatives, or needing real-world context on how problems are solved in practice. Saves a fully-cited report to docs/research/ and replies with a digest plus the file path.
tools: Glob, Grep, Read, WebFetch, WebSearch, Write, Skill
model: opus
skills: [community-research-methodology, research-persistence]
---

You are a Community Research Agent. You research how the community solves problems, identify patterns and anti-patterns, surface trade-offs and disagreements, and synthesize practical wisdom from real-world usage.

Use `Skill('claude-toolkit:community-research-methodology')` to load the research-and-citation workflow, then execute it for the request in your prompt.

Use `Skill('claude-toolkit:research-persistence')` to deliver your findings: write the full report to `docs/research/` and reply with a concise digest plus the saved path.

> Note: `skills:` frontmatter pre-seeds these skills when this agent runs as a foreground subagent, but it is **inert when this agent runs as a teammate** (e.g. dispatched by the orchestrator). The in-body `Skill(...)` calls above are the load-bearing path in teammate mode — do not delete them as "redundant".
```

- [ ] **Step 3: Update the README agent lines**

In `README.md`, two Edit operations:

old_string:
```
- **community-researcher** — Research how the community solves problems, surface trade-offs and real-world experience
```

new_string:
```
- **community-researcher** — Research how the community solves problems, surface trade-offs and real-world experience; saves a cited report to docs/research/ and replies with a digest plus the path
```

old_string:
```
- **dependency-researcher** — Research library/SDK documentation from multiple sources, return focused cited reports
```

new_string:
```
- **dependency-researcher** — Research library/SDK documentation from multiple sources; saves a cited report to docs/research/ and replies with a digest plus the path
```

- [ ] **Step 4: Verify**

Run from the repo root: `claude plugin validate --strict plugins/claude-toolkit`
Expected: validation passes (agent frontmatter with the new `tools`/`skills` entries parses cleanly).

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-toolkit/agents/dependency-researcher.md plugins/claude-toolkit/agents/community-researcher.md README.md
git commit -m "feat(agents): standalone researchers persist reports via research-persistence"
```

---

### Task 5: Version bump to 1.6.0 and full validation

**Files:**
- Modify: `plugins/claude-toolkit/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json` (both version fields)

**Interfaces:**
- Consumes: all prior tasks committed.
- Produces: shippable 1.6.0.

- [ ] **Step 1: Bump plugin.json**

In `plugins/claude-toolkit/.claude-plugin/plugin.json`, Edit:

old_string:
```
  "version": "1.5.5",
```

new_string:
```
  "version": "1.6.0",
```

- [ ] **Step 2: Bump both marketplace.json fields**

In `.claude-plugin/marketplace.json`, Edit with `replace_all: true` (the string appears exactly twice — `metadata.version` and `plugins[0].version`):

old_string:
```
"version": "1.5.5"
```

new_string:
```
"version": "1.6.0"
```

After the edit, confirm the file contains zero occurrences of `1.5.5` and two of `1.6.0`.

- [ ] **Step 3: Validate at both levels**

Run from the repo root:
- `claude plugin validate --strict .` — Expected: marketplace validation passes.
- `claude plugin validate --strict plugins/claude-toolkit` — Expected: plugin validation passes.

- [ ] **Step 4: Commit**

```bash
git add plugins/claude-toolkit/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "release: claude-toolkit 1.6.0 - persisted, independently verifiable research reports"
```
