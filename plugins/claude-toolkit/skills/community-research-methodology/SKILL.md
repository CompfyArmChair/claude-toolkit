---
name: community-research-methodology
description: Use when you are an agent already executing a community/real-world research task and need the structured research-and-citation workflow. Not a trigger to research inline — the main agent must still delegate to the community-researcher agent.
---

# Community Research Methodology

This is the structured workflow for a community/real-world research task: understand the decision, decompose into queries across source types, evaluate perspectives, and synthesise a fully-cited decision report that presents the landscape rather than a single answer.

# What You Research

- **Community discussions**: Stack Overflow, Reddit, Hacker News, GitHub issues/discussions
- **Real-world experience**: Blog posts, case studies, post-mortems
- **Patterns and anti-patterns**: What works, what doesn't, and why
- **Trade-offs**: Performance vs. simplicity, flexibility vs. complexity
- **Disagreements**: Where the community is split and the rationales for each side
- **Evolution**: How thinking has changed over time

# Your Process

## Step 1: Understand the Decision Context

Extract from the prompt:
- The problem being solved
- The decision or trade-off being considered
- Any constraints (language, framework, scale, team size)
- What the main agent needs to decide

## Step 2: Decompose into Research Queries

Break down into focused queries for different aspects:

**Example decomposition:**
```
Decision: "Should we use event sourcing for our order management system?"

Research queries:
1. Event sourcing real-world experiences (success stories AND failures)
2. Event sourcing vs. traditional CRUD trade-offs
3. Event sourcing complexity and team readiness
4. Event sourcing at different scales (startup vs. enterprise)
5. Common event sourcing pitfalls and how teams addressed them
```

## Step 3: Search Multiple Source Types

For each research query, use WebSearch with targeted queries across different source types. Run multiple searches in parallel:

**Stack Overflow / Technical Q&A:**
```
"[topic] site:stackoverflow.com [key terms]"
```

**Reddit discussions:**
```
"[topic] site:reddit.com (r/programming OR r/[relevant-subreddit])"
```

**Hacker News:**
```
"[topic] site:news.ycombinator.com"
```

**GitHub issues/discussions:**
```
"[topic] site:github.com (issue OR discussion)"
```

**Blog posts and articles:**
```
"[topic] [trade-offs OR experience OR lessons learned]"
```

Fetch promising results through the raw-fetch pipeline (below), then Read the deposits to extract:
- The core argument or experience
- Supporting rationale
- Any data or evidence cited
- The context (when written, what scale, what domain)

### Fetching pages: the raw-fetch pipeline

WebFetch is banned — it summarises pages through a small side-model that fabricates. Fetch every page with the pipeline CLI instead:

1. Run: `node "<skill-base-dir>/../../fetch-page/bin/fetch-page.js" <url>` — `<skill-base-dir>` is the absolute path announced when this skill loaded ("Base directory for this skill: ..."). The command prints ONE JSON line `{verdict, path, helper, ...}` and never inlines page content.
2. Read or Grep the **web deposit** — the file at `path`. (A web deposit is a fetched-page file; it is distinct from the or-* *research deposit*, the path where deposit-aware teammates deliver their report.)
3. On verdict `ESCALATE` (bot wall / JS-only shell) or `FAIL`: you have no `Agent` tool, so you cannot spawn the page-courier yourself. Record the gap explicitly in the report — "URL X escalated (bot wall / JS shell); not fetched; findings exclude it" — and never answer from memory as if the page had been fetched. If you are an or-* teammate with `SendMessage`, you MAY ask your manager to arrange a courier run (send the URL plus the `path` and `helper` values from the JSON line); the manager decides.

**Only deposited content counts as a source.** A search result's title or snippet is a lead, not a source — you may cite only pages with a web deposit to point at. Record the deposit path and access date as you fetch; the Sources list requires them, and every load-bearing claim cites `deposit-path:line`.

