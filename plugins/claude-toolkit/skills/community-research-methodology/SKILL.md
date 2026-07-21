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

Use WebFetch on promising results to extract:
- The core argument or experience
- Supporting rationale
- Any data or evidence cited
- The context (when written, what scale, what domain)

**Only fetched content counts as a source.** A search result's title or snippet is a lead, not a source — you may cite only pages whose content you actually retrieved with WebFetch. Record the access date as you fetch; the Sources list requires it.

## Step 4: Evaluate Results

For each research area, evaluate:
- Are claims backed by source links?
- Are multiple perspectives represented?
- Are rationales included, not just opinions?
- Are there gaps in the trade-off analysis?

If insufficient, perform targeted follow-up searches. **Maximum 3 follow-up cycles per area.**

## Step 5: Synthesize Decision Report

**CRITICAL**: Every claim must be traceable to a source. Use inline citations [1], [2] etc.

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
[1] [Title](URL) - Brief description of perspective/context. Accessed YYYY-MM-DD.
    > "Verbatim excerpt that supports the claims citing [1]"
[2] [Title](URL) - Brief description. Accessed YYYY-MM-DD.
    > "Verbatim excerpt that supports the claims citing [2]"
...
```

## Step 6: Verify Every Claim

Before delivering, walk the report claim by claim:

1. For each inline citation, re-read the excerpt in the matching Sources entry. Does it actually support the claim as written? If not: fix the claim, fix the mapping, or re-fetch to find real support.
2. Any statement without a citation must be labeled inline as `(inference — no source)` — unless it merely restates the request or the report's own structure.
3. Confirm every Sources entry has a URL, an access date, and a verbatim excerpt.

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
- **Cite only sources you actually fetched** - search-result titles and snippets are leads, not sources
- **Every source entry carries an access date and a verbatim supporting excerpt** - claims must be verifiable without re-fetching
- **Label unsourced statements** as `(inference — no source)` - never present inference as sourced fact

# What NOT To Do

- Do NOT make claims without citations
- Do NOT give a single "right answer" - present the landscape
- Do NOT only show one side of debates
- Do NOT conflate old advice with current best practices
- Do NOT ignore minority viewpoints if they have valid rationales
- Do NOT present opinions as facts
- Do NOT cite a source you did not actually fetch
- Do NOT present inference as sourced fact - label it `(inference — no source)`
- Do NOT deliver without the Step 6 claim-by-claim verification pass
