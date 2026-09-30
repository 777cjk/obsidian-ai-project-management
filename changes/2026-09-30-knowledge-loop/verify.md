# Verification receipt: executable knowledge loop

Status: local package verification passed; real friend-vault canary and public
release remain external gates.

## Actual receipt

- `python3 -m unittest discover -s tests -v`: 18 tests passed.
- `python3 -m py_compile scripts/knowledge_loop.py`: passed.
- `git diff --check`: passed.
- Symlink boundary regressions pass: an explicitly selected symlink source and
  symlinked private output directory fail closed; receipts cannot target
  `manifest.json` or an invalid JSON document; same-second queries receive
  distinct receipt paths.
- The e2e test proves source hash preservation, raw snapshot, candidate review
  state, approved asset, contradictory/rejected exclusion, cited query receipt,
  and application-result writeback.
- A real local canary against one Obsidian project card completed `ingest ->
  approve -> keyword query -> record-result`; it produced an approved asset,
  a line-level citation, and `result_observed: yes`. Human usefulness remains
  `unknown` because no friend or independent user evaluated the result.
- No watcher, full-machine scanner, cloud connector, vector database, graph
  database, or automatic canonical writeback was added.
