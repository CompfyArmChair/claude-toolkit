---
name: research-deposit
description: 'Use when you are a deposit-aware research agent whose spawn prompt includes a "DEPOSIT: <path>" parameter — defines how to write full findings to disk and signal completion to the dispatching parent with a single minimal token. Not a trigger to start research; it governs how research output is delivered.'
---

# Research Deposit Protocol

You are a deposit-aware research agent. Your findings are delivered to disk, never echoed back through the parent's context.

## When this applies

Your spawn prompt includes a `DEPOSIT: <path>` parameter. That `<path>` is where your full findings must be written.

## Protocol

1. Conduct your research per your methodology skill.
2. Write your **full findings** to `<path>` using the `Write` tool — the complete report, not a summary.
3. SendMessage the dispatching parent (the manager) exactly:

       RESEARCH_DONE: <path>

   — that line and nothing else.
4. Do **not** echo findings into the message. Do **not** summarise back to the parent. The findings live on disk; the parent reads them from there (or hands the path to whoever needs them).

## If you cannot complete

If the research is blocked or only partially possible, still write what you gathered to `<path>`, then SendMessage:

    RESEARCH_BLOCKED: <path> — <one-line reason>

instead of `RESEARCH_DONE`.

## Why this matters

The whole point of deposit is to keep large findings out of the parent's (manager's) context: one token in (`DEPOSIT: <path>`), one token out (`RESEARCH_DONE: <path>`). Echoing findings into your reply defeats the protocol.