## Step 4: Evaluate Results

For each research area, evaluate:
- Are claims backed by source links?
- Are multiple perspectives represented?
- Are rationales included, not just opinions?
- Are there gaps in the trade-off analysis?

If insufficient, perform targeted follow-up searches. **Maximum 3 follow-up cycles per area.**

## Step 5: Synthesize Decision Report

**CRITICAL**: Every factual claim must be traceable to a source. Use inline citations [1], [2] etc.

```markdown
## Community Research: [Topic]

### Decision Context
[Restate what the user is trying to decide]

### Community Consensus
[What most practitioners agree on - if anything. Cite sources.]

### Common Approaches

#### Approach A: [Name]
**Advocates say**: [Key arguments for] [1][2]
**Critics say**: [Key arguments against] [3]
**Best when**: [Conditions where this shines] [1]
**Avoid when**: [Conditions where this struggles] [4]

#### Approach B: [Name]
...

### Key Trade-offs

| Factor | Approach A | Approach B | Source |
|--------|------------|------------|--------|
| Complexity | ... | ... | [5] |
| Performance | ... | ... | [6] |
| Team learning curve | ... | ... | [7] |

### Known Pitfalls
- [Common mistake 1 and how to avoid] [8]
- [Common mistake 2 and how to avoid] [9]

### Areas of Disagreement
[Where the community is split and why reasonable people disagree] [10][11]

### Evolution of Thinking
[How community opinion has changed, if relevant] [12]

### Recommendation Context
[Not a recommendation, but clarity on what factors should drive the decision]

### Sources
[1] [Title](URL) - Brief description of perspective/context. Accessed YYYY-MM-DD. Deposit: `<web-deposit path>`
    > "Verbatim excerpt that supports the claims citing [1]"
[2] [Title](URL) - Brief description. Accessed YYYY-MM-DD. Deposit: `<web-deposit path>`
    > "Verbatim excerpt that supports the claims citing [2]"
...
```

## Step 6: Verify Every Claim

Before delivering, walk the report claim by claim:

1. For each inline citation, re-read the excerpt in the matching Sources entry. Does it actually support the claim as written? If not: fix the claim, fix the mapping, or re-fetch to find real support.
2. Any statement without a citation must be labeled inline as `(inference — no source)` — unless it merely restates the request or the report's own structure.
3. Confirm every Sources entry has a URL, an access date, and a verbatim excerpt, and — for web pages — the web-deposit path.

Deliver only after this pass is clean.

# Source Quality Assessment

Note the quality/reliability of sources:
- **High**: Official blogs, well-known practitioners, detailed case studies with data
- **Medium**: Popular SO answers, upvoted Reddit threads, general tech blogs
- **Low**: Single opinions without rationale, outdated posts, unverified claims

Include sources of varying quality but note the distinction.

# Citation Requirements

- **Every factual claim needs a source**
- **Link directly to the source** (not just "Stack Overflow says...")
- **Note the date/context** when relevant (a 2019 blog post may reflect outdated practices)
- **Distinguish between**: official docs, authoritative blogs, community discussions, individual opinions
- **When sources conflict**, cite both sides
- **Cite only sources with a web deposit to point at** - search-result titles and snippets are leads, not sources
- **Every source entry carries an access date and a verbatim supporting excerpt** - claims must be verifiable without re-fetching
- **Label unsourced statements** as `(inference — no source)` - never present inference as sourced fact

# What NOT To Do

- Do NOT make claims without citations
- Do NOT give a single "right answer" - present the landscape
- Do NOT only show one side of debates
- Do NOT conflate old advice with current best practices
- Do NOT ignore minority viewpoints if they have valid rationales
- Do NOT present opinions as facts
- Do NOT cite a source without a web deposit to point at
- Do NOT present inference as sourced fact - label it `(inference — no source)`
- Do NOT deliver without the Step 6 claim-by-claim verification pass
