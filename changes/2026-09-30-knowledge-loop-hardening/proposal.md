# Proposal: knowledge loop hardening

## Current fact

The dependency-free runner proves the basic lifecycle, but several fields are
still documentary rather than operational: a source can overlap the staging
workspace, scope is not applied to retrieval, removed sources remain
queryable, and the context budget is recorded without bounding the returned
evidence. Application receipts also overwrite the previous observation.

## Judgment to change

The local canary must fail closed at the source boundary and make every
retrieval/application field truthful before we add semantic or graph layers.

## Scope

- Harden explicit source and workspace boundaries and exclude private/tooling
  directories from recursive ingest.
- Give source identity a stable root component so equal labels do not merge
  unrelated files.
- Mark removed sources stale/deleted and exclude them from approved retrieval.
- Apply `--scope`, validate positive limits, and produce bounded snippets with
  an enforced context budget.
- Make partial ingest explicit, support a strict failure mode, and preserve an
  append-only application history while keeping the latest field compatible.
- Add regression tests for each behavior and update the user-facing docs.

## Non-goals

- No full-machine crawler, live WeChat reader, watcher, vector database,
  graph database, cloud model, or automatic canonical Vault writeback.
- No claim that bounded keyword retrieval proves semantic quality or friend
  usefulness.

## Stop line

Stop after the focused and full verification suites pass. The next gate is a
clean friend-vault canary, not another infrastructure layer.
