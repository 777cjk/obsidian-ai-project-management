# Acceptance: knowledge loop hardening

## Visible artifact

The runner and its tests show that an explicit source can be ingested without
reading its own staging area, queried only within the requested scope, and
returned as cited evidence bounded by the requested context budget.

## Pass conditions

- Source/workspace overlap and symlink/private-tooling traversal fail closed.
- `.obsidian`, `.trash`, and `.vscode` are excluded from recursive ingest.
- Same label and relative filename under different source roots create distinct
  source identities.
- Missing files become `deleted`/`stale` and are absent from approved queries.
- `--scope`, positive `--limit`, and positive `--context-budget` are enforced.
- Partial ingest is visible and `--strict` exits non-zero when errors occur.
- Application observations append to `application_history` and preserve the
  latest `application` compatibility field.
- Existing lifecycle behavior and package verification remain green.

## Human gate

A friend must run one real query against their own selected sources and judge
whether the cited bounded answer is useful. That is not replaced by tests.

## Rollback

Revert the runner, regression tests, documentation/version changes, and this
package. No source workspace or canonical Vault is touched by the tests.
