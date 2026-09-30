# Proposal: first-run onboarding

## Current fact

The v0.4.0 canary loop works from a checkout, but a new friend must infer how
to get that checkout, satisfy the Python requirement, locate emitted
candidates, and load the installed Skill into a fresh host session.

## Judgment to change

Make the path from public GitHub tag to a working local canary explicit and
observable without changing source privacy or canonical writeback boundaries.

## Scope

- Document clone, verify, install, host path, Python version, and fresh-session
  activation steps.
- Make `ingest` return the candidate paths a person or agent should review.
- Clarify that the runner preserves source text but does not perform AI
  synthesis, choose a category, or infer usefulness by itself.
- Bump the package to `0.4.1`.

## Non-goals

- No full-computer scan, live WeChat reader, cloud upload, or automatic
  canonical Obsidian writeback.
- No claim of friend adoption or useful results from a synthetic canary.

## Unknowns

- Whether a friend can complete install and first use without live assistance.
- Whether the agent host exposes the expected local filesystem and shell tools.
