# Proposal: executable knowledge loop

## Current fact

The package documented a source-to-asset method and a Query Receipt contract,
but only the source-to-candidate adapters were executable. Review, retrieval,
and application-result recording still depended on manual interpretation.

## Judgment to change

Prove the core lifecycle locally with a deterministic, dependency-free canary:
an explicitly selected source becomes a private raw snapshot, an unreviewed
candidate, an explicitly approved asset, a cited keyword answer, and an
application result receipt.

## Scope

- Add `scripts/knowledge_loop.py` with `init`, `ingest`, `review`, `query`, and
  `record-result` commands.
- Keep source bytes and generated outputs private to a caller-selected
  workspace; preserve hashes, source references, review states, and receipts.
- Add an end-to-end regression fixture and document the runnable commands.
- Bump the portable package to `0.4.0`.

## Non-goals

- No whole-computer scan, live WeChat reader, cloud upload, watcher, vector
  database, graph database, or automatic canonical Obsidian writeback.
- No claim that a deterministic keyword query proves semantic retrieval quality
  or friend-vault usefulness.

## Unknowns

- The friend-vault canary still needs a real user, real files, a real question,
  and a human usefulness judgment.
- Non-UTF-8 files and heavyweight document formats still use the separate
  `obsidian-knowledge-ingest` parser adapters.
