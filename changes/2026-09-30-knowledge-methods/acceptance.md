# Acceptance: knowledge-methods baseline

## Visible artifact

`references/methods-benchmark.md` documents the research evidence, common
core, adoption/defer decisions, and the mapping to this Skill. `SKILL.md` and
`README.md` point to the baseline and make the operating loop discoverable.

## Pass conditions

- Every adopted rule has a public source URL and an explicit boundary.
- The baseline separates source, candidate, reviewed asset, memory, project,
  and application result.
- Retrieval guidance starts with deterministic/full-text recall and only then
  adds semantic, reranking, or graph context when justified.
- A user can run a bounded ingest/review/query loop without installing a vector
  database or sending personal files to a cloud service.
- Existing WeChat and canonical writeback boundaries remain unchanged.
- Repository verification and the official Skill validator pass.

## Stop line

Stop after the documented method baseline and portable contract are verified.
Do not add a watcher, full-machine scanner, graph database, or provider
integration in this change.

## Human gate

The first real friend-vault canary must confirm that the workflow is easier to
use and produces a useful cited answer. That result remains outside this
release until a human runs it.

## Rollback

Revert the research reference, its Skill/README links, the version bump, and
the focused regression test. No user vault or source data is touched.
