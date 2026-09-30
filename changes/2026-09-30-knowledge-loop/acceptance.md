# Acceptance: executable knowledge loop

## Visible artifact

`scripts/knowledge_loop.py` and `tests/test_knowledge_loop.py` demonstrate:

```text
init -> ingest -> review -> query -> record-result
```

## Pass conditions

- Ingest reads only an explicit file or directory and leaves the source hash
  unchanged.
- Each accepted text source has an immutable raw snapshot, a candidate with
  `review_status: unreviewed`, and a source hash/reference.
- Only `approve` creates a reviewed asset; rejected or contradictory entries
  stay out of query results.
- Query returns deterministic keyword hits with source references and line
  citations, and writes JSON/Markdown receipts.
- `record-result` updates the application result and the visible Markdown
  receipt.
- Empty queries fail closed without writing a receipt.
- Source and package verification pass.

## Stop line

Stop after the local canary passes. Do not expand to a full-machine crawler,
semantic index, graph backend, or automatic Obsidian canonical writeback in
this change.

## Human gate

The first clean friend-vault canary must confirm whether the workflow is useful
and whether semantic retrieval is needed. That observation remains outside
this release until a person runs it.

## Rollback

Revert the `knowledge_loop.py` runner, its tests, the documentation/version
changes, and this change package. No source workspace or canonical vault is
modified by the package tests.
